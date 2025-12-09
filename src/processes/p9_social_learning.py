from typing import List
import numpy as np
from src.core.engine import process
from src.core.context import SystemContext, DomainContext

def _is_stagnated(domain: DomainContext, stagnation_threshold: int = 50) -> bool:
    """Helper: Kiểm tra trạng thái bế tắc."""
    results = domain.long_term_memory.get('episode_results', [])
    if len(results) < stagnation_threshold:
        return False
    
    recent_results = results[-stagnation_threshold:]
    recent_success_rate = np.mean([r['success'] for r in recent_results])
    
    if recent_success_rate < 0.05:
        return True
    
    if domain.current_episode % 500 == 0:
        return True
        
    return False

@process(
    inputs=[
        'domain.q_table', 'domain.long_term_memory', 'domain.current_episode',
        'global.assimilation_rate', 'neighbors', 'agent_id'
        # 'neighbors' is expected to be passed as kwarg: List[SystemContext] or List[DomainContext]
    ],
    outputs=[
        'domain.q_table'
    ],
    side_effects=[],
    errors=[]
)
def social_learning(ctx: SystemContext, neighbors: List[SystemContext], agent_id: int):
    """
    Process: Học hỏi Xã hội (Social Learning).
    Nếu agent bế tắc, học từ agent giỏi nhất (Assimilate) và tránh sai lầm của agent tệ nhất (Aversive).
    """
    domain = ctx.domain_ctx
    global_cfg = ctx.global_ctx
    
    # 0. Check Stagnation
    if not _is_stagnated(domain):
        return

    # Check Control Group
    if global_cfg.assimilation_rate <= 0:
        return

    # 1. Find Best Agent
    best_agent_ctx = None
    max_success_rate = -1.0
    
    # Pre-calculate own success rate
    own_results = domain.long_term_memory.get('episode_results', [])
    own_success_rate = np.mean([r['success'] for r in own_results]) if own_results else 0.0

    for i, other_sys_ctx in enumerate(neighbors):
        if i == agent_id:
            continue
        
        other_domain = other_sys_ctx.domain_ctx
        other_results = other_domain.long_term_memory.get('episode_results', [])
        if not other_results:
            continue
            
        other_rate = np.mean([r['success'] for r in other_results])
        if other_rate > max_success_rate:
            max_success_rate = other_rate
            best_agent_ctx = other_domain

    # 2. Assimilate (Positive)
    if best_agent_ctx and max_success_rate > own_success_rate:
        assimilATE = global_cfg.assimilation_rate
        for state, actions in best_agent_ctx.q_table.items():
            if state not in domain.q_table:
                domain.q_table[state] = actions.copy()
            else:
                for act, q_val in actions.items():
                    curr_q = domain.q_table[state].get(act, 0.0)
                    domain.q_table[state][act] = (1 - assimilATE) * curr_q + assimilATE * q_val

    # 3. Find Worst Agent
    worst_agent_ctx = None
    min_success_rate = 1.1
    
    for i, other_sys_ctx in enumerate(neighbors):
        if i == agent_id:
            continue
        other_domain = other_sys_ctx.domain_ctx
        other_results = other_domain.long_term_memory.get('episode_results', [])
        if not other_results:
            continue
        other_rate = np.mean([r['success'] for r in other_results])
        if other_rate < min_success_rate:
            min_success_rate = other_rate
            worst_agent_ctx = other_domain
            
    # 4. Aversive Learning (Negative)
    if worst_agent_ctx and min_success_rate < own_success_rate:
        MISTAKE_THRESHOLD = -1.0
        PUNISHMENT = -10.0
        
        for state, actions in worst_agent_ctx.q_table.items():
            for act, q_val in actions.items():
                if q_val < MISTAKE_THRESHOLD:
                    # If I don't know this state, or I think it's okay -> PUNISH IT
                    if state not in domain.q_table:
                        domain.q_table[state] = {a:0.0 for a in ['up','down','left','right']}
                    
                    if domain.q_table[state].get(act, 0.0) > MISTAKE_THRESHOLD:
                        domain.q_table[state][act] = PUNISHMENT
