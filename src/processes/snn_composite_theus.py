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
from src.processes.snn_homeostasis_theus import _homeostasis_impl, _meta_homeostasis_impl
from src.processes.snn_commitment_theus import _commitment_impl

@process(
    inputs=['domain_ctx', 'domain', 
        'domain.snn_context',
        'domain.current_observation',
        'domain.td_error',
        'domain.last_action', 
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.domain_ctx.spike_queue',
        'domain.snn_context.domain_ctx.current_time',
        'domain.snn_context.global_ctx'
    ],
    outputs=['domain', 'domain_ctx', 
        'domain.snn_context',
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.synapses',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.domain_ctx.current_time'
    ],
    side_effects=[]
)
def process_snn_cycle(ctx: SystemContext):
    """
    Execute entire SNN Cycle in one optimized transaction.
    """
    snn_ctx = ctx.domain_ctx.snn_context
    ticks_per_step = getattr(snn_ctx.global_ctx, 'ticks_per_step', 10)
    
    # 1. PRE-SYNC: Objects -> Tensors
    ensure_heavy_tensors_initialized(snn_ctx)
    from src.core.snn_context_theus import sync_to_heavy_tensors
    sync_to_heavy_tensors(snn_ctx)
    
    # 2. HYSTERIA (Pre-processing)
    _hysteria_impl(ctx) 
    
    # 3. TEMPORAL LOOP (The High-Frequency Core)
    for _ in range(ticks_per_step):
        # Input Encoding
        _encode_state_to_spikes_impl(ctx)
        
        # Neural Integration
        _integrate_impl(ctx, sync=False)
        
        # Lateral Inhibition
        if snn_ctx.global_ctx.use_lateral_inhibition:
            _lateral_inhibition_vectorized(ctx)
        
        # Firing Logic
        _fire_impl(ctx, sync=False)
        
        # Immediate Learning (STDP) — Vectorized (S,) no sync back
        _stdp_3factor_impl(ctx)
        
        # Advance SNN Time
        # TRAP: _tick_impl returns values but doesn't update in-place for immutable types.
        # We must increment manually or use the return value.
        snn_ctx.domain_ctx.current_time = int(snn_ctx.domain_ctx.current_time) + 1
        _tick_impl(ctx) # For cleanup queue side-effects

    # 4. MAINTENANCE (Post-loop, Once per Step) — Vectorized
    # Homeostasis (Threshold Adaptation)
    _homeostasis_impl(ctx)
    _meta_homeostasis_impl(ctx)
    
    # Commitment (Synaptic Stability)
    _commitment_impl(ctx)
    
    # 5. POST-SYNC: Tensors -> Objects (ONE HEAVY SYNC FOR ALL)
    sync_from_heavy_tensors(snn_ctx)

    # Readout
    _encode_emotion_vector_impl(ctx)
    
    return {}
