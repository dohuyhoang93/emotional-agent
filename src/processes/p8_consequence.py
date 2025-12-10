import torch
import torch.nn.functional as F
from src.core.engine import process
from src.core.context import SystemContext

def _calculate_dynamic_weight(cycle_time, current_step, current_episode, total_episodes, use_adaptive, max_fatigue_growth, max_steps):
    """
    Helper: Tính toán trọng số tò mò (Intrinsic Weight).
    Giữ nguyên logic từ code cũ.
    """
    MIN_CURIOSITY_WEIGHT = 0.01
    MAX_CURIOSITY_WEIGHT = 0.1

    # Safe defaults if None
    cycle_time = cycle_time if cycle_time is not None else 0.001
    
    if use_adaptive:
        normalized_cycle_time = cycle_time * 1000 
        progress = current_episode / max(1, total_episodes)
        fatigue_index = (normalized_cycle_time * current_step) * (1 + max_fatigue_growth * progress)
        
        FATIGUE_THRESHOLD_START = 0.0
        FATIGUE_THRESHOLD_END = max_steps * 1.5

        if fatigue_index <= FATIGUE_THRESHOLD_START:
            return MAX_CURIOSITY_WEIGHT
        if fatigue_index >= FATIGUE_THRESHOLD_END:
            return MIN_CURIOSITY_WEIGHT
            
        weight = MAX_CURIOSITY_WEIGHT - (
            (fatigue_index - FATIGUE_THRESHOLD_START) *
            (MAX_CURIOSITY_WEIGHT - MIN_CURIOSITY_WEIGHT) /
            (FATIGUE_THRESHOLD_END - FATIGUE_THRESHOLD_START)
        )
        return weight
    else:
        MIN_CYCLE_TIME = 0.001
        MAX_CYCLE_TIME = 0.01

        if cycle_time <= MIN_CYCLE_TIME:
            return MAX_CURIOSITY_WEIGHT
        if cycle_time >= MAX_CYCLE_TIME:
            return MIN_CURIOSITY_WEIGHT
        return MAX_CURIOSITY_WEIGHT - ((cycle_time - MIN_CYCLE_TIME) * (MAX_CURIOSITY_WEIGHT - MIN_CURIOSITY_WEIGHT) / (MAX_CYCLE_TIME - MIN_CYCLE_TIME))

@process(
    inputs=[
        'domain.previous_observation', 'domain.current_observation', 'domain.selected_action', 'domain.last_reward',
        'domain.q_table', 'domain.believed_switch_states', 'domain.short_term_memory',
        'domain.E_vector', 'domain.emotion_optimizer', 'domain.emotion_model', 'domain.td_error',
        'global.learning_rate', 'global.discount_factor', 'global.use_dynamic_curiosity',
        'domain.last_cycle_time', 'domain.current_episode', 'domain.current_step',
        'global.total_episodes', 'global.use_adaptive_fatigue', 'global.fatigue_growth_rate', 'global.max_steps',
        'global.intrinsic_reward_weight', 'global.short_term_memory_limit'
    ],
    outputs=[
        'domain.q_table', 'domain.td_error', 'domain.last_reward', 'domain.short_term_memory', 'domain.E_vector'
        # E_vector is updated via optimizer step (technically pure output? No, side effect on torch graph, but we say it outputs updated state)
    ],
    side_effects=[],
    errors=[]
)
def record_consequences(ctx: SystemContext):
    """
    Process: Ghi nhận hậu quả (Consequence & Learning).
    Cập nhật Q-Table, tính toán phần thưởng nội tại, và huấn luyện mô hình cảm xúc.
    """
    domain = ctx.domain_ctx
    global_cfg = ctx.global_ctx
    
    # 0. Helper State Key
    def get_composite_key(pos, switches):
        switch_vals = tuple(switches[k] for k in sorted(switches.keys()))
        return pos + switch_vals

    if not domain.previous_observation or not domain.current_observation:
        # print("Warning: Missing observation trace. Skipping P8.")
        return

    # 1. State & Next State
    prev_pos = domain.previous_observation['agent_pos']
    curr_pos = domain.current_observation['agent_pos']
    
    state = get_composite_key(prev_pos, domain.believed_switch_states)
    next_state = get_composite_key(curr_pos, domain.believed_switch_states) # Note: assumes belief hasn't changed *within* P7? P2 runs before P3... P8 runs last. OK.
    
    action = domain.selected_action
    
    # 2. Extrinsic Reward
    reward_extrinsic = domain.last_reward['extrinsic']
    
    # Init Q-Table entry if new
    actions = ['up', 'down', 'left', 'right']
    if next_state not in domain.q_table:
        domain.q_table[next_state] = {act: 0.0 for act in actions}
    if state not in domain.q_table:
        domain.q_table[state] = {act: 0.0 for act in actions} # Should exist but just in case
        
    old_q_value = domain.q_table[state].get(action, 0.0)
    next_max_q = max(domain.q_table[next_state].values())
    
    extrinsic_td_error = reward_extrinsic + global_cfg.discount_factor * next_max_q - old_q_value
    
    # 3. Intrinsic Reward
    if global_cfg.use_dynamic_curiosity:
        # Step count from observation or domain?
        step_count = domain.current_observation.get('step_count', 1)
        
        cycle_time = getattr(domain, 'last_cycle_time', 0.001) # Safety get
        
        weight = _calculate_dynamic_weight(
            cycle_time, step_count, domain.current_episode, 
            global_cfg.total_episodes, global_cfg.use_adaptive_fatigue, 
            global_cfg.fatigue_growth_rate, global_cfg.max_steps
        )
    else:
        weight = global_cfg.intrinsic_reward_weight
        
    reward_intrinsic = weight * abs(extrinsic_td_error)
    domain.last_reward['intrinsic'] = reward_intrinsic
    
    total_reward = reward_extrinsic + reward_intrinsic
    
    # 4. Final Q Update
    final_td_error = total_reward + global_cfg.discount_factor * next_max_q - old_q_value
    new_q_value = old_q_value + global_cfg.learning_rate * final_td_error
    
    domain.q_table[state][action] = new_q_value
    domain.td_error = final_td_error
    
    # 5. Train Emotion Model (MLP)
    if domain.emotion_model and domain.emotion_optimizer:
        # Target 1: Value Prediction (Confidence -> Q Value)
        predicted_value = domain.E_vector[0]
        target_value = torch.tensor(next_max_q * global_cfg.discount_factor, dtype=torch.float32)
        loss_value = F.mse_loss(predicted_value, target_value)
        
        # Target 2: Curiosity Prediction (Excitement -> TD Error)
        normalized_td = torch.tensor(min(1.0, abs(domain.td_error)), dtype=torch.float32)
        predicted_curiosity = domain.E_vector[1]
        loss_curiosity = F.mse_loss(predicted_curiosity, normalized_td)
        
        total_loss = loss_value + loss_curiosity
        
        domain.emotion_optimizer.zero_grad()
        total_loss.backward()
        domain.emotion_optimizer.step()
        # Note: E_vector updates via backward/optimizer step? No, optimizer updates weights. 
        # E_vector itself is output of Model. It changes *next time* model runs (P3).
        # But wait, P3 sets `domain.E_vector`.
        # Here we just train the weights.
        
    # 6. Update Memory
    log_entry = {
        "state": state, # Actually storing key (tuple) is fine? Legacy stored composite. Yes.
        "action": action,
        "next_state": next_state, # store tuple
        "total_reward": total_reward
    }
    domain.short_term_memory.append(log_entry)
    if len(domain.short_term_memory) > global_cfg.short_term_memory_limit:
        domain.short_term_memory.pop(0)
