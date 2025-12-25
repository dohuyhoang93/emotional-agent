"""
SNN Learning Processes for Theus Framework
===========================================
Learning processes: Clustering & STDP với Theus @process decorator.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus import process
from src.core.snn_context_theus import SNNSystemContext


@process(
    inputs=[
        'domain_ctx.neurons',
        'domain_ctx.synapses',
        'domain_ctx.spike_queue',
        'domain_ctx.current_time',
        'global_ctx.clustering_rate'
    ],
    outputs=[
        'domain_ctx.neurons'  # prototype_vector updated
    ],
    side_effects=[]
)
def process_clustering(ctx: SNNSystemContext):
    """
    Quy trình học không gian (Unsupervised Clustering).
    
    Xoay prototype vector về phía input patterns.
    NOTE: Spatial learning - học "cái gì", không quan tâm "khi nào".
    
    Theus sẽ audit:
    - clustering_rate trong range [0.0001, 0.1]
    """
    domain = ctx.domain_ctx
    learning_rate = ctx.global_ctx.clustering_rate
    
    current_spikes = domain.spike_queue.get(domain.current_time, [])
    
    if not current_spikes:
        return  # Không có spike, skip
    
    # Với mỗi xung đến, cập nhật prototype của neurons hậu synapse
    for spike_id in current_spikes:
        if spike_id >= len(domain.neurons):
            continue
        
        spike_neuron = domain.neurons[spike_id]
        spike_vector = spike_neuron.prototype_vector
        
        # Tìm tất cả neurons nhận xung từ spike_neuron
        for synapse in domain.synapses:
            if synapse.pre_neuron_id != spike_id:
                continue
            
            if synapse.post_neuron_id >= len(domain.neurons):
                continue
            
            post_neuron = domain.neurons[synapse.post_neuron_id]
            
            # === HEBBIAN LEARNING CHO VECTOR ===
            # "Neurons that fire together, align their prototypes together"
            # Xoay prototype của post_neuron về phía spike_vector
            direction = spike_vector - post_neuron.prototype_vector
            post_neuron.prototype_vector += learning_rate * direction
            
            # Normalize để giữ độ dài = 1
            norm = np.linalg.norm(post_neuron.prototype_vector)
            if norm > 0:
                post_neuron.prototype_vector /= norm


@process(
    inputs=[
        'domain_ctx.synapses',
        'domain_ctx.neurons',
        'domain_ctx.spike_queue',
        'domain_ctx.current_time',
        'global_ctx.learning_rate',
        'global_ctx.tau_trace',
        'global_ctx.weight_decay'
    ],
    outputs=[
        'domain_ctx.synapses'  # weight, trace updated
    ],
    side_effects=[]
)
def process_stdp(ctx: SNNSystemContext):
    """
    Quy trình STDP (Spike-Timing-Dependent Plasticity).
    
    NOTE: Temporal learning - học "khi nào", không quan tâm "cái gì".
    
    Quy tắc:
    - Pre bắn TRƯỚC Post (trong 20ms) → Tăng weight (LTP)
    - Pre bắn SAU Post → Giảm weight (LTD)
    
    Theus sẽ audit:
    - learning_rate trong range [0.001, 0.5]
    - tau_trace trong range [0.5, 1.0]
    - weight_decay trong range [0.99, 1.0]
    """
    domain = ctx.domain_ctx
    learning_rate = ctx.global_ctx.learning_rate
    tau_trace = ctx.global_ctx.tau_trace
    weight_decay = ctx.global_ctx.weight_decay
    time_window = 20  # STDP time window (ms)
    
    # 1. Weight decay (tránh runaway)
    for synapse in domain.synapses:
        synapse.weight *= weight_decay
    
    # 2. Trace decay
    for synapse in domain.synapses:
        synapse.trace *= tau_trace
    
    # 3. Cập nhật trace và weight
    current_spikes = domain.spike_queue.get(domain.current_time, [])
    
    if not current_spikes:
        return  # Không có spike, skip
    
    for spike_id in current_spikes:
        # Tìm tất cả synapses liên quan đến spike này
        for synapse in domain.synapses:
            # === PRE NEURON BẮN ===
            if synapse.pre_neuron_id == spike_id:
                # Đánh dấu trace
                synapse.trace += 1.0
                
                # Kiểm tra Post neuron có bắn gần đây không
                if synapse.post_neuron_id < len(domain.neurons):
                    post_neuron = domain.neurons[synapse.post_neuron_id]
                    time_diff = domain.current_time - post_neuron.last_fire_time
                    
                    if 0 < time_diff < time_window:
                        # LTP: Pre → Post (Causal)
                        synapse.weight += learning_rate * synapse.trace
                        synapse.weight = min(synapse.weight, 1.0)  # Cap tại 1.0
            
            # === POST NEURON BẮN ===
            if synapse.post_neuron_id == spike_id:
                # Kiểm tra Pre neuron có bắn gần đây không
                if synapse.pre_neuron_id < len(domain.neurons):
                    pre_neuron = domain.neurons[synapse.pre_neuron_id]
                    time_diff = domain.current_time - pre_neuron.last_fire_time
                    
                    if 0 < time_diff < time_window:
                        # LTD: Post → Pre (Anti-causal)
                        synapse.weight -= learning_rate * 0.5
                        synapse.weight = max(synapse.weight, 0.0)  # Không âm
