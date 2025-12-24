"""
Phase 2 Experiment: Vector Upgrade Validation
==============================================
Thử nghiệm để xác thực Vector Spike và Clustering.
Mục tiêu: Chứng minh neuron học được các mẫu hình vector.
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
from src.engine.workflow_engine import WorkflowEngine
import matplotlib.pyplot as plt
import numpy as np


def inject_pattern_spike(ctx, neuron_ids, pattern_vector):
    """
    Bơm một mẫu vector vào một nhóm neuron.
    """
    for nid in neuron_ids:
        neuron = ctx.neurons[nid]
        # Normalize pattern
        normalized = pattern_vector / (np.linalg.norm(pattern_vector) + 1e-8)
        
        # Bơm mạnh để vượt ngưỡng
        neuron.potential_vector = normalized * 2.0  # Amplify
        neuron.potential = 2.0  # Đủ để vượt threshold = 1.0
        
        # Cập nhật prototype luôn để có baseline
        neuron.prototype_vector = normalized


def run_experiment(num_neurons=100, num_steps=2000):
    """
    Chạy thử nghiệm Vector SNN.
    """
    # Tạo SNN Context
    ctx = create_snn_context(num_neurons=num_neurons, connectivity=0.1)
    
    # Cập nhật params
    ctx.params['clustering_rate'] = 0.01
    
    # Tạo Workflow Engine
    engine = WorkflowEngine()
    engine.register('integrate', process_integrate_vector)
    engine.register('fire', process_fire_vector)
    engine.register('clustering', process_clustering)
    engine.register('stdp', process_stdp_basic)
    engine.register('homeostasis', process_homeostasis)
    
    # Định nghĩa workflow (thêm clustering)
    workflow = ['integrate', 'fire', 'clustering', 'stdp', 'homeostasis']
    
    # Định nghĩa 2 mẫu vector khác nhau
    pattern_A = np.array([1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    pattern_B = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0], dtype=float)
    
    # Normalize
    pattern_A /= np.linalg.norm(pattern_A)
    pattern_B /= np.linalg.norm(pattern_B)
    
    # Metrics tracking
    fire_rates = []
    similarities_A = []  # Độ tương đồng trung bình với Pattern A
    similarities_B = []  # Độ tương đồng trung bình với Pattern B
    
    print(f"Starting Vector SNN simulation: {num_neurons} neurons, {num_steps} steps")
    print(f"Pattern A: {pattern_A[:8]}...")
    print(f"Pattern B: {pattern_B[8:]}...")
    
    for step in range(num_steps):
        # Bơm mẫu vào mạng (luân phiên)
        if step % 100 == 0:
            if (step // 100) % 2 == 0:
                inject_pattern_spike(ctx, [0, 1, 2], pattern_A)
            else:
                inject_pattern_spike(ctx, [0, 1, 2], pattern_B)
        
        ctx = engine.run_timestep(workflow, ctx)
        
        # Ghi lại metrics
        fire_rates.append(ctx.metrics.get('fire_rate', 0.0))
        
        # Tính độ tương đồng trung bình của các neuron với 2 pattern
        sim_A = np.mean([
            np.dot(n.prototype_vector, pattern_A) 
            for n in ctx.neurons[:20]  # Chỉ lấy 20 neuron đầu
        ])
        sim_B = np.mean([
            np.dot(n.prototype_vector, pattern_B) 
            for n in ctx.neurons[:20]
        ])
        
        similarities_A.append(sim_A)
        similarities_B.append(sim_B)
        
        if step % 200 == 0:
            print(f"Step {step}: Fire Rate = {fire_rates[-1]:.4f}, Sim_A = {sim_A:.3f}, Sim_B = {sim_B:.3f}")
    
    # Vẽ biểu đồ
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    ax1.plot(fire_rates, alpha=0.7)
    ax1.axhline(y=ctx.params['target_fire_rate'], color='r', linestyle='--', label='Target')
    ax1.set_title('Firing Rate over Time (Vector SNN)')
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Firing Rate')
    ax1.legend()
    ax1.grid(True)
    
    ax2.plot(similarities_A, label='Similarity to Pattern A', alpha=0.7)
    ax2.plot(similarities_B, label='Similarity to Pattern B', alpha=0.7)
    ax2.set_title('Prototype Learning: Convergence to Input Patterns')
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Cosine Similarity')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('results/phase2_vector_upgrade.png')
    print("\nResults saved to results/phase2_vector_upgrade.png")
    plt.show()
    
    return ctx


if __name__ == '__main__':
    run_experiment()
