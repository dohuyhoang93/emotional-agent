"""
SNN Commitment Layer Processes for Theus Framework
===================================================
Commitment Layer với 3-state FSM để prevent catastrophic forgetting.

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
        'domain.snn_context',
        'domain.snn_context.domain_ctx.metrics', # Added
        'domain.td_error'
    ],
    outputs=[
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_commitment(
    ctx: SystemContext
):
    """
    Commitment Layer: FLUID → SOLID → REVOKED.
    
    Args:
        ctx: RL System Context
    """
    # Extract Contexts
    rl_ctx = ctx
    snn_ctx = ctx.domain_ctx.snn_context
    
    global_ctx = snn_ctx.global_ctx
    domain = snn_ctx.domain_ctx
    
    THRESHOLD_SOLIDIFY = global_ctx.commitment_threshold
    THRESHOLD_REVOKE = global_ctx.revoke_threshold
    ERROR_THRESHOLD = global_ctx.prediction_error_threshold
    
    error = abs(rl_ctx.domain_ctx.td_error)
    
    # Counters
    solidified = 0
    revoked = 0
    
    # Update commitment states
    for synapse in domain.synapses:
        # Check prediction correctness
        if error < ERROR_THRESHOLD:
            # Good prediction
            synapse.consecutive_correct += 1
            synapse.consecutive_wrong = 0
        else:
            # Bad prediction
            synapse.consecutive_wrong += 1
            synapse.consecutive_correct = 0
        
        # State transitions
        if synapse.commit_state == COMMIT_STATE_FLUID:
            # FLUID → SOLID
            if synapse.consecutive_correct >= THRESHOLD_SOLIDIFY:
                synapse.commit_state = COMMIT_STATE_SOLID
                synapse.confidence = 1.0
                solidified += 1
        
        elif synapse.commit_state == COMMIT_STATE_SOLID:
            # SOLID → REVOKED
            if synapse.consecutive_wrong >= THRESHOLD_REVOKE:
                synapse.commit_state = COMMIT_STATE_REVOKED
                synapse.confidence = 0.0
                revoked += 1
    
    # Update metrics
    domain.metrics['solidified_count'] = \
        domain.metrics.get('solidified_count', 0) + solidified
    domain.metrics['revoked_count'] = \
        domain.metrics.get('revoked_count', 0) + revoked
    
    # Count by state
    fluid_count = sum(1 for s in domain.synapses if s.commit_state == COMMIT_STATE_FLUID)
    solid_count = sum(1 for s in domain.synapses if s.commit_state == COMMIT_STATE_SOLID)
    revoked_count = sum(1 for s in domain.synapses if s.commit_state == COMMIT_STATE_REVOKED)
    
    domain.metrics['fluid_synapses'] = fluid_count
    domain.metrics['solid_synapses'] = solid_count
    domain.metrics['revoked_synapses'] = revoked_count


@process(
    inputs=[
        'domain_ctx.synapses',
        'domain_ctx.metrics' # Added
    ],
    outputs=['domain_ctx.synapses', 'domain_ctx.metrics'],
    side_effects=[]  # Pure function
)
def process_pruning(ctx: SNNSystemContext):
    """
    Xóa synapses REVOKED.
    
    NOTE: Pure function - filter list.
    
    Args:
        ctx: SNN system context
    """
    domain = ctx.domain_ctx
    
    before = len(domain.synapses)
    
    # Filter out REVOKED synapses
    domain.synapses = [
        s for s in domain.synapses
        if s.commit_state != COMMIT_STATE_REVOKED
    ]
    
    pruned = before - len(domain.synapses)
    
    # Update metrics
    domain.metrics['pruned_count'] = \
        domain.metrics.get('pruned_count', 0) + pruned
    domain.metrics['active_synapses'] = len(domain.synapses)
