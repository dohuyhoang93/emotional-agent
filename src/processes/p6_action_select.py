import random
from theus import process
from src.core.context import SystemContext

@process(
    inputs=[
        'domain.current_observation',
        'domain.believed_switch_states',
        'domain.q_table',
        'domain.current_exploration_rate'
    ],
    outputs=[
        'domain.selected_action'
    ],
    side_effects=[],
    errors=[]
)
def select_action(ctx: SystemContext):
    """
    Process: Lựa chọn hành động (Action Selection)
    Chiến lược: Epsilon-Greedy dựa trên Q-Table và Current Exploration Rate.
    """
    domain = ctx.domain_ctx
    
    # Define Actions
    actions = ['up', 'down', 'left', 'right']
    
    # 1. Check Exploration (Epsilon check)
    if random.random() < domain.current_exploration_rate:
        action = random.choice(actions)
        domain.selected_action = action
        return

    # 2. Exploitation (Max Q)
    # Re-calculate composite state key
    obs = domain.current_observation
    agent_pos = obs['agent_pos']
    
    # Helper (Duplicated from P2 - Should be utils)
    def get_composite_key(pos, switches):
        switch_vals = tuple(switches[k] for k in sorted(switches.keys()))
        return pos + switch_vals

    state_key = get_composite_key(agent_pos, domain.believed_switch_states)
    
    # Lookup Q-Values
    if state_key not in domain.q_table:
        # If unknown state, default to 0.0 for all
        q_values = {a: 0.0 for a in actions}
    else:
        q_values = domain.q_table[state_key]
        
    # Pick Max
    # Shuffle actions to break ties randomly instead of always picking first
    shuffled_actions = actions[:]
    random.shuffle(shuffled_actions)
    
    best_action = shuffled_actions[0]
    best_val = q_values.get(best_action, 0.0)
    
    for a in shuffled_actions[1:]:
        val = q_values.get(a, 0.0)
        if val > best_val:
            best_val = val
            best_action = a
            
    domain.selected_action = best_action
