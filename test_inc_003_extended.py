import numpy as np
import time
from environment import GridWorld

def test_extended_signals():
    print("🚀 Starting INC-003 Extended Physics Verification Test...")
    
    # Setup grid with static wall at (1,1) and dynamic wall at (0,2)
    settings = {
        "environment_config": {
            "grid_size": 5,
            "num_agents": 1,
            "start_positions": [[0, 0]],
            "walls": [[1, 1]],
            "dynamic_walls": [
                {"id": "gate1", "pos": [[0, 2]]}
            ],
            "dynamic_wall_rules": [
              {"id": "gate1", "type": "toggle", "inputs": ["switch1"]}
            ],
            "logical_switches": [
                {"id": "switch1", "pos": [4, 0]}
            ],
            "max_steps_per_episode": 10
        }
    }
    
    env = GridWorld(settings)
    
    # 1. Test Initial State & Action Bit (14) & Urgency (15)
    obs = env.get_observation(0)
    sensor = obs['sensor_vector']
    print(f"Initial - Ch 12 (Static): {sensor[12]}, Ch 13 (Dynamic): {sensor[13]}, Ch 14 (Action): {sensor[14]}, Ch 15 (Urgency): {sensor[15]:.2f}")
    assert sensor[12] == 0.0
    assert sensor[13] == 0.0
    assert sensor[14] == 1.0
    assert sensor[15] == 0.0 # Step 0/10
    
    # 2. Test Static Bump (12)
    env.perform_action(0, 'down') # pos (1,0) - valid
    env.perform_action(0, 'right') # attempt (1,1) - WALL
    sensor = env.get_sensor_vector(0)
    print(f"Hit STATIC Wall - Ch 12: {sensor[12]}, Ch 13: {sensor[13]}")
    assert sensor[12] == 1.0, "Should detect STATIC bump"
    assert sensor[13] == 0.0, "Should NOT detect dynamic bump"
    
    # 3. Test Dynamic Bump (13)
    # Current pos: (1,0)
    env.perform_action(0, 'up')    # back to (0,0)
    env.perform_action(0, 'right') # to (0,1)
    env.perform_action(0, 'right') # attempt (0,2) - GATE
    sensor = env.get_sensor_vector(0)
    print(f"Hit DYNAMIC Gate - Ch 12: {sensor[12]}, Ch 13: {sensor[13]}")
    assert sensor[12] == 0.0, "Should NOT detect static bump"
    assert sensor[13] == 1.0, "Should detect DYNAMIC bump"
    
    # 4. Test Urgency Ramping (15)
    print(f"Current step: {env.current_step}")
    # Perform some actions to increase steps
    for _ in range(5):
        env.new_step()
        env.current_step += 1
        env.perform_action(0, 'wait') # invalid action but increments logic if added, or just use valid move
        
    sensor = env.get_sensor_vector(0)
    expected_urgency = env.current_step / env.max_steps
    print(f"After {env.current_step} steps - Ch 15 (Urgency): {sensor[15]:.2f} (Expected: {expected_urgency:.2f})")
    assert sensor[15] == expected_urgency, "Urgency signal should map to step progress"
    
    print("✅ INC-003 Extended Physics Verification SUCCESS!")

if __name__ == "__main__":
    try:
        test_extended_signals()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Test FAILED: {e}")
        exit(1)
