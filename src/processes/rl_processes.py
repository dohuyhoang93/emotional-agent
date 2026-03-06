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
        'domain_ctx.heavy_q_table',
        'domain_ctx.current_exploration_rate',
        'domain_ctx.heavy_gated_network'
    ],
    outputs=['domain_ctx', 'domain_ctx.last_action', 'domain_ctx.heavy_last_q_values'],
    side_effects=[]
)
def select_action_gated(ctx: SystemContext):
    """
    Select action using emotion gating from SNN.
    """
    obs = ctx.domain_ctx.current_observation
    emotion = ctx.domain_ctx.heavy_snn_emotion_vector
    
    # 1. Fallback: No Emotion -> Standard Epsilon-Greedy
    if emotion is None:
        if np.random.rand() < ctx.domain_ctx.current_exploration_rate:
            action = np.random.randint(0, 8)
        else:
            state_key = observation_to_state_key(obs) # Use helper
            q_values = ctx.domain_ctx.heavy_q_table.get(state_key, [0.0] * 8)
            action = int(np.argmax(q_values))
        
        return {
            'last_action': action,
            'heavy_last_q_values': torch.tensor([0.0] * 8).detach()
        }
    
    # 2. Emotion Magnitude Calculation
    # Compliant check: 'emotion' usually is list or tensor
    try:
        # Convert list to tensor if needed
        if isinstance(emotion, (list, tuple)):
            emo_tensor = torch.tensor(emotion, dtype=torch.float32).detach()
        else:
            emo_tensor = emotion # Assume tensor or compliant object
            
        emotion_magnitude = float(torch.norm(emo_tensor).item())
    except Exception:
        emotion_magnitude = 0.0

    # 3. Dynamic Exploration
    adjusted_exploration = ctx.domain_ctx.current_exploration_rate * (1.0 + 0.5 * emotion_magnitude)
    adjusted_exploration = min(adjusted_exploration, 1.0)
    
    # 4. Q-Value Prediction (Network vs Table)
    if ctx.domain_ctx.heavy_gated_network is not None:
        # Neural Network Path
        net = ctx.domain_ctx.heavy_gated_network
        obs_tensor = observation_to_tensor(obs) # Use helper
        
        net.eval()
        with torch.no_grad():
            q_values_tensor = net(obs_tensor, emo_tensor if 'emo_tensor' in locals() else emotion)
        net.train()
        
        q_values_list = q_values_tensor.tolist()
    else:
        # Tabular Path
        state_key = observation_to_state_key(obs) # Use helper
        q_values_list = ctx.domain_ctx.heavy_q_table.get(state_key, [0.0] * 8)

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
        'domain_ctx.heavy_q_table',
        'domain_ctx.last_reward',
        'domain_ctx.current_observation',
        'domain_ctx.last_action',
        'domain_ctx.heavy_gated_network',
        'domain_ctx.heavy_gated_optimizer',
        'domain_ctx.previous_observation',
        'domain_ctx.heavy_previous_snn_emotion_vector',
        'domain_ctx.heavy_snn_emotion_vector'
    ],
    outputs=['domain_ctx', 
        'domain_ctx.heavy_q_table',
        'domain_ctx.td_error'
    ],
    side_effects=[]
)
def update_q_learning(ctx: SystemContext):
    """
    Update Q-table and Network with TD-learning.
    """
    # 0. Check Initialization
    if ctx.domain_ctx.previous_observation is None:
        ctx.log("DEBUG: previous_observation is None, skipping Q-learning", level="debug")
        return {'td_error': 0.0}
    
    # 1. Prepare State Keys
    obs_prev = ctx.domain_ctx.previous_observation
    obs_next = ctx.domain_ctx.current_observation
    
    if obs_prev is None or obs_next is None:
        ctx.log("DEBUG: One observation is None, skipping Q-learning", level="debug")
        return {'td_error': 0.0}
    
    prev_state_key = observation_to_state_key(obs_prev)
    next_state_key = observation_to_state_key(obs_next)
    
    action = ctx.domain_ctx.last_action
    
    # 2. Reward Extraction
    raw_reward = ctx.domain_ctx.last_reward
    if isinstance(raw_reward, dict):
        reward = raw_reward.get('total', 0.0)
    else:
        try:
            reward = float(raw_reward)
        except:
            reward = 0.0
    
    # MIGRATION FIX: Không tạo dict RỖNG để chứa delta.
    # Engine trong Theus thiết kế theo kiểu Ghi đè (Overwrite) State,
    # Do đó, nếu ta trả về {key: value}, toàn bộ Q-Table sẽ bị xoá và thay bằng 1 cặp {key: value} này.
    # Giải pháp: Lấy nguyên bộ Q-Table hiện tại, cập nhật trực tiếp (mutate), và trả về nguyên bộ đó.
    full_q_table = ctx.domain_ctx.heavy_q_table

    # Check Prev State
    if prev_state_key not in full_q_table:
        full_q_table[prev_state_key] = [0.0] * 8
    else:
        # Self-Healing: Nếu bị hỏng định dạng float do lỗi serialize, Reset.
        val = full_q_table[prev_state_key]
        is_valid = isinstance(val, (list, tuple)) or (hasattr(val, '__class__') and val.__class__.__name__ == 'TrackedList')
        if not is_valid: 
             ctx.log(f"WARNING: Q-Table Corruption detected at {prev_state_key}. Resetting.", level="warn")
             full_q_table[prev_state_key] = [0.0] * 8

    # Check Next State (for max_q)
    if next_state_key not in full_q_table:
        full_q_table[next_state_key] = [0.0] * 8
    else:
        val = full_q_table[next_state_key]
        is_valid = isinstance(val, (list, tuple)) or (hasattr(val, '__class__') and val.__class__.__name__ == 'TrackedList')
        if not is_valid:
             full_q_table[next_state_key] = [0.0] * 8
    
    # Calculation
    current_q_list = full_q_table[prev_state_key]
    next_q_list = full_q_table[next_state_key]
    
    current_q = current_q_list[action]
    max_next_q = max(next_q_list)
    
    gamma = 0.95
    td_error = reward + gamma * max_next_q - current_q
    
    alpha = 0.1
    # Cập nhật mảng trên Q-Table toàn cục
    updated_q_list = list(current_q_list)
    try:
        updated_q_list[action] += alpha * td_error
        full_q_table[prev_state_key] = updated_q_list
    except Exception as e:
        ctx.log(f"CRITICAL ERROR: {e}. Key: {prev_state_key}. Resetting.", level="error")
        full_q_table[prev_state_key] = [0.0] * 8
    
    # Final Result: Trả về ENTIRE TABLE để Engine đồng bộ đè lên State mà không làm mất dữ liệu
    result_delta = {
        'td_error': td_error,
        'heavy_q_table': full_q_table
    }
    
    # 4. Neural Network Training (Deep RL)
    if ctx.domain_ctx.heavy_gated_network is not None and ctx.domain_ctx.heavy_gated_optimizer is not None:
        net = ctx.domain_ctx.heavy_gated_network
        opt = ctx.domain_ctx.heavy_gated_optimizer
        
        prev_emo = ctx.domain_ctx.heavy_previous_snn_emotion_vector
        curr_emo = ctx.domain_ctx.heavy_snn_emotion_vector
        
        if prev_emo is not None and curr_emo is not None:
            # Conversion
            state_tensor = observation_to_tensor(obs_prev)
            next_state_tensor = observation_to_tensor(obs_next)
            
            # Forward Q(s,a)
            # Ensure emotion is tensor compatible
            if isinstance(prev_emo, list): prev_emo = torch.tensor(prev_emo).float()
            if isinstance(curr_emo, list): curr_emo = torch.tensor(curr_emo).float()

            q_values = net(state_tensor, prev_emo)
            current_q_val = q_values[action]
            
            # Target Q
            with torch.no_grad():
                next_q_values = net(next_state_tensor, curr_emo)
                max_next_q_tensor = torch.max(next_q_values)
                target_q_val = reward + 0.95 * max_next_q_tensor
            
            # Backprop
            loss = torch.nn.functional.mse_loss(current_q_val, target_q_val)
            opt.zero_grad()
            loss.backward()
            opt.step()

    return result_delta
