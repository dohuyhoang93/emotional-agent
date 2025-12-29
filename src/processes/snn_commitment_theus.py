"""
SNN Commitment Layer Processes for Theus Framework
===================================================
Commitment Layer với 3-state FSM để prevent catastrophic forgetting.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus.contracts import process
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
    
    # === VECTORIZED UPDATE ===
    from src.core.snn_context_theus import ensure_tensors_initialized, sync_from_tensors
    
    ensure_tensors_initialized(snn_ctx)
    t = domain.tensors
    
    commit_states = t['commit_states']
    con_correct = t['consecutive_correct']
    con_wrong = t['consecutive_wrong']
    
    # 1. Update Counters (Global Error Broadcast)
    if error < ERROR_THRESHOLD:
        # Good prediction: Increment correct, Reset wrong for ALL synapses
        con_correct += 1
        con_wrong[:] = 0 # Reset all to 0
    else:
        # Bad prediction: Increment wrong, Reset correct
        con_wrong += 1
        con_correct[:] = 0
        
    # 2. State Transitions
    
    # FLUID -> SOLID
    # Condition: Is Fluid AND Correct streak met
    newly_solid_mask = (commit_states == COMMIT_STATE_FLUID) & (con_correct >= THRESHOLD_SOLIDIFY)
    commit_states[newly_solid_mask] = COMMIT_STATE_SOLID
    # Note: Confidence update? Logic says confidence=1.0. Tensors don't store confidence yet.
    # It will be updated on Sync if we map it, OR we skip it for now.
    # The original loop updated object immediately.
    # Sync_from_tensors does NOT update 'confidence'. 
    # Can we derive confidence from state? Yes.
    # But for full fidelity, we might need a 'confidence' tensor later.
    # For now, Commit State is the Source of Truth.
    
    # SOLID -> REVOKED
    newly_revoked_mask = (commit_states == COMMIT_STATE_SOLID) & (con_wrong >= THRESHOLD_REVOKE)
    commit_states[newly_revoked_mask] = COMMIT_STATE_REVOKED
    
    # 3. Metrics
    solidified = np.sum(newly_solid_mask)
    revoked = np.sum(newly_revoked_mask)
    
    domain.metrics['solidified_count'] = \
        domain.metrics.get('solidified_count', 0) + int(solidified)
    domain.metrics['revoked_count'] = \
        domain.metrics.get('revoked_count', 0) + int(revoked)
    
    # Sync Back to Objects (O(S) but necessary for Pruning)
    sync_from_tensors(snn_ctx)
    
    # Count by state (Vectorized)
    fluid_count = np.sum(commit_states == COMMIT_STATE_FLUID)
    solid_count = np.sum(commit_states == COMMIT_STATE_SOLID)
    revoked_count = np.sum(commit_states == COMMIT_STATE_REVOKED)
    
    domain.metrics['fluid_synapses'] = int(fluid_count)
    domain.metrics['solid_synapses'] = int(solid_count)
    domain.metrics['revoked_synapses'] = int(revoked_count)


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
