# Root Cause: Broken Q-Learning Implementation

## Vấn đề phát hiện

**Success rate: 1/104 episodes (~1%)**

## Root Cause

### Q-Learning Update hiện tại (SAI):

```python
# src/processes/rl_processes.py, line 237-245
def update_q_learning(ctx: SystemContext):
    current_q = ctx.domain_ctx.q_table[state][action]
    
    # TD-error (simplified - no next state) ← VẤN ĐỀ Ở ĐÂY!
    td_error = reward - current_q
    
    # Update Q-value
    alpha = 0.1
    ctx.domain_ctx.q_table[state][action] += alpha * td_error
```

### Vấn đề:

**TD-error chỉ dùng immediate reward**, không có next state!

```
td_error = reward - Q(s, a)
```

**Đúng phải là**:
```
td_error = reward + gamma * max(Q(s', a')) - Q(s, a)
```

### Tại sao đây là vấn đề nghiêm trọng?

1. **Không học được long-term value**
   - Agent chỉ học immediate reward
   - Không biết action nào dẫn đến goal trong tương lai

2. **Logic maze task**
   - Cần bật switch trước
   - Rồi mới đến goal
   - Reward chỉ có ở goal
   - → Agent không biết "bật switch" có giá trị

3. **Ví dụ cụ thể**:
   ```
   State A: Đứng trước switch
   Action: Bật switch
   Reward: 0 (không có immediate reward)
   
   Current Q-learning:
   td_error = 0 - Q(A, bật) = -Q(A, bật)
   → Q(A, bật) giảm! ❌
   
   Correct Q-learning:
   td_error = 0 + gamma * max(Q(B, ...)) - Q(A, bật)
   → Nếu Q(B, ...) cao (gần goal), Q(A, bật) tăng! ✅
   ```

---

## Fix

### Option 1: Fix Tabular Q-Learning

```python
def update_q_learning(ctx: SystemContext):
    # Current state & action
    state = str(ctx.domain_ctx.current_observation)
    action = ctx.domain_ctx.last_action
    reward = ctx.domain_ctx.last_reward.get('total', 0.0)
    
    # Next state
    next_state = str(ctx.domain_ctx.current_observation)  # After action
    
    # Initialize Q-values
    if state not in ctx.domain_ctx.q_table:
        ctx.domain_ctx.q_table[state] = [0.0] * 4
    if next_state not in ctx.domain_ctx.q_table:
        ctx.domain_ctx.q_table[next_state] = [0.0] * 4
    
    # Q-learning update
    current_q = ctx.domain_ctx.q_table[state][action]
    max_next_q = max(ctx.domain_ctx.q_table[next_state])
    
    # Correct TD-error
    gamma = 0.95
    td_error = reward + gamma * max_next_q - current_q
    
    # Update
    alpha = 0.1
    ctx.domain_ctx.q_table[state][action] += alpha * td_error
    
    ctx.domain_ctx.td_error = td_error
```

### Vấn đề với Option 1:

**Confusion về state timing**:
- `current_observation` là state SAU action
- Cần `previous_observation` (state TRƯỚC action)

### Option 2: Sử dụng previous_observation

```python
def update_q_learning(ctx: SystemContext):
    # Previous state (before action)
    prev_state = str(ctx.domain_ctx.previous_observation)
    
    # Current state (after action = next state)
    next_state = str(ctx.domain_ctx.current_observation)
    
    action = ctx.domain_ctx.last_action
    reward = ctx.domain_ctx.last_reward.get('total', 0.0)
    
    # Skip if no previous state (first step)
    if ctx.domain_ctx.previous_observation is None:
        ctx.domain_ctx.td_error = 0.0
        return
    
    # Initialize Q-values
    if prev_state not in ctx.domain_ctx.q_table:
        ctx.domain_ctx.q_table[prev_state] = [0.0] * 4
    if next_state not in ctx.domain_ctx.q_table:
        ctx.domain_ctx.q_table[next_state] = [0.0] * 4
    
    # Q-learning update
    current_q = ctx.domain_ctx.q_table[prev_state][action]
    max_next_q = max(ctx.domain_ctx.q_table[next_state])
    
    # Correct TD-error
    gamma = 0.95
    td_error = reward + gamma * max_next_q - current_q
    
    # Update
    alpha = 0.1
    ctx.domain_ctx.q_table[prev_state][action] += alpha * td_error
    
    ctx.domain_ctx.td_error = td_error
```

---

## Dự kiến kết quả

### Trước fix:
- Success rate: ~1%
- Agent random walk

### Sau fix:
- Success rate: ~50-80% (sau 100-200 episodes)
- Agent học được sequence: đến switch → bật → đến goal

---

## Implementation

Tôi sẽ implement Option 2 vì:
1. Đúng về mặt lý thuyết
2. `previous_observation` đã có trong context
3. Đơn giản, rõ ràng
