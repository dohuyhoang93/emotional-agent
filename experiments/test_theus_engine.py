"""
Test SNN với Theus Engine
==========================
Test workflow execution với Theus Engine.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

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
from src.processes.snn_imagination_theus import (
    process_imagination_loop,
    process_dream_learning
)
from src.processes.snn_social_theus import (
    process_extract_top_synapses,
    process_sandbox_evaluation
)
from src.processes.snn_resync_theus import (
    process_periodic_resync
)


def test_workflow_manual():
    """
    Test workflow thủ công (không dùng Theus Engine).
    
    NOTE: Đây là fallback test khi chưa có Theus Engine integration.
    """
    print("=" * 60)
    print("Testing SNN Workflow (Manual)")
    print("=" * 60)
    
    # Create context
    ctx = create_snn_context_theus(num_neurons=100, connectivity=0.15)
    
    # Inject initial spike
    ctx.domain_ctx.spike_queue[0] = [0, 1, 2]
    for i in range(3):
        ctx.domain_ctx.neurons[i].potential = 2.0
    
    # Run workflow for 100 steps
    for step in range(100):
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
        
        if step % 10 == 0:
            process_meta_homeostasis_fixed(ctx)
        
        # Advanced
        if step % 50 == 0:
            process_imagination_loop(ctx)
            process_dream_learning(ctx)
        
        # Resync
        if step % 100 == 0:
            process_periodic_resync(ctx)
        
        # Tick
        process_tick(ctx)
        
        # Log
        if step % 10 == 0:
            fire_rate = ctx.domain_ctx.metrics.get('fire_rate', 0.0)
            print(f"Step {step}: fire_rate={fire_rate:.4f}")
    
    # Validate
    assert ctx.domain_ctx.current_time == 100
    
    total_fires = sum(n.fire_count for n in ctx.domain_ctx.neurons)
    assert total_fires > 0
    
    print(f"\n✅ Workflow OK: {total_fires} total fires in 100 steps")
    print(f"✅ Imagination count: {ctx.domain_ctx.metrics.get('imagination_count', 0)}")
    print(f"✅ Nightmare count: {ctx.domain_ctx.nightmare_count}")
    print(f"✅ Resync count: {ctx.domain_ctx.metrics.get('resync_count', 0)}")


def test_imagination_processes():
    """Test imagination processes."""
    print("\n" + "=" * 60)
    print("Testing Imagination Processes")
    print("=" * 60)
    
    ctx = create_snn_context_theus(num_neurons=50)
    
    # Set last imagination time
    ctx.domain_ctx.last_imagination_time = 0
    ctx.domain_ctx.current_time = 500
    
    # Run imagination
    process_imagination_loop(ctx)
    
    # Check spike injected
    assert 501 in ctx.domain_ctx.spike_queue
    assert len(ctx.domain_ctx.spike_queue[501]) > 0
    
    # Check metrics
    assert ctx.domain_ctx.metrics['imagination_count'] == 1
    
    print("✅ Imagination loop OK")
    
    # Test dream learning
    ctx.domain_ctx.metrics['fire_rate'] = 0.1  # High fire rate
    process_dream_learning(ctx)
    
    # Check nightmare triggered
    assert ctx.domain_ctx.nightmare_count > 0
    assert ctx.domain_ctx.metrics['dream_type'] == 'nightmare'
    
    print("✅ Dream learning OK")


def test_social_processes():
    """Test social learning processes."""
    print("\n" + "=" * 60)
    print("Testing Social Learning Processes")
    print("=" * 60)
    
    ctx = create_snn_context_theus(num_neurons=50)
    
    # Set some synapses with high confidence
    for i in range(min(10, len(ctx.domain_ctx.synapses))):
        ctx.domain_ctx.synapses[i].confidence = 0.9
        ctx.domain_ctx.synapses[i].weight = 0.8
    
    # Extract top synapses
    process_extract_top_synapses(ctx)
    
    # Check metrics
    assert 'top_synapse_ids' in ctx.domain_ctx.metrics
    assert ctx.domain_ctx.metrics['top_synapse_count'] > 0
    
    print("✅ Extract top synapses OK")
    
    # Test sandbox evaluation (no shadows yet)
    process_sandbox_evaluation(ctx)
    
    print("✅ Sandbox evaluation OK")


def test_resync_process():
    """Test resync process."""
    print("\n" + "=" * 60)
    print("Testing Resync Process")
    print("=" * 60)
    
    ctx = create_snn_context_theus(num_neurons=50)
    
    # Set time to trigger resync
    ctx.domain_ctx.current_time = 1000
    
    # Set some neurons with small values
    ctx.domain_ctx.neurons[0].potential = 1e-7  # Very small
    ctx.domain_ctx.neurons[1].prototype_vector *= 0  # Zero vector
    
    # Run resync
    process_periodic_resync(ctx)
    
    # Check resync happened
    assert ctx.domain_ctx.metrics['resync_count'] == 1
    assert ctx.domain_ctx.neurons[0].potential == 0.0  # Reset
    
    # Check prototype normalized
    norm = np.linalg.norm(ctx.domain_ctx.neurons[1].prototype_vector)
    assert 0.9 < norm < 1.1  # Should be ~1.0
    
    print("✅ Resync process OK")


if __name__ == '__main__':
    import numpy as np
    
    test_workflow_manual()
    test_imagination_processes()
    test_social_processes()
    test_resync_process()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
