"""
SNN Dream Processes for Theus Framework
=======================================
Processes for managing inputs during Sleep/Dream state.

Author: Theus Agent
Date: 2025-12-27
"""
import numpy as np
from theus.contracts import process
from src.core.context import SystemContext

@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context',
        'domain_ctx.dream_queue',
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.snn_context.domain_ctx.current_time',
        'domain_ctx.snn_context.global_ctx.dream_noise_level'
    ],
    outputs=['domain_ctx', 
        'domain_ctx.snn_context.domain_ctx.neurons', # Potentials updated
        'domain_ctx.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_inject_dream_stimulus(ctx: SystemContext):
    """
    Stimulate neurons randomly to simulate 'REM' activity.
    """
    try:
        _inject_impl(ctx)
    except Exception:
        import traceback
        print(f"CRASH in process_inject_dream_stimulus: {traceback.format_exc()}")
        raise

def _inject_impl(ctx: SystemContext):
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    val = getattr(global_ctx, 'dream_noise_level', 0.1)
    # print(f"DEBUG: noise_level val type: {type(val)}")
    
    try:
        noise_level = float(val)
    except Exception as e:
        print(f"DEBUG: noise_level float cast failed: {e}")
        print(f"DEBUG: noise_level dir: {dir(val)}")
        noise_level = 0.1 # Fallback
        
    active_count = 0
    
    for neuron in domain.neurons:
        # Random input curren
        input_current = np.random.uniform(0, noise_level)
        
        # Possibility of 'burst' (PGO waves)
        if np.random.random() < 0.01: # 1% chance of strong stimulus
            input_current += 0.5
            
        neuron.potential += input_current
        
        if input_current > 0.1:
            active_count += 1
            
    domain.metrics['dream_stimulus_active_neurons'] = active_count
