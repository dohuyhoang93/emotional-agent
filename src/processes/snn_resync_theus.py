"""
SNN Resync Process for Theus Framework
=======================================
Periodic resync để fix drift với Theus @process decorator.

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
        'global_ctx.tau_decay'
    ],
    outputs=[
        'domain_ctx.neurons',
        'domain_ctx.metrics'
    ],
    side_effects=[]  # Pure function
)
def process_periodic_resync(ctx: SNNSystemContext):
    """
    Periodic Resync - Fix numerical drift.
    
    Cơ chế:
    1. Mỗi 1000 steps, reset các giá trị rất nhỏ về 0
    2. Normalize prototype vectors
    3. Clamp thresholds
    
    NOTE: Pure function - chỉ cleanup internal state.
    """
    domain = ctx.domain_ctx
    
    # Chỉ chạy mỗi 1000 steps
    if domain.current_time % 1000 != 0:
        return
    
    resync_count = 0
    
    for neuron in domain.neurons:
        # Reset potential rất nhỏ về 0
        if abs(neuron.potential) < 1e-6:
            neuron.potential = 0.0
            resync_count += 1
        
        # Reset potential_vector rất nhỏ
        neuron.potential_vector[np.abs(neuron.potential_vector) < 1e-6] = 0.0
        
        # Normalize prototype_vector
        norm = np.linalg.norm(neuron.prototype_vector)
        if norm > 0:
            neuron.prototype_vector /= norm
        else:
            # Reset nếu bị zero vector
            neuron.prototype_vector = np.random.randn(neuron.vector_dim)
            neuron.prototype_vector /= np.linalg.norm(neuron.prototype_vector)
            resync_count += 1
        
        # Clamp threshold
        neuron.threshold = np.clip(
            neuron.threshold,
            ctx.global_ctx.threshold_min,
            ctx.global_ctx.threshold_max
        )
    
    # Update metrics
    domain.metrics['resync_count'] = \
        domain.metrics.get('resync_count', 0) + 1
    domain.metrics['resync_neurons'] = resync_count
