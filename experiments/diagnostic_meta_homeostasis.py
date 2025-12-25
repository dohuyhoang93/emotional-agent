"""
Diagnostic Script: Meta-Homeostasis Bug Reproduction
=====================================================
Script này tái hiện các lỗi logic trong Meta-Homeostasis.
"""
import sys
sys.path.append('.')

from src.core.snn_context import create_snn_context
from src.processes.snn_vector_ops import process_integrate_vector, process_fire_vector
from src.processes.snn_integrate_fire import process_homeostasis
from src.processes.snn_meta import process_meta_homeostasis
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


def test_integral_windup():
    """
    Test 1: Integral Windup
    Kiểm tra xem integral term có tích lũy vô hạn không.
    """
    print("\n=== TEST 1: INTEGRAL WINDUP ===")
    
    ctx = create_snn_context(num_neurons=100, connectivity=0.15)
    
    engine = WorkflowEngine()
    engine.register('integrate', process_integrate_vector)
    engine.register('fire', process_fire_vector)
    engine.register('meta_homeostasis', process_meta_homeostasis)
    
    # Workflow CHỈ có meta_homeostasis (không có homeostasis thường)
    workflow = ['integrate', 'fire', 'meta_homeostasis']
    
    pattern_A = np.array([1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    pattern_A /= np.linalg.norm(pattern_A)
    
    # Tracking
    fire_rates = []
    integral_values = []
    adjustment_values = []
    
    for step in range(2000):
        if step % 100 == 0:
            inject_pattern_spike(ctx, [0, 1, 2], pattern_A)
        
        ctx = engine.run_timestep(workflow, ctx)
        
        fire_rates.append(ctx.metrics.get('fire_rate', 0.0))
        integral_values.append(ctx.pid_state['threshold']['error_integral'])
        adjustment_values.append(ctx.metrics.get('meta_threshold_adj', 0.0))
        
        if step % 500 == 0:
            print(f"Step {step}: Fire={fire_rates[-1]:.3f}, Integral={integral_values[-1]:.3f}, Adj={adjustment_values[-1]:.3f}")
    
    # Vẽ biểu đồ
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    
    ax1.plot(fire_rates)
    ax1.axhline(y=0.02, color='r', linestyle='--', label='Target')
    ax1.set_title('Fire Rate (Meta-Homeostasis Only)')
    ax1.set_ylabel('Fire Rate')
    ax1.legend()
    ax1.grid(True)
    
    ax2.plot(integral_values, color='orange')
    ax2.set_title('Integral Term (Error Accumulation)')
    ax2.set_ylabel('Integral Value')
    ax2.grid(True)
    
    ax3.plot(adjustment_values, color='green')
    ax3.set_title('Threshold Adjustment')
    ax3.set_ylabel('Adjustment')
    ax3.set_xlabel('Time (ms)')
    ax3.grid(True)
    
    plt.tight_layout()
    plt.savefig('results/diagnostic_integral_windup.png')
    print("\nResults saved to results/diagnostic_integral_windup.png")
    plt.show()
    
    # Kiểm tra windup
    max_integral = max(abs(x) for x in integral_values)
    print(f"\n[RESULT] Max integral value: {max_integral:.2f}")
    if max_integral > 10.0:
        print("❌ INTEGRAL WINDUP DETECTED!")
    else:
        print("✅ Integral bounded")


def test_conflict():
    """
    Test 2: Conflict với Homeostasis
    Kiểm tra xem hai quy trình có kéo co nhau không.
    """
    print("\n=== TEST 2: CONFLICT WITH HOMEOSTASIS ===")
    
    ctx = create_snn_context(num_neurons=100, connectivity=0.15)
    
    engine = WorkflowEngine()
    engine.register('integrate', process_integrate_vector)
    engine.register('fire', process_fire_vector)
    engine.register('meta_homeostasis', process_meta_homeostasis)
    engine.register('homeostasis', process_homeostasis)
    
    # Workflow CẢ HAI
    workflow = ['integrate', 'fire', 'meta_homeostasis', 'homeostasis']
    
    pattern_A = np.array([1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    pattern_A /= np.linalg.norm(pattern_A)
    
    # Tracking
    fire_rates = []
    meta_adjustments = []
    thresholds = []
    
    for step in range(2000):
        if step % 100 == 0:
            inject_pattern_spike(ctx, [0, 1, 2], pattern_A)
        
        # Lưu threshold trước khi chạy
        threshold_before = ctx.neurons[0].threshold
        
        ctx = engine.run_timestep(workflow, ctx)
        
        # Lưu threshold sau khi chạy
        threshold_after = ctx.neurons[0].threshold
        
        fire_rates.append(ctx.metrics.get('fire_rate', 0.0))
        meta_adjustments.append(ctx.metrics.get('meta_threshold_adj', 0.0))
        thresholds.append(threshold_after)
        
        if step % 500 == 0:
            delta = threshold_after - threshold_before
            print(f"Step {step}: Fire={fire_rates[-1]:.3f}, Threshold={threshold_after:.3f}, Delta={delta:.6f}")
    
    # Vẽ biểu đồ
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    ax1.plot(fire_rates)
    ax1.axhline(y=0.02, color='r', linestyle='--', label='Target')
    ax1.set_title('Fire Rate (Meta + Homeostasis)')
    ax1.set_ylabel('Fire Rate')
    ax1.legend()
    ax1.grid(True)
    
    ax2.plot(thresholds, color='purple')
    ax2.set_title('Neuron[0] Threshold Over Time')
    ax2.set_ylabel('Threshold')
    ax2.set_xlabel('Time (ms)')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('results/diagnostic_conflict.png')
    print("\nResults saved to results/diagnostic_conflict.png")
    plt.show()
    
    # Kiểm tra oscillation
    threshold_std = np.std(thresholds[1000:])  # Chỉ xét nửa sau
    print(f"\n[RESULT] Threshold std dev (last 1000 steps): {threshold_std:.6f}")
    if threshold_std > 0.1:
        print("❌ OSCILLATION DETECTED!")
    else:
        print("✅ Stable")


if __name__ == '__main__':
    print("Meta-Homeostasis Diagnostic Suite")
    print("=" * 50)
    
    # Chạy tests
    test_integral_windup()
    test_conflict()
    
    print("\n" + "=" * 50)
    print("Diagnostic complete!")
