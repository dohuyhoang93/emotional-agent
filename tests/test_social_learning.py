"""
Test Social Learning (Process Based)
=====================================
Test social learning process (Pure POP).
"""
import sys

sys.path.append('.')

from src.core.snn_context_theus import SNNGlobalContext, SNNSystemContext, SNNDomainContext, SynapseState
from src.processes.snn_social_learning_theus import process_social_learning_protocol

def test_social_learning_process_logic():
    print("=" * 60)
    print("Test: Social Learning Process")
    print("=" * 60)
    
    # 1. Setup Contexts
    snn_global_config = SNNGlobalContext(
        num_neurons=10,
        connectivity=1.0,
        seed=42
    )
    # Set params (which are usually in Global but can be overridden)
    # For now relying on default getattrs in process if not present
    # Or inject them manually into global context helper wrapper
    # The process reads global_snn_ctx.global_ctx
    snn_global_config.social_elite_ratio = 0.5 
    snn_global_config.social_learner_ratio = 0.5 
    snn_global_config.social_synapses_per_transfer = 2
    
    # Create 2 agents
    domain0 = SNNDomainContext(agent_id=0) # Elite
    agent0_ctx = SNNSystemContext(global_ctx=snn_global_config, domain_ctx=domain0)
    
    domain1 = SNNDomainContext(agent_id=1) # Learner
    agent1_ctx = SNNSystemContext(global_ctx=snn_global_config, domain_ctx=domain1)
    
    population_contexts = [agent0_ctx, agent1_ctx]
    
    # Setup Synapses
    # Agent 0 (Elite): High weights
    for i in range(5):
        s = SynapseState(synapse_id=i, pre_neuron_id=0, post_neuron_id=1, weight=0.9)
        domain0.synapses.append(s)
        
    # Agent 1 (Learner): Empty or different
    # Let's give it some random synapses
    s = SynapseState(synapse_id=100, pre_neuron_id=1, post_neuron_id=2, weight=0.1)
    domain1.synapses.append(s)
    
    print(f"  Agent 0 Synapses: {len(domain0.synapses)}")
    print(f"  Agent 1 Synapses: {len(domain1.synapses)}")
    
    # 2. Setup Rankings
    # Agent 0: Reward 100
    # Agent 1: Reward 0
    rankings = [(0, 100.0), (1, 0.0)]
    
    # 3. Run Process
    print("  Running process_social_learning_protocol...")
    # Using Agent 0 as the 'Global/Leader' context
    process_social_learning_protocol(agent0_ctx, population_contexts, rankings)
    
    # 4. Verify Injection
    # Agent 1 should have received top 2 synapses from Agent 0
    # Total synapses for Agent 1 = 1 (old) + 2 (injected) = 3
    final_count = len(domain1.synapses)
    print(f"  Agent 1 Final Synapses: {final_count}")
    
    assert final_count == 3, f"Agent 1 should have 3 synapses, got {final_count}"
    
    # Check injected properties
    # Validating that new synapses are copies of Agent 0's high weight syns
    new_syns = [s for s in domain1.synapses if s.synapse_id not in [100]] # Filter out original
    assert len(new_syns) == 2
    for s in new_syns:
        assert s.weight == 0.9, "Injected synapse should have weight 0.9"
        # IDs were remapped? Yes, logic re-IDs them.
        print(f"  Injected Synapse ID: {s.synapse_id} Weight: {s.weight}")

    # Check Metrics
    injected_metric = domain1.metrics.get('social_learning_injected', 0)
    print(f"  Metric 'social_learning_injected': {injected_metric}")
    assert injected_metric == 2
    
    print("\n✅ Social Learning Process Logic verified!")

if __name__ == '__main__':
    test_social_learning_process_logic()
