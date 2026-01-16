# Theus Framework v3.0 - AI Quick Reference

> **Target:** AI Coding Assistants (Claude, GPT-4, Gemini, Copilot)  
> **Purpose:** Copy-paste patterns for Theus-based projects

---

## 🚀 Standard Imports

```python
from dataclasses import dataclass, field
from theus import TheusEngine, process, ContractViolationError
from theus.context import BaseSystemContext, BaseDomainContext, BaseGlobalContext
```

---

## 📐 Context Definition Pattern

```python
@dataclass
class MyDomainContext(BaseDomainContext):
    # DATA ZONE (Persistent, Transactional)
    items: list = field(default_factory=list)
    counter: int = 0
    
    # SIGNAL ZONE (Transient, prefix: sig_, cmd_)
    sig_alert: bool = False
    cmd_stop: bool = False
    
    # HEAVY ZONE (Zero-Copy, No Rollback, prefix: heavy_)
    heavy_tensor: object = None

@dataclass
class MyGlobalContext(BaseGlobalContext):
    max_limit: int = 1000
    app_name: str = "MyApp"

@dataclass
class MySystemContext(BaseSystemContext):
    domain_ctx: MyDomainContext = field(default_factory=MyDomainContext)
    global_ctx: MyGlobalContext = field(default_factory=MyGlobalContext)
```

---

## 📝 Process Definition Pattern

```python
from theus.contracts import process, SemanticType

@process(
    inputs=['domain_ctx.items', 'global_ctx.max_limit'],
    outputs=['domain_ctx.items', 'domain_ctx.counter', 'domain_ctx.sig_alert'],
    errors=['ValueError'],
    semantic=SemanticType.EFFECT
)
def my_process(ctx, item_name: str, value: int):
    """Process docstring."""
    # 1. Validation
    if value < 0:
        raise ValueError("Value must be positive")
    
    # 2. Read inputs (immutable)
    max_limit = ctx.global_ctx.max_limit
    
    # 3. Business logic
    new_item = {"name": item_name, "value": value}
    
    # 4. Write outputs
    ctx.domain_ctx.items.append(new_item)
    ctx.domain_ctx.counter += 1
    
    # 5. Trigger signal if needed
    if ctx.domain_ctx.counter > max_limit:
        ctx.domain_ctx.sig_alert = True
    
    return "Success"
```

---

## ⚙️ Engine Initialization Pattern

```python
# 1. Create context
sys_ctx = MySystemContext()

# 2. Initialize engine
engine = TheusEngine(sys_ctx, strict_mode=True)

# 3. Register process (auto-discovers name from function)
engine.register(my_process)

# 4. Execute
result = engine.execute(my_process, item_name="Test", value=100)
# OR by name:
result = engine.execute("my_process", item_name="Test", value=100)
```

---

## 🔄 Workflow YAML (Flux DSL)

```yaml
# workflows/main_workflow.yaml
steps:
  # Simple process call
  - process: "validate_input"
  
  # Conditional branching
  - flux: if
    condition: "domain['is_valid'] == True"
    then:
      - "process_data"
      - "save_result"
    else:
      - "handle_error"
  
  # Loop
  - flux: while
    condition: "domain['items_left'] > 0"
    do:
      - "process_next_item"
  
  # Nested block
  - flux: run
    steps:
      - "cleanup"
      - "finalize"
```

### Execute Workflow

```python
engine.execute_workflow("workflows/main_workflow.yaml")
```

---

## ⚠️ Common Errors & Fixes

| Error | Cause | Fix |
|:------|:------|:----|
| `ContractViolationError` | Writing to undeclared output | Add path to `outputs=[]` |
| `PermissionError: Illegal Read` | Reading undeclared input | Add path to `inputs=[]` |
| `PermissionError: Illegal Write` | Writing to input-only path | Move path from `inputs` to `outputs` |
| `ContextLockedError` | Modifying ctx outside process | Use `with engine.edit()` |

---

## 🎯 Contract Path Rules

| Context | Path Format | Example |
|:--------|:------------|:--------|
| Domain | `domain_ctx.field` | `domain_ctx.items` |
| Global | `global_ctx.field` | `global_ctx.max_limit` |
| Nested | `domain_ctx.nested.field` | `domain_ctx.user.name` |

> **CRITICAL:** Always use `domain_ctx` NOT `domain`. Rust Core enforces strict paths.

---

## 🏷️ Zone Prefixes

| Zone | Prefix | Behavior |
|:-----|:-------|:---------|
| DATA | (none) | Transactional, Rollback on error |
| SIGNAL | `sig_`, `cmd_` | Transient, Reset on read |
| META | `meta_` | Observability only |
| HEAVY | `heavy_` | Zero-copy, NO rollback |

---

## 🔍 Audit Levels

| Level | Exception | Action |
|:------|:----------|:-------|
| **S** (Safety) | `AuditStopError` | Emergency stop system |
| **A** (Abort) | `AuditAbortError` | Hard stop workflow |
| **B** (Block) | `AuditBlockError` | Rollback transaction only |
| **C** (Count) | None | Log warning only |

---

*Generated for Theus Framework v3.0.0 - AI Developer Documentation*
