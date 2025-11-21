from src.context import AgentContext
import torch
from src.models import EmotionCalculatorMLP
from src.logger import log, log_error # Import the new logger

def calculate_emotions(context: AgentContext) -> AgentContext:
    """
    Process tính toán E_vector mới bằng MLP.
    """
    log(context, "info", "  [P] 3. Calculating machine emotions...")
    
    # Chuẩn bị các vector đầu vào cho MLP
    n_vector = context.N_vector
    
    # Tạo b_vector phức hợp: vị trí + niềm tin công tắc
    pos_tensor = torch.tensor(context.current_observation['agent_pos'], dtype=torch.float32)
    switch_states_tensor = torch.tensor(
        [float(context.believed_switch_states[key]) for key in sorted(context.believed_switch_states.keys())],
        dtype=torch.float32
    )
    b_vector = torch.cat((pos_tensor, switch_states_tensor))

    m_vector = torch.zeros(1) 

    # Nối các vector lại
    mlp_input = torch.cat((n_vector, b_vector, m_vector))

    # Lấy model từ context
    model = context.emotion_model

    # Tính toán E_vector mới (không có no_grad để cho phép backprop)
    new_e_vector = model(mlp_input)
    
    context.E_vector = new_e_vector
    # In ra giá trị đã được detach khỏi đồ thị tính toán
    log(context, "verbose", f"    > E_vector mới: {context.E_vector.detach().numpy()}")
    
    return context