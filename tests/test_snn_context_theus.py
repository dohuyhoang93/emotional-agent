"""
Test SNN Theus Context
=======================
Unit tests cho SNN Context design với Theus framework.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

import pytest
import numpy as np
from src.core.snn_context_theus import (
    SNNGlobalContext,
    SNNDomainContext,
    SNNSystemContext,
    NeuronState,
    SynapseState,
    create_snn_context_theus
)


def test_global_context_creation():
    """Test tạo SNNGlobalContext."""
    global_ctx = SNNGlobalContext(
        num_neurons=50,
        connectivity=0.2,
        learning_rate=0.05
    )
    
    assert global_ctx.num_neurons == 50
    assert global_ctx.connectivity == 0.2
    assert global_ctx.learning_rate == 0.05
    assert global_ctx.vector_dim == 16  # Default
    print("✅ Global context creation OK")


def test_domain_context_creation():
    """Test tạo SNNDomainContext."""
    domain_ctx = SNNDomainContext(agent_id=1)
    
    assert domain_ctx.agent_id == 1
    assert len(domain_ctx.neurons) == 0
    assert len(domain_ctx.synapses) == 0
    assert domain_ctx.current_time == 0
    assert 'threshold' in domain_ctx.pid_state
    print("✅ Domain context creation OK")


def test_neuron_state():
    """Test NeuronState."""
    neuron = NeuronState(
        neuron_id=0,
        potential=0.5,
        threshold=1.0
    )
    
    assert neuron.neuron_id == 0
    assert neuron.potential == 0.5
    assert neuron.threshold == 1.0
    assert neuron.potential_vector.shape == (16,)
    assert neuron.prototype_vector.shape == (16,)
    print("✅ Neuron state OK")


def test_synapse_state():
    """Test SynapseState."""
    synapse = SynapseState(
        synapse_id=0,
        pre_neuron_id=1,
        post_neuron_id=2,
        weight=0.7
    )
    
    assert synapse.synapse_id == 0
    assert synapse.pre_neuron_id == 1
    assert synapse.post_neuron_id == 2
    assert synapse.weight == 0.7
    assert synapse.synapse_type == "native"
    print("✅ Synapse state OK")


def test_system_context_creation():
    """Test tạo SNNSystemContext."""
    global_ctx = SNNGlobalContext(num_neurons=10)
    domain_ctx = SNNDomainContext()
    
    sys_ctx = SNNSystemContext(
        global_ctx=global_ctx,
        domain_ctx=domain_ctx
    )
    
    assert sys_ctx.global_ctx.num_neurons == 10
    assert sys_ctx.domain_ctx.current_time == 0
    assert sys_ctx.cycle_count == 0
    assert sys_ctx.is_running == True
    print("✅ System context creation OK")


def test_create_snn_context_theus():
    """Test factory function."""
    ctx = create_snn_context_theus(
        num_neurons=20,
        connectivity=0.1,
        learning_rate=0.02
    )
    
    # Check global context
    assert ctx.global_ctx.num_neurons == 20
    assert ctx.global_ctx.connectivity == 0.1
    assert ctx.global_ctx.learning_rate == 0.02
    
    # Check domain context
    assert len(ctx.domain_ctx.neurons) == 20
    assert len(ctx.domain_ctx.synapses) > 0
    
    # Check neurons initialized
    for neuron in ctx.domain_ctx.neurons:
        assert neuron.threshold == ctx.global_ctx.initial_threshold
        assert neuron.prototype_vector.shape == (16,)
        # Check normalized
        norm = np.linalg.norm(neuron.prototype_vector)
        assert 0.9 < norm < 1.1  # Should be ~1.0
    
    # Check synapses
    expected_synapses = int(20 * 19 * 0.1)  # Approximate
    actual_synapses = len(ctx.domain_ctx.synapses)
    # NOTE: Random variance có thể lớn với sample nhỏ
    assert abs(actual_synapses - expected_synapses) < 20  # Tolerance tăng lên
    
    for synapse in ctx.domain_ctx.synapses:
        assert 0 <= synapse.pre_neuron_id < 20
        assert 0 <= synapse.post_neuron_id < 20
        assert synapse.pre_neuron_id != synapse.post_neuron_id
        assert 0.3 <= synapse.weight <= 0.7
    
    print(f"✅ Factory function OK: {actual_synapses} synapses created")


def test_context_inheritance():
    """Test context kế thừa từ Theus base classes."""
    from theus import BaseGlobalContext, BaseDomainContext, BaseSystemContext
    
    global_ctx = SNNGlobalContext()
    domain_ctx = SNNDomainContext()
    sys_ctx = SNNSystemContext(
        global_ctx=global_ctx,
        domain_ctx=domain_ctx
    )
    
    assert isinstance(global_ctx, BaseGlobalContext)
    assert isinstance(domain_ctx, BaseDomainContext)
    assert isinstance(sys_ctx, BaseSystemContext)
    
    print("✅ Context inheritance OK")


def test_pid_state_structure():
    """Test PID state structure."""
    domain_ctx = SNNDomainContext()
    
    assert 'threshold' in domain_ctx.pid_state
    assert 'learning_rate' in domain_ctx.pid_state
    
    assert 'error_integral' in domain_ctx.pid_state['threshold']
    assert 'error_prev' in domain_ctx.pid_state['threshold']
    
    assert domain_ctx.pid_state['threshold']['error_integral'] == 0.0
    assert domain_ctx.pid_state['threshold']['error_prev'] == 0.0
    
    print("✅ PID state structure OK")


def test_metrics_dict():
    """Test metrics dictionary."""
    domain_ctx = SNNDomainContext()
    
    # Initially empty
    assert len(domain_ctx.metrics) == 0
    
    # Can add metrics
    domain_ctx.metrics['fire_rate'] = 0.02
    domain_ctx.metrics['similarity'] = 0.5
    
    assert domain_ctx.metrics['fire_rate'] == 0.02
    assert domain_ctx.metrics['similarity'] == 0.5
    
    print("✅ Metrics dict OK")


def test_spike_queue():
    """Test spike queue structure."""
    domain_ctx = SNNDomainContext()
    
    # Initially empty
    assert len(domain_ctx.spike_queue) == 0
    
    # Can add spikes
    domain_ctx.spike_queue[0] = [1, 2, 3]
    domain_ctx.spike_queue[1] = [4, 5]
    
    assert domain_ctx.spike_queue[0] == [1, 2, 3]
    assert domain_ctx.spike_queue[1] == [4, 5]
    
    print("✅ Spike queue OK")


def test_hyperparameters_ranges():
    """Test hyperparameters trong range hợp lý."""
    global_ctx = SNNGlobalContext()
    
    # Network
    assert 0 < global_ctx.connectivity < 1
    assert global_ctx.vector_dim > 0
    
    # Neuron
    assert 0 < global_ctx.tau_decay <= 1
    assert global_ctx.refractory_period > 0
    assert global_ctx.threshold_min < global_ctx.threshold_max
    
    # Learning
    assert 0 < global_ctx.learning_rate < 1
    assert 0 < global_ctx.clustering_rate < 1
    assert 0 < global_ctx.tau_trace <= 1
    assert 0 < global_ctx.weight_decay <= 1
    
    # Homeostasis
    assert 0 < global_ctx.target_fire_rate < 1
    assert 0 < global_ctx.homeostasis_rate < 1
    
    # Meta-Homeostasis
    assert global_ctx.meta_pid_kp > 0
    assert global_ctx.meta_pid_ki > 0
    assert global_ctx.meta_pid_kd > 0
    assert global_ctx.meta_max_integral > 0
    assert global_ctx.meta_max_output > 0
    
    print("✅ Hyperparameters ranges OK")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing SNN Theus Context")
    print("=" * 60)
    
    test_global_context_creation()
    test_domain_context_creation()
    test_neuron_state()
    test_synapse_state()
    test_system_context_creation()
    test_create_snn_context_theus()
    test_context_inheritance()
    test_pid_state_structure()
    test_metrics_dict()
    test_spike_queue()
    test_hyperparameters_ranges()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
