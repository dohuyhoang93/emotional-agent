import os
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
    print("\n[Main] Attempting external mutation...")
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
