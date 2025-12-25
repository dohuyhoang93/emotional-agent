"""
SNN Imagination Processes for Theus Framework
==============================================
Imagination & Dream Learning với Theus @process decorator.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus import process
from src.core.snn_context_theus import SNNSystemContext


@process(
    inputs=[
        'domain_ctx.neurons',
        'domain_ctx.current_time',
        'domain_ctx.last_imagination_time',
        'global_ctx.imagination_interval'
    ],
    outputs=[
        'domain_ctx.spike_queue',
        'domain_ctx.last_imagination_time',
        'domain_ctx.metrics'
    ],
    side_effects=[]  # Pure function - no external calls
)
def process_imagination_loop(ctx: SNNSystemContext):
    """
    Quy trình Tưởng tượng (Offline Learning).
    
    Cơ chế:
    1. Tách rời sensor input (Sleep paralysis)
    2. Tự sinh spike từ ký ức (Replay)
    3. Quan sát kết quả cảm xúc
    
    NOTE: Pure function - chỉ thay đổi SNN internal state.
    """
    domain = ctx.domain_ctx
    
    # Check interval
    time_since_last = domain.current_time - domain.last_imagination_time
    if time_since_last < ctx.global_ctx.imagination_interval:
        return  # Not time yet
    
    # Update last imagination time
    domain.last_imagination_time = domain.current_time
    
    # Chọn ngẫu nhiên một neuron để replay
    if not domain.neurons:
        return
    
    seed_neuron_id = np.random.randint(0, len(domain.neurons))
    seed_neuron = domain.neurons[seed_neuron_id]
    
    # Tự sinh spike (hallucination)
    # NOTE: Sử dụng prototype_vector làm "ký ức"
    hallucinated_vector = seed_neuron.prototype_vector.copy()
    
    # Bơm vào spike queue (giả lập sensor input)
    next_time = domain.current_time + 1
    if next_time not in domain.spike_queue:
        domain.spike_queue[next_time] = []
    domain.spike_queue[next_time].append(seed_neuron_id)
    
    # Update metrics
    domain.metrics['imagination_count'] = \
        domain.metrics.get('imagination_count', 0) + 1


@process(
    inputs=[
        'domain_ctx.neurons',
        'domain_ctx.metrics.fire_rate',
        'global_ctx.nightmare_threshold',
        'global_ctx.threshold_min',
        'global_ctx.threshold_max'
    ],
    outputs=[
        'domain_ctx.neurons',  # threshold adjusted
        'domain_ctx.nightmare_count',
        'domain_ctx.fantasy_count',
        'domain_ctx.metrics'
    ],
    side_effects=[]  # Pure function
)
def process_dream_learning(ctx: SNNSystemContext):
    """
    Học từ kết quả tưởng tượng.
    
    Heuristic:
    - Fire rate > threshold → Nightmare (stress/overload)
    - Fire rate < threshold/2 → Boredom (underload)
    - Normal range → Pleasant dream
    
    NOTE: Pure function - chỉ điều chỉnh thresholds.
    """
    domain = ctx.domain_ctx
    global_ctx = ctx.global_ctx
    
    current_fire_rate = domain.metrics.get('fire_rate', 0.0)
    nightmare_threshold = global_ctx.nightmare_threshold
    
    # Nightmare: Fire rate quá cao
    if current_fire_rate > nightmare_threshold:
        # Tăng threshold để giảm fire rate
        for neuron in domain.neurons:
            neuron.threshold += 0.05
            neuron.threshold = min(neuron.threshold, global_ctx.threshold_max)
        
        # Update counters
        domain.nightmare_count += 1
        domain.metrics['nightmare_triggered'] = 1
        domain.metrics['dream_type'] = 'nightmare'
    
    # Pleasant dream: Fire rate ổn định
    elif nightmare_threshold / 2 < current_fire_rate < nightmare_threshold:
        domain.fantasy_count += 1
        domain.metrics['nightmare_triggered'] = 0
        domain.metrics['dream_type'] = 'pleasant'
    
    # Boredom: Fire rate quá thấp
    else:
        # Giảm threshold để tăng fire rate
        for neuron in domain.neurons:
            neuron.threshold -= 0.02
            neuron.threshold = max(neuron.threshold, global_ctx.threshold_min)
        
        domain.metrics['nightmare_triggered'] = 0
        domain.metrics['dream_type'] = 'boredom'
