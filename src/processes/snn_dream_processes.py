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
    outputs=[],
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
        ctx.log('error', f"CRASH in process_inject_dream_stimulus: {traceback.format_exc()}")
        raise
    return {}

def _inject_impl(ctx: SystemContext):
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    val = getattr(global_ctx, 'dream_noise_level', 0.1)
    
    try:
        noise_level = float(val)
    except Exception as e:
        ctx.log('debug', f"DEBUG: noise_level float cast failed: {e}")
        ctx.log('debug', f"DEBUG: noise_level dir: {dir(val)}")
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
            

@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context',
        'domain_ctx.snn_context.domain_ctx.metrics',
        'domain_ctx.intrinsic_reward'
    ],
    outputs=[],
    side_effects=[]
)
def apply_dream_reward(ctx: SystemContext):
    """
    Evaluate Dream Coherence and apply intrinsic reward/penalty.
    Used during SLEEP phase to reinforce stable patterns.
    
    Logic:
    - Goldilocks Zone (5% - 30% firing): Coherent (+0.1)
    - Silence (<5%): Boring (-0.2)
    - Epilepsy (>40%): Nightmare (-0.5)
    """
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    
    # Calculate Actual Firing Rate (Network Response)
    # Better than input noise check - captures epilepsy/silence
    current_time = domain.current_time
    active_neurons = 0
    for neuron in domain.neurons:
        if neuron.last_fire_time == current_time:
            active_neurons += 1
            
    total_neurons = len(domain.neurons)
    
    if total_neurons > 0:
        firing_rate = active_neurons / total_neurons
    else:
        firing_rate = 0.0
        
    # Coherence Reward Logic
    reward = 0.0
    
    if 0.05 <= firing_rate <= 0.3:
        # Coherent Dream (Good)
        reward = 0.1
        state = "COHERENT"
    elif firing_rate < 0.05:
        # Silence (Bad - nothing happening)
        reward = -0.2
        state = "SILENCE"
    else:
        # Epilepsy/Nightmare (Bad - chaos)
        reward = -0.5
        state = "NIGHTMARE"
        
    # Inject into intrinsic reward (for STDP to pick up)
    
    # Metrics
    domain.metrics['dream_coherence_state'] = state
    domain.metrics['dream_firing_rate'] = firing_rate
    domain.metrics['dream_reward'] = reward
    
    return {
        'domain_ctx.intrinsic_reward': reward
    }
