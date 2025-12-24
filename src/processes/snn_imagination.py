"""
Imagination Loop: Dream Learning
=================================
Cơ chế tưởng tượng - SNN tự mô phỏng để học nhân quả.
"""
from src.core.snn_context import SNNContext
import numpy as np
from typing import List, Tuple


def process_imagination_loop(ctx: SNNContext) -> SNNContext:
    """
    Quy trình Tưởng tượng (chạy trong chế độ Offline).
    
    Cơ chế:
    1. Tách rời sensor input (Sleep paralysis)
    2. Tự sinh spike từ ký ức (Replay)
    3. Quan sát kết quả cảm xúc
    4. Tạo Reflex Policy (Preemptive Inhibition/Boost)
    """
    # Chỉ chạy khi ở chế độ Dream (mỗi 500ms)
    dream_interval = 500
    if ctx.current_time % dream_interval != 0:
        return ctx
    
    # Chọn ngẫu nhiên một neuron để "replay"
    if not ctx.neurons:
        return ctx
    
    seed_neuron_id = np.random.randint(0, len(ctx.neurons))
    seed_neuron = ctx.neurons[seed_neuron_id]
    
    # Tự sinh spike (hallucination)
    # NOTE: Sử dụng prototype_vector làm "ký ức"
    hallucinated_vector = seed_neuron.prototype_vector.copy()
    
    # Bơm vào spike queue (giả lập sensor input)
    next_time = ctx.current_time + 1
    if next_time not in ctx.spike_queue:
        ctx.spike_queue[next_time] = []
    ctx.spike_queue[next_time].append(seed_neuron_id)
    
    # Ghi log
    ctx.metrics['imagination_count'] = ctx.metrics.get('imagination_count', 0) + 1
    
    return ctx


def process_dream_learning(ctx: SNNContext) -> SNNContext:
    """
    Học từ kết quả tưởng tượng.
    
    Heuristic: 
    - Nếu fire rate quá cao (>2%) → Nightmare (stress/overload)
    - Nếu fire rate quá thấp (<1%) → Boredom (underload)
    """
    # Chỉ chạy sau imagination events
    if ctx.current_time % 500 != 0:
        return ctx
    
    current_fire_rate = ctx.metrics.get('fire_rate', 0.0)
    
    # DEBUG: Log fire rate
    if ctx.current_time % 500 == 0:
        print(f"[DREAM] Step {ctx.current_time}: fire_rate={current_fire_rate:.4f}, threshold=0.02")
    
    # Nightmare: Fire rate quá cao (giảm từ 10% xuống 2% để demo)
    if current_fire_rate > 0.02:  # >2% (giảm từ 0.10)
        print(f"[NIGHTMARE] Triggered! fire_rate={current_fire_rate:.4f}")
        
        # Tăng ngưỡng cho TẤT CẢ neurons để giảm fire rate (MẠNH HƠN)
        for neuron in ctx.neurons:
            neuron.threshold += 0.05  # Tăng từ 0.01 lên 0.05
            neuron.threshold = min(neuron.threshold, 3.0)
        
        ctx.metrics['nightmare_count'] = ctx.metrics.get('nightmare_count', 0) + 1
        ctx.social_signals['fear'] = 0.8  # Set fear signal
        print(f"[NIGHTMARE] Count now: {ctx.metrics['nightmare_count']}")
    
    # Pleasant dream: Fire rate ổn định
    elif 0.01 < current_fire_rate < 0.02:
        ctx.social_signals['fear'] = 0.1  # Low fear
    
    return ctx
