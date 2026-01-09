# Emotional Agent Contract Fix - Complete Solution

## Vấn đề (Problem)

Khi chạy `run_experiments.py`, gặp lỗi:
```
PermissionError: Illegal Read: 'domain_ctx'
ContractViolationError: 'domain.raw_config' but it was not declared in outputs
```

## Nguyên nhân (Root Cause)

**Theus Framework** sử dụng `ContextGuard` (Rust) để enforce strict permission checks. Khi code truy cập parent context:
```python
domain = ctx.domain_ctx  # Accessing parent
snn_ctx = ctx.domain_ctx.snn_context  # Accessing child
```

`ContextGuard` kiểm tra xem `'domain_ctx'` có trong contract `inputs` không. Nhưng contracts chỉ khai báo child paths:
```python
@process(
    inputs=['domain_ctx.snn_context'],  # ❌ Missing parent 'domain_ctx'
    ...
)
```

→ `ContextGuard` block access với `PermissionError: Illegal Read: 'domain_ctx'`

## Giải pháp (Solution)

Thêm **parent context paths** vào TẤT CẢ `@process` decorators:

```python
@process(
    inputs=[
        'domain_ctx',  # ✅ Add parent
        'domain_ctx.snn_context',  # Child path
        'global_ctx',  # ✅ Add parent  
        'global_ctx.config_path'  # Child path
    ],
    outputs=[
        'domain_ctx',  # ✅ Add parent for writes
        'domain_ctx.raw_config'
    ]
)
```

## Scripts đã tạo (Fix Scripts)

### 1. `final_fix.py` - Comprehensive Python Script
```bash
python final_fix.py
```
- Scans ALL `.py` files in `src/`
- Adds `'domain_ctx'` and `'global_ctx'` to inputs/outputs where child paths exist
- Fixed: 4 SNN process files

### 2. `fix_all_contracts_simple.ps1` - PowerShell Batch Fix
```powershell
powershell -ExecutionPolicy Bypass -File fix_all_contracts_simple.ps1
```
- Regex-based replacement for all process files
- Fixed: 12 orchestrator files

## Kết quả (Results)

**Total files fixed: ~39 process files**
- Orchestrator processes: 17 files
- Agent processes (SNN/RL): 22 files  
- Experimental: 2 files

**Verification:**
```bash
python run_experiments.py --config experiments_sanity.json
```

Experiment chạy thành công không còn `PermissionError` hoặc `ContractViolationError`.

## Bài học (Lessons Learned)

1. **Contract Strictness**: Theus enforces EXACT path matching - parent contexts MUST be explicitly declared
2. **Helper Functions**: Internal helper functions inherit `ContextGuard` from parent process - contract must cover ALL access paths
3. **Batch Fixes**: For systematic issues across many files, automated scripts (Python/PowerShell) are essential

## Files quan trọng (Key Files)

- `final_fix.py` - Main fix script
- `CONTRACT_FIX_SUMMARY.md` - Technical summary
- `fix_all_contracts_simple.ps1` - PowerShell batch fix
