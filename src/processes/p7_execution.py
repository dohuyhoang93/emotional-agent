from src.context import AgentContext
from environment import GridWorld # Thêm import để type hinting

def execute_action(context: AgentContext, environment: GridWorld, agent_id: int) -> AgentContext:
    """
    Process thực thi hành động, nhận phần thưởng, và quan sát trạng thái mới.
    Đã được cập nhật cho môi trường đa tác nhân.
    """
    # 1. Lưu lại quan sát hiện tại (S_t) trước khi hành động
    context.previous_observation = context.current_observation
    
    # 2. Thực hiện hành động đã chọn (a_t) cho agent cụ thể
    extrinsic_reward = environment.perform_action(agent_id, context.selected_action)
    context.last_reward['extrinsic'] = extrinsic_reward
    
    # 3. Quan sát trạng thái mới (S_t+1) của agent cụ thể
    context.current_observation = environment.get_observation(agent_id)
    
    return context

