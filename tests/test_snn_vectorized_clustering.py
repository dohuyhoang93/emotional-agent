import pytest
import numpy as np
import copy
import time
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.snn_context_theus import create_snn_context_theus, ensure_tensors_initialized, sync_to_tensors, sync_from_tensors
from src.processes.snn_learning_theus import _clustering_impl_vectorized

# --- MOCK WRAPPER ---
class MockDomain:
    def __init__(self, snn_ctx):
        self.snn_context = snn_ctx

class MockContext:
    def __init__(self, snn_ctx):
        self.domain_ctx = MockDomain(snn_ctx)

# --- MOCK OLD IMPLEMENTATION FOR CORRECTNESS CHECK ---
def _clustering_impl_old_mock(ctx):
    snn_ctx = ctx.domain_ctx.snn_context
    learning_rate = 0.001
    
    current_spikes = snn_ctx.domain_ctx.spike_queue.get(snn_ctx.domain_ctx.current_time, [])
    if not current_spikes: return
    
    for spike_id in current_spikes:
        if spike_id >= len(snn_ctx.domain_ctx.neurons): continue
        spike_neuron = snn_ctx.domain_ctx.neurons[spike_id]
        spike_vector = spike_neuron.prototype_vector
        
        for synapse in snn_ctx.domain_ctx.synapses:
            if synapse.pre_neuron_id != spike_id: continue
            if synapse.post_neuron_id >= len(snn_ctx.domain_ctx.neurons): continue
            
            post_neuron = snn_ctx.domain_ctx.neurons[synapse.post_neuron_id]
            direction = spike_vector - post_neuron.prototype_vector
            post_neuron.prototype_vector += learning_rate * direction
            
            norm = np.linalg.norm(post_neuron.prototype_vector)
            if norm > 0:
                post_neuron.prototype_vector /= norm

@pytest.fixture
def clustering_ctx():
    """Create SNN context with controlled state for Clustering test."""
    # 3 neurons: 0 -> 1 connected
    ctx = create_snn_context_theus(num_neurons=3, connectivity=1.0)
    
    # Init prototypes with known values
    # Neuron 0: [1, 0, 0, ...]
    # Neuron 1: [0, 1, 0, ...]
    neurons = ctx.domain_ctx.neurons
    neurons[0].prototype_vector = np.zeros(16)
    neurons[0].prototype_vector[0] = 1.0
    
    neurons[1].prototype_vector = np.zeros(16)
    neurons[1].prototype_vector[1] = 1.0
    
    ctx.domain_ctx.current_time = 100
    ensure_tensors_initialized(ctx)
    return MockContext(ctx)

def test_clustering_update(clustering_ctx):
    """Test that post-neuron prototypes move towards firing neuron prototype."""
    snn_domain = clustering_ctx.domain_ctx.snn_context.domain_ctx
    t = snn_domain.tensors
    
    # Spike from Neuron 0
    snn_domain.spike_queue[100] = [0]
    
    # Initial state
    proto_0 = t['prototypes'][0].copy() # [1, 0, ...]
    proto_1 = t['prototypes'][1].copy() # [0, 1, ...]
    
    # Run Vectorized Clustering
    _clustering_impl_vectorized(clustering_ctx)
    
    # Check Update
    # Neuron 1 is connected to Neuron 0 (0->1). So 1 should move towards 0.
    # New 1 = Old 1 + lr * (Old 0 - Old 1)
    lr = 0.001
    expected_vec = proto_1 + lr * (proto_0 - proto_1)
    expected_vec /= np.linalg.norm(expected_vec)
    
    # We verify that actual updated prototype matches expected
    actual_proto_1 = t['prototypes'][1]
    
    assert np.allclose(actual_proto_1, expected_vec, atol=1e-5)
    
    # Verify Neuron 0 did NOT change (it was the spiker, not post)
    # UNLESS 0 points to itself? Connectivity=1.0 usually excludes self.
    # In create_snn_context_theus, diagonal is skipped. So 0->0 doesn't exist.
    assert np.allclose(t['prototypes'][0], proto_0, atol=1e-5)

def test_clustering_benchmark():
    """Benchmark Vectorized vs Mock Old."""
    N = 100
    ctx = create_snn_context_theus(num_neurons=N, connectivity=0.5)
    ensure_tensors_initialized(ctx)
    
    # 10 spikes
    ctx.domain_ctx.spike_queue[ctx.domain_ctx.current_time] = list(range(10))
    
    ctx_old = MockContext(copy.deepcopy(ctx))
    ctx_new = MockContext(copy.deepcopy(ctx))
    
    start = time.time()
    for _ in range(50):
        _clustering_impl_old_mock(ctx_old)
    t_old = time.time() - start
    
    start = time.time()
    for _ in range(50):
        _clustering_impl_vectorized(ctx_new)
    t_new = time.time() - start
    
    print(f"\nClustering Benchmark (N={N}, 50 steps):")
    print(f"Old: {t_old:.4f}s")
    print(f"New: {t_new:.4f}s")
    print(f"Speedup: {t_old/t_new:.2f}x")
    
    assert t_new < t_old
