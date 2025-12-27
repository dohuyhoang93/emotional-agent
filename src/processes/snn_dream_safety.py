"""
SNN Dream Safety Processes
===========================
Processes for ensuring stability and coherence during Dream state.

Author: Theus Agent
Date: 2025-12-27
"""
from theus import process
from src.core.context import SystemContext

@process(
    inputs=[
        'domain.snn_context',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.domain_ctx.neurons',
        'domain.td_error'
    ],
    outputs=[
        'domain.td_error',
        'domain.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_dream_coherence_reward(ctx: SystemContext):
    """
    Generate synthetic reward (td_error) based on neural coherence.
    
    Logic:
    - Measures 'Active Ratio' (percentage of neurons firing).
    - If too low (< 5%) -> Chaos/Silence (Penalty -0.1)
    - If too high (> 30%) -> Epilepsy/Seizure (Penalty -0.5)
    - If optimal (5% - 30%) -> Coherence (Reward +0.1)
    
    This guides STDP to consolidate stable, moderate-activity patterns.
    """
    snn_ctx = ctx.domain_ctx.snn_context
    if snn_ctx is None:
        return
        
    domain = snn_ctx.domain_ctx
    
    # Calculate Active Ratio
    firing_count = 0
    total_neurons = len(domain.neurons)
    
    for neuron in domain.neurons:
        if neuron.fire_count > 0:
            firing_count += 1
            
    active_ratio = firing_count / total_neurons if total_neurons > 0 else 0
    
    # Reward Logic
    reward = 0.0
    
    if active_ratio < 0.05:
        # Too quiet / Noise only
        reward = -0.1
        state = "underactive"
    elif active_ratio > 0.30:
        # Seizure / Epilepsy
        reward = -0.5
        state = "epilepsy"
    else:
        # Sweet spot (Coherent activation)
        reward = 0.1
        state = "coherent"
        
    # Validation Logging
    domain.metrics['dream_coherence_state'] = state
    domain.metrics['dream_active_ratio'] = active_ratio
    
    # Update TD Error for STDP
    # Note: Dream reinforcement is subtle, so we use small values.
    ctx.domain_ctx.td_error = reward
