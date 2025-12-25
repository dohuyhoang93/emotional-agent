"""
SNN Social Learning Processes for Theus Framework
==================================================
Social learning: Viral Synapse Transfer với Theus @process decorator.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus import process
from src.core.snn_context_theus import SNNSystemContext, SynapseState


@process(
    inputs=[
        'domain_ctx.synapses',
        'global_ctx.viral_top_k'
    ],
    outputs=[
        'domain_ctx.metrics'
    ],
    side_effects=[]  # Pure function - chỉ đọc synapses
)
def process_extract_top_synapses(ctx: SNNSystemContext):
    """
    Trích xuất top-k synapse hiệu quả nhất để chia sẻ.
    
    Tiêu chí: Synapse có weight cao và confidence cao.
    
    NOTE: Pure function - chỉ đọc, không ghi synapses.
    Kết quả lưu vào metrics để external system lấy.
    """
    domain = ctx.domain_ctx
    top_k = ctx.global_ctx.viral_top_k
    
    # Lọc native synapses
    native_synapses = [
        s for s in domain.synapses
        if s.synapse_type == "native"
    ]
    
    # Sắp xếp theo utility score
    sorted_synapses = sorted(
        native_synapses,
        key=lambda s: s.weight * s.confidence,
        reverse=True
    )
    
    # Lưu top-k IDs vào metrics
    top_ids = [s.synapse_id for s in sorted_synapses[:top_k]]
    domain.metrics['top_synapse_ids'] = top_ids
    domain.metrics['top_synapse_count'] = len(top_ids)


@process(
    inputs=[
        'domain_ctx.synapses',
        'domain_ctx.viral_synapses_received'
    ],
    outputs=[
        'domain_ctx.shadow_synapses',
        'domain_ctx.viral_synapses_received',
        'domain_ctx.metrics'
    ],
    side_effects=[]  # Pure function
)
def process_inject_viral_synapses(ctx: SNNSystemContext):
    """
    Tiêm viral synapses vào shadow sandbox.
    
    NOTE: Viral synapses được inject từ external system.
    Process này chỉ chuyển chúng vào shadow_synapses.
    """
    domain = ctx.domain_ctx
    
    # NOTE: Viral synapses phải được inject từ bên ngoài
    # vào domain.shadow_synapses trước khi gọi process này
    
    # Count viral synapses
    viral_count = len(domain.shadow_synapses)
    domain.viral_synapses_received += viral_count
    
    # Update metrics
    domain.metrics['viral_injected'] = viral_count
    domain.metrics['total_viral_received'] = domain.viral_synapses_received


@process(
    inputs=[
        'domain_ctx.synapses',
        'domain_ctx.shadow_synapses',
        'global_ctx.shadow_confidence_threshold'
    ],
    outputs=[
        'domain_ctx.synapses',
        'domain_ctx.shadow_synapses',
        'domain_ctx.metrics'
    ],
    side_effects=[]  # Pure function
)
def process_sandbox_evaluation(ctx: SNNSystemContext):
    """
    Đánh giá shadow vs native synapses.
    
    Nếu shadow tốt hơn native → Promote shadow, revoke native.
    
    NOTE: Pure function - chỉ thay đổi synapse types.
    """
    domain = ctx.domain_ctx
    threshold = ctx.global_ctx.shadow_confidence_threshold
    
    # Nhóm synapses theo (pre, post) pair
    synapse_groups = {}
    
    # Group native synapses
    for syn in domain.synapses:
        key = (syn.pre_neuron_id, syn.post_neuron_id)
        if key not in synapse_groups:
            synapse_groups[key] = {'native': None, 'shadow': None}
        if syn.synapse_type == "native":
            synapse_groups[key]['native'] = syn
    
    # Group shadow synapses
    for syn in domain.shadow_synapses:
        key = (syn.pre_neuron_id, syn.post_neuron_id)
        if key not in synapse_groups:
            synapse_groups[key] = {'native': None, 'shadow': None}
        synapse_groups[key]['shadow'] = syn
    
    # Evaluate each group
    takeover_count = 0
    
    for key, group in synapse_groups.items():
        native = group['native']
        shadow = group['shadow']
        
        if native is None or shadow is None:
            continue
        
        # Compare performance
        if shadow.confidence > native.confidence + threshold:
            # Takeover: Promote shadow, revoke native
            native.synapse_type = "revoked"
            shadow.synapse_type = "native"
            
            # Move shadow to main synapses
            domain.synapses.append(shadow)
            
            takeover_count += 1
    
    # Remove promoted shadows from shadow list
    domain.shadow_synapses = [
        s for s in domain.shadow_synapses
        if s.synapse_type == "shadow"
    ]
    
    # Remove revoked synapses
    domain.synapses = [
        s for s in domain.synapses
        if s.synapse_type != "revoked"
    ]
    
    # Update metrics
    domain.metrics['viral_takeover_count'] = \
        domain.metrics.get('viral_takeover_count', 0) + takeover_count
    domain.metrics['shadow_count'] = len(domain.shadow_synapses)
