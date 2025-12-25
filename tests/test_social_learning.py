"""
Test Social Learning
=====================
Test social learning manager.
"""
import sys
sys.path.append('.')

from src.coordination.multi_agent_coordinator import MultiAgentCoordinator
from src.coordination.social_learning import SocialLearningManager
from src.core.context import GlobalContext
from src.core.snn_context_theus import SNNGlobalContext
from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld


def test_social_learning():
    """Test social learning."""
    print("=" * 60)
    print("Test: Social Learning")
    print("=" * 60)
    
    # Setup
    global_ctx = GlobalContext(
        initial_needs=[0.5, 0.5],
        initial_emotions=[0.0, 0.0],
        total_episodes=1,
        max_steps=10,
        seed=42,
        switch_locations={},
        initial_exploration_rate=1.0
    )
    
    snn_global_ctx = SNNGlobalContext(
        num_neurons=30,
        vector_dim=16,
        connectivity=0.15,
        seed=42
    )
    
    # Create coordinator with 5 agents
    coordinator = MultiAgentCoordinator(
        num_agents=5,
        global_ctx=global_ctx,
        snn_global_ctx=snn_global_ctx
    )
    
    # Create social learning manager
    social_learning = SocialLearningManager(
        coordinator=coordinator,
        elite_ratio=0.2,
        learner_ratio=0.5,
        synapses_per_transfer=5
    )
    
    print(f"  ✅ Created social learning manager")
    print(f"  ✅ Elite ratio: {social_learning.elite_ratio}")
    print(f"  ✅ Learner ratio: {social_learning.learner_ratio}")
    
    # Create environment
    settings = {
        "initial_needs": [0.5, 0.5],
        "initial_emotions": [0.0, 0.0],
        "switch_locations": {},
        "environment_config": {
            "grid_size": 5,
            "max_steps_per_episode": 10,
            "num_agents": 5,
            "start_positions": [[0, i] for i in range(5)]
        }
    }
    env = GridWorld(settings)
    adapter = EnvironmentAdapter(env)
    
    # Run one episode
    print("\n  Running episode...")
    coordinator.run_episode(env, adapter)
    
    # Get initial synapse counts
    initial_counts = [
        len(agent.snn_ctx.domain_ctx.synapses)
        for agent in coordinator.agents
    ]
    print(f"  ✅ Initial synapse counts: {initial_counts}")
    
    # Perform social learning
    print("\n  Performing social learning...")
    social_learning.perform_social_learning()
    
    # Get final synapse counts
    final_counts = [
        len(agent.snn_ctx.domain_ctx.synapses)
        for agent in coordinator.agents
    ]
    print(f"  ✅ Final synapse counts: {final_counts}")
    
    # Check transfer stats
    stats = social_learning.get_transfer_stats()
    print(f"\n  ✅ Transfer stats:")
    print(f"     Total transfers: {stats['total_transfers']}")
    print(f"     Total synapses: {stats['total_synapses']}")
    print(f"     Avg per transfer: {stats['avg_synapses_per_transfer']:.2f}")
    
    # Validate synapses were transferred
    assert stats['total_transfers'] > 0, "No transfers occurred"
    assert stats['total_synapses'] > 0, "No synapses transferred"
    
    print("\n✅ Social learning works!")


if __name__ == '__main__':
    test_social_learning()
    
    print("\n" + "=" * 60)
    print("✅ SOCIAL LEARNING TESTS COMPLETE!")
    print("=" * 60)
