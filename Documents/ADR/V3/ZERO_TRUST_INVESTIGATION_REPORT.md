# Báo Cáo Điều Tra: Zero Trust State Mutation

**Ngày:** 2026-01-27  
**Phiên bản Theus:** 3.0.22  
**Trạng thái:** 🔴 Chưa hoàn thành - Phát hiện vấn đề kiến trúc sâu

---

## 1. Mục Tiêu Ban Đầu

Xác minh rằng Theus Framework thực thi **"Zero Trust Memory"** - nghĩa là:
- Mọi mutation (thay đổi state) phải được **logged** (ghi lại).
- Transactions thất bại phải được **rollback** hoàn toàn (không để lại tác dụng phụ).
- Mutations qua Proxy phải hoạt động như mutations qua `tx.update()`.

## 2. Test Cases

Script `verify_universal_mutation.py` kiểm tra 6 kịch bản:

| Test | Mô tả | Kết quả |
|------|-------|---------|
| 1 | Functional Pattern (return output) | ✅ PASS |
| 2 | Idiomatic Zero Trust (Proxy Mutation) | ❌ FAIL |
| 3 | Explicit API (`tx.update()`) | ✅ PASS |
| 4 | Audit Violation (Read-Only Enforcement) | ✅ PASS |
| 5 | Idiomatic Rollback (Mutation then Crash) | ❌ FAIL |
| 6 | Explicit Rollback (`tx.update()` then Crash) | ✅ PASS |

---

## 3. Các Vấn Đề Phát Hiện & Sửa Chữa

### 3.1 Transaction Struct Thiếu Fields (✅ ĐÃ SỬA)

**Vấn đề:** `Transaction` struct trong `engine.rs` thiếu `delta_log` và `shadow_cache`.

**Nguyên nhân:** Merge code không hoàn chỉnh từ các phiên trước.

**Giải pháp:** Thêm fields và khởi tạo trong cả 2 constructors:
```rust
pub delta_log: Arc<Mutex<Vec<DeltaEntry>>>,
pub shadow_cache: Arc<Mutex<HashMap<usize, (PyObject, PyObject)>>>,
pub path_to_shadow: Arc<Mutex<HashMap<String, PyObject>>>,
```

---

### 3.2 DeltaEntry Không Implement Clone (✅ ĐÃ SỬA)

**Vấn đề:** `#[derive(Clone)]` thất bại vì `Py<PyAny>` không implement `Clone`.

**Giải pháp:** Implement manual Clone với `Python::with_gil`:
```rust
impl Clone for DeltaEntry {
    fn clone(&self) -> Self {
        Python::with_gil(|py| {
            DeltaEntry {
                path: self.path.clone(),
                value: self.value.as_ref().map(|v| v.clone_ref(py)),
                // ...
            }
        })
    }
}
```

---

### 3.3 ProcessContext Thiếu Transaction Getter (✅ ĐÃ SỬA)

**Vấn đề:** Python side không thể access `ctx.transaction`.

**Nguyên nhân:** Field `tx` không được expose qua `#[getter]`.

**Giải pháp:** Thêm getter trong `structures.rs`:
```rust
#[getter]
fn transaction(&self, py: Python) -> Option<PyObject> {
    self.tx.as_ref().map(|t| t.clone_ref(py).into_py(py))
}
```

---

### 3.4 ContextGuard Không Shadow Dict (✅ ĐÃ SỬA)

**Vấn đề:** `apply_guard` trong `guards.rs` wrap raw dict không qua `get_shadow`.

**Nguyên nhân:** Logic chỉ shadow Objects và Nested Proxies, bỏ qua plain `dict`.

**Giải pháp:** Thêm `get_shadow` call cho dict type:
```rust
if type_name == "dict" {
    let shadow = tx_bound.borrow_mut().get_shadow(py, val, Some(full_path))?;
    // wrap shadow in SupervisorProxy
}
```

---

### 3.5 Shallow Copy Gây State Leak (✅ ĐÃ SỬA)

**Vấn đề:** `copy.copy()` chỉ shallow copy container, inner dicts vẫn shared.

**Debug Output:**
```
get_shadow COPY: domain (Original: X1, Shadow: X2)
get_shadow COPY: domain.data (Original: Y1, Shadow: Y2)  
# Y1 là child của X1, Y2 là child của X2
# Mutation tới Y2 không ảnh hưởng X2 (Correct!)
# Nhưng nếu commit X2, nó chứa Y-original, không phải Y2!
```

**Giải pháp:** Đổi sang `copy.deepcopy()`:
```rust
let shadow = copy_mod.call_method1("deepcopy", (&val,))?;
```

---

### 3.6 SupervisorProxy Không Shadow Nested Objects (✅ ĐÃ SỬA)

**Vấn đề:** `__getattr__` và `__getitem__` trả về raw children không qua shadow.

**Nguyên nhân:** Logic cũ chỉ wrap trong Proxy, không gọi `tx.get_shadow()`.

**Giải pháp:** Thêm `get_shadow` call trong cả 2 methods:
```rust
let val_shadow = if let Some(ref tx) = self.transaction {
    match tx_bound.call_method1("get_shadow", (val, path)) {
        Ok(s) => s.unbind(),
        Err(_) => val
    }
} else { val };
```

---

### 3.7 CAS Không Nhận Proxy Mutations (✅ ĐÃ SỬA)

**Vấn đề:** `engine.py` commit dùng `tx.pending_data` - không chứa proxy mutations.

**Nguyên nhân:** Proxy mutations đi vào shadow objects, không vào `pending_data` dict.

**Giải pháp:** 
1. Thêm `path_to_shadow: HashMap<String, PyObject>` để track shadows theo path.
2. Thêm `get_shadow_updates()` method để extract root shadows cho commit.
3. Sửa `engine.py`:
```python
shadow_data = tx.get_shadow_updates()
self._core.compare_and_swap(start_version, data=shadow_data, ...)
```

---

## 4. Vấn Đề Kiến Trúc Chưa Giải Quyết 🔴

### 4.1 Shadow Caching Conflicts

**Debug Output:**
```
delta_log.len=2, path_to_shadow.len=1
delta_log entry: path=domain.data[idiomatic]
delta_log entry: path=domain.data.idiomatic_update
path_to_shadow entry: root=domain
get_shadow_updates returning: {'domain': {'data': {'functional': 'Success'}}}
                                          # MISSING 'idiomatic' và 'idiomatic_update'!
```

**Root Cause:**
1. **Test 1 (Functional):** Tạo shadow cho 'domain', commit thành công.
2. **Test 2 (Idiomatic):** Engine tạo Transaction MỚI.
3. Transaction mới có `path_to_shadow` mới (empty), nhưng `get_shadow()` được gọi từ Proxy **sử dụng Transaction của Test 2**.
4. Shadow được tạo với path='domain' (root), stored trong Transaction 2.
5. Mutations (`domain.data['idiomatic']`) logged vào `delta_log`.
6. **NHƯNG:** Shadow của 'domain' trong `path_to_shadow` là **deepcopy tại thời điểm Test 2 bắt đầu**, không chứa mutations từ Test 1.
7. Khi commit, `get_shadow_updates()` trả về shadow cũ (without 'idiomatic').

**Giải thích đơn giản:**
- Shadow được tạo **trước** khi mutation xảy ra.
- Mutation đi vào **nested shadow** (`domain.data`).
- Commit lấy **root shadow** (`domain`) - không chứa nested mutation.

---

## 5. Giải Pháp Đề Xuất

### Option A: Delta Replay (Recommended)

Thay vì track shadows, replay `delta_log` lên State hiện tại khi commit:

```python
def commit():
    current_state = engine.state.data.to_dict()  # Fresh copy
    for delta in delta_log:
        set_nested_value(current_state, delta.path, delta.value)
    compare_and_swap(data=current_state)
```

**Ưu điểm:** Đơn giản, reliable, không cần shadow tracking.  
**Nhược điểm:** Không detect conflicting mutations (2 processes mutate same path).

### Option B: Full State Shadow

Deepcopy toàn bộ State vào Transaction ngay khi tạo:

```python
def __init__(self, engine):
    self._shadow_state = copy.deepcopy(engine.state.data.to_dict())
```

**Ưu điểm:** Isolation hoàn toàn, hỗ trợ conflict detection.  
**Nhược điểm:** Memory overhead với large states.

### Option C: Path-Tracking Shadow (Current Approach - Broken)

Track từng path được access và shadow riêng. Hiện không hoạt động vì nested mutation propagation.

---

## 6. Các Files Đã Sửa Đổi

| File | Thay đổi |
|------|----------|
| `src/engine.rs` | Transaction struct, `get_shadow()`, `get_shadow_updates()`, constructors |
| `src/delta.rs` | Manual Clone impl |
| `src/structures.rs` | `ProcessContext.transaction` getter |
| `src/guards.rs` | Dict shadowing trong `apply_guard` |
| `src/proxy.rs` | `__getattr__`, `__getitem__` shadowing |
| `theus/engine.py` | Commit logic với `get_shadow_updates()` |

---

## 7. Kết Luận

### Đã Xác Nhận:
1. ✅ Delta logging hoạt động (mutations được log).
2. ✅ Shadow creation hoạt động (deepcopy tạo isolated copies).
3. ✅ Path extraction hoạt động (root paths retrieved correctly).
4. ❌ **Shadow propagation KHÔNG hoạt động** - nested mutations không propagate lên root shadow.

### Cần Quyết Định:
Chọn Option A (Delta Replay) hoặc Option B (Full State Shadow) để hoàn thành Zero Trust Memory.

---

**Người thực hiện:** Gemini/Antigravity  
**Thời gian:** ~1 giờ debugging
