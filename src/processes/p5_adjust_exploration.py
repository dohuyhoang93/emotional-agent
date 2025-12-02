from src.context import AgentContext
from src.logger import log, log_error # Import the new logger

def adjust_exploration(context: AgentContext) -> AgentContext:
    """
    Process điều chỉnh chính sách hành vi dựa trên Cảm xúc Máy (E_vector).
    Sử dụng logic mới: exploration_rate = base_rate + emotional_boost.
    """
    log(context, "info", "  [P] 5. Adjusting policy...")
    
    # NOTE: confidence được tính và cập nhật vào context trong process p3
    confidence = context.confidence
    
    # 1. Tính toán "Sự không chắc chắn" (Uncertainty)
    uncertainty = 1.0 - confidence
    
    # 2. Tính toán "Sự bùng nổ Cảm xúc" (Emotional Boost)
    # Đây là thành phần phản ứng, tăng vọt khi agent mất tự tin
    emotional_boost = uncertainty * context.emotional_boost_factor
    
    # 3. Cập nhật "Tỷ lệ Khám phá Nền" (Base Rate)
    # Đây là thành phần suy giảm chậm theo thời gian, đại diện cho sự "trưởng thành"
    context.base_exploration_rate *= context.base_exploration_decay
    
    # 4. Tính toán exploration_rate mới
    new_exploration_rate = context.base_exploration_rate + emotional_boost
    
    # 5. Đảm bảo exploration_rate không thấp hơn mức tối thiểu
    final_exploration_rate = max(context.policy['min_exploration'], new_exploration_rate)
    
    # 6. Cập nhật chính sách trong context
    context.policy['exploration_rate'] = final_exploration_rate
    
    log(context, "verbose", f"    > Confidence: {confidence:.3f} -> Uncertainty: {uncertainty:.3f}")
    log(context, "verbose", f"    > Emotional Boost: {emotional_boost:.3f}")
    log(context, "verbose", f"    > Base Rate: {context.base_exploration_rate:.3f}")
    log(context, "verbose", f"    > New Exploration Rate: {final_exploration_rate:.3f}")

    # --- STRATEGY 1: THE FINISHER ---
    # [DISABLED] Tạm thời vô hiệu hóa để kiểm tra hiệu suất khi để exploration tự nhiên
    # Nếu đã đi được 90% chặng đường, ép buộc khai thác mạnh nhưng KHÔNG tuyệt đối (0.05)
    # để tránh bị kẹt trong các vòng lặp vô tận (infinite loops).
    # if context.total_episodes > 0 and context.current_episode > 0.9 * context.total_episodes:
    #     final_exploration_rate = 0.05
    #     context.policy['exploration_rate'] = final_exploration_rate
    #     log(context, "verbose", f"    > [THE FINISHER] Activated! Force exploration to 0.05")

    return context