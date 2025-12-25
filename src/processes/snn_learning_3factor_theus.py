"""
SNN 3-Factor Learning Processes for Theus Framework
====================================================
Synaptic Tagging với 3-factor learning rule (Hebbian × Dopamine).

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus import process
from src.core.snn_context_theus import (
    SNNSystemContext,
    COMMIT_STATE_FLUID,
    COMMIT_STATE_SOLID,
    COMMIT_STATE_REVOKED
)
from src.core.context import SystemContext


@process(
    inputs=[
        'domain_ctx.synapses',
        'domain_ctx.neurons',
        'domain_ctx.spike_queue',
        'domain_ctx.current_time',
        'global_ctx.learning_rate',
        'global_ctx.tau_trace_fast',
        'global_ctx.tau_trace_slow',
        'global_ctx.dopamine_learning_rate',
        'global_ctx.solid_learning_rate_factor',
        'rl_ctx.domain_ctx.td_error'  # ← Dopamine signal từ RL!
    ],
    outputs=[
        'domain_ctx.synapses'  # weight, traces updated
    ],
    side_effects=[]  # Pure function
)
def process_stdp_3factor(
    snn_ctx: SNNSystemContext,
    rl_ctx: SystemContext
):
    """
    3-Factor Learning: Hebbian + Dopamine với Protected Learning.
    
    Δw = η_dopamine · eligibility · D(t)
    
    where:
    - eligibility = trace_fast + trace_slow
    - D(t) = tanh(TD-error)  # Dopamine signal
    
    Protected Learning (Phase 7):
    - FLUID: Full learning rate
    - SOLID: 10% learning rate (protected)
    - REVOKED: Skip learning
    
    Multi-timescale traces:
    - trace_fast: Decay ~20ms (immediate Hebbian)
    - trace_slow: Decay ~5000ms (synaptic tag for delayed reward)
    
    NOTE: Nhận dopamine từ RL context.
    Pure function - no side effects.
    
    Args:
        snn_ctx: SNN system context
        rl_ctx: RL system context (for TD-error)
    """
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Compute dopamine signal từ TD-error
    td_error = rl_ctx.domain_ctx.td_error
    dopamine = np.tanh(td_error)  # Normalize [-1, 1]
    
    # 1. Decay traces
    for synapse in domain.synapses:
        synapse.trace_fast *= global_ctx.tau_trace_fast
        synapse.trace_slow *= global_ctx.tau_trace_slow
    
    # 2. Update traces on spike
    current_spikes = domain.spike_queue.get(domain.current_time, [])
    
    for spike_id in current_spikes:
        for synapse in domain.synapses:
            if synapse.pre_neuron_id == spike_id:
                # Increment traces
                synapse.trace_fast += 1.0
                synapse.trace_slow += 1.0
                synapse.last_active_time = domain.current_time
    
    # 3. Compute eligibility
    for synapse in domain.synapses:
        synapse.eligibility = synapse.trace_fast + synapse.trace_slow
    
    # 4. 3-Factor Learning với Protected Learning
    for synapse in domain.synapses:
        # Skip REVOKED synapses
        if synapse.commit_state == COMMIT_STATE_REVOKED:
            continue
        
        # Adjust learning rate based on commitment state
        if synapse.commit_state == COMMIT_STATE_SOLID:
            # Protected: 10% learning rate
            effective_lr = (
                global_ctx.dopamine_learning_rate *
                global_ctx.solid_learning_rate_factor
            )
        else:  # FLUID
            # Full learning rate
            effective_lr = global_ctx.dopamine_learning_rate
        
        # Δw = η · eligibility · dopamine
        delta_weight = effective_lr * synapse.eligibility * dopamine
        
        synapse.weight += delta_weight
        synapse.weight = np.clip(synapse.weight, 0.0, 1.0)
    
    # 5. Weight decay (optional)
    for synapse in domain.synapses:
        if synapse.commit_state != COMMIT_STATE_REVOKED:
            synapse.weight *= global_ctx.weight_decay
            synapse.weight = np.clip(synapse.weight, 0.0, 1.0)
