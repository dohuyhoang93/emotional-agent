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
        'domain_ctx.intrinsic_reward', # Novelty
        'domain_ctx.td_error',         # Surprise (New)
        'domain_ctx.metrics',
        'global_ctx.intrinsic_reward_weight', # w1 (Novelty)
        'global_ctx.surprise_reward_weight',  # w2 (Surprise)
        'global_ctx.confidence_decay'         # EMA alpha
    ],
    outputs=['domain_ctx', 
        'domain_ctx.last_reward',
        'domain_ctx.metrics'
    ],
    side_effects=[]  # Pure function
)
def combine_rewards(ctx: SystemContext):
    """
    Kết hợp Extrinsic + Intrinsic (Novelty + Surprise).
    Tính toán Confidence (Meta-cognition).
    
    Formula:
        R_total = R_ex + (w1 * Novelty) + (w2 * |TD_Error|)
        
    Confidence (EMA):
        C_inst = (1 - Novelty) * exp(-|TD_Error|)
        C_t = alpha * C_inst + (1 - alpha) * C_{t-1}
        
    Args:
        ctx: System context
    """
    domain = ctx.domain_ctx
    global_ctx = ctx.global_ctx
    import numpy as np
    
    # 1. Get Extrinsic
    try:
        raw_reward = domain.last_reward
        if isinstance(raw_reward, dict):
            extrinsic = float(raw_reward.get('extrinsic', 0.0))
        else:
            extrinsic = float(raw_reward) if raw_reward else 0.0
    except:
        extrinsic = 0.0
            
    # 2. Get Intrinsic Components
    # Component A: Novelty (from SNN Bridge)
    try:
        novelty = float(getattr(domain, 'intrinsic_reward', 0.0))
    except:
        novelty = 0.0
    
    # Component B: Surprise (|TD-Error|)
    try:
        td_error = float(getattr(domain, 'td_error', 0.0))
    except:
        td_error = 0.0
    surprise = abs(td_error)
    
    # Weights
    try:
        w_novelty = float(getattr(global_ctx, 'intrinsic_reward_weight', 0.1))
        # Default Surprise Weight smaller than Novelty to avoid instability
        w_surprise = float(getattr(global_ctx, 'surprise_reward_weight', 0.05))
    except:
        w_novelty = 0.1
        w_surprise = 0.05
    
    # 3. Calculate Hybrid Reward
    intrinsic_total = (w_novelty * novelty) + (w_surprise * surprise)
    total_reward = extrinsic + intrinsic_total
    
    # 4. Meta-Cognition: Calculate Confidence (EMA)
    # Instantaneous Confidence: High if Low Novelty AND Low Error
    # Using simple exp decay logic: exp(-|TD|)
    # Bound to [0, 1]
    confidence_inst = (1.0 - novelty) * np.exp(-surprise)
    
    # EMA Smoothing
    try:
        prev_conf = float(domain.metrics.get('confidence', 0.5))
    except:
        prev_conf = 0.5
        
    try:
        ema_alpha = float(getattr(global_ctx, 'confidence_decay', 0.1))
    except:
        ema_alpha = 0.1
        
    confidence = (ema_alpha * confidence_inst) + ((1.0 - ema_alpha) * prev_conf)
    confidence = np.clip(confidence, 0.0, 1.0)
    
    # 5. Update Context
    if not isinstance(domain.last_reward, dict):
        domain.last_reward = {'extrinsic': extrinsic}
    
    domain.last_reward['intrinsic'] = intrinsic_total
    domain.last_reward['intrinsic_novelty'] = novelty
    domain.last_reward['intrinsic_surprise'] = surprise
    domain.last_reward['total'] = total_reward
    
    # Update Metrics
    domain.metrics['confidence'] = confidence
    domain.metrics['novelty'] = novelty
    domain.metrics['surprise'] = surprise
    domain.metrics['total_reward'] = total_reward



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
