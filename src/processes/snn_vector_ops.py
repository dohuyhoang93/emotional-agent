"""
SNN Vector Operations: Cosine Similarity & Clustering
======================================================
Các quy trình xử lý Vector Spike.
"""
from src.core.snn_context import SNNContext
import numpy as np


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Tính độ tương đồng Cosine giữa 2 vector.
    
    Returns:
        Giá trị trong khoảng [-1, 1]. 1 = giống hệt, -1 = ngược hướng.
    """
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return np.dot(vec_a, vec_b) / (norm_a * norm_b)


def process_integrate_vector(ctx: SNNContext) -> SNNContext:
    """
    Quy trình tích phân Vector Spike.
    NOTE: Thay thế process_integrate cho Phase 2.
    """
    tau_decay = ctx.params['tau_decay']
    
    # Rò rỉ điện thế (cả scalar và vector)
    for neuron in ctx.neurons:
        neuron.potential *= tau_decay
        neuron.potential_vector *= tau_decay
    
    # Xử lý các xung đến từ hàng đợi
    current_spikes = ctx.spike_queue.get(ctx.current_time, [])
    
    for spike_neuron_id in current_spikes:
        spike_neuron = ctx.neurons[spike_neuron_id]
        
        # Tìm tất cả synapse xuất phát từ neuron này
        for synapse in ctx.synapses:
            if synapse.pre_neuron_id == spike_neuron_id:
                post_neuron = ctx.neurons[synapse.post_neuron_id]
                
                # Tính độ tương đồng giữa Vector xung và Prototype của neuron hậu
                similarity = cosine_similarity(
                    spike_neuron.prototype_vector,
                    post_neuron.prototype_vector
                )
                
                # Trọng số hiệu quả = trọng số synapse * độ tương đồng
                effective_weight = synapse.weight * max(0, similarity)  # ReLU
                
                # Cộng điện thế scalar
                post_neuron.potential += effective_weight
                
                # Cộng điện thế vector (weighted sum)
                post_neuron.potential_vector += effective_weight * spike_neuron.prototype_vector
    
    return ctx


def process_fire_vector(ctx: SNNContext) -> SNNContext:
    """
    Quy trình bắn xung Vector.
    NOTE: Khi neuron bắn, nó phát ra Prototype Vector của nó.
    """
    fired_neurons = []
    refractory_period = 5  # ms
    
    for neuron in ctx.neurons:
        # Kiểm tra refractory period
        time_since_last_fire = ctx.current_time - neuron.last_fire_time
        if time_since_last_fire < refractory_period:
            continue
        
        # Điều kiện bắn: Điện thế scalar vượt ngưỡng
        if neuron.potential >= neuron.threshold:
            fired_neurons.append(neuron.neuron_id)
            neuron.last_fire_time = ctx.current_time
            neuron.fire_count += 1
            
            # Reset điện thế
            neuron.potential = -0.1
            neuron.potential_vector = np.zeros(neuron.vector_dim)
    
    # Đưa các xung vào hàng đợi
    if fired_neurons:
        next_time = ctx.current_time + 1
        if next_time not in ctx.spike_queue:
            ctx.spike_queue[next_time] = []
        ctx.spike_queue[next_time].extend(fired_neurons)
    
    # Cập nhật metrics
    ctx.metrics['fire_rate'] = len(fired_neurons) / len(ctx.neurons) if ctx.neurons else 0.0
    
    return ctx


def process_clustering(ctx: SNNContext) -> SNNContext:
    """
    Quy trình học Không gian (Unsupervised Clustering).
    Xoay Prototype Vector về phía các input thường gặp.
    NOTE: Học khi NHẬN input, không phải khi bắn.
    """
    learning_rate = ctx.params.get('clustering_rate', 0.001)
    
    # Học cho tất cả neuron đang nhận input
    current_spikes = ctx.spike_queue.get(ctx.current_time, [])
    
    if not current_spikes:
        return ctx
    
    # Với mỗi xung đến, cập nhật prototype của các neuron hậu synapse
    for spike_id in current_spikes:
        spike_neuron = ctx.neurons[spike_id]
        spike_vector = spike_neuron.prototype_vector
        
        # Tìm tất cả neuron nhận xung từ spike_neuron
        for synapse in ctx.synapses:
            if synapse.pre_neuron_id == spike_id:
                post_neuron = ctx.neurons[synapse.post_neuron_id]
                
                # Xoay Prototype của post_neuron về phía spike_vector
                # (Hebbian: "Neurons that fire together, wire together")
                direction = spike_vector - post_neuron.prototype_vector
                post_neuron.prototype_vector += learning_rate * direction
                
                # Normalize để giữ độ dài = 1
                norm = np.linalg.norm(post_neuron.prototype_vector)
                if norm > 0:
                    post_neuron.prototype_vector /= norm
    
    return ctx
