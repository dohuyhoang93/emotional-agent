
import sys
import os
import yaml
from types import SimpleNamespace
from theus.engine import TheusEngine
from theus.contracts import process

def test_wiring():
    print("\n--- Test Python -> Rust Wiring ---")
    
    # 1. Setup Context & Engine
    # Mock complete context structure to satisfy TheusEngine.__init__
    ctx = SimpleNamespace(
        val=0, 
        logs=[],
        global_ctx=SimpleNamespace(),
        domain_ctx=SimpleNamespace(),
        system_ctx=SimpleNamespace()
    )
    eng = TheusEngine(ctx)
    
    # 2. Define & Register Process (Python Side)
    # TheusEngine.register_process delegates to Rust.
    
    @process(inputs=[], outputs=[])
    def my_process(guard):
        print(" -> Python Process Executed via Rust Flux!")
        
    eng.register_process("my_process", my_process)
    
    # 3. Create Temporary Workflow File
    wf_data = {
        "name": "Test Wiring",
        "steps": [
            "my_process",
            {"flux": "run", "steps": ["my_process"]}
        ]
    }
    
    wf_path = "temp_wiring_test.yaml"
    with open(wf_path, 'w') as f:
        yaml.dump(wf_data, f)
        
    try:
        # 4. Execute Workflow
        # This calls TheusEngine.execute_workflow -> RustEngine.execute_workflow
        print("Calling eng.execute_workflow()...")
        eng.execute_workflow(wf_path)
        print("✅ Wiring Verified: Execution completed without error.")
        
    finally:
        if os.path.exists(wf_path):
            os.remove(wf_path)

if __name__ == "__main__":
    test_wiring()
