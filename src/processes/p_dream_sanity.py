from theus import process
from src.core.context import SystemContext

@process(
    inputs=[
        'domain_ctx.snn_context.domain_ctx.spike_queue',
        'domain.believed_switch_states',
        'domain_ctx.snn_context.domain_ctx.metrics'
    ],
    outputs=[
        'domain_ctx.snn_context.domain_ctx.spike_queue',
        'domain_ctx.snn_context.domain_ctx.metrics'
    ],
    side_effects=[],
    errors=[]
)
def process_dream_sanity_check(ctx: SystemContext):
    """
    Mental Simulation: Kiểm thử kịch bản giấc mơ dựa trên Belief (Phase 13 Lite).
    
    Logic:
    - Nếu SNN replay một trạng thái (spike vector) mâu thuẫn với Belief (vd: đi xuyên tường),
      chúng ta sẽ "tỉnh mộng" hoặc giảm cường độ (suppress).
    - Đây là cơ chế sơ khai của World Model Validation.
    """
    domain = ctx.domain_ctx
    snn_ctx = domain.snn_context
    
    if snn_ctx is None:
        return

    snn_domain = snn_ctx.domain_ctx
    
    # Check belief from RL domain?
    # domain.believed_switch_states might not exist if not declared/implemented in context
    # assuming access via domain_ctx
    
    # 1. Decode Dream State (Heuristic)
    if snn_domain.metrics.get('dream_type') == 'nightmare':
        # Nightmare violates internal stability -> Suppress
        snn_domain.metrics['dream_suppressed'] = 1
        # Clear/Reduce queue to calm down
        snn_domain.spike_queue.clear()
        
    pass
