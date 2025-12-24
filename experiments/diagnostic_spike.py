"""
Deep Diagnostic Script - Track Fire Rate Spike
===============================================
Chạy experiment với logging chi tiết để điều tra spike.
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


def inject_pattern_spike(ctx, neuron_ids, pattern_vector):
    """Bơm pattern vào neuron."""
    for nid in neuron_ids:
        if nid < len(ctx.neurons):
            neuron = ctx.neurons[nid]
            normalized = pattern_vector / (np.linalg.norm(pattern_vector) + 1e-8)
            neuron.potential_vector = normalized * 2.0
            neuron.potential = 2.0
            neuron.prototype_vector = normalized


def run_diagnostic():
    """Chạy diagnostic với logging chi tiết."""
    num_neurons = 100
    num_steps = 5000
    
    ctx = create_snn_context(num_neurons=num_neurons, connectivity=0.15)
    ctx.params['pid_kp'] = 0.01
    ctx.params['pid_ki'] = 0.001
    ctx.params['pid_kd'] = 0.005
    
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
    
    # Tracking
    fire_rates = []
    avg_thresholds = []
    avg_weights = []
    max_weights = []
    
    print(f"Starting Diagnostic: {num_neurons} neurons, {num_steps} steps\n")
    
    for step in range(num_steps):
        # Kill neurons
        if step == 1000:
            print(f"\n[STRESS TEST] Step {step}: Killing 10% neurons...")
            for i in range(num_neurons // 10):
                ctx.neurons[i].threshold = 999.0
        
        # Pattern injection
        if step % 100 == 0:
            inject_pattern_spike(ctx, [10, 11, 12], pattern_A)
        
        # Run workflow
        ctx = engine.run_timestep(workflow, ctx)
        
        # Track metrics
        fire_rate = ctx.metrics.get('fire_rate', 0.0)
        fire_rates.append(fire_rate)
        
        # Track thresholds
        alive_neurons = [n for n in ctx.neurons if n.threshold < 10.0]
        if alive_neurons:
            avg_threshold = np.mean([n.threshold for n in alive_neurons])
            avg_thresholds.append(avg_threshold)
        else:
            avg_thresholds.append(0)
        
        # Track weights
        weights = [s.weight for s in ctx.synapses]
        avg_weights.append(np.mean(weights) if weights else 0)
        max_weights.append(np.max(weights) if weights else 0)
        
        # Log critical moments
        if step % 500 == 0:
            print(f"Step {step}:")
            print(f"  Fire rate: {fire_rate:.4f}")
            print(f"  Avg threshold: {avg_thresholds[-1]:.4f}")
            print(f"  Avg weight: {avg_weights[-1]:.4f}")
            print(f"  Max weight: {max_weights[-1]:.4f}")
            
            # Check for spike
            if fire_rate > 0.10:
                print(f"  ⚠️ SPIKE DETECTED!")
                # Detailed inspection
                firing_neurons = sum(1 for n in ctx.neurons if (step - n.last_fire_time) < 10)
                print(f"  Firing neurons (last 10ms): {firing_neurons}")
                print(f"  Total synapses: {len(ctx.synapses)}")
    
    # Final analysis
    print("\n=== FINAL ANALYSIS ===")
    print(f"Fire rate range: {min(fire_rates):.4f} - {max(fire_rates):.4f}")
    print(f"Threshold range: {min(avg_thresholds):.4f} - {max(avg_thresholds):.4f}")
    print(f"Weight range: {min(avg_weights):.4f} - {max(avg_weights):.4f}")
    print(f"Max weight range: {min(max_weights):.4f} - {max(max_weights):.4f}")
    
    # Find spike moments
    spikes = [(i, fr) for i, fr in enumerate(fire_rates) if fr > 0.10]
    if spikes:
        print(f"\nSpike moments ({len(spikes)} total):")
        for step, fr in spikes[:10]:  # First 10
            print(f"  Step {step}: fire_rate={fr:.4f}, threshold={avg_thresholds[step]:.4f}, weight={avg_weights[step]:.4f}")


if __name__ == '__main__':
    run_diagnostic()
