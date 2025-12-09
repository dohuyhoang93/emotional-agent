from src.core.engine import process
from src.core.context import SystemContext

@process(
    inputs=[
        'domain.short_term_memory', 
        'global.switch_locations', 
        'domain.believed_switch_states', 
        'domain.q_table',
        'domain.last_reward'
    ], 
    outputs=[
        'domain.believed_switch_states', 
        'domain.q_table'
    ],
    side_effects=[],
    errors=[]
)
def update_belief(ctx: SystemContext):
    """
    Process: Cập nhật niềm tin (Belief Update)
    Logic: Dựa vào ký ức hành động trước đó để suy luận trạng thái công tắc và tránh tường.
    """
    domain = ctx.domain_ctx
    global_cfg = ctx.global_ctx
    
    if not domain.short_term_memory:
        return

    last_experience = domain.short_term_memory[-1]
    # last_experience structure assumed: {'state':..., 'action':..., 'reward':..., 'next_state':..., 'done':...}
    
    next_state_pos = last_experience["next_state"] # Tuple (y, x)
    
    # 1. Cập nhật niềm tin về công tắc
    # Nếu agent đi vào ô công tắc, ta tin rằng công tắc đó đã đảo trạng thái (Toggle)
    for switch_id, switch_pos in global_cfg.switch_locations.items():
        if next_state_pos == switch_pos:
            domain.believed_switch_states[switch_id] = not domain.believed_switch_states[switch_id]
            # Log could go here
            
    # 2. Heuristic: Phạt va chạm
    # Nếu agent đứng yên sau hành động (composite state không đổi) và reward thấp -> đâm vào tường?
    # Cần logic tính composite state. Trong legacy code, hàm này nằm trong AgentContext.
    # Trong POP mới, nó nên là một Utility Helper hoặc method của DomainContext? 
    # Tạm thời tái hiện logic tính toán trạng thái phức hợp ở đây (Helper function).
    
    state_pos = last_experience["state"]
    action = last_experience["action"]
    
    # Helper lấy trạng thái (Pos + Switches)
    def get_composite_key(pos, switches):
        # Sort keys for deterministic order
        switch_vals = tuple(switches[k] for k in sorted(switches.keys()))
        return pos + switch_vals

    current_composite = get_composite_key(state_pos, domain.believed_switch_states)
    next_composite = get_composite_key(next_state_pos, domain.believed_switch_states)
    
    # Nếu trạng thái không đổi và bị phạt nặng -> Đâm tường
    # Note: Using last_reward['extrinsic'] instead of memory for raw penalty check
    if current_composite == next_composite and domain.last_reward['extrinsic'] < -0.4:
        penalty = -0.1
        if current_composite not in domain.q_table:
            domain.q_table[current_composite] = {a: 0.0 for a in ['up', 'down', 'left', 'right']}
        
        domain.q_table[current_composite][action] += global_cfg.learning_rate * penalty