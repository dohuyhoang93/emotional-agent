"""
Memory Leak Profiling Script for EmotionAgent
Simple approach: Run experiments and report memory usage before/after each episode.
"""
import sys
import os
import gc
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

import tracemalloc
tracemalloc.start(10)

# Imports
from core.context import SystemContext, GlobalContext, DomainContext
from core.snn_context_theus import SNNSystemContext, SNNGlobalContext, SNNDomainContext
from coordination.multi_agent_coordinator import MultiAgentExperiment
from theus import TheusEngine
from theus.config import AuditRecipe, ConfigFactory
from environment import GridWorld

# Minimal config for profiling
EXPERIMENT_CONFIG = {
    "name": "MemoryProfileTest",
    "description": "Memory profiling test",
    "grid_size": [10, 10],
    "start_pos": [0, 0],
    "goal_pos": [9, 9],
    "walls": [],
    "visual_mode": False,
    "num_episodes": 5,  # Just 5 episodes for profiling
    "max_steps_per_episode": 200,
    "num_agents": 1,  # Single agent
    "curiosity_weight": 0.5,
    "learning_rate": 0.1,
    "discount_factor": 0.99
}

def profile_experiment():
    print("="*60)
    print("MEMORY PROFILING: Multi-Agent Experiment")
    print("="*60)
    
    # Take initial snapshot
    gc.collect()
    initial_current, initial_peak = tracemalloc.get_traced_memory()
    print(f"\nInitial: {initial_current/1024/1024:.2f} MB")
    
    # Create experiment
    experiment = MultiAgentExperiment(EXPERIMENT_CONFIG)
    gc.collect()
    after_init, _ = tracemalloc.get_traced_memory()
    print(f"After experiment init: {after_init/1024/1024:.2f} MB (+{(after_init-initial_current)/1024/1024:.2f} MB)")
    
    # Track memory per episode
    memories = []
    
    for episode in range(EXPERIMENT_CONFIG['num_episodes']):
        experiment.run_episode()
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        memories.append(current)
        print(f"Episode {episode}: {current/1024/1024:.2f} MB (peak: {peak/1024/1024:.2f} MB)")
    
    # Calculate growth rate
    if len(memories) > 1:
        growth = (memories[-1] - memories[0]) / (len(memories) - 1)
        print(f"\nAverage growth per episode: {growth/1024:.1f} KB")
    
    # Take snapshots
    gc.collect()
    snapshot = tracemalloc.take_snapshot()
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
        tracemalloc.Filter(False, "tracemalloc"),
    ))
    
    print("\n" + "="*60)
    print("TOP MEMORY CONSUMERS")
    print("="*60)
    top_stats = snapshot.statistics('lineno')
    for stat in top_stats[:20]:
        print(f"  {stat.size/1024:.1f} KB: {stat.traceback}")
    
    # Suspect analysis
    print("\n" + "="*60)
    print("SUSPECT ANALYSIS")
    print("="*60)
    
    if experiment.agents:
        agent = experiment.agents[0]
        snn = agent.snn_ctx.domain_ctx
        print(f"\nneurons count: {len(snn.neurons)}")
        print(f"synapses count: {len(snn.synapses)}")
        print(f"spike_queue keys: {len(snn.spike_queue)}")
        
        rl = agent.domain_ctx
        print(f"short_term_memory length: {len(rl.short_term_memory)}")
        print(f"heavy_q_table entries: {len(rl.heavy_q_table)}")
        print(f"heavy_recorder_buffer length: {len(rl.heavy_recorder_buffer)}")
    
    tracemalloc.stop()

if __name__ == "__main__":
    profile_experiment()
