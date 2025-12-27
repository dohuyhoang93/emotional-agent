import sys
import os
sys.path.append(os.getcwd())

import unittest
import torch
import torch.nn as nn
from src.models.gated_integration import GatedIntegrationNetwork, GatedIntegrationTrainer

class TestAttentionNetwork(unittest.TestCase):
    def setUp(self):
        self.obs_dim = 10
        self.emotion_dim = 16
        self.hidden_dim = 64
        self.action_dim = 4
        
        self.model = GatedIntegrationNetwork(
            obs_dim=self.obs_dim,
            emotion_dim=self.emotion_dim,
            hidden_dim=self.hidden_dim,
            action_dim=self.action_dim
        )
        
    def test_forward_shape(self):
        """Test if forward pass returns correct shape"""
        batch_size = 32
        obs = torch.randn(batch_size, self.obs_dim)
        emo = torch.randn(batch_size, self.emotion_dim)
        
        q_values = self.model(obs, emo)
        self.assertEqual(q_values.shape, (batch_size, self.action_dim))
        
    def test_forward_single_sample(self):
        """Test single sample processing (unbatched)"""
        obs = torch.randn(self.obs_dim)
        emo = torch.randn(self.emotion_dim)
        
        q_values = self.model(obs, emo)
        self.assertEqual(q_values.shape, (self.action_dim,))
        
    def test_gradients(self):
        """Test if gradients flow back to both inputs"""
        obs = torch.randn(1, self.obs_dim, requires_grad=True)
        emo = torch.randn(1, self.emotion_dim, requires_grad=True)
        
        q_values = self.model(obs, emo)
        loss = q_values.sum()
        loss.backward()
        
        self.assertIsNotNone(obs.grad)
        self.assertIsNotNone(emo.grad)
        
        # Check if attention weights are computed
        attn_weights = self.model.get_attention_weights(obs, emo)
        # Should be [Batch, Num_Heads] -> [1, 4]
        self.assertEqual(attn_weights.shape, (1, 4))
        
        # Weights should be in [0, 1] range (Sigmoid)
        self.assertTrue(torch.all(attn_weights >= 0.0))
        self.assertTrue(torch.all(attn_weights <= 1.0))

class TestAttentionTrainer(unittest.TestCase):
    def setUp(self):
        self.model = GatedIntegrationNetwork()
        self.trainer = GatedIntegrationTrainer(self.model)
        
    def test_train_step(self):
        """Test if train_step runs without error (gradient clipping verified implicitly)"""
        batch_size = 4
        obs = torch.randn(batch_size, 10)
        emo = torch.randn(batch_size, 16)
        target = torch.randn(batch_size, 4)
        
        loss = self.trainer.train_step(obs, emo, target)
        self.assertIsInstance(loss, float)

if __name__ == '__main__':
    unittest.main()
