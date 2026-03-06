import sys
import json
import numpy as np

# Load config
with open('experiments.json', 'r') as f:
    config = json.load(f)
params = next(e for e in config["experiments"] if e["name"] == "multi_agent_complex_maze")["parameters"]

from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld

env = GridWorld({'environment_config': params['environment_config']})
env_adapter = EnvironmentAdapter(env)
obs_dict = env.reset()

from src.coordination.multi_agent_coordinator import MultiAgentCoordinator
from src.core.snn_context_theus import SNNGlobalContext
from src.core.context import GlobalContext

global_ctx = GlobalContext(
    initial_needs=[0.5, 0.5],
    initial_emotions=[0.0] * 16,
    total_episodes=1, max_steps=50, seed=42, switch_locations={}, initial_exploration_rate=1.0
)
global_ctx.start_positions = [[0, 0]]

snn_global_ctx = SNNGlobalContext(
    num_neurons=1024,
    vector_dim=16,
    connectivity=0.1,
    social_elite_ratio=0.2,
    social_learner_ratio=0.5,
    social_synapses_per_transfer=10,
    use_neural_darwinism=True,
    darwinism_interval=100,
    selection_pressure=0.1,
    reproduction_rate=0.05
)

coordinator = MultiAgentCoordinator(
    num_agents=1, 
    global_ctx=global_ctx, 
    snn_global_ctx=snn_global_ctx
)
agent = coordinator.agents[0]
agent.environment_adapter = env_adapter
agent.rl_ctx.domain_ctx.environment_adapter = env_adapter
agent.reset(obs_dict[0])


print("Starting debug run...")

# Thử chay 15 bước để xem firing
from src.processes.snn_composite_theus import process_snn_cycle

for step in range(15):
    ctx = agent.rl_ctx
    snn_ctx = ctx.domain_ctx.snn_context
    
    print(f"\n--- STEP {step} ---")
    
    # Using actual sparse observation from environment
    real_obs = env.get_sensor_vector(0)
    ctx.domain_ctx.current_observation = real_obs
    print(f"Real Sensor Vector (Max): {np.max(real_obs):.4f}")
    print(f"DEBUG IN SCRIPT: tau_decay={snn_ctx.global_ctx.tau_decay}")
    
    # CHẠY TRỰC TIẾP SNN CYCLE (Bypass rl action và perception lỗi dict)
    delta = process_snn_cycle(ctx)
    if delta and 'current_time' in delta:
        ctx.domain_ctx.snn_context.domain_ctx.current_time = delta['current_time']
    
    if snn_ctx is not None and getattr(snn_ctx.domain_ctx, 'heavy_tensors', None):
        t = snn_ctx.domain_ctx.heavy_tensors
        if 'potentials' in t and 'thresholds' in t:
            pots = t['potentials']
            thresh = t['thresholds']
            
            can_fire = (pots >= thresh)
            spikes = np.where(can_fire)[0]
            
            print(f"Max Potentials: {np.max(pots):.4f}, Min Threshold: {np.min(thresh):.4f}")
            print(f"Pots[:20]: {[round(x, 2) for x in pots[:20]]}")
            print(f"Number of Neurons vượt ngưỡng (>= thresh): {len(spikes)}")
            
            metrics = snn_ctx.domain_ctx.metrics
            print(f"Reported Avg Firing Rate: {metrics.get('avg_firing_rate', 0.0):.6f}")
