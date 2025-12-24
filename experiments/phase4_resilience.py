"""
Phase 4 Experiment: Resilience & Imagination
=============================================
Thử nghiệm các cơ chế Anti-fragile.
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
from src.processes.snn_meta import process_meta_homeostasis
from src.processes.snn_resync import process_periodic_resync
from src.processes.snn_imagination import process_imagination_loop, process_dream_learning
from src.tools.brain_biopsy import BrainBiopsy
from src.engine.workflow_engine import WorkflowEngine
import matplotlib.pyplot as plt
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


def run_resilience_experiment(num_neurons=100, num_steps=5000):  # Tăng từ 2000 lên 5000
    """
    Chạy thử nghiệm Resilience (LONG RUN để test nightmare runaway).
    """
    # Tạo SNN Context
    ctx = create_snn_context(num_neurons=num_neurons, connectivity=0.15)
    
    # Giảm PID gains để tránh oscillation
    ctx.params['pid_kp'] = 0.01  # Giảm từ 0.1
    ctx.params['pid_ki'] = 0.001  # Giảm từ 0.01
    ctx.params['pid_kd'] = 0.005  # Giảm từ 0.05
    
    # Tạo Workflow Engine
    engine = WorkflowEngine()
    engine.register('integrate', process_integrate_vector)
    engine.register('fire', process_fire_vector)
    engine.register('clustering', process_clustering)
    engine.register('stdp', process_stdp_basic)
    engine.register('homeostasis', process_homeostasis)
    engine.register('meta_homeostasis', process_meta_homeostasis)
    engine.register('resync', process_periodic_resync)
    engine.register('imagination', process_imagination_loop)
    engine.register('dream_learning', process_dream_learning)
    
    # Workflow (BẬT LẠI tất cả features)
    workflow = [
        'integrate', 'fire', 'clustering', 'stdp',
        # 'meta_homeostasis',  # VẪN TẮT - gây oscillation
        'homeostasis',  # Chỉ dùng homeostasis thường
        'resync',
        'imagination', 'dream_learning'  # BẬT LẠI
    ]
    
    # Pattern
    pattern_A = np.array([1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    pattern_A /= np.linalg.norm(pattern_A)
    
    # Metrics tracking
    fire_rates = []
    resync_times = []
    imagination_counts = []
    nightmare_counts = []
    
    print(f"Starting Resilience experiment: {num_neurons} neurons, {num_steps} steps")
    
    for step in range(num_steps):
        # Simulate một số neuron bị "hỏng" (stress test - giảm xuống 10%)
        if step == 1000:
            print(f"\n[STRESS TEST] Step {step}: Killing 10% neurons...")
            for i in range(num_neurons // 10):  # Kill neurons 0-9
                ctx.neurons[i].threshold = 999.0  # Vô hiệu hóa
        
        # Bơm pattern định kỳ (vào neurons KHÔNG bị kill)
        if step % 100 == 0:
            # Bơm vào neurons 10-12 (KHÔNG bị kill)
            inject_pattern_spike(ctx, [10, 11, 12], pattern_A)
        
        # Chạy workflow
        ctx = engine.run_timestep(workflow, ctx)
        
        # Track metrics
        fire_rates.append(ctx.metrics.get('fire_rate', 0.0))
        
        if ctx.metrics.get('last_resync_time') == step:
            resync_times.append(step)
        
        imagination_counts.append(ctx.metrics.get('imagination_count', 0))
        nightmare_counts.append(ctx.metrics.get('nightmare_count', 0))
        
        if step % 500 == 0:
            print(f"Step {step}: Fire={fire_rates[-1]:.3f}, Resync={len(resync_times)}, Dreams={imagination_counts[-1]}")
    
    # Brain Biopsy (inspect sau khi chạy)
    print("\n=== BRAIN BIOPSY ===")
    pop_info = BrainBiopsy.inspect_population(ctx)
    print(f"Active neurons: {pop_info['population']['active_neurons']}/{pop_info['population']['total_neurons']}")
    print(f"Total synapses: {pop_info['connectivity']['total_synapses']}")
    
    # Vẽ biểu đồ
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Fire rate
    ax1.plot(fire_rates, alpha=0.3, label='Raw', color='blue')
    
    # Thêm rolling average để dễ nhìn
    window = 50
    if len(fire_rates) >= window:
        smoothed = np.convolve(fire_rates, np.ones(window)/window, mode='valid')
        ax1.plot(range(window-1, len(fire_rates)), smoothed, alpha=0.8, label='Smoothed (50ms)', color='darkblue', linewidth=2)
    
    ax1.axhline(y=ctx.params['target_fire_rate'], color='r', linestyle='--', label='Target')
    ax1.axvline(x=1000, color='red', alpha=0.5, linestyle=':', label='Neuron Kill (10%)')
    ax1.set_title('Fire Rate (with 10% Neuron Kill at step 1000)')
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Firing Rate')
    ax1.legend()
    ax1.grid(True)
    
    # Resync events
    for resync_time in resync_times:
        ax1.axvline(x=resync_time, color='green', alpha=0.2, linestyle='-')
    
    # Imagination count
    ax2.plot(imagination_counts, color='purple')
    ax2.set_title('Imagination Events (Dream Mode)')
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Cumulative Count')
    ax2.grid(True)
    
    # Nightmare count
    ax3.plot(nightmare_counts, color='darkred')
    ax3.set_title('Nightmare Events (Fear-based Learning)')
    ax3.set_xlabel('Time (ms)')
    ax3.set_ylabel('Cumulative Count')
    ax3.grid(True)
    
    # Resync count
    resync_counts = list(range(len(resync_times)))
    ax4.plot(resync_times, resync_counts, 'go-')
    ax4.set_title('Periodic Resync Events')
    ax4.set_xlabel('Time (ms)')
    ax4.set_ylabel('Resync Count')
    ax4.grid(True)
    
    plt.tight_layout()
    plt.savefig('results/phase4_resilience.png')
    print("\nResults saved to results/phase4_resilience.png")
    plt.show()
    
    return ctx


if __name__ == '__main__':
    run_resilience_experiment()
