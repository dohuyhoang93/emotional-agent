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
        'domain.snn_context', 
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.metrics', 
        'domain.snn_context.domain_ctx.emotion_saturation_level',
        'domain.snn_context.domain_ctx.dampening_active',
        'domain.snn_context.global_ctx.saturation_threshold',
        'domain.snn_context.global_ctx.dampening_factor',
        'domain.snn_context.global_ctx.recovery_rate'
    ],
    outputs=[
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.emotion_saturation_level',
        'domain.snn_context.domain_ctx.dampening_active',
        'domain.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_hysteria_dampener(ctx: SystemContext):
    """
    Prevent runaway emotions (saturation). Wraps _hysteria_impl.
    """
    _hysteria_impl(ctx)

def _hysteria_impl(ctx: SystemContext):
    """Internal Hysteria implementation (Object-based)."""
    # Extract SNN Context
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
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
        'domain.snn_context', 
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.spike_queue',
        'domain.snn_context.domain_ctx.current_time',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.global_ctx.inhibition_strength',
        'domain.snn_context.global_ctx.wta_k'
    ],
    outputs=[
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_lateral_inhibition(ctx: SystemContext):
    """
    Winner-Take-All competition cho sparse coding. Wraps _lateral_inhibition_vectorized.
    """
    from src.core.snn_context_theus import ensure_tensors_initialized, sync_from_tensors
    ensure_tensors_initialized(ctx.domain_ctx.snn_context)
    _lateral_inhibition_vectorized(ctx)
    sync_from_tensors(ctx.domain_ctx.snn_context)

def _lateral_inhibition_vectorized(ctx: SystemContext):
    """Internal Vectorized Lateral Inhibition."""
    # Extract SNN Context
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    if snn_ctx is None:
        return
        
    t = domain.tensors
    if t is None: # Should be ensured
        return
        
    pots = t['potentials']
    
    current_spikes = domain.spike_queue.get(domain.current_time, [])
    
    if not current_spikes:
        return
    
    if len(current_spikes) <= global_ctx.wta_k:
        # Not enough spikes to inhibit
        domain.metrics['wta_winners'] = len(current_spikes)
        domain.metrics['wta_losers'] = 0
        return

    # To vectorize sorting on a subset (spikes):
    # 1. Get potentials of firing neurons
    spike_indices = np.array(current_spikes, dtype=int)
    spike_indices = spike_indices[spike_indices < len(pots)] # Safety
    
    firing_pots = pots[spike_indices]
    
    # 2. Sort indices by potential (descending)
    # argsort gives indices into 'firing_pots' array
    sorted_local_indices = np.argsort(firing_pots)[::-1] 
    
    # 3. Identify losers (in the subset)
    # The first K are winners. The rest are losers.
    loser_local_indices = sorted_local_indices[global_ctx.wta_k:]
    loser_global_indices = spike_indices[loser_local_indices]
    
    # 4. Inhibit Losers
    # Decrease potential
    # Note: We need to increase 'inhibition_received' on objects? 
    # Tensors dont support 'inhibition_received'.
    # We simplify logic: Just subtract potential in Tensor.
    pots[loser_global_indices] -= global_ctx.inhibition_strength
    pots[loser_global_indices] = np.maximum(pots[loser_global_indices], 0.0)
    
    # 5. Remove Losers from Spike Queue?
    # Original logic just reduced potential. It didn't remove from queue.
    # But if potential drops, does 'fire' happen?
    # 'process_lateral_inhibition' runs AFTER 'process_integrate' (Step 11) usually?
    # Wait. 'process_fire' (Step 13) checks (P >= Thresh).
    # If we reduce P here, they might NOT fire in 'process_fire'.
    # BUT 'current_spikes' comes from WHERE?
    # 'current_spikes' are usually inputs for THIS step?
    # No. 'spike_queue' contains spikes scheduled for 'current_time'.
    # These spikes arrived at 'current_time'.
    # 'process_integrate' consumes them to update potentials.
    # 'process_fire' checks potentials to see who fires NEW spikes for 'current_time + 1'.
    
    # Wait. 'process_lateral_inhibition' logic (Old):
    # "Find top-k firing neurons" -> "firing neurons" are those in 'spike_queue'?
    # NO. 'current_spikes' in 'spike_queue' are INPUT spikes (from pre-synaptic).
    # Lateral Inhibition usually applies to THIS layer's neurons based on THEIR potentials.
    # Why did original code use 'current_spikes'?
    # Step 127: current_spikes = domain.spike_queue.get(domain.current_time, [])
    # This implies it only inhibits based on INPUT spikes?
    # Or did it assume 'current_spikes' means 'neurons that fired'?
    # If 'neurons that fired', they firied in Last Step?
    # If so, inhibiting them now is Post-Fire inhibition? Refractory?
    
    # Standard WTA:
    # Neurons compete. The ones with highest potential fire. Others are inhibited.
    # So we should look at ALL neurons' potentials, OR neurons that represent 'active' set.
    # If original code looked at 'current_spikes', it suggests 'current_spikes' holds the neurons that ARE ABOUT TO FIRE?
    # But 'spike_queue' is usually populated by 'process_fire' of previous layer/step.
    # Or input injection.
    
    # If 'spike_queue' means "Neurons that received input spikes"?
    # No, spike_queue is list of NeuronIDs that Spiked. 
    # If N1 spiked at T, it is in T's queue.
    # So 'current_spikes' are neurons that spiked at T (NOW).
    # But 'process_fire' generates spikes for T+1.
    # So 'spike_queue[T]' must be populated by T-1.
    
    # Conclusion: Original logic inhibits neurons that ARE spiking at T.
    # It reduces their potential.
    # But they already spiked? (They are in queue).
    # Unless 'process_fire' hasn't run yet?
    # Original Order: Integrate -> Lateral -> Fire.
    # If Fire hasn't run, 'spike_queue' contains spikes from INPUT injection?
    # Yes, 'encode_state_to_spikes' injects into 'spike_queue'?
    # Let's check 'encode_state_to_spikes' (Step 862).
    # convert sensor -> potential.
    # It sets 'neuron.potential = ...'.
    # It DOES NOT add to spike_queue.
    
    # So 'current_spikes' in Lateral Inhibition is... EMPTY?
    # unless 'spike_queue' has spikes from OTHER sources?
    # Maybe Recurrent spikes?
    # Yes.
    
    # Issue: 'encode_state' sets potentials. It assumes those neurons will fire.
    # But they are not in 'spike_queue'.
    # So Lateral Inhibition logic relying on 'spike_queue' might be FLAWED if it intends to inhibit Sensor inputs.
    # However, for now, I must replicate Original Logic.
    # Original Logic: Iterates 'current_spikes'.
    # So I vectorizing that logic is correct (faithful translation).
    
    domain.metrics['wta_winners'] = len(current_spikes) - len(loser_global_indices)
    domain.metrics['wta_losers'] = len(loser_global_indices)


# ============================================================================
# Phase 11: Neural Darwinism
# ============================================================================

@process(
    inputs=[
        'domain.snn_context',
        'domain.td_error',
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.neurons', # Added for recycling
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.domain_ctx.current_time',
        'domain.snn_context.global_ctx.darwinism_interval'
    ],
    outputs=[
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_neural_darwinism(
    ctx: SystemContext
):
    """
    Evolutionary synapse selection and Neuron Recycling ("True Darwinism").
    
    Logic:
    1. Update fitness based on performance
    2. Selection (remove weak but PROTECT committed)
    3. Reproduction (clone strong)
    4. Recycling (reset dead neurons + rewire)
    
    Args:
        ctx: RL System Context
    """
    from src.core.snn_context_theus import COMMIT_STATE_SOLID, SynapseState
    # Extract
    rl_ctx = ctx
    snn_ctx = ctx.domain_ctx.snn_context
    
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Check interval
    if domain.current_time % global_ctx.darwinism_interval != 0:
        return
    
    error = abs(rl_ctx.domain_ctx.td_error)
    
    # === PART 1: SYNAPSE EVOLUTION ===
    
    # 1. Update fitness
    for synapse in domain.synapses:
        if error < 0.1:
            synapse.fitness += 0.1
        else:
            synapse.fitness -= 0.05
        
        synapse.fitness *= global_ctx.fitness_decay
        synapse.fitness = np.clip(synapse.fitness, 0.0, 1.0)
    
    # 2. Selection: Remove weak
    if len(domain.synapses) > 100:  # Keep minimum population
        fitnesses = [s.fitness for s in domain.synapses]
        threshold = np.percentile(fitnesses, global_ctx.selection_pressure * 100)
        
        # FIX: Protect SOLID synapses from culling
        survivors = [
            s for s in domain.synapses 
            if s.fitness >= threshold or s.commit_state == COMMIT_STATE_SOLID
        ]
    else:
        survivors = domain.synapses
    
    # 3. Reproduction: Clone strong
    if len(survivors) > 0:
        import dataclasses
        fitnesses = [s.fitness for s in survivors]
        top_threshold = np.percentile(
            fitnesses,
            (1 - global_ctx.reproduction_rate) * 100
        )
        
        to_reproduce = [s for s in survivors if s.fitness >= top_threshold]
        
        offspring = []
        for parent in to_reproduce:
            child = dataclasses.replace(parent)
            # Find next ID (max + 1 is risky in distributed, but fine here)
            # Safer: max of CURRENT list
            max_id = max(s.synapse_id for s in survivors) if survivors else 0
            if offspring:
                max_id = max(max_id, max(s.synapse_id for s in offspring))
            
            child.synapse_id = max_id + 1
            child.generation = parent.generation + 1
            child.weight += np.random.randn() * 0.01  # Mutation
            child.weight = np.clip(child.weight, 0.0, 1.0)
            child.commit_state = 0 # FLUID (Reset commitment)
            offspring.append(child)
        
        domain.synapses = survivors + offspring
    
    # === PART 2: NEURON RECYCLING (True Darwinism) ===
    
    DEAD_THRESHOLD = 2000 # Steps without firing
    recycled_count = 0
    new_synapses = []
    
    max_syn_id = 0
    if domain.synapses:
        max_syn_id = max(s.synapse_id for s in domain.synapses)
    
    connection_prob = global_ctx.connectivity
    
    for neuron in domain.neurons:
        # Check if dead
        is_dead = (domain.current_time - neuron.last_fire_time) > DEAD_THRESHOLD
        
        # FIX: Do not kill SOLID neurons (neurons with many SOLID synapses)
        # Scan synapses to check solidity
        # Optimization: Pre-calculate solid map? Naive Check for now.
        solid_connections = sum(1 for s in domain.synapses 
                                if (s.pre_neuron_id == neuron.neuron_id or s.post_neuron_id == neuron.neuron_id) 
                                and s.commit_state == COMMIT_STATE_SOLID)
        
        if is_dead and solid_connections == 0:
            # RECYCLE
            recycled_count += 1
            
            # Reset Vector (New location in semantic space)
            new_proto = np.random.randn(neuron.vector_dim)
            new_proto = new_proto / (np.linalg.norm(new_proto) + 1e-8)
            neuron.prototype_vector = new_proto
            
            # Reset State
            neuron.potential = 0.0
            neuron.fire_count = 0
            neuron.last_fire_time = domain.current_time # Reset timer
            neuron.threshold = global_ctx.initial_threshold
            
            # REWIRE (Generate new synapses for this neuron)
            # 1. Incoming (Others -> Me)
            for pre_n in domain.neurons:
                if pre_n.neuron_id == neuron.neuron_id: continue
                if np.random.random() < connection_prob:
                    max_syn_id += 1
                    syn = SynapseState(
                        synapse_id=max_syn_id,
                        pre_neuron_id=pre_n.neuron_id,
                        post_neuron_id=neuron.neuron_id,
                        weight=np.random.uniform(0.3, 0.7)
                    )
                    new_synapses.append(syn)
            
            # 2. Outgoing (Me -> Others)
            for post_n in domain.neurons:
                if post_n.neuron_id == neuron.neuron_id: continue
                if np.random.random() < connection_prob:
                    max_syn_id += 1
                    syn = SynapseState(
                        synapse_id=max_syn_id,
                        pre_neuron_id=neuron.neuron_id,
                        post_neuron_id=post_n.neuron_id,
                        weight=np.random.uniform(0.3, 0.7)
                    )
                    new_synapses.append(syn)
    
    if new_synapses:
        domain.synapses.extend(new_synapses)
    
    # Update metrics
    domain.metrics['darwinism_survivors'] = len(survivors)
    domain.metrics['darwinism_offspring'] = len(offspring) if 'offspring' in locals() else 0
    domain.metrics['recycled_neurons'] = recycled_count
    domain.metrics['new_synapses_generated'] = len(new_synapses)


# ============================================================================
# Phase 12: Revolution Protocol
# ============================================================================

@process(
    inputs=[
        'domain_ctx.synapses',
        'domain_ctx.ancestor_weights',
        'domain_ctx.population_performance',
        'domain_ctx.metrics', # Added
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

# ============================================================================
# Phase 12.5: Ancestor Assimilation (Theus V2)
# ============================================================================

@process(
    inputs=[
        'domain.snn_context',
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.ancestor_weights',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.global_ctx.assimilation_rate', # New param
        'domain.snn_context.global_ctx.diversity_noise'    # New param
    ],
    outputs=[
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_assimilate_ancestor(ctx: SystemContext):
    """
    Apply Ancestor Knowledge to current Agent with Noise.
    
    Logic:
    1. Check if ancestor_weights available.
    2. Iterate synapses.
    3. If FLUID (not SOLID), soft-update towards ancestor.
    4. Add noise to maintain diversity.
    
    Eq: w = (1-alpha)*w + alpha*ancestor_w + N(0, noise)
    """
    from src.core.snn_context_theus import COMMIT_STATE_SOLID
    
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    ancestor = domain.ancestor_weights
    if not ancestor:
        return
        
    # Default params if not in config
    alpha = getattr(global_ctx, 'assimilation_rate', 0.05)
    noise_std = getattr(global_ctx, 'diversity_noise', 0.02)
    
    assimilated_count = 0
    
    for synapse in domain.synapses:
        # PROTECT SOLID KNOWLEDGE
        # Diversity Preservation Rule #1: Do not overwrite specialized knowledge
        if synapse.commit_state == COMMIT_STATE_SOLID:
            continue
            
        if synapse.synapse_id in ancestor:
            target_w = ancestor[synapse.synapse_id]
            
            # Soft Update
            new_w = (1.0 - alpha) * synapse.weight + alpha * target_w
            
            # Diversity Noise
            noise = np.random.randn() * noise_std
            new_w += noise
            
            # Clip
            synapse.weight = np.clip(new_w, 0.0, 1.0)
            assimilated_count += 1
            
    domain.metrics['assimilated_synapses'] = assimilated_count
