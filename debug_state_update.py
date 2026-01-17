
import sys
import os
import time
from theus.engine import TheusEngine
from theus.structures import StateUpdate
from src.orchestrator.context import OrchestratorSystemContext, OrchestratorGlobalContext, OrchestratorDomainContext

def test_state_update():
    print("--- Debug: Testing State Update ---")
    
    # Setup
    global_ctx = OrchestratorGlobalContext(config_path="experiments_sanity.json")
    domain_ctx = OrchestratorDomainContext()
    system_ctx = OrchestratorSystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)
    
    engine = TheusEngine(context=system_ctx, strict_mode=True)
    
    # Verify initial Rust State
    state_data = engine.state.data
    # Convert Rust Map to Dict if needed for printing
    print(f"Initial Rust State Domain: {state_data.get('domain')}")
    
    # Simulate Implicit Mapping Update logic
    # Engine does this:
    # 1. Capture version
    version = engine.state.version
    
    # 2. Prepare update dict
    update_data = {
        "domain": {
            "sig_total_experiments": 1,
            "sig_experiment_active_idx": 0
        }
    }
    
    print("\nApplying CAS Update (Implicit Mapping Simulation)...")
    # Correct signature: (version, data, heavy, signal)
    engine._core.compare_and_swap(version, update_data, None, None)
    
    # Verify Rust State after update
    new_state_data = engine.state.data
    new_domain = new_state_data.get('domain')
    
    total = None
    if isinstance(new_domain, dict):
        total = new_domain.get('sig_total_experiments')
    else:
        # If wrapped object
        total = getattr(new_domain, 'sig_total_experiments', None)
        
    print(f"Updated Rust State Domain signals: total={total}")
    
    if total == 1:
        print("✅ SUCCESS: State Updated Correctly.")
    else:
        print("❌ FAILURE: State Update Failed.")

if __name__ == "__main__":
    test_state_update()
