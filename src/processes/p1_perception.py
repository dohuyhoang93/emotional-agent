from theus.contracts import process
from src.core.context import SystemContext
from src.adapters.environment_adapter import EnvironmentAdapter
import numpy as np



@process(
    inputs=['domain_ctx', 'domain_ctx.current_observation'], 
    outputs=['domain_ctx', 'domain_ctx.current_observation', 'domain_ctx.previous_observation'],
    side_effects=['env_adapter.get_sensor_vector']  # Updated
)
def perception(ctx: SystemContext, env_adapter: EnvironmentAdapter = None, agent_id: int = None):
    """
    Process: Nhận thức (Perception)
    Mục tiêu: Đọc trạng thái từ môi trường và cập nhật vào Domain Context.
    
    Support cả dict (legacy) và vector (sensor system mới).
    """
    # Auto-resolve dependencies from context if not passed (for Engine compatibility)
    if env_adapter is None:
        env_adapter = getattr(ctx.domain_ctx, 'env_adapter', None)
    if agent_id is None:
        agent_id = getattr(ctx.domain_ctx, 'agent_id', 0)
        
    if env_adapter is None:
        # Cannot proceed without adapter
        return
    # 1. Lưu observation cũ
    ctx.domain_ctx.previous_observation = ctx.domain_ctx.current_observation
    
    # 2. Lấy observation mới qua Adapter
    agent_id = int(agent_id) # Force cast to int to fix KeyError '0' if it's string
    
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

