"""
RL Processes với SNN Integration
==================================
RL processes tích hợp SNN với Theus framework.

CRITICAL: Side-effects handling cho environment interaction.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import torch
from theus import process
from src.core.context import SystemContext
from src.adapters.snn_rl_interface import SNNRLInterface
from src.processes.snn_core_theus import (
    process_integrate,
    process_fire,
    process_tick
)
from src.processes.snn_learning_theus import (
    process_clustering,
    process_stdp
)


@process(
    inputs=[
        'domain_ctx.current_observation',
        'domain_ctx.snn_context'  # Nested SNN context
    ],
    outputs=[
        'domain_ctx.snn_emotion_vector',
        'domain_ctx.snn_context'  # Updated SNN state
    ],
    side_effects=[]  # Pure - SNN internal only, NO env calls
)
def calculate_emotions_snn(ctx: SystemContext):
    """
    Tính emotion vector từ SNN thay vì MLP.
    
    Flow:
    1. Encode observation → SNN spikes
    2. Run SNN forward (internal processes)
    3. Extract emotion vector
    
    CRITICAL: Pure function - SNN chạy internal, KHÔNG gọi env.
    Tất cả SNN processes đều pure, không side effects.
    
    Args:
        ctx: System context
    """
    domain = ctx.domain_ctx
    snn_ctx = domain.snn_context
    
    if snn_ctx is None:
        # Fallback: Không có SNN, skip
        return
    
    # 1. Encode observation → SNN spikes
    SNNRLInterface.encode_state_to_spikes(ctx, snn_ctx)
    
    # 2. Run SNN forward (internal processes)
    # NOTE: Tất cả processes này đều pure, không side effects
    process_integrate(snn_ctx)
    process_fire(snn_ctx)
    process_clustering(snn_ctx)
    process_stdp(snn_ctx)
    
    # 3. Extract emotion vector
    SNNRLInterface.encode_emotion_vector(snn_ctx, ctx)
    
    # domain.snn_emotion_vector đã được update
    # snn_ctx đã được update (SNN state changed)


@process(
    inputs=[
        'domain_ctx.snn_context',
        'domain_ctx.td_error'
    ],
    outputs=[
        'domain_ctx.snn_context'  # SNN attention modulated
    ],
    side_effects=[]  # Pure function
)
def modulate_snn_attention(ctx: SystemContext):
    """
    Điều chỉnh SNN attention dựa trên TD-error.
    
    Top-down Modulation: RL điều khiển SNN focus.
    
    NOTE: Pure function - chỉ thay đổi SNN thresholds.
    
    Args:
        ctx: System context
    """
    domain = ctx.domain_ctx
    snn_ctx = domain.snn_context
    
    if snn_ctx is None:
        return
    
    # Tính modulation strength từ TD-error
    td_error = domain.td_error
    
    # Positive TD-error → Tăng curiosity attention
    if td_error > 0:
        SNNRLInterface.modulate_attention(
            ctx, snn_ctx,
            region='curiosity',
            strength=min(td_error, 1.0)  # Clip [0, 1]
        )
    # Negative TD-error → Tăng fear attention
    else:
        SNNRLInterface.modulate_attention(
            ctx, snn_ctx,
            region='fear',
            strength=min(-td_error, 1.0)
        )


@process(
    inputs=[
        'domain_ctx.snn_context'
    ],
    outputs=[
        'domain_ctx.intrinsic_reward'
    ],
    side_effects=[]  # Pure function - read-only
)
def compute_intrinsic_reward_snn(ctx: SystemContext):
    """
    Tính intrinsic reward từ SNN novelty.
    
    Novelty Detection: Dựa trên clustering similarity.
    
    NOTE: Pure function - chỉ đọc SNN state.
    
    Args:
        ctx: System context
    """
    domain = ctx.domain_ctx
    snn_ctx = domain.snn_context
    
    if snn_ctx is None:
        domain.intrinsic_reward = 0.0
        return
    
    # Compute novelty từ SNN
    SNNRLInterface.compute_intrinsic_reward(snn_ctx, ctx)
    
    # domain.intrinsic_reward đã được update


@process(
    inputs=[
        'domain.last_reward',
        'domain.intrinsic_reward',
        'global.intrinsic_reward_weight'
    ],
    outputs=[
        'domain.last_reward'  # Combined reward
    ],
    side_effects=[]  # Pure function
)
def combine_rewards(ctx: SystemContext):
    """
    Kết hợp extrinsic và intrinsic rewards.
    
    Total reward = extrinsic + α × intrinsic
    
    NOTE: Pure function - chỉ tính toán.
    
    Args:
        ctx: System context
    """
    domain = ctx.domain_ctx
    
    extrinsic = domain.last_reward.get('extrinsic', 0.0)
    intrinsic = domain.intrinsic_reward
    weight = ctx.global_ctx.intrinsic_reward_weight
    
    # Combined reward
    total = extrinsic + weight * intrinsic
    
    # Update
    domain.last_reward['intrinsic'] = intrinsic
    domain.last_reward['total'] = total


# ============================================================================
# CRITICAL: Environment Interaction với Side-Effects
# ============================================================================

@process(
    inputs=[
        'domain_ctx.selected_action'
    ],
    outputs=[
        'domain_ctx.current_observation',
        'domain_ctx.last_reward'
    ],
    side_effects=['env_adapter.step']  # ← KHAI BÁO RÕ RÀNG!
)
def execute_action_with_env(ctx: SystemContext):
    """
    Execute action trong environment.
    
    CRITICAL: Có side effects - gọi env.step()
    
    NOTE: Theus sẽ KHÔNG rollback được external state!
    Environment state changes là permanent.
    
    Args:
        ctx: System context
    """
    domain = ctx.domain_ctx
    env_adapter = ctx.env_adapter  # Injected dependency
    
    # Execute action (SIDE EFFECT!)
    # NOTE: Đây là external call, không thể rollback
    next_obs, reward, done, info = env_adapter.step(domain.selected_action)
    
    # Update context
    domain.current_observation = next_obs
    domain.last_reward = {
        'extrinsic': reward,
        'intrinsic': 0.0,  # Will be computed by SNN
        'total': reward
    }
    
    # Store done flag
    if 'episode_done' not in domain.metrics:
        domain.metrics = {}
    domain.metrics['episode_done'] = done


@process(
    inputs=[],
    outputs=[
        'domain_ctx.current_observation'
    ],
    side_effects=['env_adapter.reset']  # ← KHAI BÁO RÕ RÀNG!
)
def reset_environment(ctx: SystemContext):
    """
    Reset environment.
    
    CRITICAL: Có side effects - gọi env.reset()
    
    NOTE: Theus sẽ KHÔNG rollback được external state!
    
    Args:
        ctx: System context
    """
    env_adapter = ctx.env_adapter  # Injected dependency
    
    # Reset environment (SIDE EFFECT!)
    initial_obs = env_adapter.reset()
    
    # Update context
    ctx.domain_ctx.current_observation = initial_obs
