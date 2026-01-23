use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, RwLock};

// FEASIBILITY KEY 1: Holding PyObject Refs in Rust Struct
struct SafePyRef(Py<PyAny>);

// Manual Clone Implementation required because Py<T> clone_ref needs Python GIL
// BUT here we just want to clone the struct itself.
// Actually Py<T> is Clone. The issue might be deriving Clone on a struct used in Ar<RwLock<...>>?
// Let's implement Clone manually to be safe and use py.clone_ref() if needed,
// OR just rely on Py<T> being a pointer.
// Py<T> implements Clone (increments refcount).
// Manual Clone Implementation: Removed because Py<T> clone requires GIL or specific context.
// HashMap values do not need to be Clone basically.
// If we need to clone the struct, we should do it explicitly with GIL.

// Rust requires explicit Send/Sync for Py<T> if you want to share it across threads.
// PyO3's Py<T> IS Send, but we wrap it to be explicit about our "Gatekeeper" role.
unsafe impl Send for SafePyRef {}
unsafe impl Sync for SafePyRef {}

#[pyclass]
struct NanoSupervisor {
    // The "Supervisor State": Map of Key -> (Lock, PyRef)
    // We use RwLock to prove we can gate access.
    heap: Arc<RwLock<HashMap<String, SafePyRef>>>,
}

#[pymethods]
impl NanoSupervisor {
    #[new]
    fn new() -> Self {
        NanoSupervisor {
            heap: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    // FEASIBILITY KEY 5: Atomic Write
    fn set(&self, py: Python, key: String, val: PyObject) -> PyResult<()> {
        let mut heap = self.heap.write().map_err(|_| {
            pyo3::exceptions::PyRuntimeError::new_err("Lock Poisoned")
        })?;
        
        // "Gatekeeper" Logic could go here (e.g. check key permission)
        heap.insert(key, SafePyRef(val));
        Ok(())
    }

    // FEASIBILITY KEY 3: Rust Reading PyObject (Reference Zero Copy)
    fn get(&self, py: Python, key: String) -> PyResult<Option<PyObject>> {
        let heap = self.heap.read().map_err(|_| {
            pyo3::exceptions::PyRuntimeError::new_err("Lock Poisoned")
        })?;

        if let Some(safe_ref) = heap.get(&key) {
            // Return a new reference (Clone the PyPtr, not the data)
            // This is O(1)
            Ok(Some(safe_ref.0.clone_ref(py))) 
        } else {
            Ok(None)
        }
    }
}

pub fn register(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<NanoSupervisor>()?;
    Ok(())
}
