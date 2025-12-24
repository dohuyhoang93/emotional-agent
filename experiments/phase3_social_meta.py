"""
Phase 3 Experiment: Multi-Agent Social Learning
================================================
Thử nghiệm với nhiều agent học từ nhau qua Viral Synapses.
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
from src.processes.snn_social import (
    extract_top_synapses,
    inject_viral_synapses,
    process_sandbox_evaluation
)
from src.processes.snn_meta import process_meta_homeostasis
from src.engine.workflow_engine import WorkflowEngine
import matplotlib.pyplot as plt
import numpy as np


def inject_pattern_spike(ctx, neuron_ids, pattern_vector):
    """Bơm pattern vào neuron."""
    for nid in neuron_ids:
        neuron = ctx.neurons[nid]
        normalized = pattern_vector / (np.linalg.norm(pattern_vector) + 1e-8)
        neuron.potential_vector = normalized * 2.0
        neuron.potential = 2.0
        neuron.prototype_vector = normalized


def run_multi_agent_experiment(num_agents=3, num_neurons=50, num_steps=1000):
    """
    Chạy thử nghiệm Multi-Agent.
    """
    # Tạo quần thể agents
    agents = []
    for i in range(num_agents):
        ctx = create_snn_context(num_neurons=num_neurons, connectivity=0.15)
        ctx.agent_id = i
        agents.append(ctx)
    
    # Tạo Workflow Engine
    engine = WorkflowEngine()
    engine.register('integrate', process_integrate_vector)
    engine.register('fire', process_fire_vector)
    engine.register('clustering', process_clustering)
    engine.register('stdp', process_stdp_basic)
    engine.register('homeostasis', process_homeostasis)
    engine.register('sandbox_eval', process_sandbox_evaluation)
    engine.register('meta_homeostasis', process_meta_homeostasis)
    
    # Workflow (thêm social và meta)
    workflow = [
        'integrate', 'fire', 'clustering', 'stdp',
        'sandbox_eval', 'meta_homeostasis', 'homeostasis'
    ]
    
    # Định nghĩa patterns
    pattern_A = np.array([1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    pattern_B = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0], dtype=float)
    pattern_A /= np.linalg.norm(pattern_A)
    pattern_B /= np.linalg.norm(pattern_B)
    
    # Metrics tracking
    fire_rates = {i: [] for i in range(num_agents)}
    viral_transfers = []
    shadow_counts = []  # Track realtime
    
    print(f"Starting Multi-Agent simulation: {num_agents} agents, {num_neurons} neurons each")
    
    for step in range(num_steps):
        # Bơm pattern vào TẤT CẢ agents (liên tục để duy trì hoạt động)
        if step % 50 == 0:  # Tăng tần suất bơm
            # Agent 0 học Pattern A
            inject_pattern_spike(agents[0], [0, 1, 2], pattern_A)
            # Agent 1 học Pattern B
            if num_agents > 1:
                inject_pattern_spike(agents[1], [0, 1, 2], pattern_B)
            # Agent 2 học Pattern A (để có baseline)
            if num_agents > 2:
                inject_pattern_spike(agents[2], [0, 1, 2], pattern_A)
        
        # Chạy simulation cho từng agent
        for i, ctx in enumerate(agents):
            agents[i] = engine.run_timestep(workflow, ctx)
            fire_rates[i].append(agents[i].metrics.get('fire_rate', 0.0))  # FIX: Dùng agents[i]
        
        # Track shadow count realtime
        if step % 10 == 0:
            count = sum(1 for s in agents[1].synapses if s.synapse_type == "shadow")
            shadow_counts.append(count)
        
        # Social Learning: Trao đổi tri thức mỗi 200 steps
        if step > 0 and step % 200 == 0:
            # Agent 0 chia sẻ cho Agent 1
            if num_agents > 1:
                top_synapses = extract_top_synapses(agents[0], top_k=5)
                agents[1] = inject_viral_synapses(agents[1], top_synapses, source_agent_id=0)
                viral_transfers.append(step)
                print(f"Step {step}: Agent 0 shared {len(top_synapses)} synapses to Agent 1")
        
        if step % 200 == 0:
            print(f"Step {step}: Fire rates = {[f'{fire_rates[i][-1]:.3f}' for i in range(num_agents)]}")
    
    # Vẽ biểu đồ
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Fire rates
    for i in range(num_agents):
        ax1.plot(fire_rates[i], label=f'Agent {i}', alpha=0.7)
    ax1.axhline(y=agents[0].params['target_fire_rate'], color='r', linestyle='--', label='Target')
    ax1.set_title('Multi-Agent Fire Rates')
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Firing Rate')
    ax1.legend()
    ax1.grid(True)
    
    # Viral transfers
    for transfer_time in viral_transfers:
        ax1.axvline(x=transfer_time, color='green', alpha=0.3, linestyle=':')
    
    # Shadow synapse count (realtime)
    ax2.plot(range(0, num_steps, 10), shadow_counts, color='purple')
    ax2.set_title('Shadow Synapses in Agent 1 (Viral Knowledge)')
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Count')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('results/phase3_social_meta.png')
    print("\nResults saved to results/phase3_social_meta.png")
    plt.show()
    
    return agents


if __name__ == '__main__':
    run_multi_agent_experiment()
