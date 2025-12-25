"""
Test SNN-RL Interface
======================
Test interface layer giữa SNN và RL Agent.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

import numpy as np
import torch
from src.core.snn_context_theus import create_snn_context_theus
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.adapters.snn_rl_interface import SNNRLInterface


def create_mock_rl_context():
    """Tạo mock RL context."""
    global_ctx = GlobalContext()
    domain_ctx = DomainContext()
    
    # Mock observation
    domain_ctx.current_observation = {
        'agent_pos': (3, 5)
    }
    
    # Mock TD-error
    domain_ctx.td_error = 0.5
    
    return SystemContext(
        global_ctx=global_ctx,
        domain_ctx=domain_ctx
    )


def test_encode_emotion_vector():
    """Test encode emotion vector từ SNN."""
    print("=" * 60)
    print("Test: Encode Emotion Vector (SNN → RL)")
    print("=" * 60)
    
    # Create contexts
    snn_ctx = create_snn_context_theus(num_neurons=100)
    rl_ctx = create_mock_rl_context()
    
    # Set some emotion neurons to fire
    for i in range(84, 100):
        if i < len(snn_ctx.domain_ctx.neurons):
            neuron = snn_ctx.domain_ctx.neurons[i]
            neuron.prototype_vector[0] = np.random.randn()
    
    # Encode emotion
    SNNRLInterface.encode_emotion_vector(snn_ctx, rl_ctx)
    
    # Check result
    assert rl_ctx.domain_ctx.snn_emotion_vector is not None
    assert rl_ctx.domain_ctx.snn_emotion_vector.shape == (16,)
    assert isinstance(rl_ctx.domain_ctx.snn_emotion_vector, torch.Tensor)
    
    # Check normalized
    norm = torch.norm(rl_ctx.domain_ctx.snn_emotion_vector).item()
    assert 0.9 < norm < 1.1  # Should be ~1.0
    
    print(f"✅ Emotion vector: {rl_ctx.domain_ctx.snn_emotion_vector[:4]}")
    print(f"✅ Norm: {norm:.4f}")


def test_encode_state_to_spikes():
    """Test encode RL state thành SNN spikes."""
    print("\n" + "=" * 60)
    print("Test: Encode State to Spikes (RL → SNN)")
    print("=" * 60)
    
    # Create contexts
    snn_ctx = create_snn_context_theus(num_neurons=100)
    rl_ctx = create_mock_rl_context()
    
    # Encode state
    SNNRLInterface.encode_state_to_spikes(rl_ctx, snn_ctx)
    
    # Check input neurons có potential cao
    for i in range(min(16, len(snn_ctx.domain_ctx.neurons))):
        neuron = snn_ctx.domain_ctx.neurons[i]
        assert neuron.potential > 0  # Should be injected
        assert np.linalg.norm(neuron.potential_vector) > 0
    
    print(f"✅ Input neurons injected")
    print(f"✅ Neuron 0 potential: {snn_ctx.domain_ctx.neurons[0].potential:.4f}")


def test_modulate_attention():
    """Test top-down modulation."""
    print("\n" + "=" * 60)
    print("Test: Modulate Attention (RL → SNN)")
    print("=" * 60)
    
    # Create contexts
    snn_ctx = create_snn_context_theus(num_neurons=100)
    rl_ctx = create_mock_rl_context()
    
    # Save original thresholds
    fear_neuron = snn_ctx.domain_ctx.neurons[50]
    original_threshold = fear_neuron.threshold
    
    # Modulate fear region (increase attention)
    SNNRLInterface.modulate_attention(
        rl_ctx, snn_ctx,
        region='fear',
        strength=0.5  # Positive = increase attention
    )
    
    # Check threshold decreased (easier to fire)
    new_threshold = fear_neuron.threshold
    assert new_threshold < original_threshold
    
    print(f"✅ Original threshold: {original_threshold:.4f}")
    print(f"✅ New threshold: {new_threshold:.4f}")
    print(f"✅ Attention increased!")


def test_compute_intrinsic_reward():
    """Test intrinsic reward computation."""
    print("\n" + "=" * 60)
    print("Test: Compute Intrinsic Reward (SNN → RL)")
    print("=" * 60)
    
    # Create contexts
    snn_ctx = create_snn_context_theus(num_neurons=100)
    rl_ctx = create_mock_rl_context()
    
    # Set some neurons to fire với low similarity (high novelty)
    snn_ctx.domain_ctx.current_time = 10
    
    for i in range(5):
        neuron = snn_ctx.domain_ctx.neurons[i]
        neuron.last_fire_time = 10
        # Set potential_vector khác prototype (low similarity)
        neuron.potential_vector = np.random.randn(16)
        neuron.potential_vector /= np.linalg.norm(neuron.potential_vector)
    
    # Compute intrinsic reward
    SNNRLInterface.compute_intrinsic_reward(snn_ctx, rl_ctx)
    
    # Check result
    assert 0.0 <= rl_ctx.domain_ctx.intrinsic_reward <= 1.0
    
    print(f"✅ Intrinsic reward: {rl_ctx.domain_ctx.intrinsic_reward:.4f}")
    print(f"✅ Novelty detected!")


def test_integration():
    """Test full integration flow."""
    print("\n" + "=" * 60)
    print("Test: Full Integration Flow")
    print("=" * 60)
    
    # Create contexts
    snn_ctx = create_snn_context_theus(num_neurons=100)
    rl_ctx = create_mock_rl_context()
    
    # 1. RL → SNN: Encode state
    SNNRLInterface.encode_state_to_spikes(rl_ctx, snn_ctx)
    
    # 2. Run SNN forward (simplified)
    from src.processes.snn_core_theus import process_integrate, process_fire
    process_integrate(snn_ctx)
    process_fire(snn_ctx)
    
    # 3. SNN → RL: Extract emotion
    SNNRLInterface.encode_emotion_vector(snn_ctx, rl_ctx)
    
    # 4. SNN → RL: Intrinsic reward
    SNNRLInterface.compute_intrinsic_reward(snn_ctx, rl_ctx)
    
    # 5. RL → SNN: Modulate attention
    SNNRLInterface.modulate_attention(
        rl_ctx, snn_ctx,
        region='curiosity',
        strength=rl_ctx.domain_ctx.intrinsic_reward  # Use novelty
    )
    
    # Check all outputs
    assert rl_ctx.domain_ctx.snn_emotion_vector is not None
    assert 0.0 <= rl_ctx.domain_ctx.intrinsic_reward <= 1.0
    
    print(f"✅ Full flow complete!")
    print(f"✅ Emotion vector shape: {rl_ctx.domain_ctx.snn_emotion_vector.shape}")
    print(f"✅ Intrinsic reward: {rl_ctx.domain_ctx.intrinsic_reward:.4f}")


if __name__ == '__main__':
    test_encode_emotion_vector()
    test_encode_state_to_spikes()
    test_modulate_attention()
    test_compute_intrinsic_reward()
    test_integration()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
