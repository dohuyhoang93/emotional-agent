---
id: INC-025
title: ContextGuard Bypass via _inner/_target (Silent Data Loss & Performance Risk)
area: core
severity: critical
introduced_in: v3.0.23 (Workaround cho INC-020)
fixed_in: pending
status: investigating
---

# INC-025: ContextGuard Bypass via `_inner`/`_target` (Silent Data Loss)

**Date:** 2026-03-25  
**Component:** `theus.guards.ContextGuard`, `src/processes/snn_dream_processes.py`, `src/coordination/multi_agent_coordinator.py`  
**Severity:** Critical (Data Loss + Security Hole)  
**Author:** Antigravity Investigation Team  
**Status:** Investigating

---

## 1. Executive Summary

Trong các vòng lặp mô phỏng có kích hoạt phase Dream (Sleep Cycle), hệ thống ghi nhận **Silent Data Loss**: mặc dù log nội bộ của quy trình cho thấy các tham số như `dream_reward` và `dream_firing_rate` được tính toán thành công, các giá trị này **không bao giờ xuất hiện** trong State cuối cùng của Episode.

Nguyên nhân gốc rễ được xác định là do cơ chế **ContextGuard Bypass** — Các quy trình truy cập trực tiếp đối tượng Python thô qua thuộc tính `_inner` và `_target`, bỏ qua hoàn toàn cơ chế theo dõi Delta của `ContextGuard`. Đây vốn là một Workaround tạm thời được đưa vào để tránh crash COW (`INC-020`), nhưng đã trở thành một lỗ hổng kiến trúc nghiêm trọng.

---

## 2. Phân tích Kỹ thuật & Nguyên nhân Gốc rễ

### 2.1 Kiến trúc ContextGuard (Đúng)

```
Process Code
    │
    ▼  __setattr__ / __setitem__
ContextGuard (Python Wrapper)
    │  Chain of Custody
    │  ─ Zone Physics (const_, internal_)
    │  ─ Contract Check (allowed_outputs)
    ▼
SupervisorProxy (Rust)
    │  Delta Logging
    │  ─ log_internal(path, "SET", ...)
    ▼
Transaction (Rust)
    │  Delta Registry
    ▼
Engine Commit  ──►  State Update Permanent
```

### 2.2 Con đường Bypass (Thực trạng)

Các quy trình hiện tại đang "vượt rào" bằng cách truy cập trực tiếp:

```python
# snn_dream_processes.py — Phát hiện tại Lines 49-53, 114-118
target = getattr(ctx, '_target', None)       # <--- Lấy object thô
dc = getattr(target, 'domain_ctx', None)     # <--- Bỏ qua Guard
snn_ctx = getattr(dc, 'snn_context', None)   # <--- Không qua Proxy
# ...
domain.metrics['dream_reward'] = reward      # <--- MUTATION KHÔNG ĐƯỢC THEO DÕI
```

Khi mutation xảy ra trực tiếp trên raw Python object, toàn bộ lớp Delta Tracking bị bỏ qua:

```
Process Code
    │  getattr(_target)
    ▼  (Ctrl+Alt+Delete Chain)
Python Raw Object  ──►  mutation xảy ra trong bộ nhớ Python
                         NHƯNG Transaction KHÔNG biết
                         NHƯNG SupervisorProxy KHÔNG biết
                         ──►  Engine commit ghi đè/bỏ qua
```

### 2.3 Các vị trí bị ảnh hưởng

| File | Dòng | Bypass Type | Dữ liệu bị mất |
|---|---|---|---|
| `src/processes/snn_dream_processes.py` | 49-53 | `getattr(ctx, '_target', None)` | `snn_context` mutations |
| `src/processes/snn_dream_processes.py` | 114-118 | `getattr(ctx, '_target', None)` | `domain.metrics` |
| `src/coordination/multi_agent_coordinator.py` | ~113 | `._inner` unwrapping | System context |

### 2.4 Lý do Bypass Được Đưa Vào (Context từ INC-020)

Khi Engine v3.0.20-23 còn bị lỗi COW (Copy-On-Write) panic khi truy cập nested context phức tạp (`snn_context` chứa Tensor và Numpy array), nhóm phát triển đã dùng `_target` làm lối thoát tạm thời. Điều này đã được ghi nhận tại:

- `src/orchestrator/context_helpers.py` — file đã bị disabled hoàn toàn
- Các inline fallback còn sót lại tại `snn_dream_processes.py`

---

## 3. Phân tích Hiệu năng (Performance Investigation)

Câu hỏi đặt ra: **Nếu khóa `_target`, các phép ghi dữ liệu lớn (NumPy/SHM) có bị giảm hiệu năng?**

### 3.1 Cơ chế HEAVY Zone (Đã tích hợp sẵn)

Kết quả điều tra xác nhận rằng nhân Rust (`src/guards.rs` và `src/zones.rs`) **đã tự động bỏ qua Delta Logging cho vùng `HEAVY`**:

```rust
// src/guards.rs:380 — __setattr__
if zone != ContextZone::Heavy {
    // Chỉ ghi Delta cho các zone KHÁC  
    tx_ref.log_internal(full_path, "SET", ...)?;
}
// Heavy zone: mutation thực trực tiếp KHÔNG qua Delta
```

Tương tự, `src/zones.rs` đảm bảo `heavy_` prefix luôn resolve về `ContextZone::Heavy`:

```rust
if segment.starts_with("heavy_") || segment == "heavy" {
    return ContextZone::Heavy;
}
```

### 3.2 Bottleneck Thực sự: Python `_deep_unwrap`

Mặc dù Rust đã tối ưu HEAVY zone ở tầng engine, tại lớp Python Wrapper (`theus/guards.py`), hàm `_deep_unwrap` vẫn được gọi đệ quy cho **mọi lần ghi**, bao gồm cả HEAVY:

```python
# guards.py __setattr__ / __setitem__ — Gọi trước khi kiểm tra Zone
def _deep_unwrap(v):
    if isinstance(v, ContextGuard):
        return _deep_unwrap(v._inner)   # Đệ quy toàn bộ
    if isinstance(v, dict):
        return {k: _deep_unwrap(sub_v) for k, sub_v in v.items()}  # O(N) trên mọi dict
    if isinstance(v, list):
        return [_deep_unwrap(sub_v) for sub_v in v]  # O(N) trên mọi list
    return v

value = _deep_unwrap(value)  # Được gọi TRƯỚC khi biết đây là HEAVY zone
```

Đây là nơi tạo ra chi phí thực sự khi ghi dữ liệu lớn — **không phải do Delta Tracking**.

### 3.3 Kết luận Hiệu năng

- `_target` bypass **không cần thiết** để tối ưu hiệu năng cho HEAVY data
- Python `_deep_unwrap` là bottleneck cần được tối ưu riêng (Shallow Unwrap cho HEAVY)
- Việc sử dụng `_target` như một "optimization" là sai lầm về mặt kiến trúc

---

## 4. Impact Assessment

| Loại Impact | Mô tả | Mức độ |
|---|---|---|
| Silent Data Loss | Metrics SNN bị mất sau mỗi Dream Cycle | Critical |
| Security Hole | Bypass hoàn toàn IO Contract + Zone Physics | Critical |
| Cognitive Drift | Agent log "học xong" nhưng thực tế Brain State không thay đổi | High |
| Maintainability | Code phân tán với bypass pattern khó debug | Medium |
| Performance Risk | `_deep_unwrap` O(N) có thể gây chậm với dữ liệu lớn | Medium |

---

## 5. Resolution Strategy

### 5.1 Tầng Python Wrapper (`guards.py`)

**Vấn đề A: Chặn truy cập `_target` từ User-Space**
- Hiện tại: `_inner` và `_target` nằm trong whitelist `__getattr__`, cho phép truy cập tự do
- Rust Guard (`src/guards.rs:307-321`) đã chặn `_`-prefixed attrs khi `strict_guards=True`, nhưng Python Wrapper chưa áp dụng tương đương
- Cần đồng bộ hóa: Python Wrapper phải block `_inner`/`_target` khi `_strict_guards=True`

**Vấn đề B: `_deep_unwrap` Performance**
- Áp dụng **Shallow Unwrap** cho HEAVY zone: chỉ unwrap một lớp Guard ngoài cùng
- Bỏ qua đệ quy vào nội dung dict/list khi biết đây là HEAVY assignment

### 5.2 Tầng Process Code

- `snn_dream_processes.py`: Loại bỏ toàn bộ fallback `_target` logic
- Thay thế bằng Explicit Return cho các trường `metrics` cần cập nhật
- Khai báo đầy đủ `outputs=['domain_ctx.metrics']` trong Contract

### 5.3 Tầng Engine (`validator.py` + `engine.py`)

Xem INC-023 để biết chi tiết về Strict Input Validation — hai INC này cần được resolve song song.

---

## 6. Trạng thái Điều tra

- [x] Xác nhận vị trí bypass trong `snn_dream_processes.py`
- [x] Xác nhận vị trí bypass trong `multi_agent_coordinator.py`  
- [x] Điều tra tác động đến hiệu năng HEAVY zone
- [x] Xác nhận Rust Core đã tối ưu HEAVY zone sẵn
- [x] Phát hiện bottleneck thực sự (`_deep_unwrap`)
- [ ] Plan triển khai chưa được duyệt

---
**Status:** Investigation Complete — Awaiting Implementation Approval  
**Assigned to:** Antigravity Team  
**Related:** INC-020, INC-023
