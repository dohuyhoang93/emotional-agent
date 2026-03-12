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
    COMMIT_STATE_REVOKED,
    ensure_heavy_tensors_initialized,
    sync_from_heavy_tensors
)
from src.core.context import SystemContext


@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context',
        'domain_ctx.snn_context.domain_ctx.metrics', # Added
        'domain_ctx.td_error'
    ],
    outputs=['domain_ctx', 
        'domain_ctx.snn_context.domain_ctx.synapses',
        'domain_ctx.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_commitment(ctx: SystemContext):
    """Decorator wrap cho _commitment_impl."""
    _commitment_impl(ctx)
    snn_ctx = ctx.domain_ctx.snn_context if hasattr(ctx, 'domain_ctx') else ctx
    return {
        'synapses': snn_ctx.domain_ctx.synapses,
        'metrics': snn_ctx.domain_ctx.metrics
    }

def _commitment_impl(ctx: SystemContext):
    """
    Commitment Layer Logic (Vectorized).
    """
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        rl_ctx = ctx
        snn_ctx = ctx.domain_ctx.snn_context
    else:
        rl_ctx = ctx
        snn_ctx = ctx
        
    global_ctx = snn_ctx.global_ctx
    domain = snn_ctx.domain_ctx
    
    avg_reward = domain.metrics.get('avg_reward', -1.0)
    base_threshold = int(global_ctx.commitment_threshold)
    
    if avg_reward < -20:
        THRESHOLD_SOLIDIFY = base_threshold * 5
    elif avg_reward < 0:
        THRESHOLD_SOLIDIFY = base_threshold * 2
    else:
        THRESHOLD_SOLIDIFY = base_threshold
        
    domain.metrics['commitment_threshold_dynamic'] = THRESHOLD_SOLIDIFY

    THRESHOLD_REVOKE = int(global_ctx.revoke_threshold)
    ERROR_THRESHOLD = float(global_ctx.prediction_error_threshold)
    try:
        error = abs(float(rl_ctx.domain_ctx.td_error))
    except Exception:
        error = 0.0
    
    ensure_heavy_tensors_initialized(snn_ctx)
    t = domain.heavy_tensors
    commit_states = t['commit_states']
    con_correct = t['consecutive_correct']
    con_wrong = t['consecutive_wrong']
    
    try:
        current_episode = int(rl_ctx.domain_ctx.current_episode)
    except:
        current_episode = 0
    
    if current_episode != domain.last_commitment_update_episode:
        domain.last_commitment_update_episode = current_episode
        if error < ERROR_THRESHOLD:
            t['consecutive_correct'] += 1
            t['consecutive_wrong'][:] = 0
        else:
            t['consecutive_wrong'] += 1
            t['consecutive_correct'][:] = 0
        
    newly_solid_mask = (commit_states == COMMIT_STATE_FLUID) & (t['consecutive_correct'] >= THRESHOLD_SOLIDIFY)
    commit_states[newly_solid_mask] = COMMIT_STATE_SOLID
    
    newly_revoked_mask = (commit_states == COMMIT_STATE_SOLID) & (t['consecutive_wrong'] >= THRESHOLD_REVOKE)
    commit_states[newly_revoked_mask] = COMMIT_STATE_REVOKED
    
    is_solid = (commit_states == COMMIT_STATE_SOLID)
    incoming_solid_count = np.sum(is_solid, axis=0)
    
    if 'weights' in t:
        incoming_total_count = np.sum(t['weights'] > 0, axis=0)
    else:
        incoming_total_count = np.ones(commit_states.shape[0])
    
    incoming_total_count[incoming_total_count == 0] = 1.0 
    ratios = (incoming_solid_count / incoming_total_count).astype(np.float32)
    t['solidity_ratios'] = ratios
    
    domain.metrics.update({
        'avg_solidity_ratio': float(np.mean(ratios)),
        'solid_neurons_count': int(np.sum(ratios > 0.5)),
        'solidified_count': domain.metrics.get('solidified_count', 0) + int(np.sum(newly_solid_mask)),
        'revoked_count': domain.metrics.get('revoked_count', 0) + int(np.sum(newly_revoked_mask)),
        'fluid_synapses': int(np.sum(commit_states == COMMIT_STATE_FLUID)),
        'solid_synapses': int(np.sum(commit_states == COMMIT_STATE_SOLID)),
        'revoked_synapses': int(np.sum(commit_states == COMMIT_STATE_REVOKED))
    })
    return {}


@process(
    inputs=['domain_ctx', 
        'domain_ctx.synapses',
        'domain_ctx.metrics' # Added
    ],
    outputs=['domain_ctx', 'domain_ctx.synapses', 'domain_ctx.metrics'],
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
    
    # FIX: Safe len via Core Patch
    before = len(domain.synapses)
    
    # Filter out REVOKED synapses
    domain.synapses = [
        s for s in domain.synapses
        if s.commit_state != COMMIT_STATE_REVOKED
    ]
    
    # FIX: Safe len via Core Patch
    pruned = before - len(domain.synapses)
    
    # Update metrics
    domain.metrics['pruned_count'] = \
        domain.metrics.get('pruned_count', 0) + pruned
    domain.metrics['active_synapses'] = len(domain.synapses)
    return {}
