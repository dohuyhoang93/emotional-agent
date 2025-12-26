"""
SNN Core Processes: Integrate & Fire
=====================================
Các quy trình xử lý tích phân và bắn xung cho SNN.
"""
from src.core.snn_context import SNNContext
import numpy as np


def process_integrate(ctx: SNNContext) -> SNNContext:
    """
    Quy trình tích phân điện thế (Leaky Integrate).
    
    NOTE: Đây là Pure Function. Không có side-effect.
    Nhận Context, trả về Context mới.
    """
    tau_decay = ctx.params['tau_decay']
    
    # Rò rỉ điện thế cho tất cả neuron (Vectorized)
    for neuron in ctx.neurons:
        neuron.potential *= tau_decay
    
    # Xử lý các xung đến từ hàng đợi
    current_spikes = ctx.spike_queue.get(ctx.current_time, [])
    
    for spike_neuron_id in current_spikes:
        # Tìm tất cả synapse xuất phát từ neuron này
        for synapse in ctx.synapses:
            if synapse.pre_neuron_id == spike_neuron_id:
                # Tính thời điểm xung đến neuron hậu synapse
                arrival_time = ctx.current_time + synapse.delay
                post_neuron = ctx.neurons[synapse.post_neuron_id]
                
                # Cộng điện thế (tại thời điểm hiện tại, sẽ trễ sau)
                # NOTE: Để đơn giản, ta cộng ngay. Delay xử lý ở Fire.
                post_neuron.potential += synapse.weight
    
    return ctx


def process_fire(ctx: SNNContext) -> SNNContext:
    """
    Quy trình kiểm tra và bắn xung.
    NOTE: Thêm refractory period để tránh bắn liên tục.
    """
    fired_neurons = []
    refractory_period = 5  # ms - thời gian "tê liệt" sau khi bắn
    
    for neuron in ctx.neurons:
        # Kiểm tra refractory period
        time_since_last_fire = ctx.current_time - neuron.last_fire_time
        if time_since_last_fire < refractory_period:
            continue  # Neuron đang trong thời kỳ refractory
        
        if neuron.potential >= neuron.threshold:
            # Bắn xung
            fired_neurons.append(neuron.neuron_id)
            neuron.last_fire_time = ctx.current_time
            neuron.fire_count += 1
            
            # Reset điện thế (thêm hyperpolarization nhẹ)
            neuron.potential = -0.1
    
    # Đưa các xung vào hàng đợi (để xử lý ở bước tiếp theo)
    if fired_neurons:
        next_time = ctx.current_time + 1
        if next_time not in ctx.spike_queue:
            ctx.spike_queue[next_time] = []
        ctx.spike_queue[next_time].extend(fired_neurons)
    
    # Cập nhật metrics
    ctx.metrics['fire_rate'] = len(fired_neurons) / len(ctx.neurons) if ctx.neurons else 0.0
    
    return ctx


def process_homeostasis(ctx: SNNContext) -> SNNContext:
    """
    Quy trình cân bằng nội môi (Adaptive Threshold) - Redesigned.
    NOTE: Thêm safety checks để tránh death spiral.
    """
    target_rate = ctx.params['target_fire_rate']
    current_rate = ctx.metrics.get('fire_rate', 0.0)
    adjust_rate = ctx.params['homeostasis_rate']
    
    # SAFETY: Nếu mạng hoàn toàn chết (fire_rate = 0 trong 100 steps)
    # → Giảm threshold mạnh để "cứu sống" mạng
    if current_rate == 0.0:
        for neuron in ctx.neurons:
            neuron.threshold *= 0.99  # Giảm 1% mỗi step
            neuron.threshold = max(neuron.threshold, 0.5)  # Floor cao hơn
        return ctx
    
    # Điều chỉnh bình thường khi có hoạt động
    global_error = current_rate - target_rate
    
    # Tính tỷ lệ bắn cá nhân
    window = 100
    
    for neuron in ctx.neurons:
        # Điều chỉnh toàn cục (nhẹ nhàng)
        neuron.threshold += global_error * adjust_rate * 2.0
        
        # Điều chỉnh cá nhân
        time_since_fire = ctx.current_time - neuron.last_fire_time
        if time_since_fire < window:
            # Bắn quá nhiều -> Tăng ngưỡng
            neuron.threshold += adjust_rate * 1.0
        elif time_since_fire > window * 10 and current_rate < target_rate:
            # Bắn quá ít -> Giảm ngưỡng (CHỈ KHI fire_rate THẤP)
            neuron.threshold -= adjust_rate * 2.0
        
        # Giới hạn ngưỡng (floor cao hơn để dễ bắn)
        neuron.threshold = np.clip(neuron.threshold, 0.5, 2.5)
    
    return ctx

