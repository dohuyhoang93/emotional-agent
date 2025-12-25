"""
Minimal E2E Test
=================
Test tối giản để validate Phase 1.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

from src.agents.rl_agent import RLAgent
from src.core.context import GlobalContext
from src.core.snn_context_theus import SNNGlobalContext
from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld


def main():
    print("=" * 60)
    print("Minimal E2E Test - Phase 1")
    print("=" * 60)
    
    # Setup
    global_ctx = GlobalContext(
        initial_needs=[0.5, 0.5],
        initial_emotions=[0.0, 0.0],
        total_episodes=1,
        max_steps=5,
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
    
    # Create agent
    print("\n1. Creating agent...")
    agent = RLAgent(
        agent_id=0,
        global_ctx=global_ctx,
        snn_global_ctx=snn_global_ctx
    )
    print(f"   ✅ Agent created")
    
    # Create environment
    settings = {
        "initial_needs": [0.5, 0.5],
        "initial_emotions": [0.0, 0.0],
        "switch_locations": {},
        "environment_config": {
            "grid_size": 5,
            "max_steps_per_episode": 5,
            "num_agents": 1
        }
    }
    env = GridWorld(settings)
    adapter = EnvironmentAdapter(env)
    
    # Reset
    print("\n2. Resetting...")
    obs_dict = env.reset()
    agent.reset(obs_dict[0])
    print(f"   ✅ Position: {obs_dict[0]['agent_pos']}")
    
    # Try one step
    print("\n3. Running one step...")
    try:
        action = agent.step(adapter)
        print(f"   ✅ Action: {action}")
        print(f"   ✅ Step completed!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   (Expected if workflow incomplete)")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
