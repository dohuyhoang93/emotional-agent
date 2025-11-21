from src.context import AgentContext
import torch
import torch.nn.functional as F
from src.logger import log, log_error # Import the new logger

def _calculate_dynamic_weight(cycle_time: float) -> float:
    """
    Tính toán trọng số tò mò (intrinsic_reward_weight) một cách linh động
    dựa trên "Giả thuyết Mệt mỏi" (System Fatigue Hypothesis).
    """
    # Các ngưỡng này có thể được chuyển ra file settings.json trong tương lai
    MIN_CYCLE_TIME = 0.001  # Thời gian xử lý tối thiểu, agent "rảnh rỗi"
    MAX_CYCLE_TIME = 0.01   # Thời gian xử lý tối đa, agent "mệt mỏi"
    MIN_CURIOSITY_WEIGHT = 0.01 # Mức tò mò tối thiểu khi "mệt"
    MAX_CURIOSITY_WEIGHT = 0.1  # Mức tò mò tối đa khi "rảnh"

    if cycle_time <= MIN_CYCLE_TIME:
        return MAX_CURIOSITY_WEIGHT
    if cycle_time >= MAX_CYCLE_TIME:
        return MIN_CURIOSITY_WEIGHT
    
    # Nội suy tuyến tính ngược: cycle_time càng cao, weight càng thấp
    weight = MAX_CURIOSITY_WEIGHT - (
        (cycle_time - MIN_CYCLE_TIME) *
        (MAX_CURIOSITY_WEIGHT - MIN_CURIOSITY_WEIGHT) /
        (MAX_CYCLE_TIME - MIN_CYCLE_TIME)
    )
    return weight

def record_consequences(context: AgentContext) -> AgentContext:
    """
    Process ghi nhận hậu quả, thực hiện cập nhật Q-learning và huấn luyện MLP cảm xúc.
    """
    log(context, "info", "  [P] 8. Recording consequences & Learning...")

    # --- 1. Cập nhật Q-Learning ---
    # Sử dụng trạng thái phức hợp (vị trí + niềm tin về công tắc)
    state = context.get_composite_state(context.previous_observation['agent_pos'])
    action = context.selected_action
    
    # Lấy phần thưởng ngoại lai (được set trong p7_execution)
    reward_extrinsic = context.last_reward['extrinsic']

    # Sử dụng trạng thái phức hợp cho next_state
    next_state = context.get_composite_state(context.current_observation['agent_pos'])
    
    actions = ['up', 'down', 'left', 'right']
    if next_state not in context.q_table:
        context.q_table[next_state] = {act: 0.0 for act in actions}

    old_q_value = context.q_table[state][action]
    next_max_q = max(context.q_table[next_state].values())

    # --- Logic tính R_nội mới ---
    # 1. Tính TD-error chỉ dựa trên phần thưởng ngoại lai để đo lường "sự ngạc nhiên cơ bản"
    extrinsic_td_error = reward_extrinsic + context.discount_factor * next_max_q - old_q_value
    
    # 2. Tính phần thưởng nội tại dựa trên sự ngạc nhiên đó
    if context.use_dynamic_curiosity:
        dynamic_intrinsic_weight = _calculate_dynamic_weight(context.last_cycle_time)
        log(context, "verbose", f"    > Dynamic Weight: {dynamic_intrinsic_weight:.4f}")
    else:
        dynamic_intrinsic_weight = context.intrinsic_reward_weight
    
    reward_intrinsic = dynamic_intrinsic_weight * abs(extrinsic_td_error)
    context.last_reward['intrinsic'] = reward_intrinsic # Lưu lại để log

    # 3. Tính tổng phần thưởng
    total_reward = reward_extrinsic + reward_intrinsic

    # 4. Tính toán TD-error cuối cùng và cập nhật Q-value
    final_td_error = total_reward + context.discount_factor * next_max_q - old_q_value
    new_q_value = old_q_value + context.learning_rate * final_td_error
    
    context.q_table[state][action] = new_q_value
    context.td_error = final_td_error # Cập nhật td_error chính của context
    
    log(context, "verbose", f"    > R_ngoại: {reward_extrinsic:.2f}, R_nội: {reward_intrinsic:.3f} -> Total: {total_reward:.3f}")
    log(context, "verbose", f"    > Cập nhật Q-value cho (state={state}, action='{action}') thành {new_q_value:.3f}")

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
    
    log(context, "verbose", f"    > Huấn luyện MLP: Total Loss={total_loss.item():.4f} (Value Loss: {loss_value.item():.4f}, Curiosity Loss: {loss_curiosity.item():.4f})")

    # --- 3. Ghi log vào bộ nhớ ngắn hạn ---
    log_entry = {
        "state": state, # Lưu trạng thái phức hợp
        "action": action,
        "next_state": next_state, # Lưu trạng thái phức hợp
        "total_reward": total_reward
    }
    context.short_term_memory.append(log_entry)
    # Giới hạn bộ nhớ để tránh quá tải
    if len(context.short_term_memory) > 100:
        context.short_term_memory.pop(0)

    return context
