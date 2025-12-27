"""
SNN Dream Processes for Theus Framework
=======================================
Processes for managing inputs during Sleep/Dream state.

Author: Theus Agent
Date: 2025-12-27
"""
import numpy as np
from theus import process
from src.core.context import SystemContext

@process(
    inputs=[
        'domain.snn_context',
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.current_time',
        'domain.snn_context.global_ctx.dream_noise_level'
    ],
    outputs=[
        'domain.snn_context.domain_ctx.neurons', # Potentials updated
        'domain.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_inject_dream_stimulus(ctx: SystemContext):
    """
    Inject random noise / replay patterns into neurons during sleep.
    
    Logic:
    - Stimulate neurons randomly to simulate 'REM' activity.
    - Low-level noise allows existing strong connections (Solid) to fire chains,
      reinforcing established memories (Consolidation).
    """
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    noise_level = getattr(global_ctx, 'dream_noise_level', 0.1)
    
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
