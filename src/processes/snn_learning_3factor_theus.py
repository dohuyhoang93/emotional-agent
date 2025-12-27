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
        'domain.snn_context', # Implicit dependency
        'domain.td_error',
        'domain.snn_context.domain_ctx.synapses' 
    ],
    outputs=[
        'domain.snn_context.domain_ctx.synapses'
    ],
    side_effects=[]
)
def process_stdp_3factor(ctx: SystemContext):
    """
    3-Factor Learning: Hebbian + Dopamine với Protected Learning. Wraps _stdp_3factor_impl.
    """
    _stdp_3factor_impl(ctx)

def _stdp_3factor_impl(ctx: SystemContext):
    """Internal 3-factor learning implementation."""
    # Extract Contexts
    rl_ctx = ctx
    snn_ctx = ctx.domain_ctx.snn_context
    
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Compute dopamine signal từ TD-error
    # Compute dopamine signal từ TD-error
    td_error = rl_ctx.domain_ctx.td_error
    dopamine = float(np.tanh(td_error))  # Ensure scalar
    
    # Pre-fetch spikes for O(1) lookup
    current_spikes = set(domain.spike_queue.get(domain.current_time, []))
    
    # Single loop over synapses (O(S))
    for synapse in domain.synapses:
        # 1. Decay traces
        synapse.trace_fast *= global_ctx.tau_trace_fast
        synapse.trace_slow *= global_ctx.tau_trace_slow
        
        # 2. Update traces on spike
        if synapse.pre_neuron_id in current_spikes:
            synapse.trace_fast += 1.0
            synapse.trace_slow += 1.0
            synapse.last_active_time = domain.current_time
            
        # 3. Compute eligibility
        synapse.eligibility = synapse.trace_fast + synapse.trace_slow
        
        # 4 & 5. Learning & Decay (Skip REVOKED)
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
        
        # Weight decay
        synapse.weight *= global_ctx.weight_decay
        
        # Single clip at the end
        if synapse.weight > 1.0: synapse.weight = 1.0
        elif synapse.weight < 0.0: synapse.weight = 0.0
