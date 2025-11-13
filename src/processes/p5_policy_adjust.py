from src.context import AgentContext

def adjust_policy(context: AgentContext) -> AgentContext:
    """
    Process điều chỉnh chính sách hành vi dựa trên Cảm xúc Máy (E_vector).
    """
    print("  [P] 5. Adjusting policy...")
    
    # Giả định:
    # E_vector[0]: Mức độ tự tin/giá trị kỳ vọng của trạng thái hiện tại.
    # E_vector[1]: Mức độ tò mò/bất ổn (sẽ được huấn luyện để tương quan với td_error).
    
    confidence = context.E_vector[0].item()
    
    # Điều chỉnh exploration_rate một cách linh hoạt
    # Nếu tự tin cao -> giảm khám phá, tăng khai thác
    # Nếu tự tin thấp -> tăng khám phá
    decay_modifier = 1.0 - (confidence * 0.01) # Tự tin càng cao, decay càng mạnh
    
    new_exploration_rate = context.policy['exploration_rate'] * context.policy['exploration_decay'] * decay_modifier
    
    context.policy['exploration_rate'] = max(context.policy['min_exploration'], new_exploration_rate)
    
    print(f"    > Tự tin: {confidence:.3f}. Exploration rate được điều chỉnh thành: {context.policy['exploration_rate']:.3f}")

    return context