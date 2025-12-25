"""
Minimal Test - RLAgent với Orchestration
==========================================
Test để debug AttributeError trong encode_state_to_spikes.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

from src.agents.rl_agent import RLAgent
from src.core.context import GlobalContext
from src.core.snn_context_theus import SNNGlobalContext
from environment import GridWorld
from src.adapters.environment_adapter import EnvironmentAdapter

def main():
    print("=" * 70)
    print("MINIMAL RLAGENT TEST")
    print("=" * 70)
    
    # Create contexts
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
        num_neurons=50,
        vector_dim=16,
        connectivity=0.15,
        seed=42
    )
    
    # Create agent
    print("\n1. Creating RLAgent...")
    try:
        agent = RLAgent(
            agent_id=0,
            global_ctx=global_ctx,
            snn_global_ctx=snn_global_ctx
        )
        print("✅ Agent created")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Create environment
    print("\n2. Creating Environment...")
    env_config = {
        "initial_needs": [0.5, 0.5],
        "initial_emotions": [0.0, 0.0],
        "switch_locations": {},
        "environment_config": {
            "grid_size": 8,
            "max_steps_per_episode": 5,
            "num_agents": 1,
            "start_positions": [[0, 0]]
        }
    }
    env = GridWorld(env_config)
    adapter = EnvironmentAdapter(env)
    print("✅ Environment created")
    
    # Reset
    print("\n3. Resetting...")
    obs_dict = env.reset()
    agent.reset(obs_dict[0])
    print(f"✅ Reset complete. Observation: {obs_dict[0]}")
    
    # Take one step
    print("\n4. Taking one step...")
    try:
        action = agent.step(adapter)
        print(f"✅ Step complete. Action: {action}")
    except Exception as e:
        print(f"❌ Step failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
