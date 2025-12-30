"""
Test Revolution Protocol (Process Based)
========================================
Test revolution protocol process (Pure POP).
"""
import sys
import numpy as np

sys.path.append('.')

from src.core.snn_context_theus import SNNGlobalContext, SNNSystemContext, SNNDomainContext, SynapseState
from src.processes.snn_advanced_features_theus import process_revolution_protocol

def test_revolution_process_logic():
    print("=" * 60)
    print("Test: Revolution Protocol (Process)")
    print("=" * 60)
    
    # 1. Setup Contexts
    snn_global_config = SNNGlobalContext(
        num_neurons=10,
        connectivity=1.0,
        revolution_threshold=0.5, # 50% outperform
        revolution_window=5,
        top_elite_percent=0.5
    )
    
    # Create 2 agents sharing GLOBAL context
    # Direct instantiation to ensure sharing
    domain0 = SNNDomainContext(agent_id=0)
    agent0_ctx = SNNSystemContext(global_ctx=snn_global_config, domain_ctx=domain0)
    
    domain1 = SNNDomainContext(agent_id=1)
    agent1_ctx = SNNSystemContext(global_ctx=snn_global_config, domain_ctx=domain1)
    
    population_contexts = [agent0_ctx, agent1_ctx]
    
    # Setup Synapses with Weights
    # Agent 0: High weights (Elite)
    # Agent 1: Low weights
    for i in range(5):
        agent0_ctx.domain_ctx.synapses.append(SynapseState(synapse_id=i, pre_neuron_id=0, post_neuron_id=1, weight=0.9))
        agent1_ctx.domain_ctx.synapses.append(SynapseState(synapse_id=i, pre_neuron_id=0, post_neuron_id=1, weight=0.1))

    # Pre-populate ancestor weights so process doesn't exit early (Initialization Phase)
    agent0_ctx.domain_ctx.ancestor_weights = {0: 0.5, 1: 0.5}

    # 2. Setup History (In Lead Agent 0)
    # Baseline is 10.0
    agent0_ctx.domain_ctx.ancestor_baseline_reward = 10.0
    
    # Add performance history: 4 entries > 10.0 (High), 1 entry < 10.0
    # Ratio = 4/5 = 0.8 > 0.5 (Threshold) -> TRIGGER
    history = [12.0, 15.0, 11.0, 9.0, 13.0]
    agent0_ctx.domain_ctx.population_performance = history
    
    # Mock Population Performance for Voting (Agent 0 is elite)
    # The process reads population_performance from EACH context for voting
    agent0_ctx.domain_ctx.population_performance = history # Agent 0 Avg = 12.0
    agent1_ctx.domain_ctx.population_performance = [5.0]*5 # Agent 1 Avg = 5.0
    
    # 3. Run Process
    print("  Running process_revolution_protocol...")
    process_revolution_protocol(agent0_ctx, None, population_contexts)
    
    # 4. Verify Trigger
    triggered = getattr(agent0_ctx.domain_ctx, 'revolution_triggered', False)
    print(f"  Revolution Triggered: {triggered}")
    assert triggered == True, "Revolution should fulfill condition"
    
    # 5. Verify Ancestor Update
    ancestor = agent0_ctx.domain_ctx.ancestor_weights
    print(f"  Ancestor Weights Keys: {list(ancestor.keys())}")
    assert ancestor is not None, "Ancestor weights shoud be generated"
    assert len(ancestor) > 0
    # Should reflect Elite (Agent 0) weights ~0.9
    avg_weight = np.mean(list(ancestor.values()))
    print(f"  Ancestor Avg Weight: {avg_weight}")
    assert avg_weight > 0.8, "Ancestor should be based on Elite (Agent 0)"
    
    # 6. Verify Reset
    assert len(agent0_ctx.domain_ctx.population_performance) == 0, "History should be cleared"
    assert agent0_ctx.domain_ctx.ancestor_baseline_reward > 10.0, "Baseline should increase (to elite avg)"
    
    print("\n✅ Revolution Process Logic verified!")

if __name__ == '__main__':
    test_revolution_process_logic()
