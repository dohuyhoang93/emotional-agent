"""
Dream Decoding Process
======================
Decodes SNN spike patterns back into physical states (State Decoding).
Part of Semantic Dream Learning (Phase 13).

Author: Do Huy Hoang
Date: 2025-12-26
"""
import numpy as np
from theus.contracts import process
from src.core.context import SystemContext

@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context',
        'domain_ctx.snn_context.domain_ctx.spike_queue',
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.metrics'
    ],
    outputs=[],
    side_effects=[]
)
def process_decode_dream(ctx: SystemContext):
    """
    Giải mã giấc mơ: Spike Queue -> Physical State (x, y).
    """
    try:
        _decode_impl(ctx)
    except Exception:
        import traceback
        print(f"CRASH in process_decode_dream: {traceback.format_exc()}")
        raise

def _decode_impl(ctx: SystemContext):
    domain = ctx.domain_ctx
    snn_ctx = domain.snn_context
    if snn_ctx is None: return

    snn_domain = snn_ctx.domain_ctx
    
    # Cast current_time to int for safety
    try:
        current_time = int(snn_domain.current_time)
    except:
        current_time = 0
    
    # Get active spikes
    spikes = snn_domain.spike_queue.get(current_time, [])
    if not spikes:
        return
        
    # Get prototypes of active neurons
    active_prototypes = []
    for nid in spikes:
        if nid < len(snn_domain.neurons):
            active_prototypes.append(snn_domain.neurons[nid].prototype_vector)
            
    if not active_prototypes:
        return
        
    # Mean vector representing the dream state
    dream_vector = np.mean(active_prototypes, axis=0) # 16-dim
    
    # Simple Argmax Decoding
    x_dim = np.argmax(dream_vector[0:8])
    y_dim = np.argmax(dream_vector[8:16])
    
    # Store decoded state in metrics (explicit cast)
    snn_domain.metrics['dream_state_x'] = int(x_dim)
    snn_domain.metrics['dream_state_y'] = int(y_dim)
