# Phase 24 Specification: Rust Core Migration & Optimization

## 1. Overview
Current system uses a Python-based `ContextGuard` (Tier 1) which incurs significant overhead. This phase migrates the entire Guard logic to Rust (`theus_core`), implementing a **Tiered Optimization Model** to achieve "Industrial Grade" performance.

## 2. Current Architecture vs Target
**Current (Python):**
*   `ContextGuard` (Python) wraps everything.
*   Lists/Dicts are wrapped in `ContextGuard`.
*   Tensors are wrapped in `ContextGuard`.
*   Overhead: High (Python function calls for every access).

**Target (Rust - Tiered):**
*   **Tier 1 (Lists/Dicts):** `TrackedList` / `TrackedDict` (Already exists in `structures.rs`).
    *   *Action:* Ensure they are used. (Done in `guards.rs` logic).
*   **Tier 2 (Tensors - NEW):** `TheusTensorGuard`.
    *   *Action:* Create new struct wrapping Numpy/Torch tensors.
    *   *Features:* Zero-copy arithmetic (`+`, `-`, `*`), `shape`, `len`, `dtype`. Bypass Transaction Log for values (only log access/reference changes).
*   **Tier 3 (Generic Objects):** `ContextGuard` (Rust).
    *   *Action:* Enhance `guards.rs` to support Magic Methods (`__len__`, `__call__`, etc.) as a fallback proxy.

## 3. Implementation Plan

### 3.1. Create `src/tensor_guard.rs`
Define `TheusTensorGuard` using `pyo3` and `numpy` (or just strict `PyObject` proxying if we want to be library-agnostic).
Ideally, verify input type is "ndarray" or "Tensor".

```rust
#[pyclass]
pub struct TheusTensorGuard {
    inner: PyObject,
    path: String,
    tx: Option<Py<Transaction>>,
}

#[pymethods]
impl TheusTensorGuard {
    fn __add__(&self, other: PyObject) -> PyResult<PyObject> { ... }
    fn __len__(&self) -> usize { ... }
    // Implement full arithmetic suite
}
```

### 3.2. Update `src/guards.rs`
1.  **Modify `apply_guard`:**
    *   Detect if `val` is a Tensor (check type name "ndarray", "Tensor").
    *   Return `TheusTensorGuard` instead of `ContextGuard`.
2.  **Enhance `ContextGuard`:**
    *   Implement `__len__`, `__call__`, `__iter__`.
    *   Implement `__add__` et al. (Generic fallback using `PyObject::call_method1`).

### 3.3. Build & Switch
1.  Update `Cargo.toml` to include dependencies if needed.
2.  Run `maturin develop` or `pip install -e .` (Rust compilation).
3.  Update `contracts.py` to import `ContextGuard` from `theus_core`.

### 3.4. Technical Refinements (From Review)
1.  **Type Discovery Optimization:**
    *   Avoid string-based type checking (`val_type == "ndarray"`).
    *   Use **Cached Type References**: Import `numpy` and `torch` once (lazy static or module state) and use `val.is_instance(numpy_array_type)` for checking.
2.  **Memory Safety (GC Protocol):**
    *   `ContextGuard` holds a reference to `Transaction`, and `Transaction` holds references to Objects (Shadows). This creates Cycles.
    *   **Action:** Must implement `#[pyclass(gc)]` and `__traverse__` / `__clear__` protocols in Rust to allow Python's Cyclic GC to reclaim memory.

## 4. Performance Goals
*   **Attribute Access:** < 100ns (vs ~500ns Python).
*   **Tensor Arithmetic:** Zero Overhead (Direct C Dispatch).
*   **Memory:** No Python Object allocation for every access (Rust structs are lighter).
*   **Leak Safety:** Zero leak in `Optimization_Sanity_Check` (verify via `tracemalloc`).

## 5. Verification
*   Re-run `Optimization_Sanity_Check`.
*   Expect run time to drop from ~2.5 mins/episode to < 30s/episode.
*   **Leak Test:** Monitor RSS memory usage over 1000 steps.
