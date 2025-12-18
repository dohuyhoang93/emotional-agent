from theus import process
from src.core.context import SystemContext
from src.adapters.environment_adapter import EnvironmentAdapter

@process(
    inputs=[
        'domain.selected_action',
        'domain.current_observation',
        'domain.last_reward'
    ], 
    outputs=[
        'domain.current_observation',
        'domain.previous_observation',
        'domain.last_reward'
    ],
    side_effects=[
        'env_adapter.perform_action',
        'env_adapter.get_observation'
    ]
)
def execute_action(ctx: SystemContext, env_adapter: EnvironmentAdapter, agent_id: int):
    """
    Process: Thực thi hành động (Execution)
    Tác động vật lý lên môi trường và nhận lại Reward + Quan sát mới.
    """
    domain = ctx.domain_ctx
    
    # 1. Archive current State to Previous
    # (Để phục vụ cho P8 tính toán TD-Error: S, A, R, S')
    domain.previous_observation = domain.current_observation
    
    # 2. Execute Action
    action = domain.selected_action
    if action is None:
        # Fallback if no action selected (should not happen if P6 runs)
        action = 'up' # Dummy or skip?
    
    reward = env_adapter.perform_action(agent_id, action)
    domain.last_reward['extrinsic'] = reward
    
    # 3. Perceive Result (Strictly speaking, this should be a separate P1 call)
    # But for compatibility with legacy workflow list, we do it here.
    new_obs = env_adapter.get_observation(agent_id)
    domain.current_observation = new_obs
