import numpy as np
from environment import GridWorld

def test_bump_signal():
    print("🚀 Starting INC-003 Physics Verification Test...")
    
    # Setup a simple 5x5 grid with a wall at (1,1)
    settings = {
        "environment_config": {
            "grid_size": 5,
            "num_agents": 1,
            "start_positions": [[0, 0]],
            "walls": [[1, 1]],
            "max_steps_per_episode": 10
        }
    }
    
    env = GridWorld(settings)
    
    # 1. Test Initial State
    obs = env.get_observation(0)
    sensor = obs['sensor_vector']
    print(f"Initial Sensor Channel 12: {sensor[12]}")
    assert sensor[12] == 0.0, "Channel 12 should be 0 at start"
    assert sensor[14] == 1.0, "Channel 14 (Action Bit) should be 1.0"
    
    # 2. Move to (0,1) - Valid move
    env.perform_action(0, 'right') # pos (0,1)
    sensor = env.get_sensor_vector(0)
    print(f"After valid move - Channel 12: {sensor[12]}")
    assert sensor[12] == 0.0, "No bump expected on valid move"
    
    # 3. Move to (1,1) - This is a WALL
    reward = env.perform_action(0, 'down') # attempt (1,1)
    sensor = env.get_sensor_vector(0)
    print(f"After hitting WALL - Reward: {reward}, Channel 12: {sensor[12]}")
    assert reward == -0.5, "Should get wall penalty"
    assert sensor[12] == 1.0, "Channel 12 SHOULD be 1.0 after a BUMP"
    
    # 4. Move to (0,0) - Back to valid space
    env.perform_action(0, 'left')
    sensor = env.get_sensor_vector(0)
    print(f"After returning to valid space - Channel 12: {sensor[12]}")
    assert sensor[12] == 0.0, "Bump signal should clear after valid move"
    
    print("✅ INC-003 Physics Verification SUCCESS!")

if __name__ == "__main__":
    try:
        test_bump_signal()
    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        exit(1)
