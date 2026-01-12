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
    # CRITICAL FIX: Always use get_observation to get the full dict (Metadata + Sensor)
    # environment.py has been updated to include 'sensor_vector' in this dict.
    try:
        full_obs = env_adapter.get_observation(agent_id)
        ctx.domain_ctx.current_observation = full_obs
        
        # Validation (Optional)
        # if 'sensor_vector' not in full_obs:
        #     print("WARNING: Sensor vector missing in observation!")
    except Exception as e:
        print(f"Perception Error: {e}")
        # Fallback? No, crash if essential.

