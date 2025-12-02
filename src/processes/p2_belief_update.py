from src.context import AgentContext
from src.logger import log, log_error # Import the new logger

def update_belief(context: AgentContext) -> AgentContext:
    """
    Process cập nhật "niềm tin" dựa trên kinh nghiệm gần nhất.
    Bao gồm suy luận trạng thái công tắc và hình phạt va chạm.
    """
    log(context, "info", "  [P] 2. Updating beliefs...")
    
    if not context.short_term_memory:
        return context

    last_experience = context.short_term_memory[-1]
    # next_state_pos là vị trí (y, x) của agent sau hành động
    next_state_pos = last_experience["next_state"] 

    # --- STRATEGY 3: SHARED BELIEFS (Thần giao cách cảm) ---
    # Cập nhật niềm tin dựa trên sự kiện toàn cục (do bất kỳ agent nào kích hoạt)
    # [DISABLED] Tắt tính năng này để kiểm tra hiệu suất
    # if context.current_observation and 'global_events' in context.current_observation:
    #     for event in context.current_observation['global_events']:
    #         if event['type'] == 'switch_toggle':
    #             switch_id = event['switch_id']
    #             new_state = event['new_state']
    #             context.believed_switch_states[switch_id] = new_state
    #             log(context, "verbose", f"    > [TELEPATHY] Received signal: Switch '{switch_id}' is now {'ON' if new_state else 'OFF'}.") 

    # --- 1. Cập nhật niềm tin về trạng thái công tắc ---
    for switch_id, switch_pos in context.switch_locations.items():
        if next_state_pos == switch_pos:
            # Nếu agent vừa bước vào vị trí công tắc, hãy chuyển đổi niềm tin về trạng thái của công tắc đó
            context.believed_switch_states[switch_id] = not context.believed_switch_states[switch_id]
            log(context, "verbose", f"    > Niềm tin mới: Công tắc '{switch_id}' đã chuyển sang {'BẬT' if context.believed_switch_states[switch_id] else 'TẮT'}.")
            # NOTE: Không cần break vì agent có thể đi qua nhiều công tắc trong một bước (nếu có)
            # Tuy nhiên, trong GridWorld hiện tại, mỗi bước chỉ đến 1 ô.

    # --- 2. Cập nhật Q-value cho hình phạt va chạm (sử dụng trạng thái phức hợp) ---
    # Chuyển đổi vị trí thành trạng thái phức hợp để truy cập Q-table
    composite_state = context.get_composite_state(last_experience["state"])
    composite_next_state = context.get_composite_state(last_experience["next_state"])
    action = last_experience["action"]

    # Nếu hành động không dẫn đến thay đổi trạng thái -> có thể đã đâm vào tường
    if composite_state == composite_next_state and context.last_reward['extrinsic'] < -0.4:
        # Giảm nhẹ Q-value để "tin" rằng hành động này tại trạng thái này là xấu
        penalty = -0.1
        # Đảm bảo composite_state có trong q_table trước khi truy cập
        if composite_state not in context.q_table:
            context.q_table[composite_state] = {a: 0.0 for a in ['up', 'down', 'left', 'right']}
        context.q_table[composite_state][action] += context.learning_rate * penalty
        log(context, "verbose", f"    > Niềm tin mới: Hành động '{action}' tại {composite_state} là xấu (phạt {penalty}).")

    return context