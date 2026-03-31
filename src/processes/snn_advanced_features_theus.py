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
    inputs=['domain_ctx.snn_context.domain_ctx.emotion_saturation_level',
             'domain_ctx.snn_context.domain_ctx.dampening_active',
             'domain_ctx.snn_context.domain_ctx.heavy_tensors',
             'domain_ctx.snn_context.domain_ctx.metrics'],
    side_effects=[]
)
def process_hysteria_dampener(ctx: SystemContext):
    """
    Apply Hysteria Dampener.
    """
    try:
        return _hysteria_impl(ctx)
    except Exception:
        import traceback
        print(f"CRASH in process_hysteria_dampener: {traceback.format_exc()}")
        raise
    return {}

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
    dampening_active = domain.dampening_active
    if fire_rate > sat_threshold:
        dampening_active = True
        current_level += 0.1
    else:
        # Recovery
        current_level -= rec_rate
    
    emotion_saturation_level = np.clip(
        current_level, 0.0, 1.0
    )
    
    # Apply dampening (Vectorized)
    heavy_tensors = domain.heavy_tensors
    if dampening_active:
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
        heavy_tensors = t
        
        # Sync back
        sync_from_heavy_tensors(snn_ctx)
        
        # Deactivate if recovered
        if emotion_saturation_level < 0.1:
            dampening_active = False
    
    # Update metrics and return delta
    new_metrics = dict(domain.metrics)
    new_metrics['saturation_level'] = emotion_saturation_level
    new_metrics['dampening_active'] = 1 if dampening_active else 0
    
    return {
        'emotion_saturation_level': emotion_saturation_level,
        'dampening_active': dampening_active,
        'heavy_tensors': heavy_tensors,
        'metrics': new_metrics
    }


# ============================================================================
# Phase 10: Lateral Inhibition
# ============================================================================

@process(
    inputs=['domain_ctx.snn_context.domain_ctx.spike_queue',
            'domain_ctx.snn_context.domain_ctx.metrics'],
    outputs=['domain_ctx.snn_context.domain_ctx.heavy_tensors', 'domain_ctx.snn_context.domain_ctx.metrics'],
    side_effects=[]
)
def process_lateral_inhibition(ctx: SystemContext):
    """
    Apply lateral inhibition.
    """
    try:
        from src.core.snn_context_theus import ensure_heavy_tensors_initialized, sync_from_heavy_tensors
        # Resolve SNN Context
        snn_ctx = ctx
        if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
            snn_ctx = ctx.domain_ctx.snn_context
            
        ensure_heavy_tensors_initialized(snn_ctx)
        delta = _lateral_inhibition_vectorized(ctx)
        sync_from_heavy_tensors(snn_ctx)
        return delta
    except Exception:
        import traceback
        ctx.log(f"CRASH in process_lateral_inhibition: {traceback.format_exc()}", level="error")
        raise
    return {}

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
        return {}
        
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
        new_metrics = dict(domain.metrics)
        new_metrics['wta_winners'] = len(current_spikes)
        new_metrics['wta_losers'] = 0
        return {'metrics': new_metrics, 'heavy_tensors': t}

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
    
    # Return deltas
    new_metrics = dict(domain.metrics)
    new_metrics['wta_winners'] = len(current_spikes) - len(loser_global_indices)
    new_metrics['wta_losers'] = len(loser_global_indices)
    
    return {'metrics': new_metrics, 'heavy_tensors': t}


# ============================================================================
# Phase 11: Neural Darwinism v2 — Monotonic Additive Plasticity
# ============================================================================

@process(
    inputs=['domain_ctx.snn_context.domain_ctx.synapses',
            'domain_ctx.snn_context.domain_ctx.neurons',
            'domain_ctx.snn_context.domain_ctx.heavy_tensors',
            'domain_ctx.td_error'],
    outputs=['domain_ctx.snn_context.domain_ctx.synapses', 
             'domain_ctx.snn_context.domain_ctx.neurons',
             'domain_ctx.snn_context.domain_ctx.heavy_tensors',
             'domain_ctx.snn_context.domain_ctx.metrics'],
    side_effects=[]
)
def process_neural_darwinism(
    ctx: SystemContext
):
    """
    Monotonic Additive Plasticity (Phase 11 v2).
    
    Nguyên lý: Không bao giờ xóa Synapse khi Weight còn lớn.
    Chỉ thu hồi "xác chết toán học" (Silent GC) và mọc rễ mới (Synaptogenesis).
    
    Logic:
    1. Silent Garbage Collection — Xóa Synapse có Weight <= threshold (Zero-Shock)
    2. Targeted Synaptogenesis — Mọc rễ mới qua Dual-Gate (ID Proximity + Cosine)
    3. Dynamic Skull Limit — Dừng mọc khi chạm trần 30% đồ thị
    """
    from src.core.snn_context_theus import SynapseState, ensure_heavy_tensors_initialized
    # Resolve SNN Context
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context
    
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx

    # Safe Cast hyperparameters
    try:
        darwinism_interval = int(global_ctx.darwinism_interval)
    except (TypeError, AttributeError):
        darwinism_interval = 100

    # Check interval — chỉ chạy theo chu kỳ
    if domain.current_time % darwinism_interval != 0:
        return {}

    # === Hyperparameters (Phase 11 v2) ===
    try:
        silent_death_threshold = float(getattr(global_ctx, 'silent_death_threshold', 0.001))
        synaptogenesis_prob = float(getattr(global_ctx, 'synaptogenesis_prob', 0.01))
        cluster_radius_ratio = float(getattr(global_ctx, 'cluster_radius_ratio', 0.1))
        cosine_sim_threshold = float(getattr(global_ctx, 'cosine_similarity_threshold', 0.3))
        max_connectivity_ratio = float(getattr(global_ctx, 'max_connectivity_ratio', 0.3))
    except (TypeError, AttributeError):
        silent_death_threshold = 0.001
        synaptogenesis_prob = 0.01
        cluster_radius_ratio = 0.1
        cosine_sim_threshold = 0.3
        max_connectivity_ratio = 0.3

    N = len(domain.neurons)
    # NOTE: Dynamic Skull Limit — trần tỷ lệ thuận với số neuron, không hardcode.
    MAX_SYNAPSES = int(N * (N - 1) * max_connectivity_ratio)
    CLUSTER_RADIUS = max(10, int(N * cluster_radius_ratio))

    # === PART 1: SILENT GARBAGE COLLECTION ===
    # NOTE: Chỉ xóa Synapse khi STDP đã tự nhiên ăn mòn Weight về mức vô hình.
    # Tại ngưỡng này, xóa vật lý không tạo bất kỳ cú sốc nào cho MLP
    # vì đóng góp toán học của nó lên Input vector = 0.
    before_count = len(domain.synapses)
    
    # NOTE: Đọc Weight từ heavy_tensors (authoritative source) thay vì object field
    # để đảm bảo tính nhất quán sau khi STDP vectorized đã cập nhật ma trận.
    ensure_heavy_tensors_initialized(snn_ctx)
    weights_matrix = domain.heavy_tensors.get('weights')
    
    if weights_matrix is not None:
        survivors = []
        for s in domain.synapses:
            if s.pre_neuron_id < N and s.post_neuron_id < N:
                w = weights_matrix[s.pre_neuron_id, s.post_neuron_id]
                if w > silent_death_threshold:
                    survivors.append(s)
                # NOTE: Synapse với w <= threshold bị loại bỏ tĩnh lặng.
                # Không gây sốc vì 0.001 * spike ≈ 0.
            else:
                survivors.append(s)  # Giữ lại nếu index out-of-range (safety)
        domain.synapses = survivors
    
    gc_count = before_count - len(domain.synapses)

    # === PART 2: TARGETED SYNAPTOGENESIS (Dual-Gate Eligibility) ===
    current_synapse_count = len(domain.synapses)
    new_synapses = []
    
    if current_synapse_count < MAX_SYNAPSES:
        # Bước 2a: Tìm Active Neurons (bắn gai gần đây)
        active_neurons = [
            n for n in domain.neurons
            if (domain.current_time - n.last_fire_time) < darwinism_interval
        ]

        if len(active_neurons) > 1:
            # Bước 2b: Pre-compute dữ liệu cho Dual-Gate
            existing_pairs = set(
                (s.pre_neuron_id, s.post_neuron_id) for s in domain.synapses
            )
            prototypes = domain.heavy_tensors.get('prototypes')  # (N, D)
            
            # NOTE: Tính max_syn_id 1 lần duy nhất để gán ID cho synapse mới
            max_syn_id = 0
            if domain.synapses:
                max_syn_id = max(s.synapse_id for s in domain.synapses)

            for n_a in active_neurons:
                if current_synapse_count + len(new_synapses) >= MAX_SYNAPSES:
                    break  # Sọ não đầy
                    
                for n_b in active_neurons:
                    if n_a.neuron_id == n_b.neuron_id:
                        continue
                    
                    # === CỔNG 1: Vật lý (ID Proximity) — O(1) lọc sơ bộ ===
                    if abs(n_a.neuron_id - n_b.neuron_id) > CLUSTER_RADIUS:
                        continue
                    
                    if (n_a.neuron_id, n_b.neuron_id) in existing_pairs:
                        continue
                    
                    if current_synapse_count + len(new_synapses) >= MAX_SYNAPSES:
                        break

                    # === CỔNG 2: Ngữ nghĩa (Cosine Similarity) ===
                    # NOTE: Chỉ tính trên ~10% cặp đã lọt Cổng 1, tiết kiệm CPU.
                    if prototypes is not None:
                        proto_a = prototypes[n_a.neuron_id]
                        proto_b = prototypes[n_b.neuron_id]
                        dot_product = np.dot(proto_a, proto_b)
                        norm_product = (np.linalg.norm(proto_a) * np.linalg.norm(proto_b)) + 1e-8
                        cosine_sim = dot_product / norm_product
                        if cosine_sim < cosine_sim_threshold:
                            continue
                    
                    # === Cả hai Cổng đều mở → Xác suất mọc ===
                    if np.random.random() < synaptogenesis_prob:
                        max_syn_id += 1
                        syn = SynapseState(
                            synapse_id=max_syn_id,
                            pre_neuron_id=n_a.neuron_id,
                            post_neuron_id=n_b.neuron_id,
                            weight=np.random.uniform(0.3, 0.5)
                        )
                        new_synapses.append(syn)
                        existing_pairs.add((n_a.neuron_id, n_b.neuron_id))

    if new_synapses:
        domain.synapses.extend(new_synapses)

    # === PART 3: TENSOR RESYNC SIGNAL ===
    # NOTE: Nếu có synapse bị GC hoặc mọc mới, buộc Tensor Engine re-init
    # để ma trận (N,N) và các index arrays (S,) được cập nhật kích thước mới.
    if gc_count > 0 or len(new_synapses) > 0:
        for key in ['syn_pre_ids', 'syn_post_ids', 'syn_commit_states',
                    '_post_synapse_map', '_fast_traces', '_slow_traces',
                    'traces', 'fitnesses', 'commit_states',
                    'consecutive_correct', 'consecutive_wrong']:
            if key in domain.heavy_tensors:
                del domain.heavy_tensors[key]
        # NOTE: Buộc re-build weights matrix từ danh sách synapses mới
        if 'weights' in domain.heavy_tensors:
            del domain.heavy_tensors['weights']

    # === METRICS ===
    new_metrics = dict(domain.metrics)
    new_metrics['darwinism_gc_count'] = gc_count
    new_metrics['darwinism_new_synapses'] = len(new_synapses)
    new_metrics['darwinism_total_synapses'] = len(domain.synapses)
    new_metrics['darwinism_skull_limit'] = MAX_SYNAPSES
    new_metrics['darwinism_skull_usage_pct'] = round(len(domain.synapses) / max(MAX_SYNAPSES, 1) * 100, 1)
    new_metrics['accum_darwinism_reward'] = 0.0  # Reset for next interval

    return {
        'synapses': list(domain.synapses),
        'neurons': domain.neurons,
        'metrics': new_metrics,
        'heavy_tensors': domain.heavy_tensors
    }



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
    outputs=['domain_ctx.snn_context.domain_ctx.metrics',
             'domain_ctx.snn_context.domain_ctx.revolution_triggered',
             'domain_ctx.snn_context.domain_ctx.last_revolution_episode',
             'domain_ctx.snn_context.domain_ctx.ancestor_weights',
             'domain_ctx.snn_context.domain_ctx.population_performance',
             'domain_ctx.snn_context.domain_ctx.ancestor_baseline_reward'],
    side_effects=[]
)
def process_revolution_protocol(
    snn_ctx: SNNSystemContext,
    rl_ctx: SystemContext = None,
    population_contexts: List[SNNSystemContext] = None
):
    """
    Cultural Evolution: Update ancestor khi quần thể vượt trội.
    """
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Single-agent mode: Skip
    if population_contexts is None or len(list(population_contexts)) <= 1:
        new_metrics = dict(domain.metrics)
        new_metrics['revolution_skipped'] = 1
        return {'metrics': new_metrics}
    
    
    # 1. Collect performance
    # NOTE: Population performance is collected by Coordinator/Metrics process 
    # and synced to SNNGlobalContext. We just read it here.
    
    # Check if we have enough history
    if not domain.population_performance:
        return {}
    
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
        new_metrics = dict(domain.metrics)
        new_metrics['revolution_skipped'] = 1
        new_metrics['revolution_cooldown_remaining'] = rev_window - (current_episode - domain.last_revolution_episode)
        return {'metrics': new_metrics}
    
    # 3. Check revolution condition
    if len(list(domain.population_performance)) < rev_window:
        return {}
    
    # Compute ancestor performance
    if not domain.ancestor_weights:
        # Initialize ancestor
        ancestor_weights = {
            s.synapse_id: s.weight
            for s in domain.synapses[:100]  # Sample
        }
        return {'ancestor_weights': ancestor_weights}
    
    # 3. Trigger revolution
    # FIX: Compare Reward vs Reward (Baseline), NOT Reward vs Weight
    current_baseline = getattr(domain, 'ancestor_baseline_reward', 0.0)
    
    # Auto-initialize baseline if first run
    if current_baseline == 0.0:
        if len(list(domain.population_performance)) > 0:
            current_baseline = np.mean(domain.population_performance)
            return {'ancestor_baseline_reward': float(current_baseline)}
        return {}

    # Count outperformers against BASELINE
    outperform_count = sum(
        1 for p in domain.population_performance
        if p > current_baseline
    )
    outperform_ratio = outperform_count / len(list(domain.population_performance))

    if outperform_ratio > rev_threshold:
        revolution_triggered = True
        last_revolution_episode = current_episode  
        
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
            
            # Update metrics
            new_metrics = dict(domain.metrics)
            if new_ancestor:
                new_metrics['revolution_count'] = new_metrics.get('revolution_count', 0) + 1
            
            # 7. Update Baseline
            elite_perfs = [p for i, p in all_perfs[:elite_count]]
            new_baseline = np.mean(elite_perfs)
            new_metrics['revolution_new_baseline'] = float(new_baseline)

            return {
                'revolution_triggered': revolution_triggered,
                'last_revolution_episode': last_revolution_episode,
                'ancestor_weights': new_ancestor if new_ancestor else domain.ancestor_weights,
                'population_performance': [],
                'ancestor_baseline_reward': float(new_baseline),
                'metrics': new_metrics
            }
            
    return {}

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
    outputs=['domain_ctx.snn_context.domain_ctx.synapses', 'domain_ctx.snn_context.domain_ctx.metrics'],
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
        return {}
        
    # Default params if not in config
    # Safe Cast
    try:
        alpha = float(getattr(global_ctx, 'assimilation_rate', 0.05))
        noise_std = float(getattr(global_ctx, 'diversity_noise', 0.02))
    except:
        alpha = 0.05
        noise_std = 0.02
    
    new_synapses = []
    assimilated_count = 0
    for synapse in domain.synapses:
        # PROTECT SOLID KNOWLEDGE
        if synapse.commit_state == COMMIT_STATE_SOLID:
            new_synapses.append(synapse)
            continue
            
        if synapse.synapse_id in ancestor:
            target_w = ancestor[synapse.synapse_id]
            
            # Soft Update
            new_w = (1.0 - alpha) * synapse.weight + alpha * target_w
            
            # Diversity Noise
            noise = np.random.randn() * noise_std
            new_w += noise
            
            # Update object (vially acceptable in current POP if returned)
            synapse.weight = float(np.clip(new_w, 0.0, 1.0))
            assimilated_count += 1
        new_synapses.append(synapse)
            
    new_metrics = dict(domain.metrics)
    new_metrics['assimilated_synapses'] = assimilated_count
    
    return {'synapses': new_synapses, 'metrics': new_metrics}
