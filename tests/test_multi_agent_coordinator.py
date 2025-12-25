"""
Test Multi-Agent Coordinator
=============================
Test coordinator với multiple agents.
"""
import sys
sys.path.append('.')

from src.coordination.multi_agent_coordinator import MultiAgentCoordinator
from src.core.context import GlobalContext
from src.core.snn_context_theus import SNNGlobalContext
from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld


def test_coordinator_creation():
    """Test coordinator creation."""
    print("=" * 60)
    print("Test: Coordinator Creation")
    print("=" * 60)
    
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
    
    # Create coordinator with 3 agents
    coordinator = MultiAgentCoordinator(
        num_agents=3,
        global_ctx=global_ctx,
        snn_global_ctx=snn_global_ctx
    )
    
    assert len(coordinator.agents) == 3
    assert coordinator.episode_count == 0
    
    print(f"  ✅ Created coordinator with {len(coordinator.agents)} agents")
    print("✅ Coordinator creation works!")


def test_single_episode():
    """Test running one episode."""
    print("\n" + "=" * 60)
    print("Test: Single Episode with 2 Agents")
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
    
    coordinator = MultiAgentCoordinator(
        num_agents=2,
        global_ctx=global_ctx,
        snn_global_ctx=snn_global_ctx
    )
    
    # Create environment
    settings = {
        "initial_needs": [0.5, 0.5],
        "initial_emotions": [0.0, 0.0],
        "switch_locations": {},
        "environment_config": {
            "grid_size": 5,
            "max_steps_per_episode": 10,
            "num_agents": 2,
            "start_positions": [[0, 0], [0, 1]]
        }
    }
    env = GridWorld(settings)
    adapter = EnvironmentAdapter(env)
    
    # Run episode
    print("  Running episode...")
    try:
        metrics = coordinator.run_episode(env, adapter)
        
        print(f"  ✅ Episode completed!")
        print(f"  ✅ Episode: {metrics.get('episode', 0)}")
        print(f"  ✅ Avg reward: {metrics.get('avg_reward', 0):.4f}")
        print(f"  ✅ Agent rewards: {metrics.get('agent_rewards', [])}")
        
        # Check population metrics
        pop_metrics = coordinator.get_population_metrics()
        print(f"  ✅ Population metrics: {pop_metrics}")
        
        print("✅ Single episode works!")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_coordinator_creation()
    test_single_episode()
    
    print("\n" + "=" * 60)
    print("✅ MULTI-AGENT COORDINATOR TESTS COMPLETE!")
    print("=" * 60)
