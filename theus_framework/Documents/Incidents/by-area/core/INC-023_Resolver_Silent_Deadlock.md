---
id: INC-023
title: Resolver Silent Deadlock in Payload Validation
area: core
severity: critical
introduced_in: v2.0
fixed_in: pending
status: reopened
---

# INC-023: Resolver Silent Deadlock in Payload Validation

**Date:** 2026-03-07  
**Re-opened:** 2026-03-25  
**Component:** `theus.validator.AuditValidator`, `theus.engine.WorkflowEngine`  
**Severity:** Critical (Logic/State Freeze)  
**Author:** SNN System Integration Team  
**Status:** Reopened — Root Cause Incomplete

---

## 1. Executive Summary

Trong thực nghiệm "Multi-Agent Complex Maze" kéo dài 400 episodes (200.000 bước thời gian), hệ thống ghi nhận hiện tượng **Cognitive Freeze**: Cấu trúc mạng SNN (1024 nơ-ron) không có bất kỳ dấu hiệu học tập nào. Trung bình Firing Rate xấp xỉ 0 và giá trị Threshold giữ nguyên ở mức khởi tạo ($0.0504$).

Điều tra ban đầu (2026-03-07) xác định nguyên nhân là do Bootstrap defaults thiếu và đề xuất thêm Warning Flag ở Engine (v3.0.24). Tuy nhiên, điều tra lại (2026-03-25) xác nhận **lỗ hổng cốt lõi chưa được giải quyết**: `AuditValidator` vẫn thực hiện **Silent Bypass** — bỏ qua toàn bộ tiến trình mà không thông báo lỗi khi thiếu Input.

---

## 2. Phân tích Kỹ thuật & Nguyên nhân Gốc rễ

### 2.1 Vòng lặp Chết (Cognitive Freeze Loop)

Sự cố xảy ra theo chuỗi nhân quả sau:

```
T=0: Factory khởi tạo metrics = {}  (chưa có 'fire_rate')
     │
     ▼
T=1: Validator quét @process(inputs=['domain_ctx.snn_context.domain_ctx.metrics.fire_rate', ...])
     │  'fire_rate' KHÔNG tồn tại trong kwargs
     │
     ▼  validate_inputs() — validator.py:33
     │  continue  <─── Silent Bypass! Engine KHÔNG phát hiện lỗi
     │
     ▼
T=1: Engine gọi Process với input thiếu
     │  Process phát hiện thiếu, tự xử lý "Fault Tolerance"
     │  return None  (Silent Skip)
     │
     ▼
T=1: metrics['fire_rate'] KHÔNG BAO GIỜ được ghi
     │
     ▼
T=2: Lặp lại T=1 vĩnh viễn → Vòng lặp chết
     SNN không học, Threshold không cập nhật → Cognitive Freeze
```

### 2.2 Mã nguồn Gốc rễ: `validator.py`

```python
# theus/validator.py — Phương thức validate_inputs
def validate_inputs(self, process_name: str, rules: List, kwargs: dict):
    for rule in rules:
        field = rule.field
        if field not in kwargs:       # <─── Chỉ kiểm tra kwargs
            continue                  # <─── SILENT BYPASS (vấn đề cốt lõi)
        # ... logic validation tiếp theo cho field này
```

**Vấn đề:**
1. Chỉ kiểm tra `kwargs` (tham số trực tiếp) — **không** kiểm tra Context State
2. Khi field thiếu: dùng `continue`, Engine không nhận được bất kỳ Signal lỗi nào
3. Không có log, không có exception → "Silent Bypass" hoàn toàn

### 2.3 Điểm Gọi trong Engine: `engine.py`

```python
# theus/engine.py — _attempt_execute (khoảng dòng 750+)
if self._validator:
    self._validator.validate_inputs(func.__name__, rules, kwargs)
    # NOTE: Gọi validate_inputs nhưng KHÔNG truyền context vào
    # Validator không có cách nào biết Context có chứa data hay không
```

Validator nhận `kwargs` nhưng không nhận `context`, nên không thể kiểm tra xem field có tồn tại trong State hay chỉ đơn giản là chưa được truyền vào.

### 2.4 Trạng thái sau v3.0.24 (Warning Flag)

Bản vá v3.0.24 chỉ thêm một Warning log, nhưng **không thay đổi logic `continue`**:

```python
# Bản vá v3.0.24 — Chỉ thêm log, không sửa bypass
if field not in kwargs:
    logger.warning(f"Missing input '{field}' — skipping process")
    continue   # <─── VẪN BYPASS. Engine tiếp tục bình thường
```

Điều này có nghĩa là cơ chế "Silent Skip" vẫn còn nguyên vẹn sau bản vá.

---

## 3. Phương pháp Điều tra

### 3.1 Audit Điều tra Code (2026-03-25)

Nhóm Antigravity đã đọc trực tiếp mã nguồn `theus/validator.py` (134 dòng) và xác nhận:
- Dòng 33: `continue` khi field thiếu trong kwargs
- Không có bất kỳ cơ chế nào để kiểm tra Context State
- Không có bất kỳ exception raise nào trong happy path

### 3.2 Xác nhận từ FSM Rust (`src/fsm.rs`)

Rust FSM **truyền đúng exceptions** từ Python callback, xác nhận rằng nếu Validator raise exception, nó sẽ được Engine nhận. Vấn đề là Validator không bao giờ raise exception → Engine không biết có gì sai.

### 3.3 Quan hệ với INC-025

INC-025 (ContextGuard Bypass) và INC-023 cùng thể hiện tư tưởng "Fault Tolerance Over Explicit Failure":
- INC-023: Validator im lặng bypass process khi thiếu input
- INC-025: Process im lặng ghi dữ liệu qua backdoor không được theo dõi

Cả hai cần được resolve cùng nhau để chuyển hệ thống về tư tưởng **Strict Contract Enforcement**.

---

## 4. Phân tích Hậu quả

| Hậu quả | Biểu hiện | Mức độ |
|---|---|---|
| Cognitive Freeze | SNN không học, metrics đóng băng | Critical |
| Silent Deadlock | Engine không hang, nhưng kết quả rỗng | Critical |
| False Positive Log | Log cho thấy "process executed" nhưng không có gì xảy ra | High |
| Debug Nightmare | Không có stacktrace để trace lỗi | High |

---

## 5. Resolution Strategy (Chưa triển khai)

### 5.1 Tầng Validator (`theus/validator.py`)

**Thay đổi cốt lõi**: Thay `continue` bằng `raise ContractViolationError`:

```python
# Hướng đi đề xuất
def validate_inputs(self, process_name: str, rules: List, kwargs: dict, context=None):
    for rule in rules:
        field = rule.field
        
        # Bước 1: Kiểm tra trong kwargs
        if field in kwargs:
            # Validate type, range, etc.
            continue
            
        # Bước 2: Kiểm tra trong Context (nếu có)
        if context is not None:
            ctx_val = self._resolve_from_context(context, field)
            if ctx_val is not None:
                continue
                
        # Bước 3: Field thực sự thiếu → Không chấp nhận
        raise ContractViolationError(
            f"Process '{process_name}': Required input '{field}' "
            f"not found in kwargs or context. "
            f"This is a Contract Violation, NOT a runtime warning."
        )
```

### 5.2 Tầng Engine (`theus/engine.py`)

Cần truyền context vào validate_inputs:

```python
# Tại điểm gọi _attempt_execute
self._validator.validate_inputs(
    func.__name__, 
    rules, 
    kwargs,
    context=self._context  # Thêm context để Validator có thể kiểm tra State
)
```

### 5.3 Tầng Process (`snn_homeostasis_theus.py`)

Khi Validator được nâng cấp, cần xóa bỏ các "Fault Tolerance" guards thủ công:

```python
# Trước (Manual Silent Skip)
def process_homeostasis(ctx):
    if ctx.domain_ctx.snn_context is None:
        return None  # Manual bypass

# Sau (rely on Validator)
def process_homeostasis(ctx):
    # Validator đã đảm bảo snn_context tồn tại trước khi gọi
    snn_ctx = ctx.domain_ctx.snn_context
    # ...
```

---

## 6. Triết lý Thiết kế (Design Philosophy)

### Vì sao "Silent Bypass" từng là hợp lý?

Trong giai đoạn đầu phát triển, Engine Theus ưu tiên **Fault Tolerance**: thà bỏ qua một process còn hơn crash toàn bộ simulation. Đây là quyết định hợp lý khi State còn không ổn định (INC-020, INC-022).

### Vì sao cần chuyển sang "Strict Contract"?

Khi hệ thống đã trưởng thành (Engine v3.0.26+), "Silent Bypass" trở thành **kẻ thù của Observability**:
- Rất khó debug vì không có stacktrace
- Tạo ra kết quả sai mà log cho thấy "thành công"
- Phá vỡ tính chính xác khoa học của các thử nghiệm ML

Tham khảo thêm: INC-025 (Context Bypass) cùng tư tưởng.

---

## 7. Trạng thái Điều tra

- [x] Xác nhận bug gốc tại `validate_inputs` (continue statement, 2026-03-07)
- [x] Xác nhận bản vá v3.0.24 chưa đủ (chỉ log, không fix logic)
- [x] Kiểm tra FSM Rust: xác nhận Exceptions được truyền đúng
- [x] Điều tra quan hệ với INC-025
- [x] Phác thảo Resolution Strategy
- [ ] Plan triển khai chưa được duyệt

---
**Status:** Investigation Complete — Awaiting Implementation Approval  
**Assigned to:** Antigravity Team  
**Related:** INC-025, INC-020

