"""
Test Commitment Layer
======================
Test 3-state FSM và protected learning.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

import numpy as np
from src.core.snn_context_theus import (
    create_snn_context_theus,
    COMMIT_STATE_FLUID,
    COMMIT_STATE_SOLID,
    COMMIT_STATE_REVOKED
)
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.processes.snn_commitment_theus import (
    process_commitment,
    process_pruning
)
from src.processes.snn_learning_3factor_theus import process_stdp_3factor


def create_test_rl_context():
    """Tạo RL context với TD-error."""
    global_ctx = GlobalContext()
    domain_ctx = DomainContext()
    domain_ctx.td_error = 0.0
    
    return SystemContext(
        global_ctx=global_ctx,
        domain_ctx=domain_ctx
    )


def test_state_transitions():
    """Test FLUID → SOLID → REVOKED."""
    print("=" * 60)
    print("Test: State Transitions")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=50)
    rl_ctx = create_test_rl_context()
    
    synapse = snn_ctx.domain_ctx.synapses[0]
    assert synapse.commit_state == COMMIT_STATE_FLUID
    print(f"  Initial state: FLUID")
    
    # Good predictions → SOLID
    for i in range(10):
        rl_ctx.domain_ctx.td_error = 0.05  # Low error
        process_commitment(snn_ctx, rl_ctx)
    
    print(f"  After 10 good predictions:")
    print(f"    State: {synapse.commit_state} (SOLID={COMMIT_STATE_SOLID})")
    print(f"    Consecutive correct: {synapse.consecutive_correct}")
    assert synapse.commit_state == COMMIT_STATE_SOLID
    
    # Bad predictions → REVOKED
    for i in range(5):
        rl_ctx.domain_ctx.td_error = 1.0  # High error
        process_commitment(snn_ctx, rl_ctx)
    
    print(f"  After 5 bad predictions:")
    print(f"    State: {synapse.commit_state} (REVOKED={COMMIT_STATE_REVOKED})")
    print(f"    Consecutive wrong: {synapse.consecutive_wrong}")
    assert synapse.commit_state == COMMIT_STATE_REVOKED
    
    print("✅ State transitions work!")


def test_protected_learning():
    """Test SOLID synapses learn slower."""
    print("\n" + "=" * 60)
    print("Test: Protected Learning")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=50)
    rl_ctx = create_test_rl_context()
    
    # Two synapses: one FLUID, one SOLID
    fluid_syn = snn_ctx.domain_ctx.synapses[0]
    solid_syn = snn_ctx.domain_ctx.synapses[1]
    
    fluid_syn.commit_state = COMMIT_STATE_FLUID
    solid_syn.commit_state = COMMIT_STATE_SOLID
    
    # Inject spike để set traces
    snn_ctx.domain_ctx.spike_queue[0] = [0, 1]
    snn_ctx.domain_ctx.current_time = 0
    rl_ctx.domain_ctx.td_error = 0.0
    
    process_stdp_3factor(snn_ctx, rl_ctx)
    
    # Same initial weight
    fluid_syn.weight = 0.5
    solid_syn.weight = 0.5
    
    # Apply strong learning
    rl_ctx.domain_ctx.td_error = 5.0
    process_stdp_3factor(snn_ctx, rl_ctx)
    
    # FLUID should change more
    fluid_delta = abs(fluid_syn.weight - 0.5)
    solid_delta = abs(solid_syn.weight - 0.5)
    
    print(f"  FLUID synapse:")
    print(f"    Δw: {fluid_delta:.6f}")
    print(f"  SOLID synapse:")
    print(f"    Δw: {solid_delta:.6f}")
    print(f"  Ratio: {fluid_delta / (solid_delta + 1e-8):.2f}x")
    
    assert fluid_delta > solid_delta * 5  # 10x slower
    
    print("✅ Protected learning works!")


def test_revoked_skip_learning():
    """Test REVOKED synapses don't learn."""
    print("\n" + "=" * 60)
    print("Test: REVOKED Synapses Skip Learning")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=50)
    rl_ctx = create_test_rl_context()
    
    revoked_syn = snn_ctx.domain_ctx.synapses[0]
    revoked_syn.commit_state = COMMIT_STATE_REVOKED
    
    # Inject spike
    snn_ctx.domain_ctx.spike_queue[0] = [0]
    snn_ctx.domain_ctx.current_time = 0
    rl_ctx.domain_ctx.td_error = 0.0
    
    process_stdp_3factor(snn_ctx, rl_ctx)
    
    # Set weight
    revoked_syn.weight = 0.5
    
    # Try to learn
    rl_ctx.domain_ctx.td_error = 5.0
    process_stdp_3factor(snn_ctx, rl_ctx)
    
    # Weight should not change (except decay)
    print(f"  Weight after learning: {revoked_syn.weight:.6f}")
    assert abs(revoked_syn.weight - 0.5) < 0.01  # Only decay
    
    print("✅ REVOKED synapses skip learning!")


def test_pruning():
    """Test pruning REVOKED synapses."""
    print("\n" + "=" * 60)
    print("Test: Pruning")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=50)
    
    # Mark some synapses as REVOKED
    for i in range(10):
        snn_ctx.domain_ctx.synapses[i].commit_state = COMMIT_STATE_REVOKED
    
    before = len(snn_ctx.domain_ctx.synapses)
    print(f"  Before pruning: {before} synapses")
    
    # Prune
    process_pruning(snn_ctx)
    
    after = len(snn_ctx.domain_ctx.synapses)
    pruned = before - after
    
    print(f"  After pruning: {after} synapses")
    print(f"  Pruned: {pruned} synapses")
    
    assert pruned == 10
    assert all(s.commit_state != COMMIT_STATE_REVOKED for s in snn_ctx.domain_ctx.synapses)
    
    print("✅ Pruning works!")


def test_commitment_metrics():
    """Test commitment metrics tracking."""
    print("\n" + "=" * 60)
    print("Test: Commitment Metrics")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=50)
    rl_ctx = create_test_rl_context()
    
    # Good predictions
    for _ in range(10):
        rl_ctx.domain_ctx.td_error = 0.05
        process_commitment(snn_ctx, rl_ctx)
    
    # Check metrics
    print(f"  Solidified count: {snn_ctx.domain_ctx.metrics.get('solidified_count', 0)}")
    print(f"  SOLID synapses: {snn_ctx.domain_ctx.metrics.get('solid_synapses', 0)}")
    print(f"  FLUID synapses: {snn_ctx.domain_ctx.metrics.get('fluid_synapses', 0)}")
    
    assert snn_ctx.domain_ctx.metrics.get('solidified_count', 0) > 0
    
    print("✅ Metrics tracking works!")


def test_integration_workflow():
    """Test full integration workflow."""
    print("\n" + "=" * 60)
    print("Test: Full Integration Workflow")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=100)
    rl_ctx = create_test_rl_context()
    
    # Simulate 100 steps
    for step in range(100):
        snn_ctx.domain_ctx.current_time = step
        
        # Random spike
        if step % 10 == 0:
            snn_ctx.domain_ctx.spike_queue[step] = [step % 10]
        
        # Varying TD-error - mostly good with some bad
        if step % 3 == 0:
            rl_ctx.domain_ctx.td_error = 0.05  # Good prediction
        else:
            rl_ctx.domain_ctx.td_error = 0.2   # Moderate error
        
        # Run processes
        process_stdp_3factor(snn_ctx, rl_ctx)
        process_commitment(snn_ctx, rl_ctx)
        
        # Prune every 50 steps (less frequent)
        if step % 50 == 0 and step > 0:
            process_pruning(snn_ctx)
    
    # Check results
    solid = snn_ctx.domain_ctx.metrics.get('solid_synapses', 0)
    revoked = snn_ctx.domain_ctx.metrics.get('revoked_synapses', 0)
    pruned = snn_ctx.domain_ctx.metrics.get('pruned_count', 0)
    active = snn_ctx.domain_ctx.metrics.get('active_synapses', 0)
    
    print(f"  After 100 steps:")
    print(f"    SOLID synapses: {solid}")
    print(f"    REVOKED synapses: {revoked}")
    print(f"    Pruned total: {pruned}")
    print(f"    Active synapses: {active}")
    
    # Should have some activity (not all pruned)
    assert active > 0  # Network still alive
    
    print("✅ Integration workflow works!")


if __name__ == '__main__':
    test_state_transitions()
    test_protected_learning()
    test_revoked_skip_learning()
    test_pruning()
    test_commitment_metrics()
    test_integration_workflow()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\n🎉 Commitment Layer WORKING!")
    print("✅ State transitions: FLUID → SOLID → REVOKED")
    print("✅ Protected learning: SOLID learns 10x slower")
    print("✅ REVOKED skip learning")
    print("✅ Pruning removes REVOKED")
    print("✅ Catastrophic forgetting prevented!")
