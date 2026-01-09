
import sys
import os
import traceback

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'theus'))

from theus.engine import TheusEngine
from src.core.snn_context_theus import create_snn_context_theus

import sys
import os
import traceback
from dataclasses import dataclass

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'theus'))

from theus.engine import TheusEngine
from theus.contracts import process
from src.core.snn_context_theus import create_snn_context_theus, SNNSystemContext
from src.orchestrator.context import OrchestratorSystemContext, OrchestratorGlobalContext, OrchestratorDomainContext

def main():
    print("--- STARTING NESTED DEBUG SCRIPT ---")
    
    # 1. Create SNN Context (The Inner Context)
    snn_sys_ctx = create_snn_context_theus()
    print("   SNN Context Created.")
    
    # 2. Create Orchestrator Context (The Outer Context)
    global_ctx = OrchestratorGlobalContext(config_path="dummy", cli_log_level="info")
    domain_ctx = OrchestratorDomainContext()
    
    # DYNAMIC INJECTION: Mirroring what likely happens in p_initialize_experiment
    # Inject snn_context into domain_ctx
    # Note: OrchestratorDomainContext is a dataclass, so we just set attribute. 
    # Python dataclasses allow dynamic attributes (it's just a class).
    domain_ctx.snn_context = snn_sys_ctx
    
    system_ctx = OrchestratorSystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)
    print("   Orchestrator Context Created & SNN Injected.")
    
    # 3. Init Engine
    print("   Initializing Engine (Strict Mode)...")
    tx_engine = TheusEngine(system_ctx, strict_mode=True)
    
    # 4. Define Process accessing nested path
    # inputs path mimics snn_dream_processes.py
    # 'domain_ctx.snn_context.global_ctx.connectivity'
    
    @process(
        inputs=[
            'domain_ctx.snn_context.global_ctx.connectivity',
            # 'domain_ctx.snn_context.global_ctx.dream_noise_level', # Try omitting this first to see if permission check fails or getattr works
        ], 
        outputs=[], 
        side_effects=[]
    )
    def debug_nested_process(ctx):
        print("\n--- INSIDE DEBUG NESTED PROCESS ---")
        
        try:
            d = ctx.domain_ctx
            s = d.snn_context
            g = s.global_ctx
            
            print(f"   g type: {type(g)}")
            
            # TEST 1: getattr for MISSING field with default
            print("   Test 1: getattr(g, 'dream_noise_level', 0.1)")
            val = getattr(g, 'dream_noise_level', 0.1)
            print(f"   val type: {type(val)}")
            print(f"   val repr: {repr(val)}")
            
            # TEST 2: Direct access to declared field
            print("   Test 2: g.connectivity")
            val2 = g.connectivity
            print(f"   val2 type: {type(val2)}")
            
        except Exception as e:
            print(f"   CRASH in process: {e}")
            traceback.print_exc()

    # Register and Run
    tx_engine.register_process("debug_nested_process", debug_nested_process)
    print("\n   Executing Nested Process...")
    tx_engine.run_process("debug_nested_process")
    print("--- FINISHED ---")

if __name__ == "__main__":
    main()

