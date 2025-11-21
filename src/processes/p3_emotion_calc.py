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

    # Tính toán m_vector (Memory Vector) dựa trên hiệu suất gần đây
    if context.short_term_memory:
        # Lấy total_reward từ các mục trong short_term_memory
        rewards = [entry['total_reward'] for entry in context.short_term_memory]
        avg_reward = sum(rewards) / len(rewards)
        # Chuẩn hóa avg_reward vào khoảng [-1, 1] bằng hàm tanh
        m_vector = torch.tensor([torch.tanh(torch.tensor(avg_reward, dtype=torch.float32))], dtype=torch.float32)
        log(context, "verbose", f"    > Avg Reward from STM: {avg_reward:.3f} -> m_vector: {m_vector.item():.3f}")
    else:
        m_vector = torch.zeros(1) # Nếu bộ nhớ rỗng, m_vector là 0
        log(context, "verbose", "    > Short-term memory empty, m_vector is zero.")

    # Nối các vector lại
    mlp_input = torch.cat((n_vector, b_vector, m_vector))

    # Lấy model từ context
    model = context.emotion_model

    # Tính toán E_vector mới (không có no_grad để cho phép backprop)
    new_e_vector = model(mlp_input)
    
    context.E_vector = new_e_vector
    context.confidence = context.E_vector[0].item() # Cập nhật confidence từ E_vector[0]
    # In ra giá trị đã được detach khỏi đồ thị tính toán
    log(context, "verbose", f"    > E_vector mới: {context.E_vector.detach().numpy()}, Confidence: {context.confidence:.3f}")
    
    return context