# Release Notes v3.0.22 (Stable)

**Date**: 2026-01-31
**Criticality**: HIGH (Fixes Crash Bugs)

## 🚀 Summary
Version 3.0.22 is a major stability release that resolves critical issues in the **Core Audit System** (Rust) and **Memory Management** (Python). It enables full compatibility with **NumPy/Vector workloads** in Heavy Zone without triggering audit crashes.

## 🐛 Bug Fixes

### 1. NumPy Equality Crash (Critical)
- **Issue**: Standard Python `bool()` checks on NumPy arrays raise `ValueError: The truth value of an array is ambiguous`.
- **Impact**: Any `infer_shadow_deltas` audit on a state containing NumPy arrays would crash the entire Engine.
- **Fix**: Updated `src/engine.rs` to implement a "Polyglot Auditor". It now detects if `rich_compare` returns an Array and falls back to `.all()` logic.
- **Verification**: New unit tests in `tests/09_v3_2/test_numpy_equality.py`.

### 2. SHM Import Failure
- **Issue**: `from theus_core.shm import MemoryRegistry` failed because PyO3 submodules were not exposed as standard import paths.
- **Impact**: `ManagedAllocator` showed warnings and failed to initialize SHM Registry.
- **Fix**: Adjusted usage in `structures.py` to `from theus_core import shm; MemoryRegistry = shm.MemoryRegistry`.
- **Verification**: New unit tests in `tests/09_v3_2/test_shm_import_mechanics.py`.

### 3. Dead Code Removal (Cleanup)
- **Removal**: Removed `TrackedList` and `TrackedDict` from `proxy.rs` and `lib.rs`.
- **Reason**: We moved to "Raw Shadow" strategy (V3 Design) where native Lists are used and compared via Shadow Cache, instead of intercepting every operation. `TrackedList` was incomplete and buggy.

## ⚡ Performance
- **Heavy Zone**: Confirmed ~2.0x overhead for full Zero-Trust Audit on massive arrays (acceptable trade-off for security).
- **Serialization**: `TheusEncoder` is 3x faster than manual casting.

## 📦 Upgrade Instructions
```bash
pip install theus==3.0.22
# Or from source:
py -m pip install .
```
