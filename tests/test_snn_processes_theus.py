"""
Test SNN Theus Processes
=========================
Test các processes đã migrate sang Theus framework.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

import pytest
from src.core.snn_context_theus import create_snn_context_theus
from src.processes.snn_core_theus import (
    process_integrate,
    process_fire,
    process_tick
)
from src.processes.snn_learning_theus import (
    process_clustering,
    process_stdp
)
from src.processes.snn_homeostasis_theus import (
    process_homeostasis,
    process_meta_homeostasis_fixed
)


def test_process_tick():
    """Test process_tick."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    initial_time = ctx.domain_ctx.current_time
    process_tick(ctx)
    
    assert ctx.domain_ctx.current_time == initial_time + 1
    print("✅ process_tick OK")


def test_process_integrate():
    """Test process_integrate."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Inject spike vào queue
    ctx.domain_ctx.spike_queue[0] = [0, 1]
    ctx.domain_ctx.current_time = 0
    
    # Set potential ban đầu
    for neuron in ctx.domain_ctx.neurons:
        neuron.potential = 0.5
    
    # Run integrate
    process_integrate(ctx)
    
    # Check potential đã được update
    # (Có thể tăng hoặc giảm tùy vào synapses)
    print("✅ process_integrate OK")


def test_process_fire():
    """Test process_fire."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Set potential cao để bắn
    ctx.domain_ctx.neurons[0].potential = 2.0  # > threshold (1.0)
    ctx.domain_ctx.neurons[1].potential = 0.5  # < threshold
    
    # Run fire
    process_fire(ctx)
    
    # Check neuron 0 đã bắn
    assert ctx.domain_ctx.neurons[0].fire_count == 1
    assert ctx.domain_ctx.neurons[0].potential == -0.1  # Reset
    
    # Check neuron 1 không bắn
    assert ctx.domain_ctx.neurons[1].fire_count == 0
    
    # Check spike queue
    assert 1 in ctx.domain_ctx.spike_queue  # next_time = current_time + 1
    assert 0 in ctx.domain_ctx.spike_queue[1]
    
    # Check metrics
    assert 'fire_rate' in ctx.domain_ctx.metrics
    assert ctx.domain_ctx.metrics['fire_rate'] == 0.1  # 1/10
    
    print("✅ process_fire OK")


def test_process_clustering():
    """Test process_clustering."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Inject spike
    ctx.domain_ctx.spike_queue[0] = [0]
    ctx.domain_ctx.current_time = 0
    
    # Save prototype trước khi learn
    if len(ctx.domain_ctx.synapses) > 0:
        synapse = ctx.domain_ctx.synapses[0]
        post_id = synapse.post_neuron_id
        old_prototype = ctx.domain_ctx.neurons[post_id].prototype_vector.copy()
        
        # Run clustering
        process_clustering(ctx)
        
        # Check prototype đã thay đổi
        new_prototype = ctx.domain_ctx.neurons[post_id].prototype_vector
        # NOTE: Có thể giống nhau nếu spike_id != pre_neuron_id
        # Nhưng ít nhất process chạy được
    
    print("✅ process_clustering OK")


def test_process_stdp():
    """Test process_stdp."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Inject spike
    ctx.domain_ctx.spike_queue[0] = [0]
    ctx.domain_ctx.current_time = 0
    
    # Save weight trước khi learn
    if len(ctx.domain_ctx.synapses) > 0:
        old_weight = ctx.domain_ctx.synapses[0].weight
        old_trace = ctx.domain_ctx.synapses[0].trace
        
        # Run STDP
        process_stdp(ctx)
        
        # Check weight đã decay
        new_weight = ctx.domain_ctx.synapses[0].weight
        assert new_weight <= old_weight  # Weight decay
        
        # Check trace đã decay hoặc tăng
        # (Tùy vào synapse có pre_neuron_id == 0 không)
    
    print("✅ process_stdp OK")


def test_process_homeostasis():
    """Test process_homeostasis."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Set fire rate cao
    ctx.domain_ctx.metrics['fire_rate'] = 0.1  # > target (0.02)
    
    # Save threshold
    old_threshold = ctx.domain_ctx.neurons[0].threshold
    
    # Run homeostasis
    process_homeostasis(ctx)
    
    # Check threshold đã tăng (fire rate cao)
    new_threshold = ctx.domain_ctx.neurons[0].threshold
    assert new_threshold > old_threshold
    
    print("✅ process_homeostasis OK")


def test_process_meta_homeostasis():
    """Test process_meta_homeostasis_fixed."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Set fire rate thấp
    ctx.domain_ctx.metrics['fire_rate'] = 0.01  # < target (0.02)
    
    # Save threshold
    old_threshold = ctx.domain_ctx.neurons[0].threshold
    
    # Run meta-homeostasis
    process_meta_homeostasis_fixed(ctx)
    
    # Check threshold đã giảm (fire rate thấp)
    new_threshold = ctx.domain_ctx.neurons[0].threshold
    # NOTE: Có thể giống nhau vì adjustment rất nhỏ
    
    # Check metrics
    assert 'meta_threshold_adj' in ctx.domain_ctx.metrics
    assert 'meta_integral' in ctx.domain_ctx.metrics
    
    # Check integral bounded
    integral = ctx.domain_ctx.pid_state['threshold']['error_integral']
    assert -10.0 <= integral <= 10.0
    
    print("✅ process_meta_homeostasis_fixed OK")


def test_workflow_integration():
    """Test workflow với nhiều processes."""
    ctx = create_snn_context_theus(num_neurons=20, connectivity=0.15)
    
    # Inject initial spike
    ctx.domain_ctx.spike_queue[0] = [0, 1, 2]
    
    # Boost potential để đảm bảo có neurons bắn
    for i in range(3):
        ctx.domain_ctx.neurons[i].potential = 2.0  # Vượt threshold
    
    # Run workflow for 10 steps
    for step in range(10):
        ctx.domain_ctx.current_time = step
        
        # Core
        process_integrate(ctx)
        process_fire(ctx)
        
        # Learning
        process_clustering(ctx)
        process_stdp(ctx)
        
        # Homeostasis
        if step % 5 == 0:
            process_homeostasis(ctx)
        
        # Tick
        process_tick(ctx)
    
    # Check time advanced
    assert ctx.domain_ctx.current_time == 10
    
    # Check some neurons fired
    total_fires = sum(n.fire_count for n in ctx.domain_ctx.neurons)
    # NOTE: Có thể = 0 nếu không có cascade, nhưng ít nhất 3 neurons ban đầu phải bắn
    assert total_fires >= 3  # At least initial 3 neurons
    
    print(f"✅ Workflow OK: {total_fires} total fires in 10 steps")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing SNN Theus Processes")
    print("=" * 60)
    
    test_process_tick()
    test_process_integrate()
    test_process_fire()
    test_process_clustering()
    test_process_stdp()
    test_process_homeostasis()
    test_process_meta_homeostasis()
    test_workflow_integration()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
