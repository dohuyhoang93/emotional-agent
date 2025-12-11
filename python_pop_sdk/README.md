# POP SDK (Process-Oriented Programming)

**The "Operating System" for AI Agents and Complex Systems.**

[![PyPI version](https://badge.fury.io/py/pop-sdk.svg)](https://badge.fury.io/py/pop-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**POP (Process-Oriented Programming)** is a paradigm shift designed for building robust, stateful AI agents. Unlike OOP which encapsulates state and behavior, POP **decouples** them completely to ensure:
1.  **Transactional Integrity**: Every action is atomic.
2.  **Safety by Default**: Inputs are immutable; outputs are strictly contracted.
3.  **Observability**: Every state change is logged and reversible.

---

## 🌟 Key Features

### 🛡️ Safety & Security
- **Context Locking ("The Vault")**: Prevents accidental state mutation from external code (`main.py`). Warning mode by default, Strict mode (crash) for CI.
- **Frozen Inputs**: Process inputs are wrapped in `FrozenList`/`FrozenDict`. Side-effects are blocked at runtime.
- **Strict Contracts**: Explicit `@process(inputs=[...], outputs=[...])` decorators prevent "State Spaghetti".

### ⚡ Developer Experience
- **POP CLI**: Bootstrap new projects instantly with `pop init`.
- **Hybrid Guard**: Friendly warnings for rapid dev, Strict enforcement for interaction.
- **Zero-Dependency Core**: Pure Python. Compatible with PyTorch, TensorFlow, or any other library.

---

## 📦 Installation

```bash
pip install pop-sdk
```

---

## 🚀 Quick Start (CLI)

The fastest way to start is using the CLI tool.

> **Note**: We recommend using `python -m pop` to ensure compatibility across all operating systems (Windows/Linux/Mac) without worrying about PATH configuration.

```bash
# 1. Initialize a new project
python -m pop init my_agent

# 2. Enter directory
cd my_agent

# 3. Run the skeleton agent
python main.py
```

Arguments:
- `python -m pop init <name>`: Create a new project folder.
- `python -m pop init .`: Initialize in current directory.

(You can also use the short command `pop init` if your Python Scripts directory is in your system PATH).

---

## 📚 Manual Usage

### 1. Define Context (Data)
```python
from dataclasses import dataclass
from pop import BaseGlobalContext, BaseDomainContext, BaseSystemContext

@dataclass
class MyGlobal(BaseGlobalContext):
    counter: int = 0

@dataclass
class MySystem(BaseSystemContext):
    global_ctx: MyGlobal
    # ... domain_ctx ...
```

### 2. Define Process (Logic)
```python
from pop import process

@process(
    inputs=['global.counter'], 
    outputs=['global.counter']
)
def increment(ctx):
    # Valid: Declared in outputs
    ctx.global_ctx.counter += 1
    return "Incremented"

@process(inputs=['global.counter'], outputs=[])
def illegal_write(ctx):
    # INVALID: Read-Only Input
    # Raises ContractViolationError
    ctx.global_ctx.counter += 1 
```

### 3. Run Engine
```python
from pop import POPEngine

system = MySystem(MyGlobal(), ...)
engine = POPEngine(system) # Default: Warning Mode

engine.register_process("inc", increment)
engine.run_process("inc")
```

---

## ⚙️ Configuration

You can control strictness via Environment Variables (supported in `.env` files):

| Variable | Values | Description |
|----------|--------|-------------|
| `POP_STRICT_MODE` | `1`, `true` | **Enabled**: Raises `LockViolationError` on unsafe external mutation. <br> **Disabled (Default)**: Logs `WARNING` but allows mutation. |

### Safe External Mutation
To modify context from `main.py` without triggering warnings/errors, use the explicit API:

```python
with engine.edit() as ctx:
    ctx.domain.my_var = 100
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
