# Chapter 10: Heavy Zone - Optimizing for AI/Tensor Workloads

Theus v2 introduces a **High-Performance Optimization** called "Heavy Zone".
This is designed for AI Agents, Machine Learning, or Image Processing where you work with large Blobs (Tensors, Images) that are too expensive to Copy.

## 1. The "Heavy" Problem
In standard Theus logic, `outputs=['domain_ctx.items']` triggers a **Shadow Copy**.
If `items` is a 1GB Tensor:
1.  Copy 1GB Tensor (Shadow).
2.  Process runs (Modify Shadow).
3.  Commit (Scan differences? Swap pointers?).
This creates massive Latency and Output Overhead ("Quota Panic").

## 2. The Solution: `heavy_` Prefix
If you name a variable starting with `heavy_` in your Context Domain, Theus treats it as a **Heavy Asset**.

```python
@dataclass
class VisionDomain(BaseDomainContext):
    # Standard Data (Protected by Shadow Copy)
    counter: int = 0
    
    # HEAVY ASSET (Bypasses Shadow Copy!)
    heavy_camera_frame: np.ndarray = field(...)
    heavy_q_table: dict = field(...)
```

## 3. Behavior Changes
When a Process inputs/outputs a `heavy_` variable:

1.  **Skip Shadow Copy:** Theus passes the **Real Reference** directly to the Process.
    - *Benefit:* Zero Copy. Performance is Native Python speed.
    - *Risk:* **No Rollback Protection**. If your process crashes, the changes to the Tensor are **Permanent** (Dirty Read).

2.  **Log Once Strategy:**
    - To avoid spamming logs ("Skipping copy..."), Theus Rust Core only warns you **ONCE** per session per variable path.

## 4. When to use?
- **Use Heavy Zone for:** Pytorch Tensors, Numpy Arrays, Large Initial Config Blobs, Q-Tables.
- **Do NOT use for:** Financial Data, Login State, or Logic Flags (where Rollback is critical).

---
**Exercise:**
Create a context with `heavy_q_table`.
Write a process that modifies it.
Crash the process intentionally.
Check if `heavy_q_table` retained the modification (It should!). Compare this with a normal variable like `counter` (which should rollback).
