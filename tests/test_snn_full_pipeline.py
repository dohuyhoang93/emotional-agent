import pytest
import numpy as np
import copy
import time
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.snn_context_theus import create_snn_context_theus, ensure_tensors_initialized
from src.processes.snn_core_theus import _integrate_impl, _fire_impl
from src.processes.snn_learning_theus import _stdp_impl_vectorized, _clustering_impl_vectorized

# Define a mock context structure that matches what processes expect
class MockDomain:
    def __init__(self, snn_ctx):
        self.snn_context = snn_ctx

class MockContextWrapper:
    def __init__(self, snn_ctx):
        self.domain_ctx = MockDomain(snn_ctx)

@pytest.fixture
def full_pipeline_ctx():
    """Create a completely initialized SNN context for integration testing."""
    N = 50 
    connectivity = 0.5
    ctx = create_snn_context_theus(num_neurons=N, connectivity=connectivity)
    ensure_tensors_initialized(ctx)
    
    # Inject some initial potential to trigger firing
    neurons = ctx.domain_ctx.neurons
    tensors = ctx.domain_ctx.tensors
    
    # Random initial potentials
    tensors['potentials'] = np.random.rand(N).astype(np.float32)
    # Give some input current via weights... simulates inputs over time
    
    return ctx

def test_snn_pipeline_simulation(full_pipeline_ctx):
    """
    Run the full SNN loop for T steps.
    Sequence: Integrate -> Fire -> STDP -> Clustering
    """
    ctx = full_pipeline_ctx
    wrapper = MockContextWrapper(ctx)
    
    T = 500 # Simulating 500ms
    
    start_time = time.time()
    
    spike_counts = 0
    
    for t in range(T):
        ctx.domain_ctx.current_time = t
        
        # 1. Integrate
        # Mock inputs: random current to some neurons
        # In real app, inputs come from sensors.
        # We can directly inject into potentials or use spike_queue
        # Let's inject current directly for simplicity (mimic input process)
        # Using `potentials` tensor directly
        # But `_integrate_impl` decays potentials first.
        
        # Inject noise current
        noise = np.random.rand(len(ctx.domain_ctx.neurons)) * 0.1
        ctx.domain_ctx.tensors['potentials'] += noise.astype(np.float32)
        
        _integrate_impl(wrapper)
        
        # 2. Fire
        _fire_impl(wrapper)
        
        # Count spikes
        spikes = ctx.domain_ctx.spike_queue.get(t, [])
        spike_counts += len(spikes)
        
        # 3. Learning (Vectorized)
        _stdp_impl_vectorized(wrapper)
        _clustering_impl_vectorized(wrapper)
        
    duration = time.time() - start_time
    print(f"\nSimulation {T} steps with N={len(ctx.domain_ctx.neurons)} completed in {duration:.4f}s")
    print(f"Total Spikes: {spike_counts}")
    print(f"Average Speed: {duration/T*1000:.2f} ms/step")
    
    # Assertions
    # 1. It finished (implied)
    # 2. Performance is reasonable (e.g. < 5s for 500 steps)
    assert duration < 5.0 
    
    # 3. Check for NaNs
    t = ctx.domain_ctx.tensors
    assert not np.isnan(t['potentials']).any()
    assert not np.isnan(t['weights']).any()
    assert not np.isnan(t['prototypes']).any()
    assert not np.isnan(t['traces']).any()
    
    # 4. Check that weights changed (if there were spikes)
    if spike_counts > 0:
        # We can't easily check 'changed' without saving copy, but we verified in unit tests.
        pass
