from src.context import AgentContext

def adjust_exploration(context: AgentContext) -> AgentContext:
    """
    Process điều chỉnh chính sách hành vi dựa trên Cảm xúc Máy (E_vector).
    Sử dụng logic mới: exploration_rate = base_rate + emotional_boost.
    """
    print("  [P] 5. Adjusting policy...")
    
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
    
    print(f"    > Confidence: {confidence:.3f} -> Uncertainty: {uncertainty:.3f}")
    print(f"    > Emotional Boost: {emotional_boost:.3f}")
    print(f"    > Base Rate: {context.base_exploration_rate:.3f}")
    print(f"    > New Exploration Rate: {final_exploration_rate:.3f}")

    return context