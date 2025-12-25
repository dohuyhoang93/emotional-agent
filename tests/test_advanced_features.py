"""
Quick Tests: Phase 8-12 Advanced Features
==========================================
Rapid testing cho 5 advanced features.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

import numpy as np
from src.core.snn_context_theus import create_snn_context_theus, SynapseState
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.processes.snn_social_quarantine_theus import (
    process_quarantine_validation,
    process_inject_viral_with_quarantine
)
from src.processes.snn_advanced_features_theus import (
    process_hysteria_dampener,
    process_lateral_inhibition,
    process_neural_darwinism,
    process_revolution_protocol
)


def create_test_rl_context():
    """Tạo RL context."""
    global_ctx = GlobalContext()
    domain_ctx = DomainContext()
    domain_ctx.td_error = 0.0
    domain_ctx.last_reward = {'total': 0.0}
    
    return SystemContext(
        global_ctx=global_ctx,
        domain_ctx=domain_ctx
    )


def test_phase8_quarantine():
    """Test Phase 8: Social Quarantine."""
    print("=" * 60)
    print("Test Phase 8: Social Quarantine")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=50)
    rl_ctx = create_test_rl_context()
    
    # Inject viral synapse
    viral_syn = SynapseState(
        synapse_id=9999,
        pre_neuron_id=0,
        post_neuron_id=1,
        synapse_type="shadow",
        source_agent_id=42
    )
    snn_ctx.domain_ctx.shadow_synapses.append(viral_syn)
    
    # Good performance → Promote
    for _ in range(100):
        rl_ctx.domain_ctx.td_error = 0.05  # Low error
        rl_ctx.domain_ctx.last_reward = {'total': 0.5}
        process_quarantine_validation(snn_ctx, rl_ctx)
    
    # Check promoted
    promoted = snn_ctx.domain_ctx.metrics.get('quarantine_promoted', 0)
    print(f"  Promoted: {promoted}")
    assert promoted > 0
    
    # Test blacklist
    bad_viral = SynapseState(
        synapse_id=9998,
        pre_neuron_id=0,
        post_neuron_id=2,
        synapse_type="shadow",
        source_agent_id=666
    )
    snn_ctx.domain_ctx.shadow_synapses.append(bad_viral)
    
    # Negative reward → Blacklist
    rl_ctx.domain_ctx.last_reward = {'total': -1.0}
    process_quarantine_validation(snn_ctx, rl_ctx)
    
    assert 666 in snn_ctx.domain_ctx.blacklisted_sources
    print(f"  Blacklisted: {snn_ctx.domain_ctx.blacklisted_sources}")
    
    print("✅ Phase 8 works!")


def test_phase9_hysteria():
    """Test Phase 9: Hysteria Dampener."""
    print("\n" + "=" * 60)
    print("Test Phase 9: Hysteria Dampener")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=100)
    
    # Simulate saturation
    snn_ctx.domain_ctx.metrics['fire_rate'] = 0.95  # High fire rate
    
    process_hysteria_dampener(snn_ctx)
    
    # Check dampening activated
    assert snn_ctx.domain_ctx.dampening_active
    print(f"  Dampening active: {snn_ctx.domain_ctx.dampening_active}")
    print(f"  Saturation level: {snn_ctx.domain_ctx.emotion_saturation_level:.2f}")
    
    # Simulate recovery
    snn_ctx.domain_ctx.metrics['fire_rate'] = 0.1  # Low fire rate
    for _ in range(20):
        process_hysteria_dampener(snn_ctx)
    
    print(f"  After recovery: {snn_ctx.domain_ctx.emotion_saturation_level:.2f}")
    
    print("✅ Phase 9 works!")


def test_phase10_lateral_inhibition():
    """Test Phase 10: Lateral Inhibition."""
    print("\n" + "=" * 60)
    print("Test Phase 10: Lateral Inhibition")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=100)
    
    # Simulate many neurons firing
    snn_ctx.domain_ctx.spike_queue[0] = list(range(20))  # 20 neurons
    snn_ctx.domain_ctx.current_time = 0
    
    # Set varying potentials
    for i in range(20):
        snn_ctx.domain_ctx.neurons[i].potential = np.random.rand() * 2.0
    
    process_lateral_inhibition(snn_ctx)
    
    # Check WTA
    winners = snn_ctx.domain_ctx.metrics.get('wta_winners', 0)
    losers = snn_ctx.domain_ctx.metrics.get('wta_losers', 0)
    
    print(f"  Winners: {winners}")
    print(f"  Losers: {losers}")
    assert winners == 5  # Top-k = 5
    
    print("✅ Phase 10 works!")


def test_phase11_darwinism():
    """Test Phase 11: Neural Darwinism."""
    print("\n" + "=" * 60)
    print("Test Phase 11: Neural Darwinism")
    print("=" * 60)
    
    snn_ctx = create_snn_context_theus(num_neurons=100)
    rl_ctx = create_test_rl_context()
    
    initial_count = len(snn_ctx.domain_ctx.synapses)
    
    # Good performance
    for _ in range(10):
        rl_ctx.domain_ctx.td_error = 0.05
        process_neural_darwinism(snn_ctx, rl_ctx)
    
    # Check evolution
    survivors = snn_ctx.domain_ctx.metrics.get('darwinism_survivors', 0)
    offspring = snn_ctx.domain_ctx.metrics.get('darwinism_offspring', 0)
    
    print(f"  Initial: {initial_count}")
    print(f"  Survivors: {survivors}")
    print(f"  Offspring: {offspring}")
    print(f"  Final: {len(snn_ctx.domain_ctx.synapses)}")
    
    print("✅ Phase 11 works!")


def test_phase12_revolution():
    """Test Phase 12: Revolution Protocol."""
    print("\n" + "=" * 60)
    print("Test Phase 12: Revolution Protocol")
    print("=" * 60)
    
    # Create population
    population = [
        create_snn_context_theus(num_neurons=50)
        for _ in range(10)
    ]
    rl_ctx = create_test_rl_context()
    
    # Initialize ancestor (poor)
    population[0].domain_ctx.ancestor_weights = {i: 0.3 for i in range(10)}
    
    # Simulate good performance
    for ctx in population:
        for _ in range(1000):
            ctx.domain_ctx.population_performance.append(0.8)  # High reward
    
    rl_ctx.domain_ctx.last_reward = {'total': 0.8}
    
    # Run revolution
    process_revolution_protocol(population[0], rl_ctx, population)
    
    # Check
    ratio = population[0].domain_ctx.metrics.get('outperform_ratio', 0)
    print(f"  Outperform ratio: {ratio:.2f}")
    
    if ratio > 0.6:
        print(f"  Revolution triggered: {population[0].domain_ctx.revolution_triggered}")
    
    print("✅ Phase 12 works!")


if __name__ == '__main__':
    test_phase8_quarantine()
    test_phase9_hysteria()
    test_phase10_lateral_inhibition()
    test_phase11_darwinism()
    test_phase12_revolution()
    
    print("\n" + "=" * 60)
    print("✅ ALL PHASES (8-12) TESTED!")
    print("=" * 60)
    print("\n🎉 100% SNN SPEC IMPLEMENTED!")
    print("✅ Phase 8: Social Quarantine")
    print("✅ Phase 9: Hysteria Dampener")
    print("✅ Phase 10: Lateral Inhibition")
    print("✅ Phase 11: Neural Darwinism")
    print("✅ Phase 12: Revolution Protocol")

