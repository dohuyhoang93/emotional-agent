import numpy as np
import time
import os
import sys

# Ensure project root is in path
if os.getcwd() not in sys.path:
    # Prioritize local theus_framework
    sys.path.insert(0, os.path.join(os.getcwd(), 'theus_framework'))
    sys.path.insert(1, os.getcwd())

import theus
print(f"DEBUG: Loaded theus from {theus.__file__}")

from src.coordination.multi_agent_coordinator import MultiAgentCoordinator
from src.core.context import GlobalContext
from src.core.snn_context_theus import SNNGlobalContext
from environment import GridWorld
from src.adapters.environment_adapter import EnvironmentAdapter

def verify_fixes():
    print("🚀 Starting RL Anomalies Verification...")
    
    # 1. Setup
    global_ctx = GlobalContext()
    global_ctx.max_steps = 20
    global_ctx.start_positions = [[0, 0]]
    global_ctx.initial_exploration_rate = 0.0 # Force exploitation or fixed seed
    
    snn_global_ctx = SNNGlobalContext()
    snn_global_ctx.num_neurons = 100
    snn_global_ctx.ticks_per_step = 10 # Our new parameter
    
    coordinator = MultiAgentCoordinator(1, global_ctx, snn_global_ctx)
    
    env_settings = {
        "environment_config": {
            "grid_size": 5,
            "num_agents": 1,
            "start_positions": [[0, 0]],
            "goal_pos": [4, 4],
            "max_steps_per_episode": 20
        }
    }
    env = GridWorld(env_settings)
    adapter = EnvironmentAdapter(env)
    
    # 2. Run Episode and Measure Time
    print("\n--- Running Episode (20 steps max) ---")
    start_time = time.time()
    metrics = coordinator.run_episode(env, adapter)
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"Episode Duration: {duration:.4f}s")
    print(f"Metrics: {metrics}")
    
    # 3. Verify Diagonal Actions
    print("\n--- Verifying Diagonal Actions ---")
    agent = coordinator.agents[0]
    env.reset()
    agent.reset(env.get_observation(0))
    
    # Action 4 is 'up-left' in coordinator (mapped to string)
    # Move to (1,1) first then try 'up-left' (4)
    env.agent_positions[0] = [1, 1]
    action_str = coordinator._action_to_string(4)
    print(f"Action 4 maps to: '{action_str}'")
    reward = env.perform_action(0, action_str)
    new_pos = tuple(env.agent_positions[0])
    print(f"Action 4 result: Pos={new_pos}, Reward={reward}")
    assert new_pos == (0, 0), f"Diagonal move 'up-left' failed! Expected (0,0), got {new_pos}"
    
    # Action 7 is 'down-right'
    env.agent_positions[0] = [1, 1]
    action_str = coordinator._action_to_string(7)
    print(f"Action 7 maps to: '{action_str}'")
    reward = env.perform_action(0, action_str)
    new_pos = tuple(env.agent_positions[0])
    print(f"Action 7 result: Pos={new_pos}, Reward={reward}")
    assert new_pos == (2, 2), f"Diagonal move 'down-right' failed! Expected (2,2), got {new_pos}"

    # 4. Verify SNN Ticks
    print("\n--- Verifying SNN Ticks per Step ---")
    env.reset()
    agent.reset(env.get_observation(0))
    # current_time should start at 0
    assert agent.snn_ctx.domain_ctx.current_time == 0
    
    print(f"DEBUG: Agent Domain Context type: {type(agent.rl_ctx.domain_ctx)}")
    print(f"DEBUG: Agent SNN Context present: {agent.rl_ctx.domain_ctx.snn_context is not None}")
    
    print("Executing 1 agent step...")
    agent.step(adapter)
    
    snn_time = agent.snn_ctx.domain_ctx.current_time
    print(f"SNN Time after 1 agent step: {snn_time} ticks")
    assert snn_time == 10, f"Expected 10 ticks (ticks_per_step=10), got {snn_time}"

    print("\n✅ All Verifications PASSED!")

if __name__ == "__main__":
    try:
        verify_fixes()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Verification FAILED: {e}")
        sys.exit(1)
