"""
Test Revolution Protocol
=========================
Test revolution protocol manager.
"""
import sys
sys.path.append('.')

from src.coordination.multi_agent_coordinator import MultiAgentCoordinator
from src.coordination.revolution_protocol import RevolutionProtocolManager
from src.core.context import GlobalContext
from src.core.snn_context_theus import SNNGlobalContext
from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld


def test_revolution_protocol():
    """Test revolution protocol."""
    print("=" * 60)
    print("Test: Revolution Protocol")
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
    
    # Create revolution protocol manager
    # Set low threshold to trigger easily
    revolution = RevolutionProtocolManager(
        coordinator=coordinator,
        threshold=-1.0,  # Negative to force trigger
        window=2,
        elite_ratio=0.2
    )
    
    print(f"  ✅ Created revolution protocol manager")
    print(f"  ✅ Threshold: {revolution.threshold}")
    print(f"  ✅ Window: {revolution.window}")
    
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
    
    # Run multiple episodes
    print("\n  Running 3 episodes...")
    for i in range(3):
        coordinator.run_episode(env, adapter)
        print(f"    Episode {i+1} complete")
        
        # Check for revolution
        if revolution.check_and_execute_revolution():
            print(f"    🔥 REVOLUTION triggered!")
    
    # Get revolution stats
    stats = revolution.get_revolution_stats()
    print(f"\n  ✅ Revolution stats:")
    print(f"     Total revolutions: {stats['total_revolutions']}")
    if stats['last_revolution']:
        print(f"     Last revolution: Episode {stats['last_revolution']['episode']}")
        print(f"     Elite IDs: {stats['last_revolution']['elite_ids']}")
        print(f"     Num weights: {stats['last_revolution']['num_weights']}")
    
    # Validate revolution occurred
    assert stats['total_revolutions'] > 0, "No revolutions occurred"
    
    # Check ancestor was updated
    assert coordinator.ancestor_weights is not None, "Ancestor not updated"
    print(f"\n  ✅ Ancestor updated: {len(coordinator.ancestor_weights)} weights")
    
    print("\n✅ Revolution protocol works!")


if __name__ == '__main__':
    test_revolution_protocol()
    
    print("\n" + "=" * 60)
    print("✅ REVOLUTION PROTOCOL TESTS COMPLETE!")
    print("=" * 60)
