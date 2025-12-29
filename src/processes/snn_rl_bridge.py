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
from src.core.snn_context_theus import SNNSystemContext


# ============================================================================
# SNN → RL: Emotion Vector (Population Code)
# ============================================================================

@process(
    inputs=['domain.snn_context'],
    outputs=[
        'domain.snn_emotion_vector',
        'domain.previous_snn_emotion_vector'
    ],
    side_effects=[]
)
def encode_emotion_vector(ctx: SystemContext):
    """
    Encode SNN neuron activity → Emotion vector cho RL. Wraps _encode_emotion_vector_impl.
    """
    _encode_emotion_vector_impl(ctx)

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
    elif snn_ctx.domain_ctx.snn_emotion_vector is not None:
         # Fallback: Use previous emotion state as context if obs not available
        query_vector = snn_ctx.domain_ctx.snn_emotion_vector.numpy()
        
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
    if ctx.domain_ctx.snn_emotion_vector is not None:
        ctx.domain_ctx.previous_snn_emotion_vector = ctx.domain_ctx.snn_emotion_vector.clone()
    
    # Convert to tensor
    ctx.domain_ctx.snn_emotion_vector = torch.tensor(
        emotion_vector,
        dtype=torch.float32
    )


# ============================================================================
# RL → SNN: State Encoding (Observation → Spikes)
# ============================================================================

@process(
    inputs=['domain.current_observation', 'domain.snn_context'],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def encode_state_to_spikes(ctx: SystemContext):
    """
    Inject sensor vector từ môi trường vào SNN. Wraps _encode_state_to_spikes_impl.
    """
    _encode_state_to_spikes_impl(ctx)

def _encode_state_to_spikes_impl(ctx: SystemContext):
    """Internal implementation."""
    obs = ctx.domain_ctx.current_observation
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        # No SNN - skip
        return
    
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
    
    # Inject vào input neurons (0-15)
    input_end = min(16, len(snn_ctx.domain_ctx.neurons))
    
    for i in range(input_end):
        neuron = snn_ctx.domain_ctx.neurons[i]
        
        # Amplify để vượt threshold
        # NOTE: Tăng từ 2.0 → 5.0 để neurons có thể bắn
        # Sensor values [0, 1], threshold = 1.0
        # Amplification 5.0 → potential [0, 5.0]
        neuron.potential = sensor_vector[i] * 5.0
        
        # Full context cho vector matching
        neuron.potential_vector = sensor_vector


# ============================================================================
# RL → SNN: Attention Modulation
# ============================================================================

@process(
    inputs=['domain.last_action', 'domain.snn_context'],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def modulate_snn_attention(ctx: SystemContext):
    """
    Modulate SNN attention dựa trên RL action.
    
    Top-down control: Action → Neuron threshold adjustment.
    
    Args:
        ctx: System context
    """
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return
    
    action = ctx.domain_ctx.last_action
    
    if action is None:
        return
    
    # Action-specific modulation
    num_neurons = len(snn_ctx.domain_ctx.neurons)
    neurons_per_action = num_neurons // 4
    
    start_idx = action * neurons_per_action
    end_idx = min(start_idx + neurons_per_action, num_neurons)
    
    # Boost threshold (easier to fire)
    for i in range(start_idx, end_idx):
        neuron = snn_ctx.domain_ctx.neurons[i]
        neuron.threshold *= 0.9  # 10% easier


# ============================================================================
# SNN → RL: Intrinsic Reward (Novelty)
# ============================================================================

@process(
    inputs=['domain.snn_context'],
    outputs=['domain.intrinsic_reward'],
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
        ctx.domain_ctx.intrinsic_reward = 0.0
        return
    
    neurons = snn_ctx.domain_ctx.neurons
    
    # Get current pattern (active neurons)
    active_vectors = []
    for neuron in neurons:
        if neuron.fire_count > 0:
            active_vectors.append(neuron.prototype_vector)
    
    if not active_vectors:
        # No activity → neutral novelty
        ctx.domain_ctx.intrinsic_reward = 0.5
        return
    
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
    ctx.domain_ctx.intrinsic_reward = np.clip(novelty, 0.0, 1.0)
