"""
SNN Social Learning Process
===========================
Viral synapse transfer (Social Learning) implementation in Theus POP.
Replaces legacy SocialLearningManager.

Author: Do Huy Hoang
Date: 2025-12-30
"""
import copy
from typing import List
from theus.contracts import process
from src.core.snn_context_theus import SNNSystemContext, SynapseState, SNNGlobalContext, SNNDomainContext

@process(
    inputs=[
        'global_ctx.social_learning_enabled',
        'domain_ctx.population_performance' 
    ],
    outputs=[
        'domain_ctx.metrics'
    ],
    side_effects=['synapse.injection']
)
def process_social_learning_protocol(
    global_snn_ctx: SNNSystemContext,
    population_contexts: List[SNNSystemContext],
    rankings: List[tuple]
):
    """
    Execute Social Learning: Transfer knowledge from Elite to Learners.
    
    Args:
        global_snn_ctx: Context containing Global Settings.
        population_contexts: List of all agent contexts.
        rankings: List of (agent_index, reward).
    """
    # Delegate to helper
    process_social_learning_with_rankings(
        population_contexts,
        rankings,
        global_snn_ctx.global_ctx
    )

def process_social_learning_with_rankings(
    population_contexts: List[SNNSystemContext],
    rankings: List[tuple], # (index, reward)
    global_config: SNNGlobalContext
):
    """
    Execute Social Learning using provided rankings.
    """
    elite_ratio = getattr(global_config, 'social_elite_ratio', 0.2)
    learner_ratio = getattr(global_config, 'social_learner_ratio', 0.5)
    synapses_k = getattr(global_config, 'social_synapses_per_transfer', 10)
    
    num_agents = len(population_contexts)
    if num_agents < 2:
        return

    # 1. Identify Groups
    # rankings is sorted list of (agent_index, reward)
    num_elite = max(1, int(num_agents * elite_ratio))
    num_learners = max(1, int(num_agents * learner_ratio))
    
    elite_indices = [r[0] for r in rankings[:num_elite]]
    learner_indices = [r[0] for r in rankings[-num_learners:]]
    
    # 2. Extract Elite Synapses
    extracted_synapses = []
    
    for idx in elite_indices:
        ctx = population_contexts[idx]
        syns = _extract_top_synapses(ctx.domain_ctx, synapses_k)
        extracted_synapses.extend(syns)
        
    # 3. Inject into Learners
    if not extracted_synapses:
        return
        
    for idx in learner_indices:
        ctx = population_contexts[idx]
        count = _inject_synapses(ctx.domain_ctx, extracted_synapses)
        
        # Log
        ctx.domain_ctx.metrics['social_learning_injected'] = count

def _extract_top_synapses(domain: SNNDomainContext, k: int) -> List[SynapseState]:
    if not domain.synapses:
        return []
        
    # Sort by abs weight
    sorted_syns = sorted(domain.synapses, key=lambda s: abs(s.weight), reverse=True)
    return sorted_syns[:k]

def _inject_synapses(domain: SNNDomainContext, synapses: List[SynapseState]) -> int:
    count = 0
    start_id = max((s.synapse_id for s in domain.synapses), default=0) + 1
    
    for syn in synapses:
        new_syn = copy.deepcopy(syn)
        # Re-ID to avoid collisions
        new_syn.synapse_id = start_id + count
        
        # Reset meta
        new_syn.pre_neuron_id = syn.pre_neuron_id # Keep topology?
        # Ideally we map topology, but if agents have identical layout (grid inputs), it works.
        # If neurons are allocated dynamically, ID mismatch ensures chaos?
        # Theus SNN assumes fixed Input Neurons (0-15).
        # Internal neurons might differ.
        # For now, we assume simple cloning (naive social learning).
        
        # Reset validation
        if hasattr(new_syn, 'quarantine_time'): new_syn.quarantine_time = 0
        if hasattr(new_syn, 'validation_score'): new_syn.validation_score = 0.0
        
        domain.synapses.append(new_syn)
        count += 1
        
    return count
