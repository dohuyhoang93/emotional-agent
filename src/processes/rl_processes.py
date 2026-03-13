"""
RL Processes for Theus Framework
=================================
Q-learning processes with Gated Integration Network.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
import torch
from theus.contracts import process
from src.core.context import SystemContext
from typing import Dict, Any, Union, Mapping, MutableSequence

# ------------------------------------------------------------------------------
# Helper Functions (Pure Logic)
# ------------------------------------------------------------------------------

def observation_to_tensor(obs: Union[Mapping[str, Any], np.ndarray, torch.Tensor]) -> torch.Tensor:
    """
    Convert observation to tensor.
    Standardized: Expects Dict input with 'sensor_vector'.
    Legacy Support: Accepts raw NDArray/Tensor via EAFP fallback.
    """
    # 1. Standard Dict Path (Priority)
    sensor_vec = None
    try:
        sensor_vec = obs.get('sensor_vector')
    except AttributeError:
        # Not a dict (has no .get), likely a raw vector (ndarray/Tensor)
        pass 

    # 2. Legacy Vector Path (Fallback if not a dict)
    if sensor_vec is None:
        # Check if obs itself is the vector
        if isinstance(obs, (np.ndarray, torch.Tensor)):
             sensor_vec = obs
        elif not hasattr(obs, 'get'):
             sensor_vec = obs

    # Process extracted vector
    if sensor_vec is not None:
        if isinstance(sensor_vec, np.ndarray):
            tensor = torch.from_numpy(sensor_vec).float()
        elif isinstance(sensor_vec, torch.Tensor):
            tensor = sensor_vec.float()
        else:
            # Try converting unknown type (e.g. list)
            try:
                tensor = torch.tensor(sensor_vec, dtype=torch.float32)
            except:
                tensor = None
                
        if tensor is not None:
             # Ensure dimension compatibility with SNN (16-dim)
             target_dim = 16
             if tensor.shape[0] == target_dim:
                  return tensor
             elif tensor.shape[0] > target_dim:
                  return tensor[:target_dim]
             else:
                  # Pad strictly to 16
                  padded = torch.zeros(target_dim)
                  padded[:tensor.shape[0]] = tensor
                  # print(f"DEBUG: Padded Tensor Shape: {padded.shape}")
                  return padded

    # 3. Fallback Key-based Feature Extraction (Blind Agent)
    x, y = 0, 0
    # Safe retrieval
    try:
        agent_pos = obs.get('agent_pos')
        if agent_pos:
            x, y = agent_pos
        else:
            pos = obs.get('position')
            if pos:
                x, y = pos
    except AttributeError:
        pass
            
    step_count = 0
    try:
        step_count = obs.get('step_count', 0)
    except AttributeError:
        pass
    
    features = [
        float(x),
        float(y),
        float(step_count) / 100.0,
        float(x) / 20.0,
        float(y) / 20.0,
    ]
    # Pad fallback to 16-dim to satisfy SNN input
    while len(features) < 16:
        features.append(0.0)
        
    return torch.tensor(features, dtype=torch.float32)


def observation_to_state_key(obs: Union[Mapping[str, Any], np.ndarray, torch.Tensor]) -> str:
    """
    Convert observation to state key for Tabular Q-learning.
    """
    # 1. Vector Input (Discretization)
    if isinstance(obs, (np.ndarray, torch.Tensor)):
        if isinstance(obs, torch.Tensor):
            obs = obs.detach().cpu().numpy()
        return str(np.round(obs, 1).tolist())

    # 2. Dict Input (Mapping)
    # Prefer explicit position key for GridWorld
    pos = None
    try:
        pos = obs.get('agent_pos') or obs.get('position')
    except AttributeError:
        pass
        
    if pos:
        return f"{pos[0]},{pos[1]}"
            
    # Fallback default
    return "0,0"

# ------------------------------------------------------------------------------
# POP Processes
# ------------------------------------------------------------------------------

@process(
    inputs=['domain_ctx', 
        'domain_ctx.current_observation',
        'domain_ctx.heavy_snn_emotion_vector',
        'domain_ctx.current_exploration_rate',
        'domain_ctx.heavy_gated_network'
    ],
    outputs=['domain_ctx', 'domain_ctx.last_action', 'domain_ctx.heavy_last_q_values'],
    side_effects=[]
)
def select_action_gated(ctx: SystemContext):
    """
    Select action using Neural Brain (Gated Integration Network).
    V3: Tabular Q-Table fallback removed.
    """
    obs = ctx.domain_ctx.current_observation
    emotion = ctx.domain_ctx.heavy_snn_emotion_vector
    
    # 1. Neural Network Check
    net = ctx.domain_ctx.heavy_gated_network
    if net is None:
        ctx.log("CRITICAL: GatedIntegrationNetwork not found. Falling back to random.", level="error")
        action = np.random.randint(0, 8)
        return {
            'last_action': action,
            'heavy_last_q_values': torch.tensor([0.0] * 8).detach()
        }

    # 2. Emotion Tensor Preparation (V3: No more manual Q-table fallback)
    if emotion is None:
        # If SNN is not active yet or emotion is None, use Neutral (Zero) vector
        emo_tensor = torch.zeros(16, dtype=torch.float32)
        emotion_magnitude = 0.0
    else:
        try:
            if isinstance(emotion, (list, tuple)):
                emo_tensor = torch.tensor(emotion, dtype=torch.float32).detach()
            else:
                emo_tensor = emotion
            emotion_magnitude = float(torch.norm(emo_tensor).item())
        except Exception:
            emo_tensor = torch.zeros(16, dtype=torch.float32)
            emotion_magnitude = 0.0

    # 3. Dynamic Exploration
    adjusted_exploration = ctx.domain_ctx.current_exploration_rate * (1.0 + 0.5 * emotion_magnitude)
    adjusted_exploration = min(adjusted_exploration, 1.0)
    
    # 4. Neural Q-Value Prediction
    obs_tensor = observation_to_tensor(obs)
    
    net.eval()
    with torch.no_grad():
        q_values_tensor = net(obs_tensor, emo_tensor)
    net.train()
    
    q_values_list = q_values_tensor.tolist()

    # 5. Action Selection
    if np.random.rand() < adjusted_exploration:
        action = np.random.randint(0, 8)
    else:
        action = int(np.argmax(q_values_list))
    
    return {
        'last_action': action,
        'heavy_last_q_values': torch.tensor(q_values_list, dtype=torch.float32).detach()
    }


@process(
    inputs=['domain_ctx', 
        'domain_ctx.last_reward',
        'domain_ctx.current_observation',
        'domain_ctx.last_action',
        'domain_ctx.heavy_gated_network',
        'domain_ctx.heavy_gated_optimizer',
        'domain_ctx.previous_observation',
        'domain_ctx.heavy_previous_snn_emotion_vector',
        'domain_ctx.heavy_snn_emotion_vector',
        'domain_ctx.metrics'
    ],
    outputs=['domain_ctx', 
        'domain_ctx.td_error',
        'domain_ctx.metrics'
    ],
    side_effects=[]
)
def update_q_learning(ctx: SystemContext):
    """
    Update Neural Brain via Backpropagation (Deep RL).
    V3: Tabular Q-Table updates removed.
    """
    # 0. Check Initialization
    obs_prev = ctx.domain_ctx.previous_observation
    obs_next = ctx.domain_ctx.current_observation
    
    if obs_prev is None or obs_next is None:
        return {'td_error': 0.0}
    
    action = ctx.domain_ctx.last_action
    if action is None or action < 0:
        return {'td_error': 0.0}
    
    # 1. Reward Extraction
    raw_reward = ctx.domain_ctx.last_reward
    if isinstance(raw_reward, dict):
        reward = raw_reward.get('total', 0.0)
    else:
        try:
            reward = float(raw_reward)
        except:
            reward = 0.0
    
    # 2. Neural Network Training
    net = ctx.domain_ctx.heavy_gated_network
    opt = ctx.domain_ctx.heavy_gated_optimizer
    
    if net is None or opt is None:
        return {'td_error': 0.0}
        
    prev_emo = ctx.domain_ctx.heavy_previous_snn_emotion_vector
    curr_emo = ctx.domain_ctx.heavy_snn_emotion_vector
    
    # Neutral fallbacks for emotions in V3
    if prev_emo is None: prev_emo = torch.zeros(16, dtype=torch.float32)
    if curr_emo is None: curr_emo = torch.zeros(16, dtype=torch.float32)
    
    # Ensure tensors
    if isinstance(prev_emo, list): prev_emo = torch.tensor(prev_emo).float()
    if isinstance(curr_emo, list): curr_emo = torch.tensor(curr_emo).float()
    
    state_tensor = observation_to_tensor(obs_prev)
    next_state_tensor = observation_to_tensor(obs_next)
    
    # Forward Pass
    q_values = net(state_tensor, prev_emo)
    current_q_val = q_values[action]
    
    # Target Q Computation (Bellman Equation)
    with torch.no_grad():
        next_q_values = net(next_state_tensor, curr_emo)
        max_next_q = torch.max(next_q_values)
        gamma = 0.95
        target_q_val = torch.tensor(reward, dtype=torch.float32) + gamma * max_next_q
    
    # Backpropagation
    loss = torch.nn.functional.mse_loss(current_q_val, target_q_val)
    td_error = float((target_q_val - current_q_val).item())
    
    opt.zero_grad()
    loss.backward()
    opt.step()
    
    # 3. Update Metrics
    metrics = dict(ctx.domain_ctx.metrics)
    metrics['neural_loss'] = float(loss.item())
    metrics['avg_q_predicted'] = float(torch.mean(q_values).item())
    
    return {
        'td_error': td_error,
        'metrics': metrics
    }
