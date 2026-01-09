
import unittest
import sys
import os
import json

sys.path.append(os.getcwd())

from environment import GridWorld as ComplexMazeEnvV2

class TestEnvSanity(unittest.TestCase):
    def test_env_reset_step(self):
        print("\n--- Testing ComplexMazeEnvV2 Sanity ---")
        
        # Load config from experiments_sanity.json
        with open('experiments_sanity.json', 'r') as f:
            data = json.load(f)
            
        env_config = data['experiments'][0]['parameters']['environment_config']
        print(f"Config: {env_config}")
        
        env = ComplexMazeEnvV2(env_config)
        print("Env Initialized.")
        
        print("Resetting Env...")
        obs = env.reset()
        print("Env Reset Done.")
        print(f"Obs Type: {type(obs)}")
        
        print("Stepping...")
        actions = {0: 0, 1: 0} # No-op
        obs, rewards, done, info = env.step(actions)
        print("Step Done.")
        print(f"Rewards: {rewards}")

if __name__ == '__main__':
    unittest.main()
