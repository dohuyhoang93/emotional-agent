"""
Test Meta-Homeostasis Fixed Version
====================================
So sánh 3 versions:
1. Homeostasis thường (baseline)
2. Meta-Homeostasis cũ (có bug)
3. Meta-Homeostasis fixed (với anti-windup)

Author: Do Huy Hoang
Date: 2025-12-25
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
from src.processes.snn_meta import process_meta_homeostasis  # Old version
from src.processes.snn_meta_fixed import process_meta_homeostasis_fixed  # New version
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


def run_comparison_test(num_neurons=100, num_steps=5000):
    """
    Chạy test so sánh 3 versions.
    """
    print("=" * 60)
    print("Meta-Homeostasis Comparison Test")
    print("=" * 60)
    
    # Pattern
    pattern_A = np.array([1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    pattern_A /= np.linalg.norm(pattern_A)
    
    # ===== TEST 1: Homeostasis thường (Baseline) =====
    print("\n[1/3] Testing: Homeostasis thường (Baseline)...")
    ctx1 = create_snn_context(num_neurons=num_neurons, connectivity=0.15)
    
    engine1 = WorkflowEngine()
    engine1.register('integrate', process_integrate_vector)
    engine1.register('fire', process_fire_vector)
    engine1.register('clustering', process_clustering)
    engine1.register('stdp', process_stdp_basic)
    engine1.register('homeostasis', process_homeostasis)
    
    workflow1 = ['integrate', 'fire', 'clustering', 'stdp', 'homeostasis']
    
    fire_rates_1 = []
    thresholds_1 = []
    
    for step in range(num_steps):
        if step % 100 == 0:
            inject_pattern_spike(ctx1, [0, 1, 2], pattern_A)
        
        ctx1 = engine1.run_timestep(workflow1, ctx1)
        fire_rates_1.append(ctx1.metrics.get('fire_rate', 0.0))
        thresholds_1.append(ctx1.neurons[0].threshold)
        
        if step % 1000 == 0:
            print(f"  Step {step}: Fire={fire_rates_1[-1]:.3f}, Threshold={thresholds_1[-1]:.3f}")
    
    # ===== TEST 2: Meta-Homeostasis cũ (Có bug) =====
    print("\n[2/3] Testing: Meta-Homeostasis cũ (Có bug)...")
    ctx2 = create_snn_context(num_neurons=num_neurons, connectivity=0.15)
    
    engine2 = WorkflowEngine()
    engine2.register('integrate', process_integrate_vector)
    engine2.register('fire', process_fire_vector)
    engine2.register('clustering', process_clustering)
    engine2.register('stdp', process_stdp_basic)
    engine2.register('meta_homeostasis', process_meta_homeostasis)
    
    workflow2 = ['integrate', 'fire', 'clustering', 'stdp', 'meta_homeostasis']
    
    fire_rates_2 = []
    thresholds_2 = []
    integrals_2 = []
    
    for step in range(num_steps):
        if step % 100 == 0:
            inject_pattern_spike(ctx2, [0, 1, 2], pattern_A)
        
        ctx2 = engine2.run_timestep(workflow2, ctx2)
        fire_rates_2.append(ctx2.metrics.get('fire_rate', 0.0))
        thresholds_2.append(ctx2.neurons[0].threshold)
        integrals_2.append(ctx2.pid_state['threshold']['error_integral'])
        
        if step % 1000 == 0:
            print(f"  Step {step}: Fire={fire_rates_2[-1]:.3f}, Threshold={thresholds_2[-1]:.3f}, Integral={integrals_2[-1]:.3f}")
    
    # ===== TEST 3: Meta-Homeostasis fixed (Với anti-windup) =====
    print("\n[3/3] Testing: Meta-Homeostasis fixed (Với anti-windup)...")
    ctx3 = create_snn_context(num_neurons=num_neurons, connectivity=0.15)
    
    # Thêm params mới
    ctx3.params['meta_pid_kp'] = 0.001
    ctx3.params['meta_pid_ki'] = 0.0001
    ctx3.params['meta_pid_kd'] = 0.0005
    ctx3.params['meta_max_integral'] = 5.0
    ctx3.params['meta_max_output'] = 0.01
    ctx3.params['meta_scale_factor'] = 0.0001
    
    engine3 = WorkflowEngine()
    engine3.register('integrate', process_integrate_vector)
    engine3.register('fire', process_fire_vector)
    engine3.register('clustering', process_clustering)
    engine3.register('stdp', process_stdp_basic)
    engine3.register('meta_homeostasis_fixed', process_meta_homeostasis_fixed)
    
    workflow3 = ['integrate', 'fire', 'clustering', 'stdp', 'meta_homeostasis_fixed']
    
    fire_rates_3 = []
    thresholds_3 = []
    integrals_3 = []
    adjustments_3 = []
    
    for step in range(num_steps):
        if step % 100 == 0:
            inject_pattern_spike(ctx3, [0, 1, 2], pattern_A)
        
        ctx3 = engine3.run_timestep(workflow3, ctx3)
        fire_rates_3.append(ctx3.metrics.get('fire_rate', 0.0))
        thresholds_3.append(ctx3.neurons[0].threshold)
        integrals_3.append(ctx3.metrics.get('meta_integral', 0.0))
        adjustments_3.append(ctx3.metrics.get('meta_threshold_adj', 0.0))
        
        if step % 1000 == 0:
            print(f"  Step {step}: Fire={fire_rates_3[-1]:.3f}, Threshold={thresholds_3[-1]:.3f}, Integral={integrals_3[-1]:.3f}")
    
    # ===== Vẽ biểu đồ so sánh =====
    print("\n" + "=" * 60)
    print("Generating comparison plots...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Fire rates comparison
    ax1.plot(fire_rates_1, alpha=0.5, label='Homeostasis (Baseline)', color='blue')
    ax1.plot(fire_rates_2, alpha=0.5, label='Meta-Homeostasis (Old/Buggy)', color='red')
    ax1.plot(fire_rates_3, alpha=0.5, label='Meta-Homeostasis (Fixed)', color='green')
    ax1.axhline(y=0.02, color='black', linestyle='--', label='Target', linewidth=2)
    ax1.set_title('Fire Rate Comparison', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Fire Rate')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Threshold comparison
    ax2.plot(thresholds_1, alpha=0.5, label='Homeostasis', color='blue')
    ax2.plot(thresholds_2, alpha=0.5, label='Meta (Old)', color='red')
    ax2.plot(thresholds_3, alpha=0.5, label='Meta (Fixed)', color='green')
    ax2.set_title('Threshold Comparison (Neuron 0)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Threshold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Integral comparison (chỉ meta versions)
    ax3.plot(integrals_2, alpha=0.7, label='Meta (Old) - NO LIMIT', color='red')
    ax3.plot(integrals_3, alpha=0.7, label='Meta (Fixed) - WITH ANTI-WINDUP', color='green')
    ax3.axhline(y=5.0, color='orange', linestyle='--', label='Upper Limit', linewidth=2)
    ax3.axhline(y=-5.0, color='orange', linestyle='--', label='Lower Limit', linewidth=2)
    ax3.set_title('Integral Term Comparison', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Time (ms)')
    ax3.set_ylabel('Integral Value')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Statistics
    stats_text = f"""
    STATISTICS (Last 2000 steps):
    
    Homeostasis (Baseline):
    - Mean Fire Rate: {np.mean(fire_rates_1[3000:]):.4f}
    - Std Fire Rate: {np.std(fire_rates_1[3000:]):.4f}
    - Max Fire Rate: {np.max(fire_rates_1[3000:]):.4f}
    
    Meta-Homeostasis (Old):
    - Mean Fire Rate: {np.mean(fire_rates_2[3000:]):.4f}
    - Std Fire Rate: {np.std(fire_rates_2[3000:]):.4f}
    - Max Fire Rate: {np.max(fire_rates_2[3000:]):.4f}
    - Max Integral: {np.max(np.abs(integrals_2)):.2f}
    
    Meta-Homeostasis (Fixed):
    - Mean Fire Rate: {np.mean(fire_rates_3[3000:]):.4f}
    - Std Fire Rate: {np.std(fire_rates_3[3000:]):.4f}
    - Max Fire Rate: {np.max(fire_rates_3[3000:]):.4f}
    - Max Integral: {np.max(np.abs(integrals_3)):.2f}
    """
    
    ax4.text(0.1, 0.5, stats_text, fontsize=10, family='monospace',
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax4.axis('off')
    ax4.set_title('Statistics', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('results/meta_homeostasis_comparison.png', dpi=150)
    print("Results saved to results/meta_homeostasis_comparison.png")
    plt.show()
    
    # ===== Validation =====
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS:")
    print("=" * 60)
    
    # Check 1: Integral bounded
    max_integral_old = np.max(np.abs(integrals_2))
    max_integral_fixed = np.max(np.abs(integrals_3))
    
    print(f"\n1. Integral Windup Check:")
    print(f"   Old version: Max integral = {max_integral_old:.2f}")
    if max_integral_old > 10.0:
        print(f"   ❌ WINDUP DETECTED!")
    else:
        print(f"   ✅ Bounded")
    
    print(f"   Fixed version: Max integral = {max_integral_fixed:.2f}")
    if max_integral_fixed <= 5.0:
        print(f"   ✅ ANTI-WINDUP WORKING!")
    else:
        print(f"   ⚠️ Integral exceeded limit")
    
    # Check 2: Oscillation
    std_old = np.std(fire_rates_2[3000:])
    std_fixed = np.std(fire_rates_3[3000:])
    std_baseline = np.std(fire_rates_1[3000:])
    
    print(f"\n2. Oscillation Check (Std of fire rate, last 2000 steps):")
    print(f"   Baseline: {std_baseline:.4f}")
    print(f"   Old version: {std_old:.4f}")
    if std_old > 0.05:
        print(f"   ❌ OSCILLATION DETECTED!")
    else:
        print(f"   ✅ Stable")
    
    print(f"   Fixed version: {std_fixed:.4f}")
    if std_fixed < 0.02:
        print(f"   ✅ STABLE!")
    elif std_fixed < std_old:
        print(f"   ⚠️ Better than old, but not perfect")
    else:
        print(f"   ❌ Still oscillating")
    
    # Check 3: Performance
    mean_fire_baseline = np.mean(fire_rates_1[3000:])
    mean_fire_fixed = np.mean(fire_rates_3[3000:])
    target = 0.02
    
    error_baseline = abs(mean_fire_baseline - target)
    error_fixed = abs(mean_fire_fixed - target)
    
    print(f"\n3. Performance Check (Mean fire rate vs target 0.02):")
    print(f"   Baseline error: {error_baseline:.4f}")
    print(f"   Fixed error: {error_fixed:.4f}")
    if error_fixed < error_baseline:
        print(f"   ✅ BETTER THAN BASELINE!")
    elif error_fixed < 0.005:
        print(f"   ✅ GOOD ENOUGH!")
    else:
        print(f"   ⚠️ Not better than baseline")
    
    print("\n" + "=" * 60)
    
    return {
        'baseline': fire_rates_1,
        'old': fire_rates_2,
        'fixed': fire_rates_3
    }


if __name__ == '__main__':
    results = run_comparison_test()
    print("\nTest complete!")
