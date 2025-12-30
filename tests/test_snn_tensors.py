import pytest
from src.core.snn_context_theus import (
    create_snn_context_theus, 
    ensure_tensors_initialized,
    sync_from_tensors
)

@pytest.fixture
def snn_ctx():
    """Create a standard SNN context."""
    return create_snn_context_theus(num_neurons=10, connectivity=1.0) # Full connectivity for easier testing

def test_ensure_tensors_initialized(snn_ctx):
    """Test that all tensors are created correctly."""
    ensure_tensors_initialized(snn_ctx)
    t = snn_ctx.domain_ctx.tensors
    
    assert 'potentials' in t
    assert 'thresholds' in t
    assert 'weights' in t
    assert 'traces' in t
    assert 'fitnesses' in t
    
    # Check shapes
    N = 10
    assert t['potentials'].shape == (N,)
    assert t['weights'].shape == (N, N)
    assert t['traces'].shape == (N, N)
    assert t['fitnesses'].shape == (N, N)

def test_sync_to_tensors(snn_ctx):
    """Test object -> tensor synchronization."""
    domain = snn_ctx.domain_ctx
    neurons = domain.neurons
    synapses = domain.synapses
    
    # Modify objects
    neurons[0].potential = 0.8
    synapses[0].trace = 0.5
    synapses[0].fitness = 0.7
    
    # Run sync
    ensure_tensors_initialized(snn_ctx) # Also calls sync_to_tensors
    t = domain.tensors
    
    # Verify tensors updated
    assert t['potentials'][0] == 0.8
    
    pre = synapses[0].pre_neuron_id
    post = synapses[0].post_neuron_id
    assert t['traces'][pre, post] == 0.5
    assert t['fitnesses'][pre, post] == 0.7

def test_sync_from_tensors(snn_ctx):
    """Test tensor -> object synchronization."""
    ensure_tensors_initialized(snn_ctx)
    t = snn_ctx.domain_ctx.tensors
    domain = snn_ctx.domain_ctx
    
    # Modify tensors
    pre = domain.synapses[0].pre_neuron_id
    post = domain.synapses[0].post_neuron_id
    
    t['traces'][pre, post] = 0.9
    t['fitnesses'][pre, post] = 0.2
    
    # Run sync back
    sync_from_tensors(snn_ctx)
    
    # Verify objects updated
    assert domain.synapses[0].trace == 0.9
    # NOTE: fitness might not update if we didn't implement sync back for it?
    # Let's check implementation behavior
    assert domain.synapses[0].fitness == 0.2
