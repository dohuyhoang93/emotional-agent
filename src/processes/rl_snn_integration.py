"""
RL Processes với SNN Integration
==================================
RL processes tích hợp SNN với Theus framework.

CRITICAL: Side-effects handling cho environment interaction.

Author: Do Huy Hoang
Date: 2025-12-25
"""
from theus.contracts import process
from src.core.context import SystemContext

# NOTE: Functions `calculate_emotions`, `modulate_attention` etc. 
# have been moved to `snn_rl_bridge.py` as pure SNN processes.
# This file now focuses on Reward Combination and Environment Side-Effects.


@process(
    inputs=['global_ctx', 'domain_ctx', 
        'domain_ctx.last_reward',
        'domain_ctx.intrinsic_reward',
        'global_ctx.intrinsic_reward_weight'
    ],
    outputs=['domain_ctx', 
        'domain_ctx.last_reward'  # Combined reward
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
    
    try:
        raw_reward = domain.last_reward
        if isinstance(raw_reward, dict):
            extrinsic = float(raw_reward.get('extrinsic', 0.0))
        else:
            extrinsic = float(raw_reward) if raw_reward else 0.0
            
        intrinsic = float(domain.intrinsic_reward)
        weight = float(ctx.global_ctx.intrinsic_reward_weight)
    except:
        extrinsic = 0.0
        intrinsic = 0.0
        weight = 0.0
    
    # Combined reward
    total = extrinsic + weight * intrinsic
    
    # Update - ensure last_reward is dict before writing
    if not isinstance(domain.last_reward, dict):
        domain.last_reward = {'extrinsic': extrinsic}
    domain.last_reward['intrinsic'] = intrinsic
    domain.last_reward['total'] = total


# ============================================================================
# CRITICAL: Environment Interaction với Side-Effects
# ============================================================================

@process(
    inputs=['domain_ctx', 
        'domain_ctx.selected_action',
        'domain_ctx.metrics'
    ],
    outputs=['domain_ctx', 
        'domain_ctx.current_observation',
        'domain_ctx.last_reward',
        'domain_ctx.metrics'
    ],
    side_effects=['env_adapter.step']  # ← KHAI BÁO RÕ RÀNG!
)
def execute_action_with_env(ctx: SystemContext, env_adapter=None, agent_id=0):
    """
    Execute action trong environment.
    
    CRITICAL: Có side effects - gọi env.step()
    
    NOTE: Theus sẽ KHÔNG rollback được external state!
    Environment state changes là permanent.
    
    Args:
        ctx: System context
        env_adapter: Environment Adapter (Injected param)
        agent_id: Agent ID (Injected param)
    """
    if env_adapter is None:
        raise ValueError("Critical: env_adapter not provided to execute_action_with_env")

    domain = ctx.domain_ctx
    
    # Execute action (SIDE EFFECT!)
    # NOTE: Đây là external call, không thể rollback
    next_obs, reward, done, info = env_adapter.step(agent_id, domain.selected_action)
    
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
    outputs=['domain_ctx', 
        'domain_ctx.current_observation'
    ],
    side_effects=['env_adapter.reset']  # ← KHAI BÁO RÕ RÀNG!
)
def reset_environment(ctx: SystemContext, env_adapter=None):
    """
    Reset environment.
    
    CRITICAL: Có side effects - gọi env.reset()
    
    NOTE: Theus sẽ KHÔNG rollback được external state!
    
    Args:
        ctx: System context
        env_adapter: Environment Adapter
    """
    if env_adapter is None:
        raise ValueError("Critical: env_adapter not provided to reset_environment")
    
    # Reset environment (SIDE EFFECT!)
    initial_obs = env_adapter.reset()
    
    # Update context
    ctx.domain_ctx.current_observation = initial_obs
