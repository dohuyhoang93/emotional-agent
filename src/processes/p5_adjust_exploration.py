from theus import process
from src.core.context import SystemContext

@process(
    inputs=[
        'global.exploration_decay',
        'global.emotional_boost_factor',
        'global.min_exploration',
        'domain.E_vector',
        'domain.base_exploration_rate'
    ],
    outputs=[
        'domain.current_exploration_rate',
        'domain.base_exploration_rate'
    ],
    side_effects=[],
    errors=[]
)
def adjust_exploration(ctx: SystemContext):
    """
    Process: Điều chỉnh độ khám phá (Exploration Rate)
    Logic: rate = base_decay * (1 + uncertainty * boost)
    """
    global_cfg = ctx.global_ctx
    domain = ctx.domain_ctx
    
    # 1. Tính toán Uncertainty (1 - Confidence)
    # E_vector[0] assumed to be Confidence
    confidence = domain.E_vector[0].item()
    uncertainty = 1.0 - confidence
    
    # 2. Emotional Boost
    boost = uncertainty * global_cfg.emotional_boost_factor
    
    # 3. Decay Base Rate
    domain.base_exploration_rate *= global_cfg.exploration_decay
    
    # 4. Tính toán Rate mới
    new_rate = domain.base_exploration_rate + boost
    
    # 5. Clamp min
    final_rate = max(global_cfg.min_exploration, new_rate)
    
    domain.current_exploration_rate = final_rate