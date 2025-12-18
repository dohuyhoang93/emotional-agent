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

# THEUS V2 SDK Imports
from theus import POPEngine
from theus.config import ConfigFactory
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld
from src.models import EmotionCalculatorMLP
from src.logger import log, log_error

# Process Imports (Now decorated with @process from theus)
from src.processes.p1_perception import perception
from src.processes.p2_belief_update import update_belief
from src.processes.p3_emotion_calc import calculate_emotions
from src.processes.p5_adjust_exploration import adjust_exploration
from src.processes.p6_action_select import select_action
from src.processes.p7_execution import execute_action
from src.processes.p8_consequence import record_consequences
from src.processes.p9_social_learning import social_learning

def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def main():
    parser = argparse.ArgumentParser(description="DeepSearch Agent - Theus V2 Migration")
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
            print(f"⚠️ Failed to load audit recipe (Auditing Disability): {e}")

    # 1. Config Loading (Legacy Simulation)
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
    # We trust 'settings' has what GridWorld needs.
    environment = GridWorld(settings)
    adapter = EnvironmentAdapter(environment)
    
    # 3. Hydrate Global Context
    switch_locs = {v: k for k, v in environment.switches.items()} # ID -> Pos
    
    common_global_ctx = GlobalContext(
        initial_needs=settings['initial_needs'],
        initial_emotions=settings['initial_emotions'],
        total_episodes=args.num_episodes,
        max_steps=environment.max_steps,
        seed=args.seed,
        switch_locations=switch_locs,
        log_level=args.log_level,
        
        # Hyperparams
        assimilation_rate=settings.get('assimilation_rate', 0.1),
        initial_exploration_rate=float(settings.get('exploration_rate', 1.0)),
        use_dynamic_curiosity=settings.get('use_dynamic_curiosity', False),
        use_adaptive_fatigue=settings.get('use_adaptive_fatigue', False),
        fatigue_growth_rate=settings.get('fatigue_growth_rate', 0.001),
        intrinsic_reward_weight=settings.get('intrinsic_reward_weight', 0.1)
    )

    # 4. Initialize Agents (System Contexts + POPEngine)
    num_agents = environment.num_agents
    system_contexts = []
    engines = []

    for i in range(num_agents):
        # Domain Context (Mutable)
        n_dim = len(settings['initial_needs'])
        e_dim = len(settings['initial_emotions'])
        
        # Init Neural Model
        b_dim = 2 + len(switch_locs)
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
        
        sys_ctx = SystemContext(global_ctx=common_global_ctx, domain_ctx=domain_ctx)
        
        # Init Engine with Audit Recipe
        # STRICT MODE: True. Because we want to verify Theus V2 capability.
        engine = POPEngine(sys_ctx, audit_recipe=audit_recipe, strict_mode=True)
        
        # Register Processes
        # Note: Names must match Audit Recipe if defined
        engine.register_process("perception", perception)
        engine.register_process("update_belief", update_belief)
        engine.register_process("calculate_emotions", calculate_emotions)
        engine.register_process("adjust_exploration", adjust_exploration)
        engine.register_process("select_action", select_action)
        engine.register_process("execute_action", execute_action)
        engine.register_process("record_consequences", record_consequences)
        engine.register_process("social_learning", social_learning)
        
        system_contexts.append(sys_ctx)
        engines.append(engine)

    # 5. Main Simulation Loop
    episode_data = []
    
    workflow_steps = [
        "perception",
        "update_belief",
        "calculate_emotions",
        "adjust_exploration",
        "social_learning", # Run social learning before action selection
        "select_action",
        "execute_action",
        "record_consequences"
    ]

    print(f"🚀 Starting Simulation: {args.num_episodes} Episodes, {num_agents} Agents.")

    for episode in range(args.num_episodes):
        if not settings.get('visual_mode'):
            log(common_global_ctx, 'info', f"Starting Episode {episode+1}/{args.num_episodes}...")
            
        # Reset Environment
        obs_dict = environment.reset()
        is_successful = False
        
        for i, eng in enumerate(engines):
            with eng.edit():
                dom = eng.ctx.domain_ctx
                dom.current_episode = episode + 1
                dom.current_step = 0
                dom.current_observation = obs_dict[i]
                dom.previous_observation = None
                dom.last_reward = {'extrinsic': 0.0, 'intrinsic': 0.0}

        episode_rewards = {i: 0.0 for i in range(num_agents)}
        steps_count = 0
        
        # Step Loop
        while not adapter.is_done() and steps_count < common_global_ctx.max_steps:
            steps_count += 1
            environment.current_step = steps_count
            
            # Run Agents
            for i, eng in enumerate(engines):
                 start_t = time.time()
                 
                 # PROCESS EXECUTION CHAIN (Synchronous)
                 for step_name in workflow_steps:
                     try:
                         # Pass runtime dependencies as kwargs
                         eng.run_process(
                             step_name,
                             env_adapter=adapter,
                             agent_id=i,
                             neighbors=system_contexts
                         )
                     except Exception as e:
                         # If any process fails, crash the agent (or simulation)
                         # Here we convert to strict crash for debugging
                         raise RuntimeError(f"Agent {i} crashed at {step_name}: {e}") from e
                 
                 end_t = time.time()
                 cycle_t = end_t - start_t
                 
                 with eng.edit():
                     eng.ctx.domain_ctx.last_cycle_time = cycle_t
                     eng.ctx.domain_ctx.current_step = steps_count
                     
                     # Accumulate Reward for Logging
                     last_r = eng.ctx.domain_ctx.last_reward
                     episode_rewards[i] += last_r['extrinsic'] + last_r['intrinsic']

            # Check Global Success
            if any(tuple(pos) == environment.goal_pos for pos in environment.agent_positions.values()):
                is_successful = True
                break
                
            if settings.get('visual_mode'):
                environment.render()
                time.sleep(0.01)

        # End Episode Logging
        log_entry = {
            'episode': episode + 1,
            'success': is_successful,
            'steps': steps_count,
            'total_reward': episode_rewards[0], 
            'final_exploration_rate': engines[0].ctx.domain_ctx.current_exploration_rate,
            'avg_cycle_time': 0.0, 
            'max_steps_env': common_global_ctx.max_steps
        }
        episode_data.append(log_entry)
        
        # Update Memory
        for eng in engines:
            dom = eng.ctx.domain_ctx
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
