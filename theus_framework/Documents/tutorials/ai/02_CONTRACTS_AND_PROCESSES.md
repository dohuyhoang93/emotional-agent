# Module 02: Contracts and Processes

> **For AI Assistants:** The `@process` decorator is the core of Theus. Every function that touches Context MUST use it.

---

## 1. The Process Contract

A Process Contract is a **legal agreement** between your code and the Theus Engine.

### Contract Declaration

```python
from theus.contracts import process, SemanticType

@process(
    inputs=['domain_ctx.items', 'global_ctx.max_limit'],
    outputs=['domain_ctx.items', 'domain_ctx.counter'],
    errors=['ValueError', 'KeyError'],
    semantic=SemanticType.EFFECT,
    side_effects=['http_request']
)
def my_process(ctx, ...):
    ...
```

### Contract Parameters

| Parameter | Type | Required | Purpose |
|:----------|:-----|:---------|:--------|
| `inputs` | `List[str]` | No | Paths with READ permission |
| `outputs` | `List[str]` | No | Paths with WRITE permission |
| `errors` | `List[str]` | No | Allowed exception types |
| `semantic` | `SemanticType` | No | Process classification |
| `side_effects` | `List[str]` | No | External effects (logging) |

---

## 2. Path Syntax

### Critical Rule: Use `domain_ctx` NOT `domain`

```python
# ✅ CORRECT
inputs=['domain_ctx.user.name']

# ❌ WRONG - Rust Core will reject
inputs=['domain.user.name']
```

### Path Examples

| Access Pattern | Contract Path |
|:---------------|:--------------|
| `ctx.domain_ctx.items` | `'domain_ctx.items'` |
| `ctx.domain_ctx.user.name` | `'domain_ctx.user.name'` |
| `ctx.global_ctx.max_limit` | `'global_ctx.max_limit'` |
| `ctx.domain_ctx.sig_alert` | `'domain_ctx.sig_alert'` |

### Parent Path Inheritance

Declaring a parent path grants access to all children:

```python
# Grants access to user.name, user.email, user.age, etc.
inputs=['domain_ctx.user']
```

---

## 3. SemanticType Classification

```python
from theus.contracts import SemanticType

class SemanticType(Enum):
    PURE = "pure"      # No side effects, deterministic
    EFFECT = "effect"  # May have side effects (default)
    GUIDE = "guide"    # Orchestration/coordination process
```

| Type | Use When | Example |
|:-----|:---------|:--------|
| `PURE` | Math, validation, transformation | `calculate_total()` |
| `EFFECT` | Database, API calls, mutations | `save_user()` |
| `GUIDE` | Workflow coordination | `decide_next_step()` |

---

## 4. Complete Process Pattern

```python
from theus.contracts import process, SemanticType

@process(
    inputs=[
        'domain_ctx.cart_items',
        'domain_ctx.user_id',
        'global_ctx.tax_rate'
    ],
    outputs=[
        'domain_ctx.cart_items',
        'domain_ctx.total_price',
        'domain_ctx.sig_checkout_ready'
    ],
    errors=['ValueError']
)
def calculate_cart_total(ctx):
    """
    Calculate total price with tax.
    
    Inputs:
        - cart_items: List of {name, price, quantity}
        - user_id: For audit logging
        - tax_rate: From global config
    
    Outputs:
        - cart_items: (unchanged, but declared for consistency)
        - total_price: Calculated sum with tax
        - sig_checkout_ready: Signal when total > 0
    """
    # 1. Read inputs (immutable access)
    items = ctx.domain_ctx.cart_items
    tax_rate = ctx.global_ctx.tax_rate
    
    # 2. Validation
    if not items:
        raise ValueError("Cart is empty")
    
    # 3. Business logic
    subtotal = sum(item['price'] * item['quantity'] for item in items)
    total = subtotal * (1 + tax_rate)
    
    # 4. Write outputs
    ctx.domain_ctx.total_price = round(total, 2)
    
    # 5. Signal for workflow
    if total > 0:
        ctx.domain_ctx.sig_checkout_ready = True
    
    return {"subtotal": subtotal, "total": total}
```

---

## 5. Async Process Pattern

```python
import asyncio
from theus.contracts import process

@process(
    inputs=['domain_ctx.query'],
    outputs=['domain_ctx.result']
)
async def fetch_data(ctx):
    """Async process for I/O operations."""
    query = ctx.domain_ctx.query
    
    # Async I/O
    await asyncio.sleep(0.1)  # Simulated API call
    result = {"data": f"Result for {query}"}
    
    ctx.domain_ctx.result = result
    return result
```

---

## 6. Contract Violations

### Violation Types

| Violation | Exception | Cause |
|:----------|:----------|:------|
| Read undeclared | `PermissionError: Illegal Read` | Accessing path not in `inputs` |
| Write undeclared | `PermissionError: Illegal Write` | Writing path not in `outputs` |
| Write to input | `ContractViolationError` | Path in `inputs` but trying to write |

### Example Violations

```python
@process(inputs=['domain_ctx.items'])  # No outputs declared!
def broken_process(ctx):
    ctx.domain_ctx.items.append("new")  # ❌ ContractViolationError
    ctx.domain_ctx.counter += 1          # ❌ PermissionError: Illegal Write
```

### Fix

```python
@process(
    inputs=['domain_ctx.items'],
    outputs=['domain_ctx.items', 'domain_ctx.counter']  # ✅ Declared
)
def fixed_process(ctx):
    ctx.domain_ctx.items.append("new")  # ✅ OK
    ctx.domain_ctx.counter += 1          # ✅ OK
```

---

## 7. The Golden Rule: No Input Signals

```python
# ❌ WRONG - Signals should NOT be inputs
@process(inputs=['domain_ctx.sig_start'])
def bad_process(ctx):
    if ctx.domain_ctx.sig_start:
        ...

# ✅ CORRECT - Handle signals in Flux DSL workflow
# workflow.yaml:
# - flux: if
#     condition: "domain['sig_start'] == True"
#     then:
#       - "good_process"
```

**Why?** Signals are transient (time-dependent). Processes must be deterministic (state-dependent) for replay.

---

## 8. Bare Decorator Usage

For simple processes, you can use `@process` without arguments:

```python
@process  # Equivalent to @process(inputs=[], outputs=[])
def read_only_process(ctx):
    # Can only read, cannot write
    print(ctx.domain_ctx.items)  # Will fail in strict mode
```

> **AI Note:** Always prefer explicit `inputs`/`outputs` for clarity.

---

## 9. AI Implementation Checklist

When generating `@process` code:

- [ ] Import: `from theus.contracts import process, SemanticType`
- [ ] Declare ALL read paths in `inputs`
- [ ] Declare ALL write paths in `outputs`
- [ ] Use `domain_ctx` not `domain` in paths
- [ ] Add parent path if accessing nested fields
- [ ] Declare allowed exceptions in `errors`
- [ ] Use `async def` for I/O-bound operations
- [ ] NEVER put signals in `inputs`
- [ ] Return meaningful result for debugging

---

*Next: [03_ENGINE_AND_TRANSACTIONS.md](./03_ENGINE_AND_TRANSACTIONS.md)*
