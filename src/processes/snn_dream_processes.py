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
        import logging
        logging.getLogger("Theus").error(f"CRASH in process_inject_dream_stimulus: {traceback.format_exc()}")
        raise
    return {}

def _inject_impl(ctx):
    # NOTE: domain_ctx.snn_context is a complex Python object that may not survive
    # Rust Core serialization. Try direct attribute access first, then fall back
    # to the underlying _target Python object (bypasses Rust proxy).
    domain_ctx = ctx.domain_ctx if not hasattr(ctx, '_target') else (ctx.domain_ctx if hasattr(ctx.domain_ctx, 'snn_context') else getattr(getattr(ctx, '_target', ctx), 'domain_ctx', ctx.domain_ctx))
    
    snn_ctx = None
    if hasattr(domain_ctx, 'snn_context'):
        snn_ctx = domain_ctx.snn_context
    
    # Fallback: reach into _target chain for live Python object
    if snn_ctx is None:
        target = getattr(ctx, '_target', None)
        if target is not None:
            dc = getattr(target, 'domain_ctx', None)
            if dc is not None:
                snn_ctx = getattr(dc, 'snn_context', None)
    
    if snn_ctx is None:
        raise AttributeError("Cannot find snn_context: domain_ctx does not contain snn_context (possibly lost during Rust serialization)")
    
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    val = getattr(global_ctx, 'dream_noise_level', 0.1)
    
    try:
        noise_level = float(val)
    except Exception as e:
        import logging
        logging.getLogger("Theus").debug(f"DEBUG: noise_level float cast failed: {e}")
        logging.getLogger("Theus").debug(f"DEBUG: noise_level dir: {dir(val)}")
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
def apply_dream_reward(ctx):
    """
    Evaluate Dream Coherence and apply intrinsic reward/penalty.
    Used during SLEEP phase to reinforce stable patterns.
    
    Logic:
    - Goldilocks Zone (5% - 30% firing): Coherent (+0.1)
    - Silence (<5%): Boring (-0.2)
    - Epilepsy (>40%): Nightmare (-0.5)
    """
    # NOTE: Same fallback pattern as _inject_impl for snn_context access
    snn_ctx = None
    try:
        snn_ctx = ctx.domain_ctx.snn_context
    except (AttributeError, RuntimeError):
        pass
    
    if snn_ctx is None:
        target = getattr(ctx, '_target', None)
        if target is not None:
            dc = getattr(target, 'domain_ctx', None)
            if dc is not None:
                snn_ctx = getattr(dc, 'snn_context', None)
    
    if snn_ctx is None:
        return {}
    
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
