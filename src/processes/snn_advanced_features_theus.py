"""
SNN Advanced Features: Phase 9-12
==================================
Hysteria Dampener, Lateral Inhibition, Neural Darwinism, Revolution Protocol.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus.contracts import process
from src.core.snn_context_theus import SNNSystemContext
from src.core.context import SystemContext
from typing import List


# ============================================================================
# Phase 9: Hysteria Dampener
# ============================================================================

@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context', 
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.snn_context.domain_ctx.metrics', 
        'domain_ctx.snn_context.domain_ctx.emotion_saturation_level',
        'domain_ctx.snn_context.domain_ctx.dampening_active',
        'domain_ctx.snn_context.global_ctx.saturation_threshold',
        'domain_ctx.snn_context.global_ctx.dampening_factor',
        'domain_ctx.snn_context.global_ctx.recovery_rate'
    ],
    outputs=['domain_ctx', 
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.snn_context.domain_ctx.emotion_saturation_level',
        'domain_ctx.snn_context.domain_ctx.dampening_active',
        'domain_ctx.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_hysteria_dampener(ctx: SystemContext):
    """
    Prevent runaway emotions (saturation). Wraps _hysteria_impl.
    """
    try:
        _hysteria_impl(ctx)
    except Exception:
        import traceback
        print(f"CRASH in process_hysteria_dampener: {traceback.format_exc()}")
        raise

def _hysteria_impl(ctx: SystemContext):
    """Internal Hysteria implementation (Object-based)."""
    # Extract SNN Context
    # Resolve SNN Context (Handle nested RL Context vs Standalone SNN Context)
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    
    fire_rate = domain.metrics.get('fire_rate', 0.0)
    try:
        current_level = float(domain.emotion_saturation_level)
    except:
        current_level = 0.0
    
    # Direct access (validated as float)
    try:
        sat_threshold = float(global_ctx.saturation_threshold)
        rec_rate = float(global_ctx.recovery_rate)
        damp_factor = float(global_ctx.dampening_factor)
    except (TypeError, AttributeError):
        # Fallback for ContextGuard issues
        sat_threshold = 0.9
        rec_rate = 0.01
        damp_factor = 0.5

    # Detect saturation
    if fire_rate > sat_threshold:
        domain.dampening_active = True
        current_level += 0.1
    else:
        # Recovery
        current_level -= rec_rate
    
    domain.emotion_saturation_level = np.clip(
        current_level, 0.0, 1.0
    )
    
    # Apply dampening
    # Apply dampening (Vectorized)
    if domain.dampening_active:
        from src.core.snn_context_theus import ensure_heavy_tensors_initialized, sync_from_heavy_tensors
        
        # Ensure tensors on the SNN context
        ensure_heavy_tensors_initialized(snn_ctx)
        t = domain.heavy_tensors
        
        # Vector Update: Multiply all thresholds
        t['thresholds'] *= (1 + damp_factor)
        
        # Clip
        np.clip(
            t['thresholds'],
            global_ctx.threshold_min,
            global_ctx.threshold_max,
            out=t['thresholds']
        )
        
        # Sync back
        sync_from_heavy_tensors(snn_ctx)
        
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
    inputs=['domain_ctx', 
        'domain_ctx.snn_context', 
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.snn_context.domain_ctx.spike_queue',
        'domain_ctx.snn_context.domain_ctx.current_time',
        'domain_ctx.snn_context.domain_ctx.metrics',
        'domain_ctx.snn_context.global_ctx.inhibition_strength',
        'domain_ctx.snn_context.global_ctx.wta_k'
    ],
    outputs=['domain_ctx', 
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.snn_context.domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_lateral_inhibition(ctx: SystemContext):
    """
    """
    """
    """
    try:
        from src.core.snn_context_theus import ensure_heavy_tensors_initialized, sync_from_heavy_tensors
        # Resolve SNN Context
        snn_ctx = ctx
        if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
            snn_ctx = ctx.domain_ctx.snn_context
            
        ensure_heavy_tensors_initialized(snn_ctx)
        _lateral_inhibition_vectorized(ctx)
        sync_from_heavy_tensors(snn_ctx)
    except Exception:
        import traceback
        print(f"CRASH in process_lateral_inhibition: {traceback.format_exc()}")
        raise

def _lateral_inhibition_vectorized(ctx: SystemContext):
    """Internal Vectorized Lateral Inhibition."""
    # Extract SNN Context
    # Resolve SNN Context (Handle nested RL Context vs Standalone SNN Context)
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    if snn_ctx is None:
        return
        
    t = domain.heavy_tensors
    if t is None: # Should be ensured
        return
        
    pots = t['potentials']
    
    current_spikes = domain.spike_queue.get(domain.current_time, [])
    
    if not current_spikes:
        return
    
    # Cast for safety
    try:
        wta_k = int(global_ctx.wta_k)
        inhib_str = float(global_ctx.inhibition_strength)
    except:
        wta_k = 5
        inhib_str = 0.5

    if len(current_spikes) <= wta_k:
        # Not enough spikes to inhibit
        domain.metrics['wta_winners'] = len(current_spikes)
        domain.metrics['wta_losers'] = 0
        return

    # To vectorize sorting on a subset (spikes):
    # 1. Get potentials of firing neurons
    spike_indices = np.array(current_spikes, dtype=int)
    # FIX: pots is numpy array wrapped in ContextGuard -> handled by Core Patch
    spike_indices = spike_indices[spike_indices < len(pots)] # Safety
    
    firing_pots = pots[spike_indices]
    
    # 2. Sort indices by potential (descending)
    # argsort gives indices into 'firing_pots' array
    sorted_local_indices = np.argsort(firing_pots)[::-1] 
    
    # 3. Identify losers (in the subset)
    # The first K are winners. The rest are losers.
    loser_local_indices = sorted_local_indices[wta_k:]
    loser_global_indices = spike_indices[loser_local_indices]
    
    # 4. Inhibit Losers
    # Decrease potential
    # Note: We need to increase 'inhibition_received' on objects? 
    # Tensors dont support 'inhibition_received'.
    # We simplify logic: Just subtract potential in Tensor.
    pots[loser_global_indices] -= inhib_str
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
    
    # FIX: Safe len via Core Patch
    domain.metrics['wta_winners'] = len(current_spikes) - len(loser_global_indices)
    domain.metrics['wta_losers'] = len(loser_global_indices)


# ============================================================================
# Phase 11: Neural Darwinism
# ============================================================================

@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context',
        'domain_ctx.td_error',
        'domain_ctx.snn_context.domain_ctx.synapses',
        'domain_ctx.snn_context.domain_ctx',
        'domain_ctx.snn_context.domain_ctx.metrics',
        'domain_ctx.snn_context.global_ctx'
    ],
    outputs=['domain_ctx', 
        'domain_ctx.snn_context.domain_ctx.synapses',
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.snn_context.domain_ctx.metrics'
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
    rl_ctx = ctx
    # Resolve SNN Context (Handle nested RL Context vs Standalone SNN Context)
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context
    
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Safe Cast
    try:
        darwinism_interval = int(global_ctx.darwinism_interval)
        fitness_decay = float(global_ctx.fitness_decay)
        selection_pressure = float(global_ctx.selection_pressure)
    except:
        darwinism_interval = 1000
        fitness_decay = 0.95  # FIX: Stronger decay (was 0.999) to prevent saturation
        selection_pressure = 0.1

    # Check interval
    if domain.current_time % darwinism_interval != 0:
        return
    
    error = abs(rl_ctx.domain_ctx.td_error)
    
    # === PART 1: SYNAPSE EVOLUTION ===
    
    # 1. Update fitness (FIX: Multiplicative instead of additive)
    for synapse in domain.synapses:
        if error < 0.1:
            # Good prediction: 5% boost (was +0.1 additive)
            synapse.fitness = min(1.0, synapse.fitness * 1.05)
        else:
            # Bad prediction: 10% penalty (was -0.05 additive)
            synapse.fitness = max(0.0, synapse.fitness * 0.90)
        
        # Apply decay
        synapse.fitness *= fitness_decay
    
    # 1b. Diversity bonus (FIX: Prevent weight homogenization)
    if len(domain.synapses) > 0:
        weight_mean = np.mean([s.weight for s in domain.synapses])
        for synapse in domain.synapses:
            diversity_factor = abs(synapse.weight - weight_mean)
            synapse.fitness += diversity_factor * 0.01  # Small bonus for diverse weights
            synapse.fitness = np.clip(synapse.fitness, 0.0, 1.0)
    
    # 2. Selection: Remove weak
    if len(domain.synapses) > 100:  # Keep minimum population
        fitnesses = [s.fitness for s in domain.synapses]
        threshold = np.percentile(fitnesses, selection_pressure * 100)
        
        # FIX: Protect SOLID synapses from culling
        survivors = [
            s for s in domain.synapses 
            if s.fitness >= threshold or s.commit_state == COMMIT_STATE_SOLID
        ]
    else:
        # FIX: Cast to list to ensure survivors is a list, not wrapped TrackedList
        survivors = list(domain.synapses)
    
    # 3. Reproduction: REMOVED (Violates SNN Spec & Causes Memory Explosion)
    # Neural Darwinism = Selection (Pruning) + Diversity (Neuron Recycling)
    # We do NOT clone synapses.
    domain.synapses = survivors
    
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
    
    # === MEMORY LEAK FIX: Cap synapse count to prevent unbounded growth ===
    # NOTE: Neural Darwinism adds new synapses but may grow faster than pruning.
    MAX_SYNAPSES = int(global_ctx.num_neurons) * 20  # ~20 synapses per neuron max
    MAX_SYNAPSES = int(global_ctx.num_neurons) * 20  # ~20 synapses per neuron max
    if len(domain.synapses) > MAX_SYNAPSES:
        # Keep strongest synapses by weight (use sorted() for TrackedList compatibility)
        sorted_synapses = sorted(domain.synapses, key=lambda s: abs(s.weight), reverse=True)
        domain.synapses = list(sorted_synapses[:MAX_SYNAPSES])
    
    # Update metrics
    domain.metrics['darwinism_survivors'] = len(survivors)
    # domain.metrics['darwinism_offspring'] = len(offspring)  # Variable not defined in this scope
    domain.metrics['recycled_neurons'] = recycled_count
    domain.metrics['new_synapses_generated'] = len(new_synapses)

    # === SYNC FIX (Phase 16) ===
    # Darwinism changes Topology (Pruning/Recycling) and Fitness (Object attributes).
    # Heavy Tensors are ignorant of these changes and will OVERWRITE objects on next sync.
    # We must INVALIDATE the cache to force Re-initialization from Objects next step.
    if hasattr(domain, 'heavy_tensors') and domain.heavy_tensors:
         # Fix: TrackedDict (v2.2.5 Rust) now supports .clear() efficiently
         domain.heavy_tensors.clear()



# ============================================================================
# Phase 12: Revolution Protocol
# ============================================================================

@process(
    inputs=['global_ctx', 'domain_ctx', 
        'domain_ctx.synapses',
        'domain_ctx.ancestor_weights',
        'domain_ctx.population_performance',
        'domain_ctx.last_revolution_episode',
        'domain_ctx.metrics',
        'rl_ctx.domain_ctx.last_reward',
        'global_ctx.revolution_threshold',
        'global_ctx.revolution_window',
        'global_ctx.top_elite_percent',
        'global_ctx.current_episode'  # For cooldown check
    ],
    outputs=['domain_ctx', 
        'domain_ctx.ancestor_weights',
        'domain_ctx.revolution_triggered',
        'domain_ctx.last_revolution_episode',
        'domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_revolution_protocol(
    snn_ctx: SNNSystemContext,
    rl_ctx: SystemContext = None,
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
    # FIX: Safe len
    if population_contexts is None or len(list(population_contexts)) <= 1:
        domain.metrics['revolution_skipped'] = 1
        return
    
    
    # 1. Collect performance
    # NOTE: Population performance is collected by Coordinator/Metrics process 
    # and synced to SNNGlobalContext. We just read it here.
    
    # Check if we have enough history
    if not domain.population_performance:
        return
    
    # 2. COOLDOWN CHECK (Prevent rapid re-triggering)
    # Safe Cast
    try:
        current_episode = int(getattr(global_ctx, 'current_episode', 0))
        rev_window = int(global_ctx.revolution_window)
        rev_threshold = float(global_ctx.revolution_threshold)
        top_elite = float(global_ctx.top_elite_percent)
    except:
        rev_window = 100
        rev_threshold = 0.6
        top_elite = 0.1

    if (current_episode - domain.last_revolution_episode) < rev_window:
        domain.metrics['revolution_skipped'] = 1
        domain.metrics['revolution_cooldown_remaining'] = global_ctx.revolution_window - (current_episode - domain.last_revolution_episode)
        return  # Still in cooldown period
    
    # 3. Check revolution condition
    # FIX: Safe len for TrackedList
    if len(list(domain.population_performance)) < rev_window:
        return  # Not enough data
    
    # Compute ancestor performance
    if not domain.ancestor_weights:
        # Initialize ancestor
        domain.ancestor_weights = {
            s.synapse_id: s.weight
            for s in domain.synapses[:100]  # Sample
        }
        return
    
    # 3. Trigger revolution
    # FIX: Compare Reward vs Reward (Baseline), NOT Reward vs Weight
    current_baseline = getattr(domain, 'ancestor_baseline_reward', 0.0)
    
    # Auto-initialize baseline if first run
    if current_baseline == 0.0:
        # Use current population mean as the first baseline
        # (Ignore ancestor_weights as they correspond to synaptic weights < 1.0, not reward)
        if len(list(domain.population_performance)) > 0:
            current_baseline = np.mean(domain.population_performance)
            domain.ancestor_baseline_reward = current_baseline
        # If no performance data yet, we wait.
        return

    # Count outperformers against BASELINE
    outperform_count = sum(
        1 for p in domain.population_performance
        if p > current_baseline
    )
    outperform_ratio = outperform_count / len(list(domain.population_performance))

    if outperform_ratio > rev_threshold:
        domain.revolution_triggered = True
        domain.last_revolution_episode = current_episode  # Update cooldown timestamp
        
        # 4. Voting: Top 10% elite
        all_perfs = [
            (i, np.mean(ctx.domain_ctx.population_performance[-100:]))
            for i, ctx in enumerate(population_contexts)
            if len(list(ctx.domain_ctx.population_performance)) > 0
        ]
        
        if all_perfs:
            all_perfs.sort(key=lambda x: x[1], reverse=True)
            elite_count = max(1, int(len(all_perfs) * top_elite))
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
            
            # 7. FIX: Reset History & Update Baseline
            # Clear performance history to prevent continuous triggering
            domain.population_performance = [] 
            
            # Update baseline to the average of the ELITE that triggered this revolution
            # This forces the next generation to beat the NEW standard
            elite_perfs = [p for i, p in all_perfs[:elite_count]]
            new_baseline = np.mean(elite_perfs)
            domain.ancestor_baseline_reward = new_baseline
            
            # Log for debugging (via metrics since we can't print easily)
            domain.metrics['revolution_new_baseline'] = new_baseline

# Helper function for direct invocation (bypasses Theus decorator)
def _revolution_impl(
    snn_ctx: SNNSystemContext,
    rl_ctx: SystemContext = None,
    population_contexts: List[SNNSystemContext] = None
):
    """Direct implementation wrapper for revolution protocol."""
    # Use __wrapped__ to access the original function before decoration
    if hasattr(process_revolution_protocol, '__wrapped__'):
        return process_revolution_protocol.__wrapped__(snn_ctx, rl_ctx, population_contexts)
    else:
        # Fallback: call directly (will fail but at least we tried)
        return process_revolution_protocol(snn_ctx, rl_ctx, population_contexts)

# ============================================================================
# Phase 12.5: Ancestor Assimilation (Theus V2)
# ============================================================================

@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context',
        'domain_ctx.snn_context.domain_ctx.synapses',
        'domain_ctx.snn_context.domain_ctx.ancestor_weights',
        'domain_ctx.snn_context.domain_ctx.metrics',
        'domain_ctx.snn_context.global_ctx.assimilation_rate', # New param
        'domain_ctx.snn_context.global_ctx.diversity_noise'    # New param
    ],
    outputs=['domain_ctx', 
        'domain_ctx.snn_context.domain_ctx.synapses',
        'domain_ctx.snn_context.domain_ctx.metrics'
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
    
    # Resolve SNN Context (Handle nested RL Context vs Standalone SNN Context)
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    ancestor = domain.ancestor_weights
    if not ancestor:
        return
        
    # Default params if not in config
    # Safe Cast
    try:
        alpha = float(getattr(global_ctx, 'assimilation_rate', 0.05))
        noise_std = float(getattr(global_ctx, 'diversity_noise', 0.02))
    except:
        alpha = 0.05
        noise_std = 0.02
    
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
