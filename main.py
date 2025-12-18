import json
import time
import torch
import random
import numpy as np
import pandas as pd
import argparse
import os
import yaml
from typing import List, Dict, Any

# POP Core Imports
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.core.engine import POPEngine
from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld
from src.models import EmotionCalculatorMLP
from src.logger import log, log_error

# Process Imports
from src.processes.p1_perception import perception
from src.processes.p2_belief_update import update_belief
from src.processes.p3_emotion_calc import calculate_emotions
from src.processes.p5_adjust_exploration import adjust_exploration
from src.processes.p6_action_select import select_action
from src.processes.p7_execution import execute_action
from src.processes.p8_consequence import record_consequences
from src.processes.p9_social_learning import social_learning

from theus.config import ConfigFactory

def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def main():
    parser = argparse.ArgumentParser(description="DeepSearch Agent - POP Architecture")
    parser.add_argument('--num-episodes', type=int, default=10, help='Number of episodes')
    parser.add_argument('--output-path', type=str, default='results/result.csv', help='Output CSV path')
    parser.add_argument('--settings-override', type=str, default='{}', help='JSON string for settings override')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--log-level', type=str, default='info', help='Log level')
    args = parser.parse_args()

    # Load Audit Recipe (V2)
    audit_recipe = None
    if os.path.exists("specs/audit_recipe.yaml"):
        try:
            audit_recipe = ConfigFactory.load_recipe("specs/audit_recipe.yaml")
            print("✅ Loaded Audit Recipe from specs/audit_recipe.yaml")
        except Exception as e:
            print(f"⚠️ Failed to load audit recipe: {e}")

    # 1. Load default config from generate_config.py structure (simulated loading defaults)
    # Ideally should load from a base json, but we use defaults + override.
    settings = {
        "initial_needs": [0.5, 0.5],
        "initial_emotions": [0.0, 0.0],
        "switch_locations": {},
        "environment_config": {
            "grid_size": 20,
            "max_steps_per_episode": 200,
            "num_agents": 2
        }
    }
    
    # Apply Overrides
    try:
        overrides = json.loads(args.settings_override)
        recursive_update(settings, overrides)
    except json.JSONDecodeError:
        print("Error parsing settings-override JSON.")

    # Set Global Seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    # 2. Initialize Environment
    # Note: Environment init requires some config overlap.
    # We pass the FULL settings to GridWorld as legacy support.
    env_config = settings.get('environment_config', {})
    if 'switch_locations' not in settings: # Generate or use default?
        pass # GridWorld handles it via logical_switches in env_config usually.
    
    # Sync settings -> environment config
    # In legacy config, switch_locations might be separate from environment_config
    # We trust 'settings' has what GridWorld needs.
    environment = GridWorld(settings)
    adapter = EnvironmentAdapter(environment)
    
    # 3. Hydrate Global Context (Shared by all agents technically, or per agent? Global is usually shared env constants)
    # But GlobalContext also contains `assimilation_rate` which is config.
    # We create ONE GlobalContext per agent to simplify if they have diff configs, 
    # but here allow sharing config.
    # Extract Switch Locations from Env if not in setting (Env might randomize them).
    # Use env.switches (dict pos->id). We need id->pos for context?
    # Context expects `switch_locations: Dict[str, Tuple[int, int]]`.
    switch_locs = {v: k for k, v in environment.switches.items()} # ID -> Pos
    
    common_global_ctx = GlobalContext(
        initial_needs=settings['initial_needs'],
        initial_emotions=settings['initial_emotions'],
        total_episodes=args.num_episodes,
        max_steps=environment.max_steps,
        seed=args.seed,
        switch_locations=switch_locs,
        log_level=args.log_level,
        
        # Hyperparams from settings
        assimilation_rate=settings.get('assimilation_rate', 0.1),
        initial_exploration_rate=float(settings.get('exploration_rate', 1.0)), # Initial Base
        use_dynamic_curiosity=settings.get('use_dynamic_curiosity', False),
        use_adaptive_fatigue=settings.get('use_adaptive_fatigue', False),
        fatigue_growth_rate=settings.get('fatigue_growth_rate', 0.001),
        intrinsic_reward_weight=settings.get('intrinsic_reward_weight', 0.1)
    )

    # 4. Initialize Agents (System Contexts)
    num_agents = environment.num_agents
    system_contexts = []
    engines = []

    for i in range(num_agents):
        # Domain Context (Mutable)
        n_dim = len(settings['initial_needs'])
        e_dim = len(settings['initial_emotions'])
        
        # Init Neural Model
        b_dim = 2 + len(switch_locs) # Pos(2) + Switches
        m_dim = 1
        model = EmotionCalculatorMLP(n_dim, b_dim, m_dim, e_dim)
        optimizer = torch.optim.Adam(model.parameters(), lr=settings.get('mlp_learning_rate', 0.01))
        
        domain_ctx = DomainContext(
            N_vector=torch.tensor(settings['initial_needs']),
            E_vector=torch.tensor(settings['initial_emotions']),
            believed_switch_states={slug: False for slug in switch_locs.keys()},
            q_table={},
            short_term_memory=[],
            long_term_memory={},
            
            emotion_model=model,
            emotion_optimizer=optimizer,
            
            base_exploration_rate=common_global_ctx.initial_exploration_rate,
            current_exploration_rate=common_global_ctx.initial_exploration_rate
        )
        
        # Pydantic requires kwargs for SystemContext!
        sys_ctx = SystemContext(global_ctx=common_global_ctx, domain_ctx=domain_ctx)
        
        # Init Engine with Audit Recipe (Dogfooding V2)
        engine = POPEngine(sys_ctx, audit_recipe=audit_recipe)
        
        # Register Processes
        engine.register_process("perception", perception)
        engine.register_process("update_belief", update_belief)
        engine.register_process("calculate_emotions", calculate_emotions)
        # engine.register_process("update_needs", ...) # Not migrated yet? Sticky Needs?
        engine.register_process("adjust_exploration", adjust_exploration)
        engine.register_process("select_action", select_action)
        engine.register_process("execute_action", execute_action)
        engine.register_process("record_consequences", record_consequences)
        engine.register_process("social_learning", social_learning)
        
        system_contexts.append(sys_ctx)
        engines.append(engine)

    # 5. Main Simulation Loop
    episode_data = []
    
    for episode in range(args.num_episodes):
        # Visual/Log
        # Visual/Log
        if not settings.get('visual_mode'):
            log(common_global_ctx, 'info', f"Starting Episode {episode+1}/{args.num_episodes}...")
            
        # Reset Environment & Agents
        obs_dict = environment.reset()
        is_successful = False
        
        for i, eng in enumerate(engines):
            # Reset Ephemeral
            dom = eng.get_domain()
            dom.current_episode = episode + 1
            dom.current_step = 0
            dom.current_observation = obs_dict[i]
            dom.previous_observation = None
            dom.last_reward = {'extrinsic': 0.0, 'intrinsic': 0.0}
            
            # Reset Needs/Emotions if config says so? (Usually keep Memory/Q/Model)
            pass

        episode_rewards = {i: 0.0 for i in range(num_agents)}
        steps_count = 0
        
        # Step Loop
        while not adapter.is_done() and steps_count < common_global_ctx.max_steps:
            steps_count += 1
            environment.current_step = steps_count # Sync for rendering
            
            # For logging cycle time
            import time
            
            # Run Agents
            for i, eng in enumerate(engines):
                 # Check success individually or globally?
                 pass
                 
                 start_t = time.time()
                 
                 # Prepare Neighbors (List of SystemContexts)
                 try:
                     eng.execute_workflow(
                         "workflows/main_loop.yaml", 
                         env_adapter=adapter,
                         agent_id=i,
                         neighbors=system_contexts
                     )
                 except Exception as e:
                     log_error(common_global_ctx, f"🔥 Agent {i} CRASHED at step {steps_count}: {e}")
                     # If Crash, we should break? Or continue other agents?
                     # For Dogfooding, we want to see the error and STOP.
                     raise e
                 
                 end_t = time.time()
                 cycle_t = end_t - start_t
                 eng.get_domain().last_cycle_time = cycle_t
                 eng.get_domain().current_step = steps_count
                 
                 # Accumulate Reward
                 last_r = eng.get_domain().last_reward
                 episode_rewards[i] += last_r['extrinsic'] + last_r['intrinsic']

            # Check Global Success
            if any(tuple(pos) == environment.goal_pos for pos in environment.agent_positions.values()):
                is_successful = True
                break
                
            if settings.get('visual_mode'):
                environment.render()
                time.sleep(0.01)

        # End Episode Logging
        # Gather stats
        avg_cycle = 0 # Placeholder
        
        log_entry = {
            'episode': episode + 1,
            'success': is_successful,
            'steps': steps_count,
            'total_reward': episode_rewards[0], # Log agent 0
            'final_exploration_rate': engines[0].get_domain().current_exploration_rate,
            'avg_cycle_time': 0.0, # Not tracking detailed avg here to save implementation time
            'max_steps_env': common_global_ctx.max_steps
        }
        episode_data.append(log_entry)
        
        # Update Long Term Memory (for Social)
        for eng in engines:
            dom = eng.get_domain()
            if 'episode_results' not in dom.long_term_memory:
                dom.long_term_memory['episode_results'] = []
            dom.long_term_memory['episode_results'].append({
                'episode': episode + 1,
                'success': is_successful,
                'steps': steps_count
            })

    # 6. Save Results
    df = pd.DataFrame(episode_data)
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    df.to_csv(args.output_path, index=False)
    print(f"Results saved to {args.output_path}")

if __name__ == "__main__":
    main()