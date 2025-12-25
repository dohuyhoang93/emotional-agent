from theus import process
from src.core.context import SystemContext
from src.adapters.environment_adapter import EnvironmentAdapter
import numpy as np

@process(
    inputs=['domain.current_observation'], 
    outputs=['domain.current_observation', 'domain.previous_observation'],
    side_effects=['env_adapter.get_sensor_vector']  # Updated
)
def perception(ctx: SystemContext, env_adapter: EnvironmentAdapter, agent_id: int):
    """
    Process: Nhận thức (Perception)
    Mục tiêu: Đọc trạng thái từ môi trường và cập nhật vào Domain Context.
    
    Support cả dict (legacy) và vector (sensor system mới).
    """
    # 1. Lưu observation cũ
    ctx.domain_ctx.previous_observation = ctx.domain_ctx.current_observation
    
    # 2. Lấy observation mới qua Adapter
    # Try sensor vector first (new system), fallback to dict (legacy)
    try:
        raw_obs = env_adapter.get_sensor_vector(agent_id)
        # Verify it's a vector
        if isinstance(raw_obs, np.ndarray) and raw_obs.shape == (16,):
            ctx.domain_ctx.current_observation = raw_obs
        else:
            # Fallback to legacy
            raw_obs = env_adapter.get_observation(agent_id)
            ctx.domain_ctx.current_observation = raw_obs
    except AttributeError:
        # Adapter doesn't have get_sensor_vector, use legacy
        raw_obs = env_adapter.get_observation(agent_id)
        ctx.domain_ctx.current_observation = raw_obs

