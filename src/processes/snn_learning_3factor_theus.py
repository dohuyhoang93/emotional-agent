"""
SNN 3-Factor Learning Processes for Theus Framework
====================================================
Synaptic Tagging với 3-factor learning rule (Hebbian × Dopamine).

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus.contracts import process
from src.core.snn_context_theus import (
    COMMIT_STATE_SOLID,
    COMMIT_STATE_REVOKED
)
from src.core.context import SystemContext


@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context', 
        'domain_ctx.td_error',
        'domain_ctx.snn_context.domain_ctx.synapses' 
    ],
    outputs=['domain_ctx', 
        'domain_ctx.snn_context.domain_ctx.synapses'
    ],
    side_effects=[]
)
def process_stdp_3factor(ctx: SystemContext):
    """
    3-Factor Learning: Hebbian + Dopamine với Protected Learning. Wraps _stdp_3factor_impl.
    """
    try:
        _stdp_3factor_impl(ctx)
    except Exception:
        import traceback
        print(f"CRASH in process_stdp_3factor: {traceback.format_exc()}")
        raise

def _stdp_3factor_impl(ctx: SystemContext):
    """Internal 3-factor learning implementation."""
    # Extract Contexts
    rl_ctx = ctx
    snn_ctx = ctx.domain_ctx.snn_context
    
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Compute dopamine signal từ TD-error
    # Use explicit float cast for safety
    try:
        td_error = float(rl_ctx.domain_ctx.td_error)
    except Exception as e:
        # print(f"DEBUG: process_stdp_3factor td_error type: {type(rl_ctx.domain_ctx.td_error)}")
        td_error = 0.0

    dopamine = float(np.tanh(td_error))  # Ensure scalar
    
    # Pre-fetch spikes for O(1) lookup
    current_spikes = set(domain.spike_queue.get(domain.current_time, []))
    
    # Cast globals used in loop
    tau_fast = float(global_ctx.tau_trace_fast)
    tau_slow = float(global_ctx.tau_trace_slow)
    w_decay = float(global_ctx.weight_decay)
    
    # Single loop over synapses (O(S))
    for synapse in domain.synapses:
        # 1. Decay traces
        synapse.trace_fast *= tau_fast
        synapse.trace_slow *= tau_slow
        
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
                float(global_ctx.dopamine_learning_rate) *
                float(global_ctx.solid_learning_rate_factor)
            )
        else:  # FLUID
            # Full learning rate
            effective_lr = float(global_ctx.dopamine_learning_rate)
            
        # Δw = η · eligibility · dopamine
        delta_weight = effective_lr * synapse.eligibility * dopamine
        
        synapse.weight += delta_weight
        
        # Weight decay
        synapse.weight *= w_decay
        
        # Single clip at the end
        if synapse.weight > 1.0: synapse.weight = 1.0
        elif synapse.weight < 0.0: synapse.weight = 0.0
