"""
SNN Imagination Processes (Theus Framework)
============================================
Theus-compatible wrappers for imagination/dream learning processes.

Author: Do Huy Hoang
Date: 2026-05-04
"""
import numpy as np
from theus.contracts import process
from src.core.snn_context_theus import SNNSystemContext


@process(
    inputs=['domain_ctx'],
    outputs=['domain_ctx'],
    side_effects=[]
)
def process_imagination_loop(ctx: SNNSystemContext):
    """
    Quy trình Tưởng tượng (chạy trong chế độ Offline).

    Cơ chế:
    1. Tách rời sensor input (Sleep paralysis)
    2. Tự sinh spike từ ký ức (Replay)
    3. Quan sát kết quả cảm xúc
    4. Tạo Reflex Policy (Preemptive Inhibition/Boost)
    """
    # Resolve context (standalone SNN or nested in RL ctx)
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context

    domain = snn_ctx.domain_ctx

    # Chỉ chạy theo chu kỳ
    dream_interval = getattr(snn_ctx.global_ctx, 'dream_interval', 500)
    if domain.current_time % dream_interval != 0:
        return {}

    if not domain.neurons:
        return {}

    # Chọn ngẫu nhiên một neuron để "replay"
    seed_neuron_id = np.random.randint(0, len(domain.neurons))

    # Bơm vào spike queue
    next_time = domain.current_time + 1
    spike_queue = dict(domain.spike_queue)
    if next_time not in spike_queue:
        spike_queue[next_time] = []
    spike_queue[next_time].append(seed_neuron_id)

    new_metrics = dict(domain.metrics)
    new_metrics['imagination_count'] = new_metrics.get('imagination_count', 0) + 1

    # Direct mutation
    domain.spike_queue = spike_queue
    domain.metrics = new_metrics
    domain.fantasy_count = domain.fantasy_count + 1

    return {
        'spike_queue': spike_queue,
        'metrics': new_metrics,
        'fantasy_count': domain.fantasy_count
    }


@process(
    inputs=['domain_ctx'],
    outputs=['domain_ctx'],
    side_effects=[]
)
def process_dream_learning(ctx: SNNSystemContext):
    """
    Học từ kết quả tưởng tượng.

    Heuristic:
    - Nếu fire rate quá cao (>2%) → Nightmare (stress/overload)
    - Nếu fire rate quá thấp (<1%) → Boredom (underload)
    """
    # Resolve context
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context

    domain = snn_ctx.domain_ctx

    dream_interval = getattr(snn_ctx.global_ctx, 'dream_interval', 500)
    if domain.current_time % dream_interval != 0:
        return {}

    current_fire_rate = domain.metrics.get('fire_rate', 0.0)
    new_metrics = dict(domain.metrics)

    nightmare_count = domain.nightmare_count
    fantasy_count = domain.fantasy_count

    if current_fire_rate > 0.02:
        # Nightmare: raise thresholds
        for neuron in domain.neurons:
            neuron.threshold = min(neuron.threshold + 0.05, 3.0)
        nightmare_count += 1
        new_metrics['nightmare_count'] = nightmare_count
        new_metrics['dream_type'] = 'nightmare'
    elif 0.01 < current_fire_rate < 0.02:
        # Pleasant dream
        fantasy_count += 1
        new_metrics['fantasy_count'] = fantasy_count

    # Direct mutation
    domain.nightmare_count = nightmare_count
    domain.fantasy_count = fantasy_count
    domain.metrics = new_metrics

    return {
        'metrics': new_metrics,
        'nightmare_count': nightmare_count,
        'fantasy_count': fantasy_count
    }
