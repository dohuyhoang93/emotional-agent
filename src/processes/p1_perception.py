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
        ctx.log("Perception Error: env_adapter not found in context.", level="error")
        return {}

    # 1. Prepare Delta
    delta = {}
    
    # 2. Lưu observation cũ
    delta['previous_observation'] = ctx.domain_ctx.current_observation
    
    # 3. Lấy observation mới qua Adapter
    agent_id = int(agent_id) # Force cast to int to fix KeyError '0' if it's string
    
    # Try sensor vector first (new system), fallback to dict (legacy)
    try:
        full_obs = env_adapter.get_observation(agent_id)
        delta['current_observation'] = full_obs
    except Exception as e:
        ctx.log(f"Perception Error: {e}", level="error")
        # Return empty delta on failure to avoid corrupted state
        return {}

    return delta

