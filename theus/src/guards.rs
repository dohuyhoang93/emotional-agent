use pyo3::prelude::*;
use pyo3::exceptions::PyPermissionError;
use pyo3::types::PyAny;
use crate::delta::Transaction;
use std::sync::{Arc, Mutex};

#[pyclass]
pub struct ContextGuard {
    #[pyo3(get, name = "_target")]
    target: PyObject,
    allowed_inputs: Vec<String>,
    allowed_outputs: Vec<String>,
    path_prefix: String,
    tx: Py<Transaction>, 
    is_admin: bool,
}

impl ContextGuard {
    pub fn new_internal(target: PyObject, inputs: Vec<String>, outputs: Vec<String>, tx: Py<Transaction>, is_admin: bool) -> Self {
         ContextGuard {
            target,
            allowed_inputs: inputs,
            allowed_outputs: outputs,
            path_prefix: "".to_string(),
            tx,
            is_admin,
        }
    }

    fn check_permissions(&self, full_path: &str, is_write: bool) -> PyResult<()> {
        if self.is_admin { return Ok(()); }
        
        let is_ok = if is_write {
             self.allowed_outputs.iter().any(|rule| {
                rule == full_path || 
                rule.starts_with(&format!("{}.", full_path)) || 
                full_path.starts_with(&format!("{}.", rule)) || 
                full_path.starts_with(&format!("{}[", rule))
             })
        } else {
             // Read: Check Inputs OR Outputs (implicit read for output path traversal)
             self.allowed_inputs.iter().chain(self.allowed_outputs.iter()).any(|rule| {
                rule == full_path || 
                rule.starts_with(&format!("{}.", full_path)) || 
                full_path.starts_with(&format!("{}.", rule)) || 
                full_path.starts_with(&format!("{}[", rule))
             })
        };

        if !is_ok {
            let op = if is_write { "Write" } else { "Read" };
            return Err(PyPermissionError::new_err(format!("Illegal {}: '{}'", op, full_path)));
        }
        Ok(())
    }

    fn apply_guard(&self, py: Python, val: PyObject, full_path: String) -> PyResult<PyObject> {
        let val_bound = val.bind(py);
        let type_name = val_bound.get_type().name()?.to_string();

        if ["int", "float", "str", "bool", "NoneType"].contains(&type_name.as_str()) {
             return Ok(val);
        }

        // Return callables (methods/functions) unwrapped to allow invocation
        // Note: This bypasses tracking for side-effects inside the method, but needed for compatibility.
        if val_bound.is_callable() {
             return Ok(val);
        }

        if type_name == "list" {
             let tx_bound = self.tx.bind(py);
             let shadow = tx_bound.call_method1("get_shadow", (&val, &full_path))?; 
             let structures = PyModule::import(py, "theus.structures")?;
             
             // Check if this path is allowed to be written
             let can_write = self.check_permissions(&full_path, true).is_ok();
             let cls_name = if can_write { "TrackedList" } else { "FrozenList" };
             
             let cls = structures.getattr(cls_name)?;
             return Ok(cls.call1((shadow, self.tx.clone_ref(py), full_path))?.unbind());
        }

        if type_name == "dict" {
             let tx_bound = self.tx.bind(py);
             let shadow = tx_bound.call_method1("get_shadow", (&val, &full_path))?; 
             let structures = PyModule::import(py, "theus.structures")?;
             
             let can_write = self.check_permissions(&full_path, true).is_ok();
             let cls_name = if can_write { "TrackedDict" } else { "FrozenDict" };

             let cls = structures.getattr(cls_name)?;
             return Ok(cls.call1((shadow, self.tx.clone_ref(py), full_path))?.unbind());
        }
        
        // Wrap everything else (Tuple, Object, Dataclass) in a new ContextGuard
        // CRITICAL: We must wrap the SHADOW to ensure method calls (unwrapped callables)
        // operate on isolated state (Snapshot Isolation).
        let tx_bound = self.tx.bind(py);
        let shadow = tx_bound.call_method1("get_shadow", (&val, &full_path))?; 

        Ok(Py::new(py, ContextGuard {
            target: shadow.unbind(),
            allowed_inputs: self.allowed_inputs.clone(),
            allowed_outputs: self.allowed_outputs.clone(),
            path_prefix: full_path,
            tx: self.tx.clone_ref(py),
            is_admin: self.is_admin,
        })?.into_py(py))
    }
}

#[pymethods]
impl ContextGuard {
    #[new]
    fn new_py(py: Python, target: PyObject, inputs: Vec<String>, outputs: Vec<String>) -> PyResult<Self> {
        let tx = Py::new(py, Transaction::new())?;
        Ok(ContextGuard {
            target,
            allowed_inputs: inputs,
            allowed_outputs: outputs,
            path_prefix: "".to_string(),
            tx,
            is_admin: false,
        })
    }

    fn __getattr__(&self, py: Python, name: String) -> PyResult<PyObject> {
        if name.starts_with("_") {
             return self.target.bind(py).getattr(name.as_str())?.extract();
        }

        let full_path = if self.path_prefix.is_empty() {
            name.clone()
        } else {
            format!("{}.{}", self.path_prefix, name)
        };

        self.check_permissions(&full_path, false)?;

        let val = self.target.bind(py).getattr(name.as_str())?.unbind();
        self.apply_guard(py, val, full_path)
    }

    fn __setattr__(&self, py: Python, name: String, value: PyObject) -> PyResult<()> {
        let full_path = if self.path_prefix.is_empty() {
            name.clone()
        } else {
            format!("{}.{}", self.path_prefix, name)
        };

        self.check_permissions(&full_path, true)?;

        let old_val = self.target.bind(py).getattr(name.as_str()).ok().map(|v| v.unbind());

        // Unwrap Tracked Objects & Nested Guards (Zombie Prevention & Isolation)
        let mut value = value;
        // Priority 1: ContextGuard (_target)
        if let Ok(inner) = value.bind(py).getattr("_target") {
             value = inner.unbind();
        } 
        // Priority 2: TrackedList/Dict (_data) - fallback if not a Guard
        else if let Ok(shadow) = value.bind(py).getattr("_data") {
             value = shadow.unbind();
        }
        
        {
            let mut tx_ref = self.tx.bind(py).borrow_mut();
            tx_ref.log_internal(
                full_path.clone(),
                "SET".to_string(),
                Some(value.clone_ref(py)),
                old_val,
                Some(self.target.clone_ref(py)),
                Some(name.clone())
            );
        }
        
        self.target.bind(py).setattr(name.as_str(), value)?;
        Ok(())
    }

    fn __getitem__(&self, py: Python, key: PyObject) -> PyResult<PyObject> {
        let target = self.target.bind(py);
        
        // 1. Try native get_item (for Sequence/Mapping)
        if let Ok(val_bound) = target.get_item(&key) {
            let val = val_bound.unbind();
            
            // Format Path: if integer, use brackets [k]. If string, use dot .k
            let full_path = if let Ok(idx) = key.extract::<isize>(py) {
                format!("{}[{}]", self.path_prefix, idx)
            } else {
                let key_str = key.to_string();
                if self.path_prefix.is_empty() {
                    key_str
                } else {
                    format!("{}.{}", self.path_prefix, key_str)
                }
            };
            
            self.check_permissions(&full_path, false)?;
            return self.apply_guard(py, val, full_path);
        }

        // 2. Fallback: If not subscriptable, assumes attribute access via dict syntax
        if let Ok(key_str) = key.extract::<String>(py) {
             return self.__getattr__(py, key_str);
        }
        
        // Return original error
        target.get_item(&key).map(|v| v.unbind())
    }

    fn __setitem__(&self, py: Python, key: PyObject, value: PyObject) -> PyResult<()> {
        // Logic for setitem (mostly dicts, lists)
        // Check if target supports set_item
        // If not, try setattr for string keys
        
        // This is tricky because ContextGuard wrapping a generic object usually shouldn't support setitem unless it's a dict.
        // But for consistency with __getitem__, we try to support both.
        
        let target = self.target.bind(py);
        
        // We can't easily "try" set_item without mutating.
        // Check type?
        let type_name = target.get_type().name()?.to_string();
        
        if ["list", "dict", "TrackedList", "TrackedDict"].contains(&type_name.as_str()) {
             // For Tracked types, we shouldn't even be here? (ContextGuard wraps regular types)
             // But if we wrap a list/dict, we should delegate.
             // Wait, if we wrap a list, we return a TrackedList via apply_guard?
             // YES. So ContextGuard should mostly NEVER wrap a list/dict directly due to __getattr__ logic.
             // EXCEPT if it was created manually in engine.rs on a root context that IS a list?
             // But valid contexts are dataclasses.
             // SO ContextGuard usually wraps Objects/Dataclasses or Tuples.
             // Tuples are immutable -> setitem fails.
             // Objects -> setitem fails? Except via setattr.
        }
        
        // For Generic Objects: map ['key'] = val to .key = val
        if let Ok(key_str) = key.extract::<String>(py) {
             return self.__setattr__(py, key_str, value);
        }

        // Default set item (will likely fail for objects, succeed for dicts if we wrapped one)
        // But we need to LOG it and CHECK permissions.
        // Assuming we wrapped a real dict (legacy case?) or custom object.
        
        // Path construction
        let full_path = if let Ok(idx) = key.extract::<isize>(py) {
            format!("{}[{}]", self.path_prefix, idx)
        } else {
            let key_str = key.to_string();
             format!("{}.{}", self.path_prefix, key_str)
        };

        self.check_permissions(&full_path, true)?;
        
        // Unwrap Value
        let mut value_to_set = value.clone_ref(py);
        if let Ok(inner) = value.bind(py).getattr("_target") {
             value_to_set = inner.unbind();
        } else if let Ok(shadow) = value.bind(py).getattr("_data") {
             value_to_set = shadow.unbind();
        }
        
        // We do NOT have easy "old_value" here for set_item without extra cost (get_item)
        let old_val = target.get_item(&key).ok().map(|v| v.unbind());
        
        {
            let mut tx_ref = self.tx.bind(py).borrow_mut();
            tx_ref.log_internal(
                full_path.clone(),
                "SET_ITEM".to_string(), // Distinct op?
                Some(value_to_set.clone_ref(py)),
                old_val,
                Some(self.target.clone_ref(py)),
                Some(key.to_string())
            );
        }

        target.set_item(key, value_to_set)?;
        Ok(())
    }
}
