# Theus v3.0.2 Release Notes

**Date:** 2026-01-20
**Status:** Production Ready

## Key Advancements

### Thread Safety & Concurrency Control
This release introduces a robust Conflict Manager implemented in Rust to handle high-concurrency scenarios safely:

- **Exponential Backoff with Jitter:** The system now intelligently manages retry intervals when conflicts occur. Instead of fixed waiting, processes wait for strictly increasing durations (multiplied by 2 on each failure) with added randomized "jitter". This mechanism effectively distributes retries over time, eliminating the "thundering herd" problem where multiple blocked processes retry simultaneously and cause repeated collisions.
- **VIP Locking (Anti-Starvation):** To ensure fairness, the system employs a priority mechanism. It tracks the number of consecutive failures for each process. If a process fails to commit its transaction 5 times in a row, it is granted a "VIP Ticket". The system then temporarily blocks other writers to guarantee the VIP process can commit its transaction successfully, preventing indefinite resource starvation (livelock).
- **Atomic Compare-And-Swap (CAS):** Optimistic concurrency control is enforced at the key level. State updates are atomic, ensuring that no data corruption occurs even when multiple parallel processes attempt to modify the same context simultaneously.

### True Parallelism
- **Multi-Process Execution:** Enabled robust support for `ProcessPool`, allowing CPU-bound tasks to bypass the Python GIL explicitly.
- **Safety Integration:** The parallel execution engine is deeply integrated with the new Concurrency Control features to ensure data consistency across process boundaries.

### Shared Memory (Heavy Context)
Optimized the Heavy Zone for efficient data handling:
- **Zero-Copy Architecture:** Leverages shared memory to pass large datasets (Tensors, DataFrames) between processes without serialization overhead.
- **Hybrid Management:** The system intelligently handles cross-platform differences in shared memory naming (Windows/Linux) to ensure data integrity and accessibility.

## Improvements
- **Core Parity:** Achieved 100% logic alignment between the Rust Core engine and Python interface.
- **Stability:** Fixed configuration templates and import paths for parallel execution examples.
- **Standardization:** Codebase enforces strict architectural rules, vetted by both `cargo clippy` (Rust) and `ruff` (Python).

### 🐛 Critical Fixes
- **Flux Signal Blindness:** Fixed a race condition where ephemeral signals emitted by async processes were missed by the Flux Workflow engine. Signals are now properly latched in `State.last_signals` for one tick.
- **Numpy Compatibility:** `ContextGuard` now natively supports Numpy scalar types (`int64`, `float32`, etc.), preventing `TypeError` during mathematical operations.



## Known Limitations
- **Sub-Interpreter Compatibility:** While Theus supports PEP-554 (Sub-interpreters), major C-extensions like `numpy` do not yet support multi-phase initialization (`numpy._core._multiarray_umath` error). Therefore, the system currently defaults to `ProcessPool` for robust execution.
- **Zombie Collector (Windows):** Automatic cleanup of shared memory from crashed processes is currently experimental on Windows due to OS-specific naming constraints (fully functional on Linux).

## Installation
```bash
pip install theus==3.0.2
```
