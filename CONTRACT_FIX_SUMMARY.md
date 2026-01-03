# Summary: Contract Alias Fix for Emotional Agent

## Root Cause
The `theus` framework's Rust `ContextGuard` enforces strict permission checks on context attribute access. When code accesses parent contexts like `ctx.domain_ctx`, the guard checks if `'domain_ctx'` is in the contract's `inputs` list.

**The Problem:**
- Legacy code uses shorthand: `domain = ctx.domain_ctx` (accessing parent context)
- Contracts only declared child paths: `inputs=['domain_ctx.snn_context']`
- `ContextGuard` blocked parent access: `PermissionError: Illegal Read: 'domain_ctx'`

## Solution Applied
Added parent context paths (`'domain_ctx'`, `'global_ctx'`) to ALL `@process` decorators where child paths exist.

**Fix Strategy:**
1. Created `final_fix.py` - comprehensive Python script
2. Scanned ALL `.py` files in `src/` directory
3. For each `@process` decorator:
   - If `inputs` contains `'domain_ctx.xxx'` → Add `'domain_ctx'`
   - If `inputs` contains `'global_ctx.xxx'` → Add `'global_ctx'`
   - Same logic for `outputs`

**Files Fixed:**
- 21 files via `fix_all_contracts.py`
- 12 files via PowerShell script
- 4 SNN files via `final_fix.py`
- 2 experimental files
- **Total: ~39 process files**

## Verification
Run: `python run_experiments.py --config experiments_sanity.json`

The experiment should now run without `PermissionError: Illegal Read` errors.
