# Chapter 2: Mechanisms of Learning (Space & Time)

**Scope**: How the network evolves its structure based on experience.

> [!IMPORTANT]
> **Implementation Status**: All mechanisms described in this chapter are **FULLY IMPLEMENTED** in the codebase as of 2025-12-30.

---

## 2.1 Spatial Learning (Vector Clustering)

**Process**: `process_clustering`  
**File**: `src/processes/snn_learning_theus.py::_clustering_impl_vectorized`  
**Status**: ✅ **IMPLEMENTED** (Vectorized)

**Goal**: To organize neurons into "Semantic Topics".

Unlike traditional SNNs where learning is only about connection weights, Theus SNNs adjust the **identity** of the neurons themselves.

### Algorithm (Vector Hebbian)
*   **Principle**: *"Neurons that fire together, align together."*
*   **Trigger**: When a `Pre-Neuron` causes a `Post-Neuron` to fire.
*   **Action**: The `Post-Neuron` rotates its `prototype_vector` slightly towards the `Pre-Neuron`'s prototype.
    ```python
    # Actual Implementation (Vectorized)
    Direction = Spike_Vector - Post_Vector
    Post_Vector += Clustering_Rate * Similarity * Direction
    Post_Vector = L2_Normalize(Post_Vector)
    ```

**Implementation Details**:
- **Similarity**: Cosine similarity between prototypes
- **Clustering Rate**: `global_ctx.clustering_rate` (default: 0.01)
- **Normalization**: L2-norm to keep vectors on unit sphere
- **Complexity**: O(K × N) where K = firing neurons, N = total neurons

### Result
*   Neurons receiving similar inputs will gradually drift their prototypes to form a **cluster centroid**.
*   The network automatically builds a "Map of Concepts" (e.g., a group of neurons specializing in "Danger", another in "Food").

---

## 2.2 Temporal Learning (STDP)

### 2.2.1 Two-Factor STDP (Hebbian)

**Process**: `process_stdp`  
**File**: `src/processes/snn_learning_theus.py::_stdp_impl_vectorized`  
**Status**: ✅ **IMPLEMENTED** (Vectorized)

**Goal**: To learn Causal Relationships (Cause -> Effect) through pure association.

> [!NOTE]
> Theus implements a **Hybrid Selectionist** architecture ("Generate-and-Test") rather than Direct Reinforcement (Gradient Descent).

#### Mechanism (Hebbian STDP)
*   **Type**: 2-Factor Unsupervised Learning.
*   **Logic**:
    1.  **LTP (Long-Term Potentiation)**: If Pre-Neuron fires *before* Post-Neuron (within timing window) -> Synapse Strengthened.
        *   Interpretation: "Pre caused Post".
    2.  **LTD (Long-Term Depression)**: If Pre-Neuron fires *after* Post-Neuron -> Synapse Weakened.
        *   Interpretation: "Pre was irrelevant to Post".

**Implementation Details**:
```python
# Trace Decay
trace *= tau_trace  # tau_trace ≈ 0.9

# Trace Update (on spike)
trace += 1.0

# LTP: Pre-spike strengthens based on post-trace
weight += lr_ltp * trace_post

# LTD: Post-spike weakens based on pre-trace  
weight -= lr_ltd * trace_pre

# Weight Decay & Clipping
weight *= 0.999
weight = clip(weight, 0.0, 1.0)
```

**Hyperparameters**:
- `tau_trace`: 0.9 (10% decay per step)
- `lr_ltp`: Learning rate for potentiation
- `lr_ltd`: Learning rate for depression
- Timing window: ~20 steps (20ms @ 1ms/step)

#### Role in Architecture (The Generator)
STDP acts as a generic "Hypothesis Generator". It continually creates potential causal links based on temporal correlation, *without knowing* if those links are actually useful for obtaining rewards.

---

### 2.2.2 Three-Factor STDP (Dopamine-Modulated)

**Process**: `process_stdp_3factor`  
**File**: `src/processes/snn_learning_3factor_theus.py::_stdp_3factor_impl`  
**Status**: ✅ **IMPLEMENTED**

> [!IMPORTANT]
> **NEW**: This section was added to reflect the actual implementation. The original spec only covered 2-Factor STDP.

**Goal**: To modulate synaptic plasticity based on reward signals from the RL layer.

#### Mechanism: Reward-Driven Learning

**Formula**:
```
Δw = η * eligibility * dopamine
```

**Components**:

1. **Eligibility Trace** (Dual Time Scales):
   ```python
   # Fast trace (short-term memory)
   trace_fast *= tau_trace_fast  # 0.9
   
   # Slow trace (long-term memory)
   trace_slow *= tau_trace_slow  # 0.95
   
   # Combined eligibility
   eligibility = trace_fast + trace_slow
   ```

2. **Dopamine Signal** (from RL):
   ```python
   td_error = reward - Q(s,a)  # From RL layer
   dopamine = tanh(td_error)   # Bounded [-1, 1]
   ```

3. **Protected Learning** (Phase 10.5):
   ```python
   if synapse.commit_state == COMMIT_STATE_SOLID:
       effective_lr = dopamine_lr * 0.1  # 10% learning rate
   elif synapse.commit_state == COMMIT_STATE_FLUID:
       effective_lr = dopamine_lr * 1.0  # 100% learning rate
   else:  # REVOKED
       continue  # Skip learning
   
   delta_weight = effective_lr * eligibility * dopamine
   synapse.weight += delta_weight
   ```

**Hyperparameters**:
- `dopamine_learning_rate`: 0.01
- `tau_trace_fast`: 0.9
- `tau_trace_slow`: 0.95
- `solid_learning_rate_factor`: 0.1

#### Integration with RL
- **TD-Error** from Q-Learning acts as global reward signal
- **Positive dopamine**: Strengthens active synapses (reward)
- **Negative dopamine**: Weakens active synapses (punishment)
- Creates **memory** of successful patterns

---

## 2.3 Synaptic Insurance (The Commitment Layer)

**Process**: `process_commitment`  
**File**: `src/processes/snn_commitment_theus.py`  
**Status**: ✅ **IMPLEMENTED** (Vectorized, Phase 10.5 Enhanced)

**Goal**: To validate the hypotheses generated by STDP using Reinforcement Signal.

This is the **Critic** component of the Selectionist architecture (equivalent to Natural Selection).

### Mechanism: The 3-State FSM

Every synapse exists in one of three states:

1.  **FLUID (Liquid)**: Default state for new synapses.
    *   **Plasticity**: 100% (full learning rate).
    *   **Vulnerability**: Can be pruned if unused.
    *   **Transition**: FLUID → SOLID when `consecutive_correct >= threshold`

2.  **SOLID (Frozen)**: Optimized State.
    *   **Trigger**: `consecutive_correct >= commitment_threshold` (default: 10)
    *   **Effect**: Plasticity drops to **10%** (not zero - allows fine-tuning).
    *   **Benefit**: Protected from catastrophic forgetting.
    *   **Transition**: SOLID → REVOKED when `consecutive_wrong >= revoke_threshold`

3.  **REVOKED (Dead)**: Failed State.
    *   **Trigger**: `consecutive_wrong >= revoke_threshold` (default: 5)
    *   **Effect**: Synapse is marked for pruning (learning rate = 0%).
    *   **Cleanup**: Removed by Neural Darwinism process.

### Implementation Details

**State Transitions** (Vectorized):
```python
# Update counters based on TD-error
if abs(td_error) < error_threshold:
    consecutive_correct += 1
    consecutive_wrong = 0
else:
    consecutive_wrong += 1
    consecutive_correct = 0

# FLUID -> SOLID
newly_solid = (state == FLUID) & (consecutive_correct >= solidify_threshold)
state[newly_solid] = SOLID

# SOLID -> REVOKED
newly_revoked = (state == SOLID) & (consecutive_wrong >= revoke_threshold)
state[newly_revoked] = REVOKED
```

**Derived Neuron Commitment** (Phase 10.5):
```python
# Calculate solidity ratio for each neuron
incoming_solid_count = sum(is_solid, axis=0)  # Per post-neuron
incoming_total_count = sum(weights > 0, axis=0)
solidity_ratio = incoming_solid_count / incoming_total_count

# Store in tensor for attention modulation
tensors['solidity_ratios'] = solidity_ratio
```

**Hyperparameters**:
- `commitment_threshold`: 10 (consecutive correct predictions)
- `revoke_threshold`: 5 (consecutive wrong predictions)
- `prediction_error_threshold`: 0.1 (TD-error tolerance)

### The Synergy
*   **STDP** says: "A happened, then B happened. Maybe they are related?" (Creates Link)
*   **Commitment** says: "That link helped us get food -> **KEEP IT**." or "That link led to pain -> **KILL IT**."

---

## 2.4 Structural Learning (Neural Darwinism)

**Process**: `process_neural_darwinism`  
**File**: `src/processes/snn_advanced_features_theus.py`  
**Status**: ✅ **IMPLEMENTED**

**Goal**: Evolutionary pruning and recycling of network structure.

The network is not static; it is a living ecosystem that evolves under selection pressure.

### Level 1: Synaptic Selection (Pruning)

**Mechanism**: Survival of the fittest.

**Implementation**:
```python
# Prune weak synapses
for synapse in synapses:
    if synapse.commit_state == COMMIT_STATE_REVOKED:
        synapses.remove(synapse)  # Delete
    elif synapse.weight < prune_threshold:
        synapses.remove(synapse)  # Too weak
    elif (current_time - synapse.last_active_time) > inactive_threshold:
        if synapse.commit_state != COMMIT_STATE_SOLID:
            synapses.remove(synapse)  # Inactive & not protected
```

**Safeguards**:
- `SOLID` synapses are **immune** to pruning
- Weight threshold: Typically 0.01
- Inactive threshold: ~2000 steps

### Level 2: Neuron Recycling (Neurogenesis)

**Problem**: "Dead Neurons" that never fire consume resources.

**Detection**:
```python
is_dead = (neuron.fire_count == 0) and has_no_solid_connections(neuron)
```

**Action (Reincarnation)**:
1.  **Reset Vector**: `prototype_vector = random_unit_vector()`
2.  **Rewire**: Remove all incoming/outgoing synapses
3.  **Result**: A "fresh" unit ready to capture new concepts

**Hyperparameters**:
- `darwinism_interval`: 100 episodes (when to run)
- `selection_pressure`: 0.1 (fraction to prune)
- `reproduction_rate`: 0.05 (fraction to recycle)

---

## 2.5 Summary: The Four Dimensions of Learning

The system learns in four complementary dimensions:

| Dimension | Mechanism | Question Answered | Time Scale |
|-----------|-----------|-------------------|------------|
| **Spatial** | Clustering | "What is this?" | Every step |
| **Temporal** | STDP (2-Factor) | "What follows this?" | Every step |
| **Reward** | STDP (3-Factor) | "Is this useful?" | Every step |
| **Stability** | Commitment | "Is this true?" | ~10 steps |
| **Structural** | Darwinism | "Is this efficient?" | ~100 episodes |

### Learning Hierarchy

```
Step-Level Learning (Fast):
├─ Clustering: Prototype alignment
├─ 2-Factor STDP: Temporal associations
└─ 3-Factor STDP: Reward-modulated weights

Episode-Level Learning (Medium):
└─ Commitment: State transitions (FLUID/SOLID/REVOKED)

Population-Level Learning (Slow):
└─ Darwinism: Structural pruning & recycling
```

---

## 2.6 Implementation Notes

### Vectorization Strategy
All learning processes are **fully vectorized** using NumPy for performance:
- Clustering: O(K × N) where K = firing neurons
- STDP: O(S) where S = number of synapses
- Commitment: O(S) with masked operations
- Darwinism: O(N + S) for pruning

### Hybrid Object-Tensor Architecture
- **Tensors**: Used for fast computation (integrate, fire, learn)
- **Objects**: Used for audit trail and complex logic
- **Sync**: Bidirectional sync between objects and tensors

### Protected Learning (Phase 10.5)
The **10% learning rate** for SOLID synapses (not "near zero") allows:
- Fine-tuning of important connections
- Adaptation to environment drift
- Balance between stability and plasticity

---

> [!NOTE]
> **Related Chapters**:
> - Chapter 3: RL-SNN Integration (Emotion gating, intrinsic rewards)
> - Chapter 4: Advanced Features (Top-down modulation, active inhibition)
> - Chapter 5: Safety Mechanisms (Quarantine, homeostasis)
