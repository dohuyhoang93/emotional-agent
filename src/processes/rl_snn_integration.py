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
    
    # 5. Prepare Result Delta
    reward_dict = {
        'extrinsic': extrinsic,
        'intrinsic': intrinsic_total,
        'intrinsic_novelty': novelty,
        'intrinsic_surprise': surprise,
        'total': total_reward
    }
    
    metrics_update = dict(domain.metrics)
    metrics_update.update({
        'confidence': confidence,
        'novelty': novelty,
        'surprise': surprise,
        'total_reward': total_reward
    })
    
    return {
        'last_reward': reward_dict,
        'metrics': metrics_update
    }



# ============================================================================
# CRITICAL: Environment Interaction với Side-Effects
# ============================================================================

@process(
    inputs=['domain_ctx', 
        'domain_ctx.selected_action',
        'domain_ctx.env_adapter',  # v3: Read from context
        'domain_ctx.agent_id',     # v3: Read from context
        'domain_ctx.metrics'
    ],
    outputs=['domain_ctx', 
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
    
    v3: Reads env_adapter and agent_id from context, not kwargs.
    
    Args:
        ctx: System context
    """
    domain = ctx.domain_ctx
    
    # v3: Read from context
    env_adapter = getattr(domain, 'env_adapter', None)
    agent_id = getattr(domain, 'agent_id', 0)
    
    if env_adapter is None:
        raise ValueError("Critical: env_adapter not found in domain_ctx. "
                         "Set it with 'engine.edit(): domain_ctx.env_adapter = adapter'")
    
    # Execute action (SIDE EFFECT!)
    # NOTE: Đây là external call, không thể rollback
    next_obs, reward, done, info = env_adapter.step(agent_id, domain.selected_action)
    
    # Update context via return
    return {
        'current_observation': next_obs,
        'last_reward': {
            'extrinsic': reward,
            'intrinsic': 0.0,  # Will be computed by SNN
            'total': reward
        }
    }
    
    # Store done flag
    # if 'episode_done' not in domain.metrics:
    #     domain.metrics = {}
    # domain.metrics['episode_done'] = done


@process(
    inputs=['domain_ctx',
        'domain_ctx.env_adapter'  # v3: Read from context
    ],
    outputs=['domain_ctx', 
        'domain_ctx.current_observation'
    ],
    side_effects=['env_adapter.reset']  # ← KHAI BÁO RÕ RÀNG!
)
def reset_environment(ctx: SystemContext):
    """
    Reset environment.
    
    CRITICAL: Có side effects - gọi env.reset()
    
    NOTE: Theus sẽ KHÔNG rollback được external state!
    
    v3: Reads env_adapter from context, not kwargs.
    
    Args:
        ctx: System context
    """
    domain = ctx.domain_ctx
    
    # v3: Read from context
    env_adapter = getattr(domain, 'env_adapter', None)
    
    if env_adapter is None:
        raise ValueError("Critical: env_adapter not found in domain_ctx.")
    
    # Reset environment (SIDE EFFECT!)
    initial_obs = env_adapter.reset()
    
    # Update context via return
    return {
        'current_observation': initial_obs
    }

@process(
    inputs=['domain_ctx', 'domain_ctx.snn_context'],
    outputs=['domain_ctx', 'domain_ctx.snn_context'],
)
def process_agent_learn_composite(ctx: SystemContext, extrinsic_reward: float = 0.0, next_obs: dict = None):
    """
    Composite process combining observation update, reward combination, and Q-learning.
    Reduces 3 transactions to 1.
    """
    from src.processes.rl_processes import update_q_learning
    
    # NOTE: previous_observation phải được set TRƯỚC khi ghi đè current_observation.
    # Nếu không, update_q_learning sẽ thấy previous_observation=None và skip hoàn toàn.
    # Đây là nguyên nhân gốc rễ khiến Q-table luôn rỗng (q_table_size=0).
    # 1. Manual update of state in current context (Pre-sync for sub-processes)
    ctx.domain_ctx.previous_observation = ctx.domain_ctx.current_observation
    ctx.domain_ctx.current_observation = next_obs
    ctx.domain_ctx.last_reward = {
        'extrinsic': extrinsic_reward,
        'intrinsic': 0.0, # Will be updated by combine_rewards
        'total': extrinsic_reward
    }
    
    combined_delta = {}
    
    # 2. Run Combine Rewards
    reward_delta = combine_rewards(ctx)
    if reward_delta:
        # Apply locally to satisfy next process in the same chain
        for k, v in reward_delta.items():
            setattr(ctx.domain_ctx, k, v)
        combined_delta.update(reward_delta)
        
    # 3. Run Q-Learning
    learn_delta = update_q_learning(ctx)
    if learn_delta:
        combined_delta.update(learn_delta)
        
    return combined_delta
