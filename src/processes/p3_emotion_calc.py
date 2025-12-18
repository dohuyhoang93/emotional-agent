import torch
from theus import process
from src.core.context import SystemContext

@process(
    inputs=[
        'domain.N_vector', 
        'domain.believed_switch_states', 
        'domain.short_term_memory',
        'domain.current_observation',
        'domain.emotion_model'
    ], 
    outputs=[
        'domain.E_vector'
    ],
    side_effects=[],
    errors=[]
)
def calculate_emotions(ctx: SystemContext):
    """
    Process: Tính toán vector cảm xúc (Machine Emotions).
    Sử dụng MLP (Multi-Layer Perceptron) nhận đầu vào là Needs, Beliefs, Memory.
    """
    domain = ctx.domain_ctx
    
    # 1. Prepare Inputs
    n_vector = domain.N_vector
    
    # Check observation availability
    if not domain.current_observation:
        print("Warning: P3 found no observation. Skipping.")
        return

    pos_tensor = torch.tensor(domain.current_observation['agent_pos'], dtype=torch.float32)
    
    # Sort keys for deterministic order
    switch_keys = sorted(domain.believed_switch_states.keys())
    switch_val_list = [float(domain.believed_switch_states[k]) for k in switch_keys]
    switch_tensor = torch.tensor(switch_val_list, dtype=torch.float32) if switch_val_list else torch.tensor([])
    
    b_vector = torch.cat((pos_tensor, switch_tensor)) if switch_val_list else pos_tensor
    if not switch_val_list: # If no switches, verify dimension match if needed, for now dynamic
        pass

    # Memory Vector (m_vector)
    if domain.short_term_memory:
        # Assuming 'total_reward' key exists in stored memory dict
        rewards = [entry.get('total_reward', 0.0) for entry in domain.short_term_memory]
        avg = sum(rewards) / len(rewards)
        m_vector = torch.tensor([torch.tanh(torch.tensor(avg, dtype=torch.float32))], dtype=torch.float32)
    else:
        m_vector = torch.zeros(1)

    # Concat
    mlp_input = torch.cat((n_vector, b_vector, m_vector))
    
    # 2. Forward Pass
    if domain.emotion_model:
        # Note: We rely on PyTorch's computational graph (autograd) being kept.
        # So we assign the tensor directly.
        new_e = domain.emotion_model(mlp_input)
        domain.E_vector = new_e
    else:
        # Fallback if no model (e.g. testing)
        pass # Keep old E_vector or set to zero?