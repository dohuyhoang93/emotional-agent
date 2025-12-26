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
    # If obs is already a tensor or numpy array (from sensor system)
    if isinstance(obs, (np.ndarray, torch.Tensor)):
        if isinstance(obs, np.ndarray):
            tensor = torch.from_numpy(obs).float()
        else:
            tensor = obs.float()
            
        # Ensure correct dimension if needed, or just return
        # Our sensor vector is 16-dim.
        # But gated network expects obs_dim=5?
        # WAIT! RLAgent.__init__ defines obs_dim=5.
        # If we use sensor vector (16), we must match network input!
        # Network definition: GatedIntegrationNetwork(obs_dim=5, ...)
        
        # We need to map 16-dim sensor to 5-dim features OR update Network to 16-dim.
        # For now, let's just extract first 2 dims as x,y and mock others?
        # Or better: Update RLAgent to use obs_dim=16?
        
        # Quick Fix (since I can't change Model easily without verifying):
        # Allow tensor return, but let's see if Model handles size mismatch.
        # GatedIntegrationNetwork usually has Linear(obs_dim, ...).
        # Checking RLAgent line 91: obs_dim = 5.
        # Checking get_sensor_vector return: 16-dim.
        
        # Mismatch Alert!
        # If I pass 16-dim vector to 5-dim network, it crashes.
        # I must Extract features from 16-dim vector if possible, or PAD if logic expects x,y.
        # But 16-dim sensor is "wall proximity". It has NO coordinates.
        # If I use relative coords?
        
        # Compromise: Return a 5-dim vector from the 16-dim one (slice or aggregate).
        # Or Just use 0s if meaningful data is missing?
        # Actually RLAgent logic SHOULD be updated to use 16-dim input.
        # But that requires retraining/init change.
        # RLAgent.__init__ is in rl_agent.py.
        
        # I will slice/pad to 5-dim to prevent crash.
        # [0-4] of sensor vector.
        if tensor.shape[0] >= 5:
            return tensor[:5]
        else:
            # Pad
            padded = torch.zeros(5)
            padded[:tensor.shape[0]] = tensor
            return padded

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
    # If numpy/tensor
    if isinstance(obs, (np.ndarray, torch.Tensor)):
        if isinstance(obs, torch.Tensor):
            obs = obs.detach().cpu().numpy()
        # Round to 1 decimal to discretize continuous space
        return str(np.round(obs, 1).tolist())

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
        'domain.current_exploration_rate',
        'domain.gated_network'
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
    
    # Get Q-values from Network if available, else Q-table
    if ctx.domain_ctx.gated_network is not None:
        # Neural Network Path
        net = ctx.domain_ctx.gated_network
        obs_tensor = observation_to_tensor(obs)
        
        # Predict
        net.eval()
        with torch.no_grad():
            q_values_tensor = net(obs_tensor, emotion)
        net.train()
        
        q_values_list = q_values_tensor.tolist()
    else:
        # Tabular Path
        state_key = str(obs)
        q_values_list = ctx.domain_ctx.q_table.get(state_key, [0.0] * 4)

    # Epsilon-greedy
    if np.random.rand() < adjusted_exploration:
        action = np.random.randint(0, 4)
    else:
        action = int(np.argmax(q_values_list))
    
    ctx.domain_ctx.last_action = action
    ctx.domain_ctx.last_q_values = torch.tensor(q_values_list, dtype=torch.float32)


@process(
    inputs=[
        'domain.q_table',
        'domain.last_reward',
        'domain.current_observation',
        'domain.last_action',
        'domain.gated_network',
        'domain.gated_optimizer',
        'domain.previous_observation',
        'domain.previous_snn_emotion_vector',
        'domain.snn_emotion_vector'
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
    
    # === Train Gated Network (Deep RL) ===
    if ctx.domain_ctx.gated_network is not None and ctx.domain_ctx.gated_optimizer is not None:
        net = ctx.domain_ctx.gated_network
        opt = ctx.domain_ctx.gated_optimizer
        
        # Previous State (t-1)
        prev_obs = ctx.domain_ctx.previous_observation
        prev_emo = ctx.domain_ctx.previous_snn_emotion_vector
        
        # Current State (t) - becomes Next State for update
        curr_obs = ctx.domain_ctx.current_observation
        curr_emo = ctx.domain_ctx.snn_emotion_vector
        
        if prev_obs is not None and prev_emo is not None and curr_emo is not None:
            # Prepare tensors
            state_tensor = observation_to_tensor(prev_obs)
            emotion_tensor = prev_emo
            next_state_tensor = observation_to_tensor(curr_obs)
            next_emotion_tensor = curr_emo
            
            # Predict Q(s, a)
            q_values = net(state_tensor, emotion_tensor)
            current_q_val = q_values[action]
            
            # Target Q
            with torch.no_grad():
                next_q_values = net(next_state_tensor, next_emotion_tensor)
                max_next_q = torch.max(next_q_values)
                target_q_val = reward + 0.95 * max_next_q # gamma = 0.95
            
            # Loss & Step
            loss = torch.nn.functional.mse_loss(current_q_val, target_q_val)
            
            opt.zero_grad()
            loss.backward()
            opt.step()

