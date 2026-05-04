"""
SNN Learning Processes: STDP
=============================
Quy trình học Hebbian cơ bản (STDP).
"""
from src.core.snn_context import SNNContext


def process_stdp_basic(ctx: SNNContext) -> SNNContext:
    """
    Spike-Timing-Dependent Plasticity (Phiên bản đơn giản).
    
    Quy tắc:
    - Nếu Pre bắn trước Post (trong cửa sổ thời gian) -> Tăng trọng số (LTP)
    - Nếu Post bắn trước Pre -> Giảm trọng số (LTD)
    - Weight decay: Giảm nhẹ tất cả weights để tránh runaway
    """
    learning_rate = ctx.params['learning_rate']
    tau_trace = ctx.params['tau_trace']
    time_window = 20  # Cửa sổ thời gian STDP (ms)
    weight_decay = 0.9999  # Decay factor (0.01% mỗi step)
    
    # WEIGHT DECAY: Giảm nhẹ tất cả weights để tránh runaway
    for synapse in ctx.synapses:
        synapse.weight *= weight_decay
    
    # Phân rã Trace
    for synapse in ctx.synapses:
        synapse.trace *= tau_trace
    
    # Cập nhật Trace cho các neuron vừa bắn
    current_spikes = ctx.spike_queue.get(ctx.current_time, [])
    
    for spike_id in current_spikes:
        # Tăng Trace cho tất cả synapse xuất phát từ neuron này
        for synapse in ctx.synapses:
            if synapse.pre_neuron_id == spike_id:
                synapse.trace += 1.0
                
                # Kiểm tra Post neuron có bắn gần đây không
                post_neuron = ctx.neurons[synapse.post_neuron_id]
                time_diff = ctx.current_time - post_neuron.last_fire_time
                
                if 0 < time_diff < time_window:
                    # LTP: Pre -> Post (Causal)
                    synapse.weight += learning_rate * synapse.trace
                    synapse.weight = min(synapse.weight, 1.0)  # Cap tại 1.0
            
            if synapse.post_neuron_id == spike_id:
                # Kiểm tra Pre neuron có bắn gần đây không
                pre_neuron = ctx.neurons[synapse.pre_neuron_id]
                time_diff = ctx.current_time - pre_neuron.last_fire_time
                
                if 0 < time_diff < time_window:
                    # LTD: Post -> Pre (Anti-causal)
                    synapse.weight -= learning_rate * 0.5
                    synapse.weight = max(synapse.weight, 0.0)  # Không âm
    
    return ctx

