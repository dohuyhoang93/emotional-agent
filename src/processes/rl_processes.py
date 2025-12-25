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
def select_action_gated(
    ctx: SystemContext,
    gated_network: GatedIntegrationNetwork
):
    """
    Select action using Gated Integration Network.
    
    Combines observation + emotion → Q-values → action.
    Uses epsilon-greedy exploration.
    
    Args:
        ctx: System context
        gated_network: Gated Integration Network
    """
    obs = ctx.domain_ctx.current_observation
    emotion = ctx.domain_ctx.snn_emotion_vector
    
    # Convert to tensors
    obs_tensor = observation_to_tensor(obs)
    
    # Forward pass
    with torch.no_grad():
        q_values = gated_network(obs_tensor.unsqueeze(0), emotion.unsqueeze(0))
        q_values = q_values.squeeze(0)
    
    # Epsilon-greedy
    if np.random.rand() < ctx.domain_ctx.current_exploration_rate:
        action = np.random.randint(0, 4)
    else:
        action = torch.argmax(q_values).item()
    
    ctx.domain_ctx.last_action = action
    ctx.domain_ctx.last_q_values = q_values


@process(
    inputs=[
        'domain_ctx.q_table',
        'domain_ctx.total_reward',
        'domain_ctx.current_observation',
        'domain_ctx.next_observation',
        'domain_ctx.last_action'
    ],
    outputs=[
        'domain_ctx.q_table',
        'domain_ctx.td_error'
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
    # Get state keys
    state = observation_to_state_key(ctx.domain_ctx.current_observation)
    next_state = observation_to_state_key(ctx.domain_ctx.next_observation)
    action = ctx.domain_ctx.last_action
    reward = ctx.domain_ctx.total_reward
    
    # Initialize Q-values if needed
    if state not in ctx.domain_ctx.q_table:
        ctx.domain_ctx.q_table[state] = np.zeros(4)
    
    if next_state not in ctx.domain_ctx.q_table:
        ctx.domain_ctx.q_table[next_state] = np.zeros(4)
    
    # TD-learning
    current_q = ctx.domain_ctx.q_table[state][action]
    next_max_q = np.max(ctx.domain_ctx.q_table[next_state])
    
    # TD-error (for SNN dopamine)
    gamma = 0.99
    td_error = reward + gamma * next_max_q - current_q
    
    # Update Q-value
    alpha = 0.1
    ctx.domain_ctx.q_table[state][action] += alpha * td_error
    
    # Store TD-error for SNN
    ctx.domain_ctx.td_error = td_error
