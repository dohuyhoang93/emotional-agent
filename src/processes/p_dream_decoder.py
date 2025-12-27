"""
Dream Decoding Process
======================
Decodes SNN spike patterns back into physical states (State Decoding).
Part of Semantic Dream Learning (Phase 13).

Author: Do Huy Hoang
Date: 2025-12-26
"""
import numpy as np
import torch
from theus import process
from src.core.context import SystemContext

@process(
    inputs=[
        'domain.snn_context',
        'domain.snn_context.domain_ctx.spike_queue',
        'domain.snn_context.domain_ctx.neurons',
        'domain.metrics'
    ],
    outputs=[
        'domain.metrics' # Writes 'dream_state_x', 'dream_state_y'
    ],
    side_effects=[]
)
def process_decode_dream(ctx: SystemContext):
    """
    Giải mã giấc mơ: Spike Queue -> Physical State (x, y).
    
    Logic:
    - Lấy các neuron đang bắn (Active Neurons) trong mơ.
    - Lấy prototype vector của chúng.
    - Dùng vector này để suy ngược ra tọa độ (x, y).
      (Dựa trên heuristic của encode_state_to_spikes: x%8, y%8).
    
    NOTE: Đây là 'Inverse Model' sơ khai.
    """
    domain = ctx.domain_ctx
    snn_ctx = domain.snn_context
    if snn_ctx is None: return

    snn_domain = snn_ctx.domain_ctx
    current_time = snn_domain.current_time
    
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
    
    # --- DECODING HEURISTIC ---
    # Encode logic was:
    # pattern[x % 8] = 1.0
    # pattern[8 + (y % 8)] = 1.0
    
    # Inverse logic: Find max index in first 8 and last 8
    # x_part = dream_vector[0:8]
    # y_part = dream_vector[8:16]
    
    # Simple Argmax Decoding
    x_dim = np.argmax(dream_vector[0:8])
    y_dim = np.argmax(dream_vector[8:16])
    
    # Store decoded state in metrics for Validator to see
    snn_domain.metrics['dream_state_x'] = int(x_dim)
    snn_domain.metrics['dream_state_y'] = int(y_dim)
