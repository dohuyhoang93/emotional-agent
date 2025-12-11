# Standard Templates for 'pop init'

TEMPLATE_ENV = """# POP SDK Configuration
# 1 = Strict Mode (Crash on Error)
# 0 = Warning Mode (Log Warning)
POP_STRICT_MODE=1
"""

TEMPLATE_CONTEXT = """from dataclasses import dataclass, field
from typing import List, Dict, Any
from pop import BaseGlobalContext, BaseDomainContext, BaseSystemContext

@dataclass
class GlobalContext(BaseGlobalContext):
    \"\"\"Reads-only configuration and constants.\"\"\"
    app_name: str = "My POP Agent"
    version: str = "0.1.0"

@dataclass
class DomainContext(BaseDomainContext):
    \"\"\"Mutable domain state.\"\"\"
    data: List[str] = field(default_factory=list)
    counter: int = 0

@dataclass
class SystemContext(BaseSystemContext):
    \"\"\"Root container.\"\"\"
    global_ctx: GlobalContext
    domain_ctx: DomainContext
    is_running: bool = True
"""

TEMPLATE_Hello_PROCESS = """from pop import process
from src.context import SystemContext

@process(
    inputs=['domain.counter', 'domain.data'],
    outputs=['domain.data', 'domain.counter']
)
def hello_world(ctx: SystemContext):
    \"\"\"
    A simple example process.
    \"\"\"
    valid_read = ctx.domain_ctx.counter
    
    # Mutation (Allowed because it is in outputs)
    ctx.domain_ctx.counter += 1
    ctx.domain_ctx.data.append(f"Hello World #{ctx.domain_ctx.counter}")
    
    print(f"[Process] Hello World! Counter is now {ctx.domain_ctx.counter}")
    return "OK"
"""

TEMPLATE_WORKFLOW = """name: "Main Workflow"
description: "A standard loop for the agent."

steps:
  - p_hello
  - p_hello
  - p_hello
"""

TEMPLATE_MAIN = """import os
import sys
from dotenv import load_dotenv

# Ensure 'src' is in path
sys.path.append(os.path.join(os.getcwd()))

from pop import POPEngine
from src.context import SystemContext, GlobalContext, DomainContext

# Import Processes to register them
from src.processes.p_hello import hello_world

def main():
    # 1. Load Environment (Strict Mode)
    load_dotenv()
    
    print("--- Initializing POP Agent ---")
    
    # 2. Setup Context
    system = SystemContext(
        global_ctx=GlobalContext(),
        domain_ctx=DomainContext()
    )
    
    # 3. Init Engine
    # Note: Strict Mode is auto-detected from env var POP_STRICT_MODE
    engine = POPEngine(system)
    
    # 4. Register Processes
    engine.register_process("p_hello", hello_world)
    
    # 5. Run Workflow (Manual)
    # In a real app, you might load this from workflows/main_workflow.yaml
    engine.run_process("p_hello")
    
    # 6. EXTERNAL MUTATION (Safe Way)
    print("\\n[Main] Attempting external mutation...")
    try:
        with engine.edit() as ctx:
            ctx.domain_ctx.counter = 100
        print(f"[Main] Counter updated safely to: {system.domain_ctx.counter}")
    except Exception as e:
        print(f"[Main] Error during mutation: {e}")
        
    # 7. Resume
    engine.run_process("p_hello")

if __name__ == "__main__":
    main()
"""
