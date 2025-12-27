"""
SNN Composite Process
=====================
Bundles the entire SNN sub-cycle into a single Theus Transaction.
Optimization for "Compute-Sync" strategy to avoid per-process overhead.

Author: Do Huy Hoang
Date: 2025-12-27
"""
from theus import process
from src.core.context import SystemContext
from src.core.snn_context_theus import ensure_tensors_initialized, sync_from_tensors

# Import Internal Implementations
from src.core.snn_context_theus import ensure_tensors_initialized, sync_from_tensors

# Import Internal Implementations
from src.processes.snn_rl_bridge import _encode_state_to_spikes_impl, _encode_emotion_vector_impl
from src.processes.snn_core_theus import _integrate_impl, _fire_impl, _tick_impl
from src.processes.snn_learning_theus import _clustering_impl
from src.processes.snn_learning_3factor_theus import _stdp_3factor_impl
from src.processes.snn_advanced_features_theus import _hysteria_impl, _lateral_inhibition_vectorized

@process(
    inputs=[
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
    outputs=[
        'domain.snn_context',
        'domain.snn_emotion_vector',
        'domain.previous_snn_emotion_vector',
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
    # 1. PERCEPTION & PRE-PROCESSING (Object Mode)
    # Hysteria updates thresholds on objects
    _hysteria_impl(ctx) 
    
    # Encode State updates potentials on objects
    _encode_state_to_spikes_impl(ctx)
    
    # 2. CORE LOOP (Tensor Mode)
    # Sync Objects -> Tensors (Potentials, Thresholds, Weights)
    ensure_tensors_initialized(ctx.domain_ctx.snn_context)
    
    # Integrate (Updates Potentials Tensor)
    _integrate_impl(ctx, sync=False)
    
    # Lateral Inhibition (Updates Potentials Tensor)
    _lateral_inhibition_vectorized(ctx)
    
    # Fire (Updates Potentials Tensor, LastFire Tensor, FireCount Object, SpikeQueue Object[MUTATION])
    # Note: _fire_impl in tensor mode writes to spike_queue (Object) directly? 
    # Yes, _fire_impl does:
    # if not sync: ... logic with tensors ... AND updates spike_queue object?
    # Let's check _fire_impl in snn_core_theus.py
    
    _fire_impl(ctx, sync=False)
    
    # Sync Tensors -> Objects (Potentials, Weights, LastFire)
    sync_from_tensors(ctx.domain_ctx.snn_context)
    
    # 3. LEARNING (Object Mode - sees updated Fire state)
    _clustering_impl(ctx)
    _stdp_3factor_impl(ctx)
    
    # 4. READOUT & MAINTENANCE (Object Mode)
    _encode_emotion_vector_impl(ctx)
    
    # 5. TICK (Advance Time)
    _tick_impl(ctx)
