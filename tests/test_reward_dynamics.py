
import sys
import os
import unittest
from unittest.mock import MagicMock
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.context import SystemContext
from src.processes.rl_snn_integration import combine_rewards

class TestRewardDynamics(unittest.TestCase):
    def setUp(self):
        # Mock Context
        self.ctx = MagicMock(spec=SystemContext)
        self.ctx.domain_ctx = MagicMock()
        self.ctx.global_ctx = MagicMock()
        
        # Default Config
        self.ctx.global_ctx.intrinsic_reward_weight = 0.5  # w1 (Novelty)
        self.ctx.global_ctx.surprise_reward_weight = 0.2   # w2 (Surprise)
        self.ctx.global_ctx.confidence_decay = 0.5         # EMA Alpha

    def test_pure_extrinsic(self):
        self.ctx.domain_ctx.last_reward = {'extrinsic': 1.0}
        self.ctx.domain_ctx.intrinsic_reward = 0.0
        self.ctx.domain_ctx.td_error = 0.0
        self.ctx.domain_ctx.metrics = {}
        
        combine_rewards(self.ctx)
        
        total = self.ctx.domain_ctx.last_reward['total']
        self.assertAlmostEqual(total, 1.0) # 1 + 0 + 0

    def test_hybrid_reward(self):
        # Scenario: Found something new (Novelty=0.8) AND Unexpected (Surprise=1.0)
        self.ctx.domain_ctx.last_reward = {'extrinsic': 0.1}
        self.ctx.domain_ctx.intrinsic_reward = 0.8
        self.ctx.domain_ctx.td_error = -1.0 # Abs = 1.0
        self.ctx.domain_ctx.metrics = {}
        
        combine_rewards(self.ctx)
        
        # Expected: 0.1 + (0.5 * 0.8) + (0.2 * 1.0) = 0.1 + 0.4 + 0.2 = 0.7
        total = self.ctx.domain_ctx.last_reward['total']
        self.assertAlmostEqual(total, 0.7)

    def test_confidence_calculation(self):
        # Scenario: Novelty=0.1 (Familiar), Error=0.0 (Perfect Prediction)
        # Expected Inst Confidence = (1-0.1) * exp(0) = 0.9 * 1 = 0.9
        self.ctx.domain_ctx.intrinsic_reward = 0.1
        self.ctx.domain_ctx.td_error = 0.0
        self.ctx.domain_ctx.metrics = {'confidence': 0.5} # Prev
        
        combine_rewards(self.ctx)
        
        # EMA: 0.5*0.9 + 0.5*0.5 = 0.45 + 0.25 = 0.7
        new_conf = self.ctx.domain_ctx.metrics['confidence']
        self.assertAlmostEqual(new_conf, 0.7)
        
    def test_confidence_crash(self):
        # Scenario: Surprise Error (Error=2.0)
        # Expected Inst = (1-0) * exp(-2) = 0.135
        self.ctx.domain_ctx.intrinsic_reward = 0.0
        self.ctx.domain_ctx.td_error = 2.0
        self.ctx.domain_ctx.metrics = {'confidence': 0.9} # Was confident
        
        combine_rewards(self.ctx)
        
        # EMA: 0.5*0.135 + 0.5*0.9 = 0.0675 + 0.45 = 0.5175
        new_conf = self.ctx.domain_ctx.metrics['confidence']
        self.assertLess(new_conf, 0.9) # Should drop

if __name__ == '__main__':
    unittest.main()
