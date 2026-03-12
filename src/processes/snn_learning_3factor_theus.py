"""
SNN 3-Factor Learning Processes for Theus Framework
====================================================
Synaptic Tagging với 3-factor learning rule (Hebbian × Dopamine).

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus.contracts import process
from src.core.snn_context_theus import (
    COMMIT_STATE_SOLID,
    COMMIT_STATE_REVOKED,
    ensure_heavy_tensors_initialized
)
from src.core.context import SystemContext


@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context', 
        'domain_ctx.td_error',
        'domain_ctx.snn_context.domain_ctx.synapses' 
    ],
    outputs=[],
    side_effects=[]
)
def process_stdp_3factor(ctx: SystemContext):
    """
    3-Factor Learning: Hebbian + Dopamine với Protected Learning. Wraps _stdp_3factor_impl.
    """
    try:
        _stdp_3factor_impl(ctx)
    except Exception:
        import traceback
        print(f"CRASH in process_stdp_3factor: {traceback.format_exc()}")
        raise
    return {}

def _stdp_3factor_impl(ctx: SystemContext):
    """Internal 3-factor learning implementation."""
    rl_ctx = ctx
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Dopamine signal từ TD-error
    try:
        td_error = float(rl_ctx.domain_ctx.td_error)
    except Exception:
        td_error = 0.0
    dopamine = float(np.tanh(td_error))
    
    # Fetch current spikes
    current_spikes = set(domain.spike_queue.get(domain.current_time, []))
    
    # NOTE: FAST PATH — skip toàn bộ khi không có spikes VÀ dopamine ~ 0.
    # Không có coincidence → Hebbian = 0. Không có dopamine → Δw = 0.
    # Trace decay vẫn cần nhưng được vectorize riêng ở cuối.
    no_learning = len(current_spikes) == 0 and abs(dopamine) < 1e-4
    
    tau_fast = float(global_ctx.tau_trace_fast)
    tau_slow = float(global_ctx.tau_trace_slow)
    w_decay  = float(global_ctx.weight_decay)
    
    ensure_heavy_tensors_initialized(snn_ctx)
    t = domain.heavy_tensors
    last_fire_times = t['last_fire_times']

    if no_learning:
        # NOTE: Vectorized trace decay — thay Python loop 74k objects bằng numpy.
        # Chỉ chạy khi có numpy trace arrays (xây dựng ở bước FULL PATH đầu tiên).
        # Nếu chưa có ('_fast_traces' chưa build), bỏ qua lần này — sẽ được tạo khi có spike.
        if '_fast_traces' in t:
            t['_fast_traces'] *= tau_fast
            t['_slow_traces'] *= tau_slow
        return

    # FULL PATH: có spikes hoặc dopamine đáng kể
    hebbian_window = 20.0
    
    # NOTE: XÂY DỰNG INDEX MAP lần đầu (lazy init, O(S) một lần).
    # _post_synapse_map[post_id] = list of synapse objects với post_neuron_id == post_id
    # Cho phép O(K×fan_in) thay vì O(S) toàn bộ khi K (số neurons fire) << N.
    if '_post_synapse_map' not in t:
        post_map = {}
        for syn in domain.synapses:
            pid = syn.post_neuron_id
            if pid not in post_map:
                post_map[pid] = []
            post_map[pid].append(syn)
        t['_post_synapse_map'] = post_map
        
        # Đồng thời build numpy trace arrays cùng kích thước synapse list
        S = len(domain.synapses)
        t['_fast_traces'] = np.array([s.trace_fast for s in domain.synapses], dtype=np.float32)
        t['_slow_traces'] = np.array([s.trace_slow for s in domain.synapses], dtype=np.float32)
    
    # Step 1: Vectorized trace decay cho toàn bộ synapses — O(S) numpy thay vì O(S) Python
    t['_fast_traces'] *= tau_fast
    t['_slow_traces'] *= tau_slow
    
    # Step 2: Hebbian update — CHỈ duyệt synapses của neurons bị fire
    # O(K × avg_fan_in) thay vì O(S) — K << N trong sparse firing regime
    cur_time = float(domain.current_time)
    post_map = t['_post_synapse_map']
    
    for post_id in current_spikes:
        for syn in post_map.get(post_id, []):
            pre_last_fire = float(last_fire_times[syn.pre_neuron_id])
            dt = cur_time - pre_last_fire
            if 0 < dt <= hebbian_window:
                syn.trace_fast += 1.0
                syn.trace_slow += 1.0
                syn.last_active_time = domain.current_time

    # Step 3: Weight update — FULLY VECTORIZED qua numpy
    # ∆w = η × eligibility × dopamine; eligibility = trace_fast + trace_slow
    fast = t['_fast_traces']
    slow = t['_slow_traces']
    eligibility = fast + slow  # (S,) vectorized
    
    # 3.1. Compute Learning Rates per synapse (vectorized)
    S = len(eligibility)
    syn_commit = t['syn_commit_states']
    
    # Base LR for all
    lrs = np.full(S, float(global_ctx.dopamine_learning_rate), dtype=np.float32)
    
    # Apply factors based on commitment
    mask_solid = (syn_commit == COMMIT_STATE_SOLID)
    lrs[mask_solid] *= float(global_ctx.solid_learning_rate_factor)
    
    # Mask out revoked
    mask_revoked = (syn_commit == COMMIT_STATE_REVOKED)
    lrs[mask_revoked] = 0.0
    
    # 3.2. Delta weight (S,)
    delta_w = lrs * eligibility * dopamine
    
    # 3.3. Update Weight Matrix (N,N) using Advanced Indexing — O(S) in C/Numpy
    pre_ids = t['syn_pre_ids']
    post_ids = t['syn_post_ids']
    weights = t['weights']
    
    weights[pre_ids, post_ids] += delta_w
    
    # 3.4. Global Weight Decay & Clipping (Vectorized N,N)
    weights *= w_decay
    np.clip(weights, 0.0, 1.0, out=weights)
    
    # NOTE: KHÔNG sync ngược lại objects tại đây. 
    # Việc sync sẽ được thực hiện 1 lần duy nhất ở snn_composite sau RL step.
    # Điều này giúp tiết kiệm 50-100ms mỗi tick.

