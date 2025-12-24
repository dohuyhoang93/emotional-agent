"""
Periodic Resync: Fix Drift from Lazy Leak
==========================================
Tính toán lại chính xác trạng thái mạng định kỳ để triệt tiêu sai số.
"""
from src.core.snn_context import SNNContext
import numpy as np


def process_periodic_resync(ctx: SNNContext) -> SNNContext:
    """
    Quy trình đồng bộ định kỳ (mỗi 1000ms).
    Tính toán lại chính xác điện thế cho tất cả neuron.
    
    NOTE: Đây là "Exact Update" thay vì "Lazy Leak".
    """
    resync_interval = 1000  # ms
    
    # Chỉ chạy khi đến chu kỳ đồng bộ
    if ctx.current_time % resync_interval != 0:
        return ctx
    
    tau_decay = ctx.params['tau_decay']
    
    # Tính toán chính xác cho từng neuron
    for neuron in ctx.neurons:
        time_since_update = ctx.current_time - neuron.last_fire_time
        
        # Exact exponential decay
        decay_factor = tau_decay ** time_since_update
        
        # Reset về giá trị chính xác
        # NOTE: Giả định potential đã được set = 0 khi bắn
        # Nếu neuron không bắn, potential sẽ decay về 0
        if time_since_update > 0:
            neuron.potential *= decay_factor
            neuron.potential_vector *= decay_factor
    
    # Ghi log
    ctx.metrics['last_resync_time'] = ctx.current_time
    ctx.metrics['resync_count'] = ctx.metrics.get('resync_count', 0) + 1
    
    return ctx
