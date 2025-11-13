from src.context import AgentContext

def update_belief(context: AgentContext) -> AgentContext:
    """
    Process cập nhật "niềm tin" dựa trên kinh nghiệm gần nhất.
    Ví dụ: nếu hành động không làm thay đổi trạng thái (đâm vào tường),
    hãy giảm nhẹ Q-value của hành động đó như một hình phạt tức thì.
    """
    print("  [P] 2. Updating beliefs...")
    
    if not context.short_term_memory:
        return context

    last_experience = context.short_term_memory[-1]
    state = last_experience["state"]
    action = last_experience["action"]
    next_state = last_experience["next_state"]

    # Nếu hành động không dẫn đến thay đổi trạng thái -> có thể đã đâm vào tường
    if state == next_state and context.last_reward['extrinsic'] < -0.4:
        # Giảm nhẹ Q-value để "tin" rằng hành động này tại trạng thái này là xấu
        penalty = -0.1
        context.q_table[state][action] += context.learning_rate * penalty
        print(f"    > Niềm tin mới: Hành động '{action}' tại {state} là xấu (phạt {penalty}).")

    return context