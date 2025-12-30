import pytest
import numpy as np
import copy
import time
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.snn_context_theus import create_snn_context_theus, ensure_tensors_initialized
from src.processes.snn_learning_theus import _stdp_impl_vectorized

# --- MOCK WRAPPER ---
class MockDomain:
    def __init__(self, snn_ctx):
        self.snn_context = snn_ctx

class MockContext:
    def __init__(self, snn_ctx):
        self.domain_ctx = MockDomain(snn_ctx)

# --- MOCK OLD IMPLEMENTATION FOR BENCHMARK ---
def _stdp_impl_old_mock(ctx):
    """
    Mock functional logic equivalent to old STDP for benchmarking.
    """
    snn_ctx = ctx.domain_ctx.snn_context
    learning_rate = 0.01
    tau_trace = 0.9
    weight_decay = 0.9999
    time_window = 20
    
    # 1. Decay
    for synapse in snn_ctx.domain_ctx.synapses:
        synapse.weight *= weight_decay
        synapse.trace *= tau_trace
        
    current_spikes = snn_ctx.domain_ctx.spike_queue.get(snn_ctx.domain_ctx.current_time, [])
    if not current_spikes: return
    
    for spike_id in current_spikes:
        for synapse in snn_ctx.domain_ctx.synapses:
             if synapse.pre_neuron_id == spike_id:
                  synapse.trace += 1.0
                  # LTP logic... (simplified for benchmark speed)
                  if synapse.post_neuron_id < len(snn_ctx.domain_ctx.neurons):
                       post = snn_ctx.domain_ctx.neurons[synapse.post_neuron_id]
                       dt = snn_ctx.domain_ctx.current_time - post.last_fire_time
                       if 0 < dt < time_window:
                            synapse.weight += learning_rate * synapse.trace
             if synapse.post_neuron_id == spike_id:
                  # LTD logic...
                   if synapse.pre_neuron_id < len(snn_ctx.domain_ctx.neurons):
                       pre = snn_ctx.domain_ctx.neurons[synapse.pre_neuron_id]
                       dt = snn_ctx.domain_ctx.current_time - pre.last_fire_time
                       if 0 < dt < time_window:
                            synapse.weight -= learning_rate * 0.5

@pytest.fixture
def stdp_ctx():
    """Create SNN context with controlled state for STDP test."""
    ctx = create_snn_context_theus(num_neurons=3, connectivity=1.0) 
    
    # Configure synapses
    synapses = ctx.domain_ctx.synapses
    for s in synapses:
        s.weight = 0.5
        s.trace = 0.1
        if s.pre_neuron_id == 2 and s.post_neuron_id == 0:
            s.weight = 0.0 # Effectively disconnected
            
    ctx.domain_ctx.current_time = 100
    ensure_tensors_initialized(ctx)
    return MockContext(ctx)

def test_stdp_decay(stdp_ctx):
    """Test weight and trace decay."""
    # No spikes
    _stdp_impl_vectorized(stdp_ctx)
    
    t = stdp_ctx.domain_ctx.snn_context.domain_ctx.tensors
    # Trace should decay: 0.1 * 0.9 = 0.09
    # Note: Diagonal is 0 (no self-loops), so check off-diagonal
    traces = t['traces']
    np.fill_diagonal(traces, 0.09) # Fill diagonal to match expected for easy comparison, or ignore it
    assert np.allclose(traces, 0.09, atol=1e-5)
    # Weight should decay: 0.5 * 0.9999 = 0.49995 (except the 0.0 one)
    w = t['weights']
    assert np.isclose(w[0, 1], 0.49995)
    assert np.isclose(w[2, 0], 0.0) # Should remain 0

def test_stdp_ltp(stdp_ctx):
    """Test LTP: Pre-fire leads to weight increase if Post fired recently."""
    snn_domain = stdp_ctx.domain_ctx.snn_context.domain_ctx
    t = snn_domain.tensors
    neurons = snn_domain.neurons
    
    # Post neuron (1) fired at 90
    neurons[1].last_fire_time = 90
    t['last_fire_times'][1] = 90
    
    # Pre neuron (0) fires NOW
    snn_domain.spike_queue[100] = [0]
    
    # Run STDP
    _stdp_impl_vectorized(stdp_ctx)
    
    # Updates happen:
    # 1. Decay: trace -> 0.09, weight -> 0.49995
    # 2. Trace update from spike 0: trace[0,1] += 1 -> 1.09
    # 3. LTP: dt = 10. w[0,1] += lr(0.01) * trace(1.09) = 0.0109 + 0.49995 = 0.51085
    
    w_expected = (0.5 * 0.9999) + (0.01 * ((0.1 * 0.9) + 1.0))
    
    # print(f"Computed: {t['weights'][0, 1]}, Expected around: {w_expected}")
    assert np.isclose(t['weights'][0, 1], w_expected, atol=1e-5)
    
def test_stdp_ltd(stdp_ctx):
    """Test LTD: Post-fire leads to weight decrease if Pre fired recently."""
    snn_domain = stdp_ctx.domain_ctx.snn_context.domain_ctx
    t = snn_domain.tensors
    neurons = snn_domain.neurons
    
    # Pre neuron (0) fired at 90
    neurons[0].last_fire_time = 90
    t['last_fire_times'][0] = 90
    
    # Post neuron (1) fires NOW
    snn_domain.spike_queue[100] = [1]
    
    # Run STDP
    _stdp_impl_vectorized(stdp_ctx)
    
    # Updates:
    # 1. Decay
    # 2. Trace update (only for 1 outgoing, i.e., 1->2). 0->1 trace decays.
    # 3. LTD: Check 0->1. Pre(0) fired -10ms ago. Good.
    # w[0,1] -= lr(0.01) * 0.5 = 0.005
    
    w_decayed = 0.5 * 0.9999
    w_expected = w_decayed - (0.01 * 0.5)
    
    assert np.isclose(t['weights'][0, 1], w_expected, atol=1e-5)

def test_stdp_benchmark():
    """Benchmark Vectorized vs Mock Old."""
    # Large context
    N = 100 # 100 neurons
    ctx = create_snn_context_theus(num_neurons=N, connectivity=0.5) 
    ensure_tensors_initialized(ctx)
    
    # Lots of spikes
    spikes = list(range(0, N, 2)) # 50 spikes
    ctx.domain_ctx.spike_queue[ctx.domain_ctx.current_time] = spikes
    
    # Copy for comparison
    ctx_old = copy.deepcopy(ctx)
    ctx_new = copy.deepcopy(ctx)
    
    # Wrap in MockContext
    ctx_old_mock = MockContext(ctx_old)
    ctx_new_mock = MockContext(ctx_new)
    
    # Measure Old
    start = time.time()
    for _ in range(20):
        _stdp_impl_old_mock(ctx_old_mock)
    t_old = time.time() - start
    
    # Measure New
    start = time.time()
    for _ in range(20):
        _stdp_impl_vectorized(ctx_new_mock)
    t_new = time.time() - start
    
    print(f"\nBenchmark (N={N}, 20 steps):")
    print(f"Old: {t_old:.4f}s")
    print(f"New: {t_new:.4f}s")
    print(f"Speedup: {t_old/t_new:.2f}x")
    
    # With N=100, speedup should be significant
    assert t_new < t_old
