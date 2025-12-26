"""
SNN Social Learning: Viral Synapse Transfer
============================================
Cơ chế học tập xã hội - trao đổi tri thức giữa các agent.
"""
from src.core.snn_context import SNNContext, SynapseRecord
import numpy as np
from typing import List, Tuple


def extract_top_synapses(ctx: SNNContext, top_k: int = 10) -> List[SynapseRecord]:
    """
    Trích xuất top-k synapse hiệu quả nhất để chia sẻ.
    
    Tiêu chí: Synapse có trọng số cao và confidence cao.
    """
    # Lọc chỉ native synapses (không lấy shadow)
    native_synapses = [s for s in ctx.synapses if s.synapse_type == "native"]
    
    # Sắp xếp theo utility score
    sorted_synapses = sorted(
        native_synapses,
        key=lambda s: s.weight * s.confidence,
        reverse=True
    )
    
    return sorted_synapses[:top_k]


def inject_viral_synapses(
    ctx: SNNContext,
    viral_synapses: List[SynapseRecord],
    source_agent_id: int
) -> SNNContext:
    """
    Tiêm các synapse từ agent khác vào dưới dạng Shadow Synapses.
    Chúng sẽ chạy song song trong Sandbox để kiểm chứng.
    """
    for viral_syn in viral_synapses:
        # Tạo shadow synapse (bản sao)
        shadow = SynapseRecord(
            synapse_id=len(ctx.synapses),  # ID mới
            pre_neuron_id=viral_syn.pre_neuron_id,
            post_neuron_id=viral_syn.post_neuron_id,
            weight=viral_syn.weight,
            trace=0.0,
            delay=viral_syn.delay,
            synapse_type="shadow",  # Đánh dấu là shadow
            source_agent_id=source_agent_id,
            confidence=0.1,  # Bắt đầu với confidence thấp
            prediction_error_accum=0.0
        )
        
        ctx.synapses.append(shadow)
    
    return ctx


def process_sandbox_evaluation(ctx: SNNContext) -> SNNContext:
    """
    Đánh giá hiệu quả của Shadow Synapses.
    Nếu shadow tốt hơn native -> Thực hiện "Đảo chính" (Revoke native, promote shadow).
    """
    # Nhóm synapses theo (pre, post) pair
    synapse_groups = {}
    for syn in ctx.synapses:
        key = (syn.pre_neuron_id, syn.post_neuron_id)
        if key not in synapse_groups:
            synapse_groups[key] = []
        synapse_groups[key].append(syn)
    
    # Kiểm tra từng nhóm
    for key, group in synapse_groups.items():
        natives = [s for s in group if s.synapse_type == "native"]
        shadows = [s for s in group if s.synapse_type == "shadow"]
        
        if not natives or not shadows:
            continue
        
        native = natives[0]
        shadow = shadows[0]
        
        # So sánh performance (confidence là proxy cho accuracy)
        if shadow.confidence > native.confidence + 0.2:  # Shadow vượt trội
            # Đảo chính: Promote shadow, demote native
            native.synapse_type = "revoked"
            shadow.synapse_type = "native"
            
            # Ghi log
            ctx.metrics['viral_takeover_count'] = ctx.metrics.get('viral_takeover_count', 0) + 1
    
    # Dọn dẹp revoked synapses (xóa sau 1000 steps)
    ctx.synapses = [s for s in ctx.synapses if s.synapse_type != "revoked"]
    
    return ctx
