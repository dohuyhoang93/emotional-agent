from src.context import AgentContext
import torch
import torch.nn.functional as F

def record_consequences(context: AgentContext) -> AgentContext:
    """
    Process ghi nhận hậu quả, thực hiện cập nhật Q-learning và huấn luyện MLP cảm xúc.
    """
    print("  [P] 8. Recording consequences & Learning...")

    # --- 1. Cập nhật Q-Learning ---
    state = context.previous_observation['agent_pos']
    action = context.selected_action
    
    # Lấy phần thưởng đã được tính toán từ các process trước
    reward_extrinsic = context.last_reward['extrinsic']
    reward_intrinsic = context.last_reward['intrinsic']
    total_reward = reward_extrinsic + reward_intrinsic
    
    next_state = context.current_observation['agent_pos']
    
    actions = ['up', 'down', 'left', 'right']
    if next_state not in context.q_table:
        context.q_table[next_state] = {act: 0.0 for act in actions}

    old_q_value = context.q_table[state][action]
    next_max_q = max(context.q_table[next_state].values())
    
    new_q_value = old_q_value + context.learning_rate * (total_reward + context.discount_factor * next_max_q - old_q_value)
    context.q_table[state][action] = new_q_value
    context.td_error = total_reward + context.discount_factor * next_max_q - old_q_value
    
    print(f"    > R_ngoại: {reward_extrinsic:.2f}, R_nội: {reward_intrinsic:.3f} -> Total: {total_reward:.3f}")
    print(f"    > Cập nhật Q-value cho (state={state}, action='{action}') thành {new_q_value:.3f}")

    # --- 2. Huấn luyện MLP Cảm xúc (Mục tiêu kép) ---
    # Mục tiêu 1: Huấn luyện E_vector[0] (tự tin) để dự đoán giá trị của trạng thái (next_max_q)
    predicted_value = context.E_vector[0]
    target_value = torch.tensor(next_max_q * context.discount_factor, dtype=torch.float32)
    loss_value = F.mse_loss(predicted_value, target_value)

    # Mục tiêu 2: Huấn luyện E_vector[1] (tò mò) để phản ánh sự ngạc nhiên (td_error)
    # Chuẩn hóa td_error về khoảng [0, 1] để làm mục tiêu cho hàm sigmoid
    normalized_td_error = torch.tensor(min(1.0, abs(context.td_error)), dtype=torch.float32)
    predicted_curiosity = context.E_vector[1]
    loss_curiosity = F.mse_loss(predicted_curiosity, normalized_td_error)

    # Tổng hợp loss và lan truyền ngược
    total_loss = loss_value + loss_curiosity
    
    optimizer = context.emotion_optimizer
    optimizer.zero_grad()
    total_loss.backward()
    optimizer.step()
    
    print(f"    > Huấn luyện MLP: Total Loss={total_loss.item():.4f} (Value Loss: {loss_value.item():.4f}, Curiosity Loss: {loss_curiosity.item():.4f})")

    # --- 3. Ghi log vào bộ nhớ ngắn hạn ---
    log_entry = {
        "state": state,
        "action": action,
        "next_state": next_state,
        "total_reward": total_reward
    }
    context.short_term_memory.append(log_entry)
    # Giới hạn bộ nhớ để tránh quá tải
    if len(context.short_term_memory) > 100:
        context.short_term_memory.pop(0)

    return context