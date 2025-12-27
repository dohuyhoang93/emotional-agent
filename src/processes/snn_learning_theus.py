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
    inputs=['domain.snn_context'],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def process_clustering(ctx):
    """
    Quy trình học không gian (Unsupervised Clustering). Wraps _clustering_impl.
    """
    _clustering_impl(ctx)

def _clustering_impl(ctx):
    """Internal clustering implementation."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return
    
    learning_rate = 0.001  # Default clustering rate
    
    current_spikes = snn_ctx.domain_ctx.spike_queue.get(snn_ctx.domain_ctx.current_time, [])
    
    if not current_spikes:
        return  # Không có spike, skip
    
    # Với mỗi xung đến, cập nhật prototype của neurons hậu synapse
    for spike_id in current_spikes:
        if spike_id >= len(snn_ctx.domain_ctx.neurons):
            continue
        
        spike_neuron = snn_ctx.domain_ctx.neurons[spike_id]
        spike_vector = spike_neuron.prototype_vector
        
        # Tìm tất cả neurons nhận xung từ spike_neuron
        for synapse in snn_ctx.domain_ctx.synapses:
            if synapse.pre_neuron_id != spike_id:
                continue
            
            if synapse.post_neuron_id >= len(snn_ctx.domain_ctx.neurons):
                continue
            
            post_neuron = snn_ctx.domain_ctx.neurons[synapse.post_neuron_id]
            
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
    inputs=['domain.snn_context'],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def process_stdp(ctx):
    """
    Quy trình STDP (Spike-Timing-Dependent Plasticity). Wraps _stdp_impl.
    """
    _stdp_impl(ctx)

def _stdp_impl(ctx):
    """Internal STDP implementation."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return
    
    learning_rate = 0.01  # Default learning rate
    tau_trace = 0.9  # Default trace decay
    weight_decay = 0.9999  # Default weight decay
    time_window = 20  # STDP time window (ms)
    
    # 1. Weight decay (tránh runaway)
    for synapse in snn_ctx.domain_ctx.synapses:
        synapse.weight *= weight_decay
    
    # 2. Trace decay
    for synapse in snn_ctx.domain_ctx.synapses:
        synapse.trace *= tau_trace
    
    # 3. Cập nhật trace và weight
    current_spikes = snn_ctx.domain_ctx.spike_queue.get(snn_ctx.domain_ctx.current_time, [])
    
    if not current_spikes:
        return  # Không có spike, skip
    
    for spike_id in current_spikes:
        # Tìm tất cả synapses liên quan đến spike này
        for synapse in snn_ctx.domain_ctx.synapses:
            # === PRE NEURON BẮN ===
            if synapse.pre_neuron_id == spike_id:
                # Đánh dấu trace
                synapse.trace += 1.0
                
                # Kiểm tra Post neuron có bắn gần đây không
                if synapse.post_neuron_id < len(snn_ctx.domain_ctx.neurons):
                    post_neuron = snn_ctx.domain_ctx.neurons[synapse.post_neuron_id]
                    time_diff = snn_ctx.domain_ctx.current_time - post_neuron.last_fire_time
                    
                    if 0 < time_diff < time_window:
                        # LTP: Pre → Post (Causal)
                        synapse.weight += learning_rate * synapse.trace
                        synapse.weight = min(synapse.weight, 1.0)  # Cap tại 1.0
            
            # === POST NEURON BẮN ===
            if synapse.post_neuron_id == spike_id:
                # Kiểm tra Pre neuron có bắn gần đây không
                if synapse.pre_neuron_id < len(snn_ctx.domain_ctx.neurons):
                    pre_neuron = snn_ctx.domain_ctx.neurons[synapse.pre_neuron_id]
                    time_diff = snn_ctx.domain_ctx.current_time - pre_neuron.last_fire_time
                    
                    if 0 < time_diff < time_window:
                        # LTD: Post → Pre (Anti-causal)
                        synapse.weight -= learning_rate * 0.5
                        synapse.weight = max(synapse.weight, 0.0)  # Không âm

