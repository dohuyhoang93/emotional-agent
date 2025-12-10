from src.core.engine import process
from src.core.context import SystemContext
from src.adapters.environment_adapter import EnvironmentAdapter

@process(
    inputs=['env_adapter', 'agent_id', 'domain.current_observation'], 
    outputs=['domain.current_observation', 'domain.previous_observation'],
    side_effects=['env_adapter.get_observation']
)
def perception(ctx: SystemContext, env_adapter: EnvironmentAdapter, agent_id: int):
    """
    Process: Nhận thức (Perception)
    Mục tiêu: Đọc trạng thái từ môi trường và cập nhật vào Domain Context.
    """
    # 1. Lưu observation cũ
    ctx.domain_ctx.previous_observation = ctx.domain_ctx.current_observation
    
    # 2. Lấy observation mới qua Adapter
    raw_obs = env_adapter.get_observation(agent_id)
    
    # 3. Cập nhật vào Domain Context
    # Lưu ý: raw_obs là dict {'agent_pos': ..., 'step_count': ..., ...}
    ctx.domain_ctx.current_observation = raw_obs
    
    # (Optional) Log nếu cần thiết, nhưng nên hạn chế log trong process high-frequency
    # print(f"Agent {agent_id} perceived: {raw_obs['agent_pos']}")
