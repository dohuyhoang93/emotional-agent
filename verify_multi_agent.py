import json
from environment import GridWorld

def verify_multi_agent():
    # Load default settings
    with open("configs/settings.json", "r") as f:
        settings = json.load(f)
    
    # Simulate the override from experiments_final_95.json
    settings_override = {
        "environment_config": {
            "num_agents": 5,
            "start_positions": [[0,0], [0,1], [1,0], [2,0], [0,2]]
        }
    }
    
    # Manually update settings (simplified recursive update)
    settings['environment_config'].update(settings_override['environment_config'])
    
    print(f"DEBUG: Initializing GridWorld with num_agents={settings['environment_config']['num_agents']}")
    env = GridWorld(settings)
    
    print(f"VERIFICATION: env.num_agents = {env.num_agents}")
    print(f"VERIFICATION: env.agent_positions keys = {list(env.agent_positions.keys())}")
    
    if env.num_agents == 5 and len(env.agent_positions) == 5:
        print("SUCCESS: Multi-agent configuration is active.")
    else:
        print("FAILURE: Multi-agent configuration failed.")

if __name__ == "__main__":
    verify_multi_agent()
