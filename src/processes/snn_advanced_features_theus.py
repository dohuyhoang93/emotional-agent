"""
SNN Advanced Features: Phase 9-12
==================================
Hysteria Dampener, Lateral Inhibition, Neural Darwinism, Revolution Protocol.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
import copy
from theus import process
from src.core.snn_context_theus import SNNSystemContext
from src.core.context import SystemContext
from typing import List


# ============================================================================
# Phase 9: Hysteria Dampener
# ============================================================================

@process(
    inputs=[
        'domain_ctx.neurons',
        'domain_ctx.metrics.fire_rate',
        'domain_ctx.emotion_saturation_level',
        'domain_ctx.dampening_active',
        'global_ctx.saturation_threshold',
        'global_ctx.dampening_factor',
        'global_ctx.recovery_rate'
    ],
    outputs=[
        'domain_ctx.neurons',
        'domain_ctx.emotion_saturation_level',
        'domain_ctx.dampening_active',
        'domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_hysteria_dampener(ctx: SNNSystemContext):
    """
    Prevent runaway emotions (saturation).
    
    Logic (from spec 9.2.2):
    1. Detect saturation (fire_rate > threshold)
    2. Apply dampening (increase thresholds)
    3. Gradual recovery
    
    Args:
        ctx: SNN system context
    """
    domain = ctx.domain_ctx
    global_ctx = ctx.global_ctx
    
    fire_rate = domain.metrics.get('fire_rate', 0.0)
    
    # Detect saturation
    if fire_rate > global_ctx.saturation_threshold:
        domain.dampening_active = True
        domain.emotion_saturation_level += 0.1
    else:
        # Recovery
        domain.emotion_saturation_level -= global_ctx.recovery_rate
    
    domain.emotion_saturation_level = np.clip(
        domain.emotion_saturation_level, 0.0, 1.0
    )
    
    # Apply dampening
    if domain.dampening_active:
        for neuron in domain.neurons:
            neuron.threshold *= (1 + global_ctx.dampening_factor)
            neuron.threshold = np.clip(
                neuron.threshold,
                global_ctx.threshold_min,
                global_ctx.threshold_max
            )
        
        # Deactivate if recovered
        if domain.emotion_saturation_level < 0.1:
            domain.dampening_active = False
    
    # Update metrics
    domain.metrics['saturation_level'] = domain.emotion_saturation_level
    domain.metrics['dampening_active'] = 1 if domain.dampening_active else 0


# ============================================================================
# Phase 10: Lateral Inhibition
# ============================================================================

@process(
    inputs=[
        'domain_ctx.neurons',
        'domain_ctx.spike_queue',
        'domain_ctx.current_time',
        'global_ctx.inhibition_strength',
        'global_ctx.wta_k'
    ],
    outputs=[
        'domain_ctx.neurons',
        'domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_lateral_inhibition(ctx: SNNSystemContext):
    """
    Winner-Take-All competition cho sparse coding.
    
    Logic:
    1. Find top-k firing neurons
    2. Inhibit losers
    3. Sparse representation
    
    Args:
        ctx: SNN system context
    """
    domain = ctx.domain_ctx
    global_ctx = ctx.global_ctx
    
    current_spikes = domain.spike_queue.get(domain.current_time, [])
    
    if not current_spikes:
        return
    
    # Sort by potential (winners)
    firing_neurons = [
        (i, domain.neurons[i]) for i in current_spikes
    ]
    firing_neurons.sort(key=lambda x: x[1].potential, reverse=True)
    
    # Top-k winners
    winners = firing_neurons[:global_ctx.wta_k]
    losers = firing_neurons[global_ctx.wta_k:]
    
    # Inhibit losers
    for idx, neuron in losers:
        neuron.inhibition_received += global_ctx.inhibition_strength
        neuron.potential -= neuron.inhibition_received
        neuron.potential = max(neuron.potential, 0.0)
    
    # Update metrics
    domain.metrics['wta_winners'] = len(winners)
    domain.metrics['wta_losers'] = len(losers)


# ============================================================================
# Phase 11: Neural Darwinism
# ============================================================================

@process(
    inputs=[
        'domain_ctx.synapses',
        'rl_ctx.domain_ctx.td_error',
        'global_ctx.selection_pressure',
        'global_ctx.reproduction_rate',
        'global_ctx.fitness_decay'
    ],
    outputs=[
        'domain_ctx.synapses',
        'domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_neural_darwinism(
    snn_ctx: SNNSystemContext,
    rl_ctx: SystemContext
):
    """
    Evolutionary synapse selection.
    
    Logic:
    1. Update fitness based on performance
    2. Selection (remove weak)
    3. Reproduction (clone strong)
    
    Args:
        snn_ctx: SNN system context
        rl_ctx: RL system context
    """
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    error = abs(rl_ctx.domain_ctx.td_error)
    
    # 1. Update fitness
    for synapse in domain.synapses:
        if error < 0.1:
            synapse.fitness += 0.1
        else:
            synapse.fitness -= 0.05
        
        synapse.fitness *= global_ctx.fitness_decay
        synapse.fitness = np.clip(synapse.fitness, 0.0, 1.0)
    
    # 2. Selection: Remove weak
    if len(domain.synapses) > 10:  # Keep minimum population
        fitnesses = [s.fitness for s in domain.synapses]
        threshold = np.percentile(fitnesses, global_ctx.selection_pressure * 100)
        
        survivors = [s for s in domain.synapses if s.fitness >= threshold]
    else:
        survivors = domain.synapses
    
    # 3. Reproduction: Clone strong
    if len(survivors) > 0:
        fitnesses = [s.fitness for s in survivors]
        top_threshold = np.percentile(
            fitnesses,
            (1 - global_ctx.reproduction_rate) * 100
        )
        
        to_reproduce = [s for s in survivors if s.fitness >= top_threshold]
        
        offspring = []
        for parent in to_reproduce:
            child = copy.deepcopy(parent)
            child.synapse_id = len(survivors) + len(offspring)
            child.generation = parent.generation + 1
            child.weight += np.random.randn() * 0.01  # Mutation
            child.weight = np.clip(child.weight, 0.0, 1.0)
            offspring.append(child)
        
        domain.synapses = survivors + offspring
    
    # Update metrics
    domain.metrics['darwinism_survivors'] = len(survivors)
    domain.metrics['darwinism_offspring'] = len(offspring) if 'offspring' in locals() else 0


# ============================================================================
# Phase 12: Revolution Protocol
# ============================================================================

@process(
    inputs=[
        'domain_ctx.synapses',
        'domain_ctx.ancestor_weights',
        'domain_ctx.population_performance',
        'rl_ctx.domain_ctx.last_reward',
        'global_ctx.revolution_threshold',
        'global_ctx.revolution_window',
        'global_ctx.top_elite_percent'
    ],
    outputs=[
        'domain_ctx.ancestor_weights',
        'domain_ctx.revolution_triggered',
        'domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_revolution_protocol(
    snn_ctx: SNNSystemContext,
    rl_ctx: SystemContext,
    population_contexts: List[SNNSystemContext] = None
):
    """
    Cultural Evolution: Update ancestor khi quần thể vượt trội.
    
    Logic (from spec 9.2.3):
    1. Track performance của tất cả agents
    2. Check nếu >60% outperform ancestor trong 1000 cycles
    3. Vote từ top 10% agents
    4. Update ancestor weights
    
    NOTE: Cần multi-agent context. Single-agent mode sẽ skip.
    
    Args:
        snn_ctx: Current agent context
        rl_ctx: RL context
        population_contexts: All agents (optional)
    """
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Single-agent mode: Skip
    if population_contexts is None or len(population_contexts) <= 1:
        domain.metrics['revolution_skipped'] = 1
        return
    
    # 1. Collect performance
    current_reward = rl_ctx.domain_ctx.last_reward.get('total', 0.0)
    domain.population_performance.append(current_reward)
    
    # Keep only recent window
    if len(domain.population_performance) > global_ctx.revolution_window:
        domain.population_performance = domain.population_performance[-global_ctx.revolution_window:]
    
    # 2. Check revolution condition
    if len(domain.population_performance) < global_ctx.revolution_window:
        return  # Not enough data
    
    # Compute ancestor performance
    if not domain.ancestor_weights:
        # Initialize ancestor
        domain.ancestor_weights = {
            s.synapse_id: s.weight
            for s in domain.synapses[:100]  # Sample
        }
        return
    
    ancestor_perf = np.mean(list(domain.ancestor_weights.values()))
    
    # Count outperformers
    outperform_count = sum(
        1 for p in domain.population_performance
        if p > ancestor_perf
    )
    outperform_ratio = outperform_count / len(domain.population_performance)
    
    # 3. Trigger revolution
    if outperform_ratio > global_ctx.revolution_threshold:
        domain.revolution_triggered = True
        
        # 4. Voting: Top 10% elite
        all_perfs = [
            (i, np.mean(ctx.domain_ctx.population_performance[-100:]))
            for i, ctx in enumerate(population_contexts)
            if len(ctx.domain_ctx.population_performance) > 0
        ]
        
        if all_perfs:
            all_perfs.sort(key=lambda x: x[1], reverse=True)
            elite_count = max(1, int(len(all_perfs) * global_ctx.top_elite_percent))
            elite_indices = [idx for idx, _ in all_perfs[:elite_count]]
            
            # 5. Compute new ancestor
            new_ancestor = {}
            for syn_id in domain.ancestor_weights.keys():
                elite_weights = []
                for idx in elite_indices:
                    elite_ctx = population_contexts[idx]
                    for syn in elite_ctx.domain_ctx.synapses:
                        if syn.synapse_id == syn_id:
                            elite_weights.append(syn.weight)
                
                if elite_weights:
                    new_ancestor[syn_id] = np.mean(elite_weights)
            
            # 6. Update ancestor
            if new_ancestor:
                domain.ancestor_weights = new_ancestor
                domain.metrics['revolution_count'] = \
                    domain.metrics.get('revolution_count', 0) + 1
    
    # Update metrics
    domain.metrics['outperform_ratio'] = outperform_ratio
