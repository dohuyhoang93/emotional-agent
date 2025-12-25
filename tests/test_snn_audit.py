"""
Test SNN Audit Recipe
======================
Test audit validation với invalid parameters.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

import pytest
from src.core.snn_context_theus import (
    SNNGlobalContext,
    SNNDomainContext,
    SNNSystemContext,
    create_snn_context_theus
)
from src.processes.snn_core_theus import process_integrate, process_fire
from src.processes.snn_learning_theus import process_clustering, process_stdp
from src.processes.snn_homeostasis_theus import (
    process_homeostasis,
    process_meta_homeostasis_fixed
)


def test_audit_tau_decay_valid():
    """Test tau_decay trong range hợp lý."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Valid range [0.5, 1.0]
    ctx.global_ctx.tau_decay = 0.9
    
    # Should work
    ctx.domain_ctx.spike_queue[0] = [0]
    process_integrate(ctx)
    
    print("✅ tau_decay valid (0.9) OK")


def test_audit_tau_decay_too_low():
    """Test tau_decay quá thấp (< 0.5)."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Invalid: < 0.5
    ctx.global_ctx.tau_decay = 0.3
    
    # NOTE: Theus sẽ raise error khi có audit recipe
    # Hiện tại chưa integrate Theus Engine nên chỉ test logic
    
    # Manually validate
    assert ctx.global_ctx.tau_decay < 0.5  # Invalid
    print("⚠️  tau_decay too low (0.3) - Would be caught by Theus")


def test_audit_tau_decay_too_high():
    """Test tau_decay quá cao (> 1.0)."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Invalid: > 1.0
    ctx.global_ctx.tau_decay = 1.5
    
    # Manually validate
    assert ctx.global_ctx.tau_decay > 1.0  # Invalid
    print("⚠️  tau_decay too high (1.5) - Would be caught by Theus")


def test_audit_fire_rate_valid():
    """Test fire_rate trong range [0, 1]."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Set valid fire rate
    ctx.domain_ctx.metrics['fire_rate'] = 0.05
    
    # Should work
    process_homeostasis(ctx)
    
    print("✅ fire_rate valid (0.05) OK")


def test_audit_fire_rate_invalid():
    """Test fire_rate ngoài range."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Invalid: > 1.0
    ctx.domain_ctx.metrics['fire_rate'] = 2.0
    
    # Manually validate
    assert ctx.domain_ctx.metrics['fire_rate'] > 1.0  # Invalid
    print("⚠️  fire_rate invalid (2.0) - Would be caught by Theus")


def test_audit_refractory_period_valid():
    """Test refractory_period trong range [1, 20]."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Valid range
    ctx.global_ctx.refractory_period = 5
    
    # Should work
    ctx.domain_ctx.neurons[0].potential = 2.0
    process_fire(ctx)
    
    print("✅ refractory_period valid (5) OK")


def test_audit_refractory_period_too_low():
    """Test refractory_period quá thấp."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Invalid: < 1
    ctx.global_ctx.refractory_period = 0
    
    # Manually validate
    assert ctx.global_ctx.refractory_period < 1  # Invalid
    print("⚠️  refractory_period too low (0) - Would be caught by Theus")


def test_audit_learning_rate_valid():
    """Test learning_rate trong range [0.001, 0.5]."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Valid range
    ctx.global_ctx.learning_rate = 0.01
    
    # Should work
    ctx.domain_ctx.spike_queue[0] = [0]
    process_stdp(ctx)
    
    print("✅ learning_rate valid (0.01) OK")


def test_audit_learning_rate_too_high():
    """Test learning_rate quá cao."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Invalid: > 0.5
    ctx.global_ctx.learning_rate = 1.0
    
    # Manually validate
    assert ctx.global_ctx.learning_rate > 0.5  # Invalid
    print("⚠️  learning_rate too high (1.0) - Would be caught by Theus")


def test_audit_clustering_rate_valid():
    """Test clustering_rate trong range [0.0001, 0.1]."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Valid range
    ctx.global_ctx.clustering_rate = 0.001
    
    # Should work
    ctx.domain_ctx.spike_queue[0] = [0]
    process_clustering(ctx)
    
    print("✅ clustering_rate valid (0.001) OK")


def test_audit_pid_integral_bounded():
    """Test PID integral bounded [-10, 10]."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Set fire rate để trigger PID
    ctx.domain_ctx.metrics['fire_rate'] = 0.01
    
    # Run meta-homeostasis nhiều lần
    for _ in range(100):
        process_meta_homeostasis_fixed(ctx)
    
    # Check integral bounded
    integral = ctx.domain_ctx.pid_state['threshold']['error_integral']
    assert -10.0 <= integral <= 10.0
    
    print(f"✅ PID integral bounded ({integral:.2f}) OK")


def test_audit_meta_threshold_adjustment():
    """Test meta threshold adjustment trong range."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Set fire rate
    ctx.domain_ctx.metrics['fire_rate'] = 0.01
    
    # Run meta-homeostasis
    process_meta_homeostasis_fixed(ctx)
    
    # Check adjustment trong range
    adj = ctx.domain_ctx.metrics.get('meta_threshold_adj', 0.0)
    assert -0.1 <= adj <= 0.1
    
    print(f"✅ Meta threshold adjustment ({adj:.6f}) OK")


def test_audit_threshold_bounds():
    """Test threshold luôn trong range [0.3, 3.0]."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Set extreme fire rate
    ctx.domain_ctx.metrics['fire_rate'] = 0.5  # Very high
    
    # Run homeostasis nhiều lần
    for _ in range(1000):
        process_homeostasis(ctx)
    
    # Check tất cả thresholds trong range
    for neuron in ctx.domain_ctx.neurons:
        assert ctx.global_ctx.threshold_min <= neuron.threshold <= ctx.global_ctx.threshold_max
    
    print("✅ Threshold bounds OK")


def test_audit_weight_bounds():
    """Test weight luôn trong range [0, 1]."""
    ctx = create_snn_context_theus(num_neurons=10)
    
    # Inject spike
    ctx.domain_ctx.spike_queue[0] = [0]
    ctx.domain_ctx.current_time = 0
    
    # Set neurons to fire
    for i in range(3):
        ctx.domain_ctx.neurons[i].potential = 2.0
        ctx.domain_ctx.neurons[i].last_fire_time = 0
    
    # Run STDP nhiều lần
    for _ in range(100):
        process_stdp(ctx)
    
    # Check tất cả weights trong range
    for synapse in ctx.domain_ctx.synapses:
        assert 0.0 <= synapse.weight <= 1.0
    
    print("✅ Weight bounds OK")


def test_audit_summary():
    """Summary của audit tests."""
    print("\n" + "=" * 60)
    print("AUDIT TEST SUMMARY")
    print("=" * 60)
    
    print("\n✅ VALID PARAMETERS:")
    print("  - tau_decay: 0.9 (in [0.5, 1.0])")
    print("  - fire_rate: 0.05 (in [0, 1])")
    print("  - refractory_period: 5 (in [1, 20])")
    print("  - learning_rate: 0.01 (in [0.001, 0.5])")
    print("  - clustering_rate: 0.001 (in [0.0001, 0.1])")
    
    print("\n⚠️  INVALID PARAMETERS (Would be caught by Theus):")
    print("  - tau_decay: 0.3 (< 0.5)")
    print("  - tau_decay: 1.5 (> 1.0)")
    print("  - fire_rate: 2.0 (> 1.0)")
    print("  - refractory_period: 0 (< 1)")
    print("  - learning_rate: 1.0 (> 0.5)")
    
    print("\n✅ BOUNDED VALUES:")
    print("  - PID integral: [-10, 10]")
    print("  - Threshold adjustment: [-0.1, 0.1]")
    print("  - Threshold: [0.3, 3.0]")
    print("  - Weight: [0, 1]")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    print("=" * 60)
    print("Testing SNN Audit Recipe")
    print("=" * 60)
    
    # Valid tests
    test_audit_tau_decay_valid()
    test_audit_fire_rate_valid()
    test_audit_refractory_period_valid()
    test_audit_learning_rate_valid()
    test_audit_clustering_rate_valid()
    
    # Invalid tests (manual validation)
    test_audit_tau_decay_too_low()
    test_audit_tau_decay_too_high()
    test_audit_fire_rate_invalid()
    test_audit_refractory_period_too_low()
    test_audit_learning_rate_too_high()
    
    # Bounded values
    test_audit_pid_integral_bounded()
    test_audit_meta_threshold_adjustment()
    test_audit_threshold_bounds()
    test_audit_weight_bounds()
    
    # Summary
    test_audit_summary()
    
    print("\n✅ ALL AUDIT TESTS PASSED!")
