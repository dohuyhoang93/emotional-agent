"""
SNN Composite Process
=====================
Bundles the entire SNN sub-cycle into a single Theus Transaction.
Optimization for "Compute-Sync" strategy to avoid per-process overhead.

Author: Do Huy Hoang
Date: 2025-12-27
"""
from theus.contracts import process
from src.core.context import SystemContext
from src.core.snn_context_theus import ensure_heavy_tensors_initialized, sync_from_heavy_tensors
import numpy as np
import torch

# Import Internal Implementations

# Import Internal Implementations
from src.processes.snn_rl_bridge import _encode_state_to_spikes_impl, _encode_emotion_vector_impl
from src.processes.snn_core_theus import _integrate_impl, _fire_impl, _tick_impl
from src.processes.snn_learning_theus import _clustering_impl
from src.processes.snn_learning_3factor_theus import _stdp_3factor_impl
from src.processes.snn_advanced_features_theus import _hysteria_impl, _lateral_inhibition_vectorized

@process(
    inputs=['domain_ctx', 'domain', 
        'domain.snn_context',
        'domain.current_observation',
        'domain.td_error',
        'domain.last_action', # Needed if modulation is used (Wait, I forgot modulation?)
        # Composite requires union of all inputs
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.domain_ctx.spike_queue',
        'domain.snn_context.domain_ctx.current_time',
        'domain.snn_context.domain_ctx.emotion_saturation_level',
        'domain.snn_context.domain_ctx.dampening_active',
        # Global params
        'domain.snn_context.global_ctx'
    ],
    outputs=['domain', 'domain_ctx', 
        'domain.snn_context',
        'domain.heavy_snn_emotion_vector',
        'domain.heavy_previous_snn_emotion_vector',
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.domain_ctx.spike_queue',
        'domain.snn_context.domain_ctx.current_time',
        'domain.snn_context.domain_ctx.emotion_saturation_level',
        'domain.snn_context.domain_ctx.dampening_active'
    ],
    side_effects=[]
)
def process_snn_cycle(ctx: SystemContext):
    """
    Execute entire SNN Cycle in one transaction.
    
    Sequence:
    1. Pre-Processing (Object Mode): Hysteria, Encoding
    2. Core Loop (Tensor Mode): Integrate -> Lateral -> Fire
    3. Post-Processing (Object Mode): Learning, Readout, Tick
    """
    # 0. CONFIGURATION
    snn_ctx = ctx.domain_ctx.snn_context
    # Get ticks per step from config (default 10)
    ticks_per_step = getattr(snn_ctx.global_ctx, 'ticks_per_step', 10)
    
    # 1. PERCEPTION & PRE-PROCESSING (Object Mode)
    # Hysteria updates thresholds on objects
    _hysteria_impl(ctx) 
    
    # 2. CORE LOOP (Tensor Mode)
    # Sync Objects -> Tensors (Potentials, Thresholds, Weights)
    ensure_heavy_tensors_initialized(snn_ctx)
    from src.core.snn_context_theus import sync_to_heavy_tensors
    sync_to_heavy_tensors(snn_ctx)
    
    # --- TEMPORAL LOOP ---
    fire_delta = {}
    tick_delta = {}
    
    for _ in range(ticks_per_step):
        # Encode State updates potentials on objects/tensors 
        # (Already synced above, but _encode_state_to_spikes_impl still uses objects mostly)
        # REFACTOR: We want constant input across all ticks
        _encode_state_to_spikes_impl(ctx)
        
        # Integrate (Updates Potentials Tensor)
        _integrate_impl(ctx, sync=False)
        
        # Lateral Inhibition (Updates Potentials Tensor)
        if snn_ctx.global_ctx.use_lateral_inhibition:
            _lateral_inhibition_vectorized(ctx)
        
        # Fire (Updates Potentials Tensor, LastFire Tensor, FireCount Object, SpikeQueue Object[MUTATION])
        _fire_delta = _fire_impl(ctx, sync=False)
        if _fire_delta: 
            fire_delta.update(_fire_delta)
        
        # 3. LEARNING (Object Mode - sees updated Fire state)
        # NOTE: Learning inside temporal loop is correct for SNN
        _clustering_impl(ctx)
        _stdp_3factor_impl(ctx)
        
        # 5. TICK (Advance Time)
        _tick_delta = _tick_impl(ctx)
        if _tick_delta: 
            tick_delta.update(_tick_delta)
            # CRITICAL: Mutate context so NEXT tick in loop sees progress
            if 'current_time' in _tick_delta:
                snn_ctx.domain_ctx.current_time = _tick_delta['current_time']
    
    # Sync Tensors -> Objects (Potentials, Weights, LastFire, Thresholds)
    sync_from_heavy_tensors(snn_ctx)

    # --- DEBUG PROBE ---
    t = snn_ctx.domain_ctx.heavy_tensors
    cur_time = snn_ctx.domain_ctx.current_time
    max_p = np.max(t['potentials'])
    avg_th = np.mean(t['thresholds'])
    if cur_time % 100 < 10: # Log start of some steps
        print(f"DEBUG SNN Step {cur_time}: Max Pot={max_p:.4f}, Avg Th={avg_th:.4f}")
    # -------------------

    # 4. READOUT & MAINTENANCE (Object Mode)
    emo_delta = _encode_emotion_vector_impl(ctx)
    if emo_delta is None: emo_delta = {}
    
    # Merge all deltas for Theus Engine
    final_delta = {}
    if fire_delta: final_delta.update(fire_delta)
    if emo_delta: final_delta.update(emo_delta)
    if tick_delta: final_delta.update(tick_delta)
    
    return final_delta
