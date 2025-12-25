"""
RL Processes for Theus Framework
=================================
Q-learning processes với Gated Integration Network.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
import torch
from theus import process
from src.core.context import SystemContext
from src.models.gated_integration import GatedIntegrationNetwork
from typing import Dict, Any


def observation_to_tensor(obs: Dict[str, Any]) -> torch.Tensor:
    """
    Convert observation dict to tensor.
    
    Args:
        obs: Observation dict from GridWorld
            - agent_pos: (x, y) tuple
            - step_count: int
            - global_events: list
        
    Returns:
        Tensor of shape (obs_dim,)
    """
    # Extract position (GridWorld format: agent_pos)
    if 'agent_pos' in obs:
        x, y = obs['agent_pos']
    elif 'position' in obs:
        x, y = obs['position']
    else:
        x, y = 0, 0
    
    # For now, simple features: [x, y, step_count, normalized_x, normalized_y]
    # TODO: Add goal position, switch states when available
    step_count = obs.get('step_count', 0)
    
    features = [
        float(x),
        float(y),
        float(step_count) / 100.0,  # Normalize
        float(x) / 20.0,  # Normalized x
        float(y) / 20.0,  # Normalized y
    ]
    
    return torch.tensor(features, dtype=torch.float32)


def observation_to_state_key(obs: Dict[str, Any]) -> str:
    """
    Convert observation to state key for Q-table.
    
    Args:
        obs: Observation dict
        
    Returns:
        State key string
    """
    # Handle GridWorld format
    if 'agent_pos' in obs:
        x, y = obs['agent_pos']
    elif 'position' in obs:
        x, y = obs['position']
    else:
        x, y = 0, 0
    
    return f"{x},{y}"


@process(
    inputs=[
        'domain.current_observation',
        'domain.snn_emotion_vector',
        'domain.q_table',
        'domain.current_exploration_rate'
    ],
    outputs=['domain.last_action', 'domain.last_q_values'],
    side_effects=[]
)
def select_action_gated(ctx: SystemContext):
    """
    Select action using emotion gating from SNN.
    
    Combines observation + emotion → Q-values → action.
    Uses epsilon-greedy exploration modulated by emotion.
    
    Args:
        ctx: System context
    """
    obs = ctx.domain_ctx.current_observation
    emotion = ctx.domain_ctx.snn_emotion_vector
    
    # Fallback: If no emotion vector, use standard epsilon-greedy
    if emotion is None:
        if np.random.rand() < ctx.domain_ctx.current_exploration_rate:
            action = np.random.randint(0, 4)
        else:
            state_key = str(obs)
            q_values = ctx.domain_ctx.q_table.get(state_key, [0.0] * 4)
            action = int(np.argmax(q_values))
        
        ctx.domain_ctx.last_action = action
        ctx.domain_ctx.last_q_values = torch.tensor([0.0] * 4)
        return
    
    # Emotion-modulated exploration
    emotion_magnitude = float(torch.norm(emotion).item())
    adjusted_exploration = ctx.domain_ctx.current_exploration_rate * (1.0 + 0.5 * emotion_magnitude)
    adjusted_exploration = min(adjusted_exploration, 1.0)
    
    # Epsilon-greedy
    if np.random.rand() < adjusted_exploration:
        action = np.random.randint(0, 4)
        q_values_list = [0.0] * 4  # Dummy values for exploration
    else:
        state_key = str(obs)
        q_values_list = ctx.domain_ctx.q_table.get(state_key, [0.0] * 4)
        action = int(np.argmax(q_values_list))
    
    ctx.domain_ctx.last_action = action
    ctx.domain_ctx.last_q_values = torch.tensor(q_values_list, dtype=torch.float32)


@process(
    inputs=[
        'domain.q_table',
        'domain.last_reward',
        'domain.current_observation',
        'domain.last_action'
    ],
    outputs=[
        'domain.q_table',
        'domain.td_error'
    ],
    side_effects=[]
)
def update_q_learning(ctx: SystemContext):
    """
    Update Q-table với TD-learning.
    
    Compute TD-error for SNN dopamine signal.
    
    Q(s,a) ← Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
    
    Args:
        ctx: System context
    """
    # Get state key
    state = str(ctx.domain_ctx.current_observation)
    action = ctx.domain_ctx.last_action
    reward = ctx.domain_ctx.last_reward.get('total', 0.0)
    
    # Initialize Q-values if needed
    if state not in ctx.domain_ctx.q_table:
        ctx.domain_ctx.q_table[state] = [0.0] * 4
    
    # Simple Q-learning update (without next state for now)
    current_q = ctx.domain_ctx.q_table[state][action]
    
    # TD-error (simplified - no next state)
    td_error = reward - current_q
    
    # Update Q-value
    alpha = 0.1
    ctx.domain_ctx.q_table[state][action] += alpha * td_error
    
    # Store TD-error for SNN
    ctx.domain_ctx.td_error = td_error

