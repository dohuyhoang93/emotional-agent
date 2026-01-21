# Chapter 2: Designing the 3-Axis Context

In Theus v3.0, the Context is not just a bag of data. It is a 3-dimensional structure that helps the Engine understand and protect your data.

## 1. The "Hybrid Context Zones" Mindset
Instead of forcing you to write `ctx.domain_ctx.data.user_id` (too verbose), Theus v3.0 uses a **Hybrid** mechanism. You write it flat (`ctx.domain_ctx.user_id`), but the Engine implicitly classifies it into **Zones** based on Naming Conventions or Schema.

| Zone | Prefix | Nature | Protection Mechanism |
| :--- | :--- | :--- | :--- |
| **DATA** | (None) | Business Asset. Persistent. | Full Transaction, Strict Replay. |
| **SIGNAL** | `sig_`, `cmd_` | Event/Command. Transient. | Transaction Reset, No Replay. |
| **META** | `meta_` | Debug Info. | Read-only (usually). |
| **HEAVY** | `heavy_` | AI Tensors/Blobs. | **Zero-Copy** (Direct RAM), No Rollback. |

> **🧠 Manifesto Connection:**
> **Principle 3.1: "Transparency is Safety".**
>
> **Why define Zones?**
> A common bug in AI is "Logic Leakage": An agent sees an old implementation detail (like a `stop_command` flag remaining `True` from 50 steps ago) and hallucinates.
> By strictly separating **Signals** (which self-destruct after 1 tick) from **Data** (which persists), Theus guarantees that your Agent only reacts to *current reality*, not historical ghosts.

## 2. Design with Dataclasses
We still use `dataclass`, but we must adhere to Zone conventions.

```python
from dataclasses import dataclass, field
from theus.context import BaseSystemContext, BaseDomainContext, BaseGlobalContext

# 1. Define Domain (Business Logic)
@dataclass
class WarehouseDomain(BaseDomainContext):
    # --- DATA ZONE (Assets) ---
    items: list = field(default_factory=list)
    total_value: int = 0
    
    # --- SIGNAL ZONE ---
    # NOTE (v3.0): Do NOT declare signals here! 
    # Signals are Dynamic Events managed by Rust.
    # They are ephemeral and don't belong in the persistent schema.
    
    # --- HEAVY ZONE (Large Data) ---
    heavy_inventory_image: object = None  # For camera snapshots

# 2. Define Global (Configuration)
@dataclass
class WarehouseConfig(BaseGlobalContext):
    max_capacity: int = 1000
    warehouse_name: str = "Main Warehouse"

# 3. Attach to System Context
@dataclass
class WarehouseContext(BaseSystemContext):
    # BaseSystemContext requires 'domain_ctx' and 'global_ctx'
    # We enforce type hinting for clarity
    domain_ctx: WarehouseDomain = field(default_factory=WarehouseDomain)
    global_ctx: WarehouseConfig = field(default_factory=WarehouseConfig)
```

> **Pro Tip (v3.0):** When you declare `items: list`, Theus automatically wraps it in a **Rust-Native `FrozenList`** at runtime. This ensures **Immutability** - you cannot modify the list directly. To change it, a Process must return a new list pattern (Copy-on-Write).

## 3. Why is Zoning Important?
When you run a **Replay (Bug Reproduction)**:
- Theus will restore exactly `items` and `total_value` (Data Zone).
- Theus will **IGNORE** `sig_restock_needed` (Signal Zone) because it is past noise.
- Theus will restore exactly `items` and `total_value` (Data Zone).
- Theus will **IGNORE** Signals because they are transient noise.

**Benefit for You:**
You can replay a bug from yesterday, and it will execute *exactly the same way*, bit-for-bit. This is **Principle 2.3: "Deterministic Replay"**. Debugging becomes a science, not guesswork.

## 4. Immutable Snapshot Mechanism
Theus protects the Context using **Snapshot Isolation** (enforced by Rust Core).

### 4.1. Default State: READ-ONLY
As soon as you initialize `Engine(ctx, strict_mode=True)`, the Context becomes an **Immutable Snapshot**.
If you try to modify it externally (External Mutation):
```python
# Code outside of @process
def hack_system(ctx):
    # This will FAIL if strict_mode=True
    ctx.domain_ctx.total_value = 9999 # -> Raises ContextError (Immutable)
```
The system raises an error to prevent Untraceable Mutations.

> **Note:** `strict_mode=True` is Highly Recommended for Production/Testing to guarantee data integrity.

### 4.2. Valid Mutation: `engine.edit()`
In special cases (like Unit Tests, Initial Data Setup), you need to modify the Context without writing a Process. Theus provides a "Master Key":

```python
# Temporarily unlock within the with block
with engine.edit() as safe_ctx:
    safe_ctx.domain_ctx.total_value = 100
    safe_ctx.domain_ctx.items.append("Setup Item")
# Exit block -> Automatically RELOCKED immediately.
```

---
**Exercise:**
Create a file `warehouse_ctx.py`. Define the Context as above.
Try writing a main function, initialize the Engine, then intentionally assign `ctx.domain_ctx.total_value = 1` without using `engine.edit()`. Observe the `ContextLockedError`.
