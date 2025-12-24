"""
Debug Script - Save metrics to file for analysis
"""
import sys
sys.path.append('.')

from src.core.snn_context import create_snn_context
from src.processes.snn_vector_ops import (
    process_integrate_vector,
    process_fire_vector,
    process_clustering
)
from src.processes.snn_integrate_fire import process_homeostasis
from src.processes.snn_learning import process_stdp_basic
from src.processes.snn_resync import process_periodic_resync
from src.processes.snn_imagination import process_imagination_loop, process_dream_learning
from src.engine.workflow_engine import WorkflowEngine
import numpy as np
import json


def inject_pattern_spike(ctx, neuron_ids, pattern_vector):
    for nid in neuron_ids:
        if nid < len(ctx.neurons):
            neuron = ctx.neurons[nid]
            normalized = pattern_vector / (np.linalg.norm(pattern_vector) + 1e-8)
            neuron.potential_vector = normalized * 2.0
            neuron.potential = 2.0
            neuron.prototype_vector = normalized


def run_debug():
    num_neurons = 100
    num_steps = 5000
    
    ctx = create_snn_context(num_neurons=num_neurons, connectivity=0.15)
    
    engine = WorkflowEngine()
    engine.register('integrate', process_integrate_vector)
    engine.register('fire', process_fire_vector)
    engine.register('clustering', process_clustering)
    engine.register('stdp', process_stdp_basic)
    engine.register('homeostasis', process_homeostasis)
    engine.register('resync', process_periodic_resync)
    engine.register('imagination', process_imagination_loop)
    engine.register('dream_learning', process_dream_learning)
    
    workflow = [
        'integrate', 'fire', 'clustering', 'stdp',
        'homeostasis', 'resync',
        'imagination', 'dream_learning'
    ]
    
    pattern_A = np.array([1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    pattern_A /= np.linalg.norm(pattern_A)
    
    # Save ALL metrics
    metrics_log = []
    
    print(f"Starting Debug: {num_neurons} neurons, {num_steps} steps\n")
    
    for step in range(num_steps):
        if step == 1000:
            print(f"[STRESS TEST] Step {step}: Killing 10% neurons...")
            for i in range(num_neurons // 10):
                ctx.neurons[i].threshold = 999.0
        
        if step % 100 == 0:
            inject_pattern_spike(ctx, [10, 11, 12], pattern_A)
        
        ctx = engine.run_timestep(workflow, ctx)
        
        # Save metrics
        fire_rate = ctx.metrics.get('fire_rate', 0.0)
        metrics_log.append({
            'step': step,
            'fire_rate': fire_rate,
            'nightmare_count': ctx.metrics.get('nightmare_count', 0),
            'imagination_count': ctx.metrics.get('imagination_count', 0)
        })
        
        # Print every 500 steps
        if step % 500 == 0:
            print(f"Step {step}: Fire={fire_rate:.4f}")
    
    # Save to file
    with open('results/metrics_debug.json', 'w') as f:
        json.dump(metrics_log, f, indent=2)
    
    print(f"\nMetrics saved to results/metrics_debug.json")
    print(f"Total steps: {len(metrics_log)}")
    
    # Check for spikes
    spikes = [m for m in metrics_log if m['fire_rate'] > 0.10]
    print(f"Spike moments (fire_rate > 0.10): {len(spikes)}")
    if spikes:
        print("First 10 spikes:")
        for m in spikes[:10]:
            print(f"  Step {m['step']}: fire_rate={m['fire_rate']:.4f}")


if __name__ == '__main__':
    run_debug()
