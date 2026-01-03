use pyo3::prelude::*;

mod delta;
mod audit;
mod engine;
mod guards;

/// Theus Core Rust Extension
#[pymodule]
fn theus_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<engine::Engine>()?;
    m.add_class::<delta::Transaction>()?;
    m.add_class::<guards::ContextGuard>()?; 
    Ok(())
}
