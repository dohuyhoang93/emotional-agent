from src.context import AgentContext

def execute_action(context: AgentContext, environment) -> AgentContext:
    """
    Process thực thi hành động, nhận phần thưởng, và quan sát trạng thái mới.
    Đây là nơi vòng lặp "Hành động-Quan sát" thực sự diễn ra.
    """
    # 1. Lưu lại quan sát hiện tại (S_t) trước khi hành động
    context.previous_observation = context.current_observation
    
    # 2. Thực hiện hành động đã chọn (a_t)
    extrinsic_reward = environment.perform_action(context.selected_action)
    context.last_reward['extrinsic'] = extrinsic_reward
    
    # 3. Quan sát trạng thái mới (S_t+1) ngay sau khi hành động
    context.current_observation = environment.get_observation()
    
    return context

