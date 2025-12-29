
import unittest
import numpy as np
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.core.snn_context_theus import (
    create_snn_context_theus,
    ensure_tensors_initialized,
    sync_from_tensors,
    sync_to_tensors,
    COMMIT_STATE_SOLID
)

class TestSNNTensorsPhase2(unittest.TestCase):
    """
    Test suite for Phase 2 Optimization Infrastructure.
    Focus:
    1. Thresholds sync (Homeostasis)
    2. Commit States sync (Commitment)
    """

    def setUp(self):
        # Create a small SNN (10 neurons)
        self.ctx = create_snn_context_theus(num_neurons=10, connectivity=0.5, seed=42)
        self.domain = self.ctx.domain_ctx
        ensure_tensors_initialized(self.ctx)

    def test_thresholds_init_and_sync(self):
        """Verify thresholds are mapped to tensors and synced back."""
        # Check Init
        self.assertIn('thresholds', self.domain.tensors)
        self.assertEqual(self.domain.tensors['thresholds'].shape, (10,))
        
        # Verify values match objects
        for i, neuron in enumerate(self.domain.neurons):
            self.assertEqual(self.domain.tensors['thresholds'][i], neuron.threshold)

        # Modify Tensors (Simulate Vectorized Homeostasis)
        # Increase threshold of neuron 0
        self.domain.tensors['thresholds'][0] += 0.5
        
        # Sync Back
        sync_from_tensors(self.ctx)
        
        # Verify Object Updated
        self.assertAlmostEqual(self.domain.neurons[0].threshold, 1.5)
        self.assertAlmostEqual(self.domain.neurons[1].threshold, 1.0) # Unchanged

    def test_commitment_tensors_init_and_sync(self):
        """Verify commitment tensors are mapped and synced back."""
        # Check Init
        self.assertIn('commit_states', self.domain.tensors)
        self.assertIn('consecutive_correct', self.domain.tensors)
        self.assertIn('consecutive_wrong', self.domain.tensors)
        
        shape = (10, 10)
        self.assertEqual(self.domain.tensors['commit_states'].shape, shape)
        self.assertEqual(self.domain.tensors['commit_states'].dtype, np.int8)

        # Modify Tensors (Simulate Vectorized Commitment)
        # Find a valid synapse
        synapse = self.domain.synapses[0]
        u, v = synapse.pre_neuron_id, synapse.post_neuron_id
        
        # Update tensor
        self.domain.tensors['commit_states'][u, v] = COMMIT_STATE_SOLID
        self.domain.tensors['consecutive_correct'][u, v] = 99
        self.domain.tensors['consecutive_wrong'][u, v] = 1
        
        # Sync Back
        sync_from_tensors(self.ctx)
        
        # Verify Object Updated
        self.assertEqual(synapse.commit_state, COMMIT_STATE_SOLID)
        self.assertEqual(synapse.consecutive_correct, 99)
        self.assertEqual(synapse.consecutive_wrong, 1)

    def test_sync_performance_sanity(self):
        """Ensure unnecessary syncs are skipped or efficient."""
        # Just a smoketest for crashes
        sync_to_tensors(self.ctx)
        sync_from_tensors(self.ctx)
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
