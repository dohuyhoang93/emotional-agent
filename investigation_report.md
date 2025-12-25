# Investigation Report: Why R-STDP Can't Learn Causality

**Ngày:** 2025-12-25  
**Goal:** Find why R-STDP + 16-dim vectors can't learn switch→gate causality

---

## Area 1: Trace Decay Parameters ✅

### Current Values

```python
# From src/core/snn_context_theus.py (line 57-58)
tau_trace_fast: float = 0.9      # Fast trace decay ~20ms
tau_trace_slow: float = 0.9998   # Slow trace decay ~5000ms
```

### Analysis

**Trace Lifetime Calculation:**
- `tau_trace_slow = 0.9998`
- After N steps: `trace = 0.9998^N`
- Half-life: `0.5 = 0.9998^N` → `N = ln(0.5)/ln(0.9998) ≈ 3465 steps`

**Typical Switch→Gate Delay:**
- Agent toggles switch at step 100
- Gate opens immediately (same step)
- Agent sees gate at step 105 (5 steps later)

**Verdict:** ✅ **TRACE LIFETIME IS SUFFICIENT!**
- 5 steps delay << 3465 steps half-life
- Trace should survive easily

**Conclusion:** Trace decay is NOT the problem!

---

## Area 2: Vector Encoding 🔍

### Current Implementation

**File:** `src/processes/snn_rl_bridge.py` → `encode_state_to_spikes`

```python
def encode_state_to_spikes(ctx, snn_ctx):
    obs = ctx.domain_ctx.current_observation
    
    # Extract agent position
    if 'agent_pos' in obs:
        x, y = obs['agent_pos']
    else:
        x, y = 0, 0
    
    # Spatial encoding (16-dim pattern)
    pattern = np.zeros(16)
    pattern[x % 8] = 1.0      # X position
    pattern[8 + (y % 8)] = 1.0  # Y position
    
    # Inject into input neurons (0-15)
    for i in range(16):
        neuron = snn_ctx.domain_ctx.neurons[i]
        neuron.potential_vector = pattern * 2.0
        neuron.potential = 2.0
```

### Problem Found! ❌

**What's encoded:**
- ✅ Agent position (x, y)

**What's NOT encoded:**
- ❌ Switch states
- ❌ Gate states  
- ❌ Broadcast events (switch toggled, gate changed)
- ❌ ANY causal information!

**Example:**
- Agent at (1, 1) → pattern = [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
- Agent toggles switch A → **SAME PATTERN!** (no change!)
- Gate A opens → **SAME PATTERN!** (no change!)

**Conclusion:** ❌ **VECTOR ENCODING IS THE PROBLEM!**
- SNN cannot distinguish "at switch" vs "normal position"
- No information about causality!

---

## Area 3: Dopamine Signal 🔍

### Current Implementation

**Dopamine Source:** TD-error from RL

```python
# From src/processes/snn_learning_3factor_theus.py (line 71-72)
td_error = rl_ctx.domain_ctx.td_error
dopamine = np.tanh(td_error)  # Normalize [-1, 1]
```

### TD-Error Calculation

**Q-Learning TD-error:**
```python
td_error = reward + gamma * max(Q(s', a')) - Q(s, a)
```

**When agent toggles switch:**
- Reward = -0.1 (step penalty)
- Q(s, a) ≈ 0 (not learned yet)
- Q(s', a') ≈ 0 (not learned yet)
- **TD-error ≈ -0.1** (very small!)
- **Dopamine ≈ tanh(-0.1) ≈ -0.1** (weak signal!)

**When agent reaches goal:**
- Reward = +10.0
- TD-error ≈ +10.0
- Dopamine ≈ tanh(10) ≈ +1.0 (strong!)

### Problem Found! ⚠️

**Dopamine only strong at goal:**
- Toggle switch → weak dopamine (-0.1)
- Open gate → weak dopamine (-0.1)
- Reach goal → strong dopamine (+1.0)

**But:**
- Trace at "toggle switch" already decayed by time agent reaches goal!
- Even with slow trace (3465 steps half-life), if agent takes 500 steps to goal:
  - Trace = 0.9998^500 ≈ 0.90 (10% decay)
  - Still alive, but weak

**Conclusion:** ⚠️ **DOPAMINE SIGNAL IS WEAK FOR INTERMEDIATE EVENTS!**

---

## 🎯 Root Cause Summary

### Primary Problem: Vector Encoding ❌

**Current:** Only encodes position (x, y)

**Missing:**
1. Switch states (ON/OFF)
2. Gate states (OPEN/CLOSED)
3. Broadcast events (toggle, open)
4. Spatial relationships (near switch, see gate)

**Impact:** SNN has NO information about causality!

### Secondary Problem: Weak Dopamine ⚠️

**Current:** Only strong dopamine at goal

**Missing:**
1. Intermediate rewards (toggle switch)
2. Shaped rewards (approach switch)
3. Event-based rewards (gate opens)

**Impact:** R-STDP has weak signal for intermediate learning!

### Non-Problem: Trace Decay ✅

**Current:** tau_trace_slow = 0.9998 (half-life 3465 steps)

**Verdict:** Sufficient for switch→gate causality!

---

## 💡 Recommended Solutions

### Solution 1: Enrich Vector Encoding (CRITICAL)

**Add broadcast events to encoding:**

```python
def encode_state_to_spikes(ctx, snn_ctx):
    obs = ctx.domain_ctx.current_observation
    pattern = np.zeros(16)
    
    # Position (0-7)
    x, y = obs.get('agent_pos', (0, 0))
    pattern[x % 8] = 1.0
    
    # NEW: Broadcast events (8-15)
    events = obs.get('broadcast_events', [])
    for event in events:
        if event.get('type') == 'switch_toggled':
            switch_id = event.get('switch_id', '')
            # Encode switch ID (A=8, B=9, C=10, D=11, E=12)
            idx = 8 + ord(switch_id) - ord('A')
            if idx < 16:
                pattern[idx] = 1.0
        
        elif event.get('type') == 'gate_changed':
            gate_id = event.get('gate_id', '')
            # Encode gate state (13-15)
            if 'open' in gate_id.lower():
                pattern[13] = 1.0
            else:
                pattern[14] = 1.0
```

**Impact:**
- Different patterns for different events!
- SNN can learn: pattern[9] (switch B) → pattern[13] (gate open)
- R-STDP can link causality!

---

### Solution 2: Add Intermediate Rewards (IMPORTANT)

**Reward shaping:**

```python
# In environment.py
def calculate_reward(self, agent_id, action):
    reward = -0.1  # Step penalty
    
    # NEW: Reward for toggling switches
    if self.agent_toggled_switch(agent_id):
        reward += 1.0  # Moderate reward
    
    # NEW: Reward for opening gates
    if self.gate_opened_this_step():
        reward += 0.5  # Small reward
    
    # Existing: Goal reward
    if self.reached_goal(agent_id):
        reward += 10.0
    
    return reward
```

**Impact:**
- Stronger dopamine for intermediate events!
- R-STDP gets signal to learn!

---

### Solution 3: Increase Trace Slow (OPTIONAL)

**Not needed, but can help:**

```python
tau_trace_slow: float = 0.9999  # Was 0.9998
# Half-life: 6931 steps (2x longer)
```

**Impact:**
- Even longer memory
- Better for very long causal chains

---

## 📋 Implementation Priority

**Priority 1: Solution 1 (Enrich Vector Encoding)**
- **CRITICAL** - Without this, SNN has no causal info
- Estimated time: 30 minutes
- Expected impact: HIGH

**Priority 2: Solution 2 (Intermediate Rewards)**
- **IMPORTANT** - Provides dopamine signal
- Estimated time: 15 minutes
- Expected impact: MEDIUM

**Priority 3: Solution 3 (Increase Trace)**
- **OPTIONAL** - Current trace is sufficient
- Estimated time: 2 minutes
- Expected impact: LOW

---

## ✅ Next Steps

1. Implement Solution 1 (vector encoding)
2. Implement Solution 2 (intermediate rewards)
3. Test with 100 episodes
4. Verify agents learn causality

**Expected Result:**
- Agents learn to toggle switches
- Agents learn switch→gate relationships
- 10-30% success rate (vs 0% now)

---

**Status:** ✅ INVESTIGATION COMPLETE  
**Root Cause:** Vector encoding lacks causal information  
**Solution:** Enrich encoding + intermediate rewards  
**Confidence:** HIGH
