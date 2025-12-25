"""
SNN Social Quarantine Processes for Theus Framework
====================================================
Social Quarantine: Safe viral synapse transfer với validation.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus import process
from src.core.snn_context_theus import SNNSystemContext
from src.core.context import SystemContext


@process(
    inputs=[
        'domain_ctx.shadow_synapses',
        'domain_ctx.current_time',
        'domain_ctx.blacklisted_sources',
        'rl_ctx.domain_ctx.td_error',
        'rl_ctx.domain_ctx.last_reward',
        'global_ctx.quarantine_duration',
        'global_ctx.validation_threshold'
    ],
    outputs=[
        'domain_ctx.shadow_synapses',
        'domain_ctx.synapses',
        'domain_ctx.blacklisted_sources',
        'domain_ctx.metrics'
    ],
    side_effects=[]  # Pure function
)
def process_quarantine_validation(
    snn_ctx: SNNSystemContext,
    rl_ctx: SystemContext
):
    """
    Validate viral synapses trong quarantine sandbox.
    
    Logic (from spec 9.2.1):
    1. Track performance trong quarantine period
    2. Promote nếu validation_score > threshold
    3. Reject và blacklist nếu negative reward
    
    NOTE: Pure function - no side effects.
    
    Args:
        snn_ctx: SNN system context
        rl_ctx: RL system context (for reward signal)
    """
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Get reward signal
    reward = rl_ctx.domain_ctx.last_reward.get('total', 0.0)
    error = abs(rl_ctx.domain_ctx.td_error)
    
    # Counters
    promoted = 0
    rejected = 0
    blacklisted = 0
    
    # Update quarantine synapses
    for synapse in domain.shadow_synapses:
        synapse.quarantine_time += 1
        
        # Update validation score based on performance
        if error < 0.1:
            # Good prediction
            synapse.validation_score += 0.1
        else:
            # Bad prediction
            synapse.validation_score -= 0.05
        
        # CRITICAL: Blacklist nếu negative reward
        if reward < 0:
            synapse.is_blacklisted = True
            if synapse.source_agent_id not in domain.blacklisted_sources:
                domain.blacklisted_sources.append(synapse.source_agent_id)
                blacklisted += 1
    
    # Check for promotion/rejection
    to_promote = []
    to_reject = []
    
    for synapse in domain.shadow_synapses:
        if synapse.quarantine_time >= global_ctx.quarantine_duration:
            if synapse.is_blacklisted:
                # Blacklisted → Reject
                to_reject.append(synapse)
                rejected += 1
            elif synapse.validation_score >= global_ctx.validation_threshold:
                # Validated → Promote
                to_promote.append(synapse)
                promoted += 1
            else:
                # Failed validation → Reject
                to_reject.append(synapse)
                rejected += 1
    
    # Promote validated synapses
    for synapse in to_promote:
        synapse.synapse_type = "native"
        domain.synapses.append(synapse)
    
    # Remove from quarantine
    domain.shadow_synapses = [
        s for s in domain.shadow_synapses
        if s not in to_promote and s not in to_reject
    ]
    
    # Update metrics
    domain.metrics['quarantine_promoted'] = \
        domain.metrics.get('quarantine_promoted', 0) + promoted
    domain.metrics['quarantine_rejected'] = \
        domain.metrics.get('quarantine_rejected', 0) + rejected
    domain.metrics['blacklisted_sources'] = len(domain.blacklisted_sources)
    domain.metrics['in_quarantine'] = len(domain.shadow_synapses)


@process(
    inputs=[
        'domain_ctx.shadow_synapses',
        'domain_ctx.blacklisted_sources'
    ],
    outputs=[
        'domain_ctx.shadow_synapses',
        'domain_ctx.metrics'
    ],
    side_effects=[]  # Pure function
)
def process_inject_viral_with_quarantine(ctx: SNNSystemContext):
    """
    Inject viral synapses vào quarantine (với blacklist check).
    
    NOTE: Viral synapses từ blacklisted sources bị reject ngay.
    
    Args:
        ctx: SNN system context
    """
    domain = ctx.domain_ctx
    
    # Filter out blacklisted sources
    before = len(domain.shadow_synapses)
    
    domain.shadow_synapses = [
        s for s in domain.shadow_synapses
        if s.source_agent_id not in domain.blacklisted_sources
    ]
    
    blocked = before - len(domain.shadow_synapses)
    
    # Update metrics
    domain.metrics['blacklist_blocked'] = \
        domain.metrics.get('blacklist_blocked', 0) + blocked
