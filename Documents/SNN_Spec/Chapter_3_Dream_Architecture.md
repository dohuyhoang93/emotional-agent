# Chapter 3: Semantic Dream & Protection Architecture

**Scope**: How the agent simulates reality, learns from it, and protects itself from "mental crashes".

> [!IMPORTANT]
> **Implementation Status**: Core dream mechanisms are **IMPLEMENTED**. Some advanced features are **PARTIALLY IMPLEMENTED** or **PLANNED**.

---

## 3.1 The Dream Cycle (Biological Simulation)

**Workflow**: `workflows/agent_dream.yaml`  
**Orchestrator**: `src/orchestrator/processes/p_run_dreaming.py`  
**Agent Method**: `src/agents/rl_agent.py::RLAgent.dream_step()`  
**Status**: ✅ **IMPLEMENTED**

Dreams in Theus SNN serve as a **Memory Consolidation** mechanism, functioning independently of external sensory input.

### A. Stimulation (`process_inject_dream_stimulus`)

**Process**: `process_inject_dream_stimulus`  
**File**: `src/processes/snn_dream_processes.py` (Lines 13-56)  
**Status**: ✅ **IMPLEMENTED**

*   **Mechanism**: The agent enters a "Sleep State" where external sensors are disconnected.
*   **Input**: The system injects **Stochastic Noise** (White Noise) into the input neurons to simulate REM sleep.
*   **Deep Sleep (PGO Waves)**: Occasional strong bursts of stimulus (probability ~1%) are injected to forcibly trigger random associative chains, retrieving dormant memories.

**Implementation**:
```python
for neuron in neurons:
    # Random input current (REM noise)
    input_current = random.uniform(0, noise_level)  # noise_level = 0.1
    
    # PGO waves (1% chance of strong burst)
    if random() < 0.01:
        input_current += 0.5  # Strong stimulus
    
    neuron.potential += input_current
```

**Hyperparameters**:
- `dream_noise_level`: 0.1 (baseline noise)
- `pgo_probability`: 0.01 (1% chance per neuron)
- `pgo_strength`: 0.5 (burst magnitude)

---

### B. Consolidation & Evaluation (`process_stdp_3factor`)

**Process**: `process_dream_coherence_reward`  
**File**: `src/processes/snn_dream_safety.py` (Lines 12-75)  
**Status**: ✅ **IMPLEMENTED**

*   **Logic**: 3-Factor STDP conditioned by an **Internal Reward Signal** (`td_error`).
*   **Coherence Reward** (`process_dream_coherence_reward`):
    *   Since there is no external environment, the brain evaluates its own activity stability.
    *   **Reward (+0.1)**: If Active Ratio is healthy (5% - 30%). This reinforces valid, coordinated memory chains.
    *   **Punishment (-0.1 → -0.5)**: If the brain is too quiet (<5%, Noise) or seizing (>30%, Epilepsy). This triggers LTD to prune bad connections.
*   **Effect**: Transformation of "Fluid" short-term memories into "Solid" long-term structures.

**Implementation**:
```python
# Calculate active ratio
firing_count = sum(1 for n in neurons if n.fire_count > 0)
active_ratio = firing_count / total_neurons

# Reward logic
if active_ratio < 0.05:
    reward = -0.1  # Too quiet (underactive)
    state = "underactive"
elif active_ratio > 0.30:
    reward = -0.5  # Seizure (epilepsy)
    state = "epilepsy"
else:
    reward = 0.1   # Coherent
    state = "coherent"

# Update TD-error for STDP
ctx.domain_ctx.td_error = reward
```

**Thresholds**:
- `underactive_threshold`: 0.05 (5%)
- `epilepsy_threshold`: 0.30 (30%)
- `coherent_reward`: +0.1
- `underactive_penalty`: -0.1
- `epilepsy_penalty`: -0.5

---

### C. Visualization (`process_decode_dream`)

**Process**: `process_decode_dream`  
**File**: `src/processes/snn_dream_processes.py`  
**Status**: ⚠️ **PARTIALLY IMPLEMENTED**

*   **Problem**: Monitoring internal state without external context.
*   **Solution**: The system decodes the `Spike_Queue` into a spatial coordinate `(x, y)` using the `process_decode_dream` inverse model.
*   **Result**: Allows observers to see "what the agent is dreaming about" (e.g., replaying a path to the goal).

> [!WARNING]
> **Implementation Note**: `process_decode_dream` exists but is a stub. Full inverse decoding (spike pattern → spatial coordinates) is **NOT YET IMPLEMENTED**. Current implementation only logs spike activity.

**Planned Implementation**:
```python
# Inverse model: Spike Pattern → Observation
# Use prototype vectors to reconstruct observation
active_protos = [neurons[i].prototype_vector for i in spike_queue]
reconstructed_obs = weighted_average(active_protos, weights=spike_strengths)
decoded_position = obs_to_position(reconstructed_obs)  # (x, y)
```

---

## 3.2 Defense Mechanisms (The Immune System)

**Goal**: To prevent "Epileptic Seizures" (Runaway Feedback Loops) common in Recurrent SNNs.

### Layer 1: Self-Regulation (Hysteria Dampener)

**Process**: `process_hysteria_dampener`  
**File**: `src/processes/snn_advanced_features_theus.py` (Lines 39-82)  
**Status**: ✅ **IMPLEMENTED**

*   **Logic**: Homeostatic Threshold Regulation.
    *   If `Fire_Rate > Panic_Threshold`: **Aggressively Increase Thresholds**.
    *   Effect: Makes neurons "numb" immediately to cool down the network.

**Implementation**:
```python
# Calculate current fire rate
current_fire_rate = metrics.get('fire_rate', 0.0)

# Panic threshold
panic_threshold = 0.3  # 30% activity

if current_fire_rate > panic_threshold:
    # Emergency brake: Raise all thresholds
    for neuron in neurons:
        neuron.threshold += 0.05  # Aggressive increase
    
    metrics['hysteria_dampener_triggered'] = True
```

**Hyperparameters**:
- `panic_threshold`: 0.3 (30% firing rate)
- `threshold_increase`: 0.05 (5% boost)

---

### Layer 2: Emergency Brake (Sanity Check)

**Process**: `process_dream_sanity_check`  
**File**: `src/processes/snn_dream_safety.py`  
**Status**: ❌ **NOT IMPLEMENTED**

*   **Logic**: If Layer 1 failed and the system is still in `Nightmare` state from the previous tick:
    *   **Action**: `Spike_Queue.clear()`
    *   **Effect**: Total blackout. Stops the seizure instantly.

> [!CAUTION]
> **Missing Feature**: `process_dream_sanity_check` is **NOT IMPLEMENTED**. The system currently relies only on `process_hysteria_dampener` (Layer 1). If Layer 1 fails, there is no emergency brake.

**Recommended Implementation**:
```python
@process(
    inputs=['domain.snn_context', 'domain.snn_context.domain_ctx.metrics'],
    outputs=['domain.snn_context.domain_ctx.spike_queue'],
    side_effects=[]
)
def process_dream_sanity_check(ctx: SystemContext):
    """Emergency brake: Clear spike queue if nightmare persists."""
    snn_ctx = ctx.domain_ctx.snn_context
    metrics = snn_ctx.domain_ctx.metrics
    
    # Check if nightmare state persisted
    if metrics.get('dream_coherence_state') == 'epilepsy':
        if metrics.get('nightmare_counter', 0) > 3:  # 3 consecutive ticks
            # Total blackout
            snn_ctx.domain_ctx.spike_queue.clear()
            metrics['sanity_check_triggered'] = True
            metrics['nightmare_counter'] = 0
        else:
            metrics['nightmare_counter'] = metrics.get('nightmare_counter', 0) + 1
    else:
        metrics['nightmare_counter'] = 0
```

---

## 3.3 The "Groggy" Effect (Wake-up Persistence)

**Status**: ✅ **IMPLEMENTED** (Emergent Behavior)

An emergent phenomenon of State Persistence.

### The Phenomenon

1.  **Nightmare**: Agent raises thresholds significantly (`+0.05`) to suppress fear/overload.
2.  **Wake Up**: The system switches workflow (`agent_main.yaml`) **without resetting** neuron states.
3.  **Result**: The agent enters reality with "High Defense" (High Thresholds). It is unresponsive and sluggish.

**Evidence in Code**:
```python
# In RLAgent.dream_step() - NO state reset
def dream_step(self, time_step):
    self.engine.execute_workflow("workflows/agent_dream.yaml")
    # Neuron states (thresholds) persist!

# In RLAgent.step() - Continues with modified thresholds
def step(self, env_adapter):
    self.engine.execute_workflow("workflows/agent_main.yaml")
    # Thresholds are still elevated from dream!
```

### The Recovery

*   **Mechanism**: `process_meta_homeostasis_fixed` (PID Controller).
*   **File**: `src/processes/snn_advanced_features_theus.py`
*   **Rate**: Very slow (`0.0001` per step).
*   **Duration**: It takes hundreds of ticks for the agent to "sober up" and return to peak performance.

**Implementation**:
```python
# Gradual threshold recovery
target_threshold = global_ctx.initial_threshold  # 0.6
recovery_rate = 0.0001

for neuron in neurons:
    # Slowly return to baseline
    if neuron.threshold > target_threshold:
        neuron.threshold -= recovery_rate
    elif neuron.threshold < target_threshold:
        neuron.threshold += recovery_rate
```

**Hyperparameters**:
- `recovery_rate`: 0.0001 (0.01% per step)
- `target_threshold`: 0.6 (baseline)
- **Recovery time**: ~1000 steps to recover from +0.05 increase

---

## 3.4 Applications

### 1. Safety Training

**Status**: ✅ **CONCEPTUALLY SUPPORTED** (not explicitly tested)

*   **Idea**: Learning to avoid "Lava" in dreams prevents burning in reality.
*   **Mechanism**: 3-Factor STDP during dreams strengthens "avoidance" synapses.
*   **Evidence**: Coherence reward reinforces stable patterns, including avoidance behaviors.

**Potential Use Case**:
```python
# During dream:
# 1. Inject "danger" stimulus (high noise to specific neurons)
# 2. If agent "avoids" (low activity in danger neurons) → Reward
# 3. STDP strengthens avoidance synapses
# 4. In reality: Agent avoids similar patterns
```

---

### 2. Prospective Memory

**Status**: ✅ **IMPLEMENTED** (via `trace_slow`)

*   **Mechanism**: Tagging synapses during dreams (`trace_slow`) primes them for rapid "One-Shot Learning" when the event actually occurs in reality (Déjà vu).
*   **Implementation**: `trace_slow` (tau=0.9998) decays very slowly (~5000ms), allowing dream-tagged synapses to remain "primed" for hours.

**Code Evidence**:
```python
# In SynapseState
trace_slow: float = 0.0  # Decays in ~5000ms

# In 3-Factor STDP
eligibility = trace_fast + trace_slow  # Both contribute
delta_weight = lr * eligibility * dopamine

# If synapse was active in dream:
# - trace_slow is high
# - When same pattern appears in reality:
#   - eligibility is already elevated
#   - Learning is MUCH faster (one-shot)
```

---

## 3.5 Dream Workflow Summary

**File**: `workflows/agent_dream.yaml`

```yaml
steps:
  # 1. Stimulation
  - process_inject_dream_stimulus  # Noise + PGO waves
  
  # 2. SNN Core with Safety
  - process_hysteria_dampener      # Layer 1 defense
  - process_integrate
  - process_lateral_inhibition
  - process_fire
  
  # 3. Learning
  - process_dream_coherence_reward # Internal reward
  - process_stdp_3factor           # Consolidation
  
  # 4. Visualization
  - process_decode_dream           # (Stub)
```

**Missing from Workflow**:
- ❌ `process_dream_sanity_check` (Layer 2 defense)
- ❌ Full `process_decode_dream` implementation

---

## 3.6 Implementation Status Summary

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| **Dream Stimulus** | ✅ Implemented | `snn_dream_processes.py` | Noise + PGO waves |
| **Coherence Reward** | ✅ Implemented | `snn_dream_safety.py` | 5-30% optimal range |
| **3-Factor STDP** | ✅ Implemented | `snn_learning_3factor_theus.py` | Uses coherence reward |
| **Hysteria Dampener** | ✅ Implemented | `snn_advanced_features_theus.py` | Layer 1 defense |
| **Sanity Check** | ❌ Not Implemented | N/A | Layer 2 defense missing |
| **Dream Decode** | ⚠️ Stub Only | `snn_dream_processes.py` | Inverse model missing |
| **Groggy Effect** | ✅ Emergent | N/A | State persistence |
| **Prospective Memory** | ✅ Implemented | `snn_context_theus.py` | Via `trace_slow` |
| **Safety Training** | ⚠️ Conceptual | N/A | Not explicitly tested |

---

> [!NOTE]
> **Related Chapters**:
> - Chapter 2: Learning Mechanisms (3-Factor STDP details)
> - Chapter 5: Safety and Homeostasis (Hysteria dampener, meta-homeostasis)
> - Chapter 7: Persistence and Monitoring (Dream recording)
