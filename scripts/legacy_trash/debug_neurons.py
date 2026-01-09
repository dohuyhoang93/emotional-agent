
import sys
import os
import numpy as np
from dataclasses import dataclass, field
from typing import List

# Fix paths
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'theus'))

from theus.engine import TheusEngine
from theus.contracts import process
from src.core.snn_context_theus import create_snn_context_theus, SNNSystemContext

def main():
    print("--- DEBUG NEURONS SCRIPT ---")
    
    # 1. Create Context
    print("1. Creating SNN Context...")
    ctx = create_snn_context_theus(num_neurons=5)
    neurons = ctx.domain_ctx.neurons
    print(f"   Neurons count: {len(neurons)}")
    print(f"   Neuron 0 type (raw): {type(neurons[0])}")
    print(f"   Neuron 0 threshold type (raw): {type(neurons[0].threshold)}")
    
    # 2. Init Engine
    print("2. Initializing Engine (Strict Mode)...")
    engine = TheusEngine(ctx, strict_mode=True)
    
    # 3. Process to access neurons via Guard
    @process(
        inputs=['domain_ctx.neurons'],
        outputs=[],
        side_effects=[]
    )
    def debug_neurons(context):
        print("\n--- INSIDE PROCESS ---")
        domain = context.domain_ctx
        neurons = domain.neurons
        print(f"   domain.neurons type: {type(neurons)}")
        
        n0 = neurons[0]
        print(f"   neurons[0] type: {type(n0)}")
        print(f"   neurons[0] dir: {dir(n0) if hasattr(n0, '__dir__') else 'No dir'}")
        
        t0 = n0.threshold
        print(f"   n0.threshold type: {type(t0)}")
        print(f"   n0.threshold value repr: {repr(t0)}")
        
        try:
            val = float(t0)
            print(f"   float(t0): {val}")
        except Exception as e:
            print(f"   float(t0) FAILED: {e}")
            
            # Unwrapping Strategy Test
            print("   Attempting Unwrap...")
            if hasattr(t0, '_target_obj'):
                print(f"   Has _target_obj: {type(t0._target_obj)}")
            
            try:
                # Assuming simple Python/Rust guard might allow direct access via property?
                pass
            except:
                pass

    engine.register_process("debug_neurons", debug_neurons)
    print("\n3. Running Process...")
    engine.run_process("debug_neurons")
    print("--- FINISHED ---")

if __name__ == "__main__":
    main()
