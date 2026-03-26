---
id: INC-022
title: SupervisorProxy Root Zone Escape (Global State Mutation Leak)
area: core
severity: critical
introduced_in: v3.0
fixed_in: v3.3
status: resolved
---

# INC-022: SupervisorProxy Root Zone Escape (Global State Mutation Leak)

**Date:** 2026-03-24  
**Component:** `theus/guards.py` · `src/proxy.rs` · `src/structures.rs`  
**Severity:** Critical (Data Integrity Compromise / Transaction Rollback Bypass)  
**Author:** Do Huy Hoang (Antigravity Assistant)  
**Status:** Resolved  

---

## 1. Executive Summary

Trong Theus v3, cơ chế phòng ngự (ContextGuard & SupervisorProxy) được thiết kế nhằm áp dụng Zero Trust Mutation và Transaction Rollback. Tuy nhiên, khi một process thực thi gán giá trị ở trực tiếp root level của Zone (ví dụ `ctx.domain['counter'] = 999`), hệ thống đã vô tình thay đổi **trực tiếp biến Global State Dictionary** thay vì tạo ra Transaction Shadow Copy.

Hậu quả là: Nếu transaction bị rollback (do code crash hoặc vi phạm quyền), dữ liệu bị sửa sẽ tồn tại trong bộ nhớ RAM vĩnh viễn, dẫn đến rò rỉ trạng thái giữa các process và phá vỡ kiến trúc Isolation & Immutability của Theus v3. Lỗi này đặc biệt nghiêm trọng bởi nó xuyên thủng lớp phòng thủ sâu nhất của Transaction.

---

## 2. Background

Hệ thống Theus v3 giới thiệu hai lớp phòng thủ:
1. **Python `ContextGuard`:** Lớp ngoài cùng, chặn các truy cập không hợp lệ theo Contract và cung cấp API Pythonic.
2. **Rust `SupervisorProxy`:** Lớp trong cùng, bọc đối tượng thư viện, kiểm soát capability theo bitmask (`CAP_READ`, `CAP_UPDATE`) và tự động kích hoạt bóng mờ (Shadow Copy) thông qua CoW Differential Shadowization khi có Transaction.

Thiết kế ban đầu: Khảo sát cho thấy khi người dùng truy cập field lồng nhau (`ctx.domain['nested'].append(...)`), `SupervisorProxy.__getitem__` hoạt động đúng bằng cách gọi `tx.get_shadow()` và trả về proxy của shadow object. Mọi mutation chỉ xảy ra trên shadow. Nếu transaction thành công, shadow diff sẽ được merge.

---

## 3. What Went Wrong

### Bug A — Thiếu Track Alias `domain_ctx` ở Lớp Python
**File:** `theus/guards.py`
Trong thiết kế mới, Rust cung cấp 2 alias an toàn là `domain_ctx` và `global_ctx`. Tuy nhiên, code Python của `ContextGuard.__getattr__` chưa được cập nhật để track 2 alias này vào danh sách *Special Attributes*. Khi process tiến hành gọi `ctx.domain_ctx`, nó bypass hoàn toàn lớp bảo vệ `ContextGuard` của vòng ngoài và tương tác với raw `SupervisorProxy` từ lõi.

### Bug B — `SupervisorProxy` Gán Trực Tiếp Vào Root Zone (Bypass Shadow)
**File:** `src/structures.rs` · `src/proxy.rs`
Hàm getter của `ProcessContext.domain` và `global` trong Rust luôn trả về `SupervisorProxy` wrap **chính đối tượng Arc** thay vì gọi shadow copy, dù process đang nằm trong transaction. Khi lệnh gán top-level (`ctx.domain['key'] = val`) được user gọi, `SupervisorProxy.__setitem__` thực thi:
```rust
self.inner.call_method1(py, "__setitem__", (key, value))?;
```
Do `self.inner` của Root Proxy trỏ trực tiếp tới `Arc<PyObject>` gốc của Shared State, dictionary này bị thay đổi In-place trên toàn hệ thống. Mặc dù Engine sau đó có throw Exception (do Contract Valdiations phát hiện sai số Output Deltas) và throw bỏ transaction, State gốc đã bị ô nhiễm do `self.inner` vừa lỡ thay đổi ở cấp độ con trỏ Python gốc.

---

## 4. Root Cause Analysis (@integrative-critical-analysis & @systems-thinking-engine)

### Micro Root Cause (Mental Model Error)
Mô hình tư duy ban đầu giả định: *"Mọi đối tượng được bọc bởi `SupervisorProxy` sẽ an toàn vì proxy sở hữu lệnh kiểm tra transaction"*. 
**Chỗ sai:** Đã nhầm lẫn giữa *ủy quyền thay đổi (capability check)* và *cách lưu trữ sự thay đổi (memory layer)*. Khung thiết kế kiến tạo ra hàm `get_shadow` cho phép tạo màng bảo vệ ở các nhánh con (children dict/list) thông qua `__getitem__`, nhưng lại mù quáng quên đi kịch bản thay đổi ở **ngay gốc (root)**. Nếu gán ở gốc (`__setitem__` trên proxy ngoài cùng), `get_shadow` chưa bao giờ được kích hoạt, proxy xé rào vào state gốc để ghi đè.

### Macro Root Cause (Structural / Feedback Loop)
**Symptom of Optimization vs. Safety:** Hệ thống được cấu trúc nhắm đến hiệu năng phi thường thông qua Differential Shadowization nhằm *tái sử dụng bộ nhớ*, chỉ copy những phần nào thực sự bị chạm tới, giữ nguyên cây bộ nhớ gốc đồ sộ (CoW).
Hệ quả: Ranh giới phòng thủ (Guard Boundary) bị đẩy lại phía sau lưng Root Proxy. Thay vì copy nông (shallow copy) State Sector khi khởi động Transaction (an toàn nhưng bị thừa thãi), Theus "chủ quan" đưa State gốc vào Proxy. Feedback loop ở đây: Vì muốn kiến trúc engine nhanh triệt để (chỉ record deltas), Theus trao thẳng "Arc Reference Global State" cho Root Proxy. Khi `__setitem__` hở sườn get_shadow, thảm hoạ xảy ra.
Việc hệ thống test cũ (`test_transaction_rollback.py`) chỉ tập trung vào `.append()` (thuộc nhánh inner) tạo ra bức tranh giả rằng CoW của Theus không thể sai lầm.

---

## 5. Ethical & Epistemic Audit (@intellectual-vitures)

- **Humility (Khiêm tốn):** Nhận lỗi rằng có một "niềm tin thái quá" vào bức tường thành mang tên Theus Guard Rules, dẫn tới việc Core Logic bị sơ suất ở vùng Root Access. Sự thật là test case cũ đã không cover toàn diện các góc tối.
- **Courage (Dũng cảm):** Giải quyết Root Leak bằng cách can thiệp sâu sát vào logic vòng kín của `structures.rs` và Rust PyO3 Memory Cycle của Theus Core `[FIX v3.3]`, thay vì viết patch che giấu bằng Python (shallow patches trên vòng tuần hoàn ContextGuard).
- **Integrity (Chính trực):** Định danh lỗi này ở mức độ Critical, bởi nó đánh vỡ trụ cột Immutability State của Engine.

---

## 6. Comprehensive Analysis & Resolution Plan

### Immediate Fix & Structural Fix (Surgical Resolution)

1. **Vá lỗ hổng Aliases [Python]:**
   Chỉnh sửa tại `theus/guards.py`, thêm `"domain_ctx", "global_ctx"` vào tuple special properties. Đảm bảo toàn bộ tương tác đều đi vòng qua sự kiểm soát an ninh của tầng `ContextGuard` như dự phòng.

2. **Ép Buộc Shadowing cho Root Zones (The Cure) [Rust]:**
   Tiêm quy tắc ở lõi Rust: Viết lại `#[getter] fn domain` và `fn global` trong Struct thư viện `ProcessContext` (`src/structures.rs`). Bất kì khi nào hệ thống lấy Sector Root khi Transaction đang tồn tại (`tx.is_some()`), bắt buộc khởi tạo Shadow Copy cho cả Root Dictionary.
   ```rust
   let inner_val = if let Some(ref tx_obj) = tx_opt {
       match tx_obj.bind(py).call_method1("get_shadow", (arc_val, Some("domain"))) { ... }
   } else { ... }
   ```
   *Thành quả:* `self.inner` của Root Proxy đã nắm bóng mờ (Shadow) nằm trong transaction thay vì nắm Reference thật của Global Arc. Bất kỳ lệnh `__setitem__` cấp cao nào đều chỉ ghi dấu trên bóng mờ một cách vô hại.

3. **Cập Nhật Test Script `[Process]`:**
   Tối ưu file manual verification `tests/manual/verify_domain_ctx_leak.py` để bổ sung block `try-except` ôm lấy logic call `engine.execute`, bắt sạch `ContractViolationError` quăng lại từ tầng Validations do Strict Mode được trigger.

---

## 7. Preventive Actions & Architecture Update

1. **Preventive (Vaccine):** 
   Bộ Local CI (`scripts/Local_CI.py full`) đã được gắn chốt Manual Script Verification `verify_domain_ctx_leak.py`. Kiểm soát mọi khả năng regressive-bug cho lỗi in-place Top-Level Memory Leak.
2. **Kiến trúc (ADR / Memory Safety Pattern):**
   *Mọi đối tượng đầu vào từ Global State (kể cả root) khi map vào Transaction Context MUST được dẫn tuyến đi qua `get_shadow`.* Theus Core Architectures ban lệnh cấm truyền trực tiếp reference `Arc<PyObject>` vào Mutable Supervisor Proxies để làm inner variable.

---

## 8. Verification

- `verify_domain_ctx_leak.py` passed: Báo cáo nhận giá trị `100` (thay vì 666/999) sau khi transaction mutates failing -> Global State was untouched, rollback triệt để.
- Được xác minh tự động bởi CI qua 341 Pytest Rules. (Tỷ lệ pass 100%)
- Rust Memory Borrow checker: `cargo clippy -- -D warnings` Success.
