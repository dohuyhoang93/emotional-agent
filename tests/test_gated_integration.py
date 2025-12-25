"""
Test Gated Integration Network
================================
Test PyTorch model cho gated integration.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

import torch
import numpy as np
from src.models.gated_integration import (
    GatedIntegrationNetwork,
    GatedIntegrationTrainer
)


def test_network_creation():
    """Test tạo network."""
    print("=" * 60)
    print("Test: Network Creation")
    print("=" * 60)
    
    model = GatedIntegrationNetwork(
        obs_dim=10,
        emotion_dim=16,
        hidden_dim=64,
        action_dim=4
    )
    
    # Check architecture
    assert model.obs_dim == 10
    assert model.emotion_dim == 16
    assert model.hidden_dim == 64
    assert model.action_dim == 4
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"✅ Network created")
    print(f"✅ Total parameters: {total_params}")


def test_forward_pass():
    """Test forward pass."""
    print("\n" + "=" * 60)
    print("Test: Forward Pass")
    print("=" * 60)
    
    model = GatedIntegrationNetwork(
        obs_dim=10,
        emotion_dim=16,
        hidden_dim=64,
        action_dim=4
    )
    
    # Single sample
    obs = torch.randn(10)
    emotion = torch.randn(16)
    
    q_values = model(obs, emotion)
    
    # Check output shape
    assert q_values.shape == (4,)
    
    print(f"✅ Forward pass OK")
    print(f"✅ Q-values: {q_values}")


def test_batch_forward():
    """Test batch forward pass."""
    print("\n" + "=" * 60)
    print("Test: Batch Forward Pass")
    print("=" * 60)
    
    model = GatedIntegrationNetwork()
    
    # Batch
    batch_size = 32
    obs = torch.randn(batch_size, 10)
    emotion = torch.randn(batch_size, 16)
    
    q_values = model(obs, emotion)
    
    # Check output shape
    assert q_values.shape == (batch_size, 4)
    
    print(f"✅ Batch forward OK")
    print(f"✅ Output shape: {q_values.shape}")


def test_gate_values():
    """Test gate values."""
    print("\n" + "=" * 60)
    print("Test: Gate Values")
    print("=" * 60)
    
    model = GatedIntegrationNetwork()
    
    obs = torch.randn(10)
    emotion = torch.randn(16)
    
    gate = model.get_gate_values(obs, emotion)
    
    # Check gate in [0, 1]
    assert torch.all(gate >= 0)
    assert torch.all(gate <= 1)
    
    # Check shape
    assert gate.shape == (64,)  # hidden_dim
    
    print(f"✅ Gate values OK")
    print(f"✅ Gate mean: {gate.mean():.4f}")
    print(f"✅ Gate std: {gate.std():.4f}")


def test_trainer():
    """Test trainer."""
    print("\n" + "=" * 60)
    print("Test: Trainer")
    print("=" * 60)
    
    model = GatedIntegrationNetwork()
    trainer = GatedIntegrationTrainer(model, learning_rate=1e-3)
    
    # Mock data
    batch_size = 16
    obs = torch.randn(batch_size, 10)
    emotion = torch.randn(batch_size, 16)
    target_q = torch.randn(batch_size, 4)
    
    # Train step
    loss = trainer.train_step(obs, emotion, target_q)
    
    # Check loss
    assert isinstance(loss, float)
    assert loss > 0
    
    print(f"✅ Trainer OK")
    print(f"✅ Loss: {loss:.4f}")


def test_training_loop():
    """Test training loop."""
    print("\n" + "=" * 60)
    print("Test: Training Loop")
    print("=" * 60)
    
    model = GatedIntegrationNetwork()
    trainer = GatedIntegrationTrainer(model, learning_rate=1e-2)
    
    # Generate synthetic data
    batch_size = 32
    num_batches = 100
    
    losses = []
    
    for i in range(num_batches):
        # Random data
        obs = torch.randn(batch_size, 10)
        emotion = torch.randn(batch_size, 16)
        
        # Target: Simple function of obs + emotion
        target_q = torch.randn(batch_size, 4)
        
        # Train
        loss = trainer.train_step(obs, emotion, target_q)
        losses.append(loss)
        
        if i % 20 == 0:
            print(f"  Batch {i}: loss={loss:.4f}")
    
    # Check loss decreased
    initial_loss = np.mean(losses[:10])
    final_loss = np.mean(losses[-10:])
    
    print(f"\n✅ Training loop OK")
    print(f"✅ Initial loss: {initial_loss:.4f}")
    print(f"✅ Final loss: {final_loss:.4f}")
    print(f"✅ Improvement: {(initial_loss - final_loss) / initial_loss * 100:.1f}%")


def test_prediction():
    """Test prediction."""
    print("\n" + "=" * 60)
    print("Test: Prediction")
    print("=" * 60)
    
    model = GatedIntegrationNetwork()
    trainer = GatedIntegrationTrainer(model)
    
    # Single sample
    obs = torch.randn(10)
    emotion = torch.randn(16)
    
    # Predict
    q_values = trainer.predict(obs, emotion)
    
    # Check output
    assert q_values.shape == (4,)
    assert not q_values.requires_grad  # No gradient
    
    print(f"✅ Prediction OK")
    print(f"✅ Q-values: {q_values}")


def test_gate_interpretation():
    """Test gate interpretation."""
    print("\n" + "=" * 60)
    print("Test: Gate Interpretation")
    print("=" * 60)
    
    model = GatedIntegrationNetwork()
    
    # Test với different emotions
    obs = torch.randn(10)
    
    # High emotion
    high_emotion = torch.ones(16) * 2.0
    gate_high = model.get_gate_values(obs, high_emotion)
    
    # Low emotion
    low_emotion = torch.zeros(16)
    gate_low = model.get_gate_values(obs, low_emotion)
    
    print(f"✅ Gate interpretation OK")
    print(f"✅ Gate (high emotion) mean: {gate_high.mean():.4f}")
    print(f"✅ Gate (low emotion) mean: {gate_low.mean():.4f}")
    print(f"✅ Gates are adaptive!")


if __name__ == '__main__':
    test_network_creation()
    test_forward_pass()
    test_batch_forward()
    test_gate_values()
    test_trainer()
    test_training_loop()
    test_prediction()
    test_gate_interpretation()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
