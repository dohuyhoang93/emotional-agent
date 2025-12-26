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
        'domain.snn_context',
        'domain.snn_context.domain_ctx.shadow_synapses',
        'domain.snn_context.domain_ctx.current_time',
        'domain.snn_context.domain_ctx.blacklisted_sources',
        'domain.snn_context.domain_ctx.metrics',
        'domain.td_error',
        'domain.last_reward'
    ],
    outputs=[
        'domain.snn_context.domain_ctx.shadow_synapses',
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.blacklisted_sources',
        'domain.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_quarantine_validation(
    ctx: SystemContext
):
    """
    Validate viral synapses trong quarantine sandbox.
    
    Args:
        ctx: RL system context
    """
    rl_ctx = ctx
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Get reward signal (Target)
    reward = rl_ctx.domain_ctx.last_reward.get('total', 0.0)
    native_error = abs(rl_ctx.domain_ctx.td_error) # |Target - Native|
    
    # Shadow Logic: Counterfactual Evaluation
    # Did the shadow synapse predict better?
    # Approximation:
    # 1. Check if Pre-neuron fired (Shadow active).
    # 2. If 'Yes', does the synapse Type match the 'Error Direction'?
    #    - If Native UNDER-estimated (Error > 0) AND Shadow is Excitatory -> REDUCES Error.
    #    - If Native OVER-estimated (Error < 0) AND Shadow is Inhibitory -> REDUCES Error.
    #    (Assumes simple signed error model)
    
    # Let's use TD Error directly (Target - Prediction)
    raw_error = rl_ctx.domain_ctx.td_error 
    
    # Init counters
    blacklisted = 0
    promoted = 0
    rejected = 0
    
    for synapse in domain.shadow_synapses:
        synapse.quarantine_time += 1
        
        # Check if active
        pre_neuron = domain.neurons[synapse.pre_neuron_id]
        if pre_neuron.last_fire_time == domain.current_time:
            # Synapse was active.
            # Would adding this weight have helped?
            # Output = Prediction.
            # New_Prediction = Prediction + Weight.
            # New_Error = Target - (Prediction + Weight) = (Target - Prediction) - Weight = raw_error - Weight
            
            new_error = abs(raw_error - synapse.weight)
            
            # IMPROVEMENT CONDITION
            if new_error < native_error:
                # Shadow improved reality!
                synapse.validation_score += 0.2  # Bonus
                domain.metrics['shadow_hit'] = domain.metrics.get('shadow_hit', 0) + 1
            else:
                # Shadow made it worse!
                synapse.validation_score -= 0.1
                domain.metrics['shadow_miss'] = domain.metrics.get('shadow_miss', 0) + 1
        
        else:
            # Synapse silent. Small decay or neutral?
            # Decay score slightly to encourage active participation?
            pass

        # CRITICAL: Blacklist logic remains (Safety Net)
        if reward < -0.5: # Major failure
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
        'domain.snn_context',
        'domain.snn_context.domain_ctx.shadow_synapses',
        'domain.snn_context.domain_ctx.blacklisted_sources',
        'domain.snn_context.domain_ctx.metrics'
    ],
    outputs=[
        'domain.snn_context.domain_ctx.shadow_synapses',
        'domain.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_inject_viral_with_quarantine(ctx: SystemContext):
    """
    Inject viral synapses vào quarantine (với blacklist check).
    
    Args:
        ctx: RL system context
    """
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    
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
