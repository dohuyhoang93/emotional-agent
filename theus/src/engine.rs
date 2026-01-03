use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use crate::audit::AuditPolicy;
use crate::guards::ContextGuard;
use crate::delta::Transaction;

#[pyclass(subclass)]
pub struct Engine {
    ctx: PyObject, 
    process_registry: HashMap<String, PyObject>, 
    audit_policy: Option<AuditPolicy>,
}

impl Engine {
    fn raise_audit_error(py: Python, err: crate::audit::AuditError) -> PyResult<PyObject> {
        let audit_mod = PyModule::import(py, "theus.audit")?;
        
        match err {
            crate::audit::AuditError::Block(msg) => {
                 let exc = audit_mod.getattr("AuditBlockError")?;
                 Err(PyErr::from_value(exc.call1((msg,))?))
            },
            crate::audit::AuditError::Interlock(msg) => {
                 let exc = audit_mod.getattr("AuditInterlockError")?;
                 Err(PyErr::from_value(exc.call1((msg,))?))
            }
        }
    }
}

#[pymethods]
impl Engine {
    #[new]
    #[pyo3(signature = (ctx, strict_mode=None, audit_recipe=None))]
    fn new(py: Python, ctx: PyObject, strict_mode: Option<bool>, audit_recipe: Option<PyObject>) -> Self {
        let mut policy = None;
        if let Some(recipe) = audit_recipe {
             if let Ok(p) = AuditPolicy::from_python(py, recipe) {
                 policy = Some(p);
             } else {
                 eprintln!("WARNING: Failed to parse Audit Policy");
             }
        }

        Engine {
            ctx,
            process_registry: HashMap::new(),
            audit_policy: policy,
        }
    }
    
    fn register_process(&mut self, name: String, func: PyObject) {
        self.process_registry.insert(name, func);
    }

    #[pyo3(signature = (process_name, **kwargs))]
    fn execute_process(&mut self, py: Python, process_name: String, kwargs: Option<&Bound<'_, pyo3::types::PyDict>>) -> PyResult<PyObject> {
        let func = self.process_registry.get(&process_name)
            .ok_or_else(|| pyo3::exceptions::PyKeyError::new_err(format!("Process '{}' not found", process_name)))?;
        
        let ctx_bound = self.ctx.bind(py);

        if let Some(policy) = &mut self.audit_policy {
             if let Err(e) = policy.evaluate(py, &process_name, "input", ctx_bound, None) {
                  return Self::raise_audit_error(py, e);
             }
        }
        
        // Transaction (New PyClass)
        let tx = Py::new(py, Transaction::new())?;

        let func_bound = func.bind(py);
        let contract = func_bound.getattr("_pop_contract")
             .map_err(|_| pyo3::exceptions::PyAttributeError::new_err(format!("Process '{}' usually needs @process decorator", process_name)))?;
             
        let inputs = contract.getattr("inputs")?.extract::<Vec<String>>()?;
        let outputs = contract.getattr("outputs")?.extract::<Vec<String>>()?;
        let declared_errors = contract.getattr("errors")?.extract::<Vec<String>>()?;
        
        // ContextGuard(ctx, inputs, outputs, "", tx)
        // Use the RUST ContextGuard directly for performance and correctness
        let guard_struct = ContextGuard::new_internal(
            self.ctx.clone_ref(py), 
            inputs, 
            outputs, 
            tx.clone_ref(py),
            false // Process Guard is NOT admin
        );
        let guard = Py::new(py, guard_struct)?;
        
        let args = (guard,);
        let result = match func_bound.call(args, kwargs) {
            Ok(res) => res.unbind(),
            Err(e) => {
                let tx_bound = tx.bind(py);
                tx_bound.call_method0("rollback")?; 
                
                // Check if error is declared or is a ContractViolationError
                let err_type = e.get_type(py).name()?.to_string();
                if declared_errors.contains(&err_type) {
                     return Err(e);
                }
                
                // Allow builtin PermissionError (mapped from our PyPermissionError) to pass?
                // Or wrap it?
                // If it is PermissionError, it means Guard blocked it. Is it a Contract Violation?
                // Yes, but Python test might expect ContractViolationError.
                // But generally PermissionError IS the enforcement.
                
                // If it is ALREADY ContractViolationError (from FrozenList etc), allow it.
                if err_type == "ContractViolationError" || err_type == "PermissionError" {
                     return Err(e);
                }

                // Otherwise, wrap as Undeclared Error Violation
                let contracts_mod = PyModule::import(py, "theus.contracts")?;
                let exc = contracts_mod.getattr("ContractViolationError")?;
                let msg = format!("Undeclared Error Violation: Caught {}: {}", err_type, e);
                return Err(PyErr::from_value(exc.call1((msg,))?));
            }
        };
        
        if let Some(policy) = &mut self.audit_policy {
            // Use Admin Guard to allow Audit to see Shadows and Read All
            let audit_guard_struct = ContextGuard::new_internal(
                self.ctx.clone_ref(py),
                vec![], // inputs ignored in admin
                vec![], // outputs ignored in admin
                tx.clone_ref(py),
                true // IS ADMIN
            );
            let audit_guard = Py::new(py, audit_guard_struct)?;

            if let Err(e) = policy.evaluate(py, &process_name, "output", audit_guard.bind(py), None) {
                 let tx_bound = tx.bind(py);
                 tx_bound.call_method0("rollback")?;
                 return Self::raise_audit_error(py, e);
            }
        }
        
        let tx_bound = tx.bind(py);
        tx_bound.call_method0("commit")?;

        Ok(result)
    }
}
