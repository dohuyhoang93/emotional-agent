"""
SNN Dream Safety Processes
===========================
Processes for ensuring stability and coherence during Dream state.

Author: Theus Agent
Date: 2025-12-27
"""
from theus.contracts import process
from src.core.context import SystemContext

@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context',
        'domain_ctx.snn_context.domain_ctx.metrics',
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.td_error'
    ],
    outputs=[],
    side_effects=[]
)
def process_dream_coherence_reward(ctx: SystemContext):
    """
    Generate intrinsic reward based on neural coherence.
    """
    try:
        _coherence_impl(ctx)
    except Exception:
        import traceback
        print(f"CRASH in process_dream_coherence_reward: {traceback.format_exc()}")
        raise
    return {}

def _coherence_impl(ctx: SystemContext):
    """Internal coherence implementation."""
    # Extract Contexts
    snn_ctx = ctx.domain_ctx.snn_context
    if snn_ctx is None: # Added this check, as it was in the original function
        return
    domain = snn_ctx.domain_ctx
    
    # 1. Calculate Coherence (Synchrony)
    # Metric: Ratio of active neurons
    active_count = 0
    # Use metrics from 'fire' process?
    # Or count now?
    # 'fire' process runs before this.
    # But fire process updates 'spike_queue' for Future.
    # We want CURRENT activity.
    # Current active neurons are those whose last_fire_time == current_time
    
    # Vectorized count
    # Tensors are synced?
    # We can check 'last_fire_time' on objects or tensors.
    
    current_time = domain.current_time
    
    # Check objects (synced)
    active_count = 0
    for neuron in domain.neurons:
        if neuron.last_fire_time == current_time:
            active_count += 1
            
    total_neurons = len(domain.neurons)
    if total_neurons == 0:
        return
        
    active_ratio = active_count / total_neurons
    
    # 2. Reward Shaping
    # Desired: ~10% activation (Lucid Dream)
    # Too low (<1%): Boredom (Negative)
    # Too high (>30%): Chaos/Seizure (Negative)
    
    reward = 0.0
    
    if active_ratio < 0.05:
        # Penalize
        reward = -0.1
    elif active_ratio > 0.30:
        # Penalize chaos
        reward = -0.05 * (active_ratio / 0.30)
    else:
        # Sweet spot
        reward = 0.1 * (1.0 - abs(active_ratio - 0.15)/0.15)
        
    # Write to TD Error (which drives modulation)
    # RL agent reads TD error for updates.
    # In Dream, we overwrite it to drive internal learning.
    
    # Cast reward to float just in case
    ctx.domain_ctx.td_error = float(reward)
    
    # Log
    domain.metrics['coherence_reward'] = float(reward)
    domain.metrics['active_ratio'] = float(active_ratio)
    
    # Update TD Error for STDP
    # Note: Dream reinforcement is subtle, so we use small values.
    ctx.domain_ctx.td_error = reward
