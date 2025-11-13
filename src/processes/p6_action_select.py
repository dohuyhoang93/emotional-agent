from src.context import AgentContext
import random
import numpy as np

def select_action(context: AgentContext) -> AgentContext:
    print("  [P] 6. Selecting action...")
    
    actions = ['up', 'down', 'left', 'right']
    state = context.current_observation['agent_pos']

    # Khởi tạo Q-value cho trạng thái mới nếu chưa có
    if state not in context.q_table:
        context.q_table[state] = {action: 0.0 for action in actions}

    # Logic chọn hành động: Epsilon-Greedy
    if random.random() < context.policy['exploration_rate']:
        # Khám phá: chọn hành động ngẫu nhiên
        context.selected_action = random.choice(actions)
        print(f"    > (Khám phá) Hành động được chọn: {context.selected_action}")
    else:
        # Khai thác: chọn hành động tốt nhất từ Q-table
        q_values = context.q_table[state]
        max_q_value = max(q_values.values())
        best_actions = [action for action, q in q_values.items() if q == max_q_value]
        context.selected_action = random.choice(best_actions) # Chọn ngẫu nhiên nếu có nhiều hành động tốt nhất
        print(f"    > (Khai thác) Hành động được chọn: {context.selected_action}")
        
    return context
