"""
SNN-RL Bridge Processes
========================
Processes kết nối SNN và RL Agent.

NOTE: Đây là PROCESSES (pure functions), không phải adapters.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
import torch
from theus.contracts import process
from src.core.context import SystemContext
from src.core.snn_context_theus import sync_to_heavy_tensors


# ============================================================================
# SNN → RL: Emotion Vector (Population Code)
# ============================================================================

@process(
    inputs=['domain_ctx', 'domain_ctx.snn_context'],
    outputs=['domain_ctx.heavy_snn_emotion_vector', 'domain_ctx.heavy_previous_snn_emotion_vector'],
    side_effects=[]
)
def encode_emotion_vector(ctx: SystemContext):
    """
    Encode SNN neuron activity → Emotion vector cho RL. 
    """
    return _encode_emotion_vector_impl(ctx)

def _encode_emotion_vector_impl(ctx: SystemContext):
    """Internal implementation."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        # No SNN - skip
        return
    
    neurons = snn_ctx.domain_ctx.neurons
    
    # Aggregate firing neurons' vectors
    active_vectors = []
    for neuron in neurons:
        if neuron.fire_count > 0:  # Has fired
            active_vectors.append(neuron.prototype_vector)
    
    # Phase 9: Attention-based Aggregation using Sigmoid Gating
    # Query: Current Observation (Context)
    # Key: Neuron Prototype Vector (Memory)
    # Value: Neuron Prototype Vector
    
    # 1. Get Query (Context)
    query_vector = None
    obs = ctx.domain_ctx.current_observation
    
    if isinstance(obs, np.ndarray) and obs.shape == (16,):
        query_vector = obs
    elif snn_ctx.domain_ctx.heavy_snn_emotion_vector is not None:
         # Fallback: Use previous emotion state as context if obs not available
        query_vector = snn_ctx.domain_ctx.heavy_snn_emotion_vector.numpy()
        
    # 2. Collect Keys/Values from Active Neurons
    active_vectors = []
    keys = []
    
    for neuron in neurons:
        if neuron.fire_count > 0:
            active_vectors.append(neuron.prototype_vector)
            keys.append(neuron.prototype_vector)
            
    if not active_vectors:
        # No activity → neutral
        emotion_vector = np.zeros(16)
    else:
        # 3. Compute Attention if Query is available
        if query_vector is not None:
             # Stack for vectorized operations
            K = np.array(keys) # [N, 16]
            Q = query_vector   # [16]
            
            # Score = Q . KT
            # Shape: [N]
            scores = np.dot(K, Q)
            
            # 4. Gating (Sigmoid)
            # Allows multi-modal attention (e.g., Fear AND Curiosity)
            # range (0, 1)
            gates = 1 / (1 + np.exp(-scores))
            
            # 5. Weighted Sum
            # V_out = Sum(Gate_i * V_i)
            # Shape: [N, 1] * [N, 16] -> [N, 16] -> Sum -> [16]
            weighted_vectors = K * gates[:, np.newaxis]
            emotion_vector = np.sum(weighted_vectors, axis=0)
            
            # Debug/Audit log (optional - keep minimal for performance)
            # print(f"Bridge Attention: {len(active_vectors)} active. Max Gate: {np.max(gates):.2f}")
            
        else:
            # Fallback to Mean if no Context
            emotion_vector = np.mean(active_vectors, axis=0)
    
    # Normalize
    norm = np.linalg.norm(emotion_vector)
    if norm > 0:
        emotion_vector = emotion_vector / norm
    
    # Shift current to previous (for RL learning)
    prev_emo = None
    if ctx.domain_ctx.heavy_snn_emotion_vector is not None:
        prev_emo = ctx.domain_ctx.heavy_snn_emotion_vector.detach().clone()
    
    # Convert current to tensor
    current_emo = torch.tensor(
        emotion_vector,
        dtype=torch.float32
    ).detach()

    return {
        'heavy_snn_emotion_vector': current_emo,
        'heavy_previous_snn_emotion_vector': prev_emo
    }


# ============================================================================
# RL → SNN: State Encoding (Observation → Spikes)
# ============================================================================

@process(
    inputs=['domain_ctx', 'domain_ctx.current_observation', 'domain_ctx.snn_context'],
    outputs=['domain_ctx.snn_context.domain_ctx.heavy_tensors'],
    side_effects=[]
)
def encode_state_to_spikes(ctx: SystemContext):
    """
    Inject sensor vector từ môi trường vào SNN.
    """
    return _encode_state_to_spikes_impl(ctx)

def _encode_state_to_spikes_impl(ctx: SystemContext):
    """Internal implementation."""
    obs = ctx.domain_ctx.current_observation
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        # No SNN - skip
        return
    
    # DEBUG: Inspect incoming observation
    # print(f"DEBUG OBS TYPE: {type(obs)}")
    # if isinstance(obs, np.ndarray):
    #     print(f"DEBUG OBS VECTOR: {obs}")
    # else:
    #     print(f"DEBUG OBS RAW: {obs}")
    
    # Observation ĐÃ LÀ vector 16-dim từ environment.get_sensor_vector()
    # KHÔNG CẦN encoding nữa!
    if isinstance(obs, np.ndarray):
        # Đã là vector - dùng trực tiếp
        sensor_vector = obs
    else:
        # Fallback: Nếu vẫn là dict (legacy), tạo vector đơn giản
        # NOTE: Sẽ bỏ sau khi chuyển hoàn toàn sang sensor system
        if 'agent_pos' in obs:
            x, y = obs['agent_pos']
        else:
            x, y = 0, 0
        
        # Simple encoding (legacy)
        pattern = np.zeros(16)
        pattern[x % 8] = 1.0
        pattern[8 + (y % 8)] = 1.0
        
        norm = np.linalg.norm(pattern)
        if norm > 0:
            pattern = pattern / norm
        
        sensor_vector = pattern
    
    # v3 POP FIX: Use heavy_tensors directly instead of looping over objects
    from src.core.snn_context_theus import ensure_heavy_tensors_initialized, sync_from_heavy_tensors
    ensure_heavy_tensors_initialized(snn_ctx)
    t = snn_ctx.domain_ctx.heavy_tensors
    
    pots = t['potentials']
    pvecs = t['potential_vectors']
    N = len(pots)
    
    amplification = float(snn_ctx.global_ctx.input_amplification_factor)
    input_end = min(16, N)
    
    # Apply to tensors (Vectorized)
    pots[:input_end] = sensor_vector[:input_end] * amplification
    pvecs[:input_end] = sensor_vector[:input_end]
    
    # Sync back for audit/object compatibility
    sync_from_heavy_tensors(snn_ctx)
    
    return {'heavy_tensors': t}


# ============================================================================
# RL → SNN: Attention Modulation
# ============================================================================

@process(
    inputs=['domain_ctx', 'domain_ctx.last_action', 'domain_ctx.snn_context'],
    outputs=['domain_ctx', 'domain_ctx.snn_context'],
    side_effects=[]
)
def modulate_snn_attention(ctx: SystemContext):
    """
    Modulate SNN attention dựa trên RL action (Top-Down Control).
    
    Refactored for Tensor Compatibility & Stability.
    
    Args:
        ctx: System context
    """
    from src.core.snn_context_theus import ensure_heavy_tensors_initialized, sync_from_heavy_tensors
    
    snn_ctx = ctx.domain_ctx.snn_context
    if snn_ctx is None:
        return
        
    action = ctx.domain_ctx.last_action
    
    # Needs action to modulate
    if action is None or action < 0:
        return
        
    snn_domain = ctx.domain_ctx.snn_context.domain_ctx
    safety = snn_domain.safety_state
    
    # === PHASE 11: DEFENSE LAYER CHECKS ===
    
    # 1. Bottom-Up Override (Emergency Brake)
    if safety['emergency_override_steps'] > 0:
        # Block Top-Down Modulation
        # And potentially force restoration? (Handled by restore_snn_attention implicitly)
        return
        
    # 2. Curiosity Veto
    if safety['veto_active']:
        # Block Top-Down Modulation
        return
        
    # 1. Ensure Tensors (Critical for Sync)
    ensure_heavy_tensors_initialized(snn_ctx)
    t = snn_ctx.domain_ctx.heavy_tensors
    thresh = t['thresholds']
    N = len(thresh)
    
    # 3. Saccadic Reset (Blink)
    # If context switch, we clear OLD attention immediately.
    # How? Reset all thresholds to baseline?
    # Or rely on 'restore_snn_attention'?
    # Saccadic Reset implies FASTER restoration.
    if safety['saccade_triggered']:
        # Rapidly push all thresholds back to baseline
        baseline = snn_ctx.global_ctx.initial_threshold
        # Strong push (e.g. 50% restoration in one step)
        thresh += (baseline - thresh) * 0.5
        # And continue to apply NEW modulation below.
    
    # 2. Action Mapping (Hardcoded for now, but documented risk)
    # WARNING: Assumes ActionSpace=8 (Phase 11b) and N is divisible.
    # Actions 0-3: Excite (Focus) -> Indices 0-25...
    # Actions 4-7: Inhibit (Ignore) -> Indices 0-25... corresponding to Action-4
    
    # Decode Action
    # base_action: 0-3 (Direction/Concept)
    if action >= 4:
        # INHIBITORY MODE
        base_action = action - 4
        modulation_factor = float(snn_ctx.global_ctx.modulation_inhibition) # Harder to fire (Inhibit)
    else:
        # EXCITATORY MODE
        base_action = action
        modulation_factor = float(snn_ctx.global_ctx.modulation_excitation) # Easier to fire (Excite)

    # Calculate Indices based on base_action
    # Risk: If N=100, N//4 = 25. Indices 0-25, 25-50, 50-75, 75-100.
    neurons_per_action = N // 4
    
    start_idx = base_action * neurons_per_action
    end_idx = min(start_idx + neurons_per_action, N)
    
    # 3. Apply Modulation (Vectorized)
    
    # Decrease threshold by 10% (Easier to fire)
    # RISK MITIGATION: Novelty Masking (Phase 10.5)
    # Only modulate SOLID neurons (committed), leave FLUID neurons (new) alone to evolve.
    
    # We use the Derived Solidity Ratio (Phase 10.5)
    if 'solidity_ratios' in t:
        solidity_ratios = t['solidity_ratios']
        # Mask: (In Action Range) AND (Is Solid > 0.5)
        
        # Create full mask first
        action_mask = np.zeros(N, dtype=bool)
        action_mask[start_idx:end_idx] = True
        
        solid_mask = (solidity_ratios > 0.5)
        
        # Combine
        final_mask = action_mask & solid_mask
        
        # Apply modulation only to Solid neurons in target group
        thresh[final_mask] *= modulation_factor
        
    else:
        # Fallback: Modulate all in range if no solidity info (Legacy/Init)
        thresh[start_idx:end_idx] *= modulation_factor
    
    # Clip to safety minimum (Prevent collapse)
    np.clip(thresh, snn_ctx.global_ctx.threshold_min, snn_ctx.global_ctx.threshold_max, out=thresh)
    
    # Sync Back
    sync_from_heavy_tensors(snn_ctx)
    
    return {'heavy_tensors': t}


@process(
    inputs=['domain_ctx', 'domain_ctx.snn_context'],
    outputs=['domain_ctx', 'domain_ctx.snn_context'],
    side_effects=[]
)
def restore_snn_attention(ctx: SystemContext):
    """
    Restore SNN attention (thresholds) to baseline.
    
    Mechanism: Elasticity (Spring force).
    Prevents Threshold Collapse from repeated Top-Down modulation.
    
    Args:
        ctx: System context
    """
    from src.core.snn_context_theus import ensure_heavy_tensors_initialized, sync_from_heavy_tensors
    
    snn_ctx = ctx.domain_ctx.snn_context
    if snn_ctx is None:
        return
        
    # 1. Ensure Tensors
    ensure_heavy_tensors_initialized(snn_ctx)
    t = snn_ctx.domain_ctx.heavy_tensors
    thresh = t['thresholds']
    
    baseline = float(snn_ctx.global_ctx.initial_threshold)
    restoration_rate = float(snn_ctx.global_ctx.restoration_rate) # Elastic return to baseline
    
    # 2. Apply Restoration Force
    # Delta = (Target - Current) * Rate
    # If Thresh < Baseline, it increases.
    delta = (baseline - thresh) * restoration_rate
    thresh += delta
    
    # 3. Clip
    np.clip(thresh, snn_ctx.global_ctx.threshold_min, snn_ctx.global_ctx.threshold_max, out=thresh)
    
    # 4. Sync Back
    sync_from_heavy_tensors(snn_ctx)
    
    return {'heavy_tensors': t}


# ============================================================================
# SNN → RL: Intrinsic Reward (Novelty)
# ============================================================================

@process(
    inputs=['domain_ctx', 'domain_ctx.snn_context'],
    outputs=['domain_ctx.intrinsic_reward'],
    side_effects=[]
)
def compute_intrinsic_reward_snn(ctx: SystemContext):
    """
    Compute intrinsic reward từ SNN novelty.
    
    Novelty = 1 - avg_similarity với existing patterns.
    
    Args:
        ctx: System context
    """
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return {'intrinsic_reward': 0.0}
    
    neurons = snn_ctx.domain_ctx.neurons
    
    # Get current pattern (active neurons)
    active_vectors = []
    for neuron in neurons:
        if neuron.fire_count > 0:
            active_vectors.append(neuron.prototype_vector)
    
    if not active_vectors:
        # No activity → neutral novelty
        return {'intrinsic_reward': 0.5}
    
    current_pattern = np.mean(active_vectors, axis=0)
    
    # Compare với all neuron prototypes
    similarities = []
    for neuron in neurons:
        sim = np.dot(current_pattern, neuron.prototype_vector)
        sim = sim / (np.linalg.norm(current_pattern) * np.linalg.norm(neuron.prototype_vector) + 1e-8)
        similarities.append(abs(sim))
    
    # Novelty = 1 - max_similarity
    max_sim = max(similarities) if similarities else 0.0
    novelty = 1.0 - max_sim
    
    # Clip to [0, 1]
    return {'intrinsic_reward': float(np.clip(novelty, 0.0, 1.0))}
