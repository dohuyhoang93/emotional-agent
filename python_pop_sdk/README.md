# POP SDK (Process-Oriented Programming)

**A Transactional, Context-Driven Framework for AI Agents & Complex Systems.**

POP (Process-Oriented Programming) is a paradigm shift from OOP. Instead of encapsulating state and behavior together, POP **decouples** them completely:
- **Context**: Dumb Data structures (State).
- **Process**: Pure Functions (Behavior) that transform Context.
- **Guard**: Strict Permissions & Transactional Integrity.

## 🌟 Key Features

- **Transactional State**: ACID-like memory transactions. Changes are isolated until commit. Rollbacks on error.
- **Deep Isolation**: Nested lists/dictionaries are automatically shadowed. Modification of deep state never leaks to the main context until approved.
- **Strict Contracts**: Define `inputs` and `outputs` for every process. Runtime enforcement prevents "State Spaghetti".
- **Zero-Dependency Core**: Pure Python. Compatible with PyTorch/TensorFlow/NumPy environments.

## 🚀 Quick Start

### 1. Define Context
```python
from dataclasses import dataclass
from pop import BaseGlobalContext, BaseDomainContext, BaseSystemContext

@dataclass
class MyGlobal(BaseGlobalContext):
    counter: int = 0

@dataclass
class MyDomain(BaseDomainContext):
    data: list = None

@dataclass
class MySystem(BaseSystemContext):
    global_ctx: MyGlobal
    domain_ctx: MyDomain
```

### 2. Define Processes
```python
from pop import process

@process(
    inputs=['global.counter'], 
    outputs=['global.counter']
)
def increment(ctx):
    ctx.global_ctx.counter += 1
    return "Incremented"
```

### 3. Run Engine
```python
from pop import POPEngine

# Init System
system = MySystem(MyGlobal(), MyDomain(data=[]))
engine = POPEngine(system)

# Register & Run
engine.register_process("p_inc", increment)
result = engine.run_process("p_inc")

print(f"Counter: {system.global_ctx.counter}")  # Output: 1
```

## 🛡️ Architecture

### The Context Guard
Every process runs inside a `ContextGuard`. This guard:
1.  **Whitelists Access**: Can only read what is in `inputs` and write to `outputs`.
2.  **Proxies Writes**: All writes go to a generic `Transaction` layer.
3.  **Prevent Leaks**: Proxies are "Auto-Unwrapped" to preventing Zombie references.

### Delta Engine
State changes are stored as a list of `DeltaEntry` operations.
- **Commit**: Applies entries to the real object.
- **Rollback**: Helper function reverses changes (Time Travel).

## 📦 Installation

```bash
pip install pop-sdk
```

## 📄 License
MIT
