"""
Phase 1 Experiment: Scalar Core Validation
===========================================
Thử nghiệm để xác thực SNN Scalar Core.
Mục tiêu: Chứng minh mạng tự cân bằng và học được.
"""
import sys
sys.path.append('.')

from src.core.snn_context import create_snn_context
from src.processes.snn_integrate_fire import (
    process_integrate, 
    process_fire, 
    process_homeostasis
)
from src.processes.snn_learning import process_stdp_basic
from src.engine.workflow_engine import WorkflowEngine
import matplotlib.pyplot as plt


def run_experiment(num_neurons=100, num_steps=1000):
    """
    Chạy thử nghiệm SNN Scalar Core.
    """
    # Tạo SNN Context
    ctx = create_snn_context(num_neurons=num_neurons, connectivity=0.1)
    
    # Tạo Workflow Engine
    engine = WorkflowEngine()
    engine.register('integrate', process_integrate)
    engine.register('fire', process_fire)
    engine.register('homeostasis', process_homeostasis)
    engine.register('stdp', process_stdp_basic)
    
    # Định nghĩa workflow
    workflow = ['integrate', 'fire', 'stdp', 'homeostasis']
    
    # Kích thích ban đầu (bơm xung vào một số neuron)
    ctx.spike_queue[0] = [0, 1, 2, 3, 4]  # 5 neuron đầu bắn
    
    # Metrics tracking
    fire_rates = []
    avg_weights = []
    
    # Chạy mô phỏng
    print(f"Starting simulation: {num_neurons} neurons, {num_steps} steps")
    for step in range(num_steps):
        ctx = engine.run_timestep(workflow, ctx)
        
        # Ghi lại metrics
        fire_rates.append(ctx.metrics.get('fire_rate', 0.0))
        avg_weight = sum(s.weight for s in ctx.synapses) / len(ctx.synapses)
        avg_weights.append(avg_weight)
        
        if step % 100 == 0:
            print(f"Step {step}: Fire Rate = {fire_rates[-1]:.4f}, Avg Weight = {avg_weight:.4f}")
    
    # Vẽ biểu đồ
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    ax1.plot(fire_rates)
    ax1.axhline(y=ctx.params['target_fire_rate'], color='r', linestyle='--', label='Target')
    ax1.set_title('Firing Rate over Time')
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Firing Rate')
    ax1.legend()
    ax1.grid(True)
    
    ax2.plot(avg_weights)
    ax2.set_title('Average Synapse Weight over Time')
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Weight')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('results/phase1_scalar_core.png')
    print("Results saved to results/phase1_scalar_core.png")
    plt.show()
    
    return ctx


if __name__ == '__main__':
    run_experiment()
