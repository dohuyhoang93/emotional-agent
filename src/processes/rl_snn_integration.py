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

# NOTE: Functions `calculate_emotions`, `modulate_attention` etc. 
# have been moved to `snn_rl_bridge.py` as pure SNN processes.
# This file now focuses on Reward Combination and Environment Side-Effects.


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
        'domain_ctx.selected_action',
        'domain_ctx.metrics'
    ],
    outputs=[
        'domain_ctx.current_observation',
        'domain_ctx.last_reward',
        'domain_ctx.metrics'
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
    # if 'episode_done' not in domain.metrics:
    #     domain.metrics = {}
    # domain.metrics['episode_done'] = done


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
