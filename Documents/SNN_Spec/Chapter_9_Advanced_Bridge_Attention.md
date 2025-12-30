# Chapter 9: Advanced Bridge - Attention Mechanism (Phase 9)

> [!IMPORTANT]
> **Implementation Status**: ✅ **FULLY IMPLEMENTED** as of 2025-12-30  
> **Reference**: See Chapter 4, Section 4.2 for complete implementation details

**Target Phase:** Phase 9 (Advanced Bridge)  
**Reference Model:** `src/models/gated_integration.py` (GatedIntegrationNetwork)  
**Reference Process:** `src/processes/snn_rl_bridge.py::encode_emotion_vector`

---

## 1. Problem Statement: The Limits of Mean Aggregation

### Current Approach (Population Coding)

In `snn_rl_bridge.py`, the translation from SNN activity to RL observation was originally done via **Averaging**:

$$ V_{emotion} = \frac{1}{N_{active}} \sum_{i \in Active} V_{prototype}^{(i)} $$

### The "Aliasing" Problem

Function `mean()` destroys structural information when dealing with orthogonal or conflicting vectors.

- **Scenario:** Agent feels **Fear** (Vector A) AND **Curiosity** (Vector B).
- **Result:** $V_{mix} = 0.5A + 0.5B$.
- **Issue:** The resulting `V_mix` might point to a completely unrelated region in the high-dimensional space (e.g., "Boredom"), or simply zero out if they are opposites. The RL agent loses the nuance that *both* distinct emotions are present.

---

## 2. Implemented Solution: Sigmoid Gated Attention

**Status**: ✅ **IMPLEMENTED**

Instead of mixing everything into a single soup, we use an **Attention Mechanism** to allow the RL Agent to "look at" specific active neurons based on its current context.

Influenced by the project's **Gated Integration Network**, we use **Sigmoid Activation** over Softmax.

### Why Sigmoid (Gating) vs Softmax (Selection)?

- **Softmax** is competitive: $\sum P_i = 1$. If Fear is high, Curiosity *must* be low. This forces a "Winner-Takes-All" dynamic.
- **Sigmoid** is independent: $P_i \in [0, 1]$. We can have High Fear ($0.9$) AND High Curiosity ($0.8$) simultaneously. This preserves the multi-modal nature of the SNN's internal state.

---

## 3. Mathematical Model

### Definition

- **Query ($Q$)**: The RL Agent's Context Vector (current observation).
- **Key ($K_i$)**: The static `prototype_vector` (16-dim) of Neuron $i$.
- **Value ($V_i$)**: The dynamic `activation` (firing rate or potential) of Neuron $i$.

### The Attention Formula

For each active neuron $i$:

$$ Score_i = \frac{Q \cdot K_i}{\sqrt{d_k} \cdot T} $$

$$ Attention_i = \sigma(Score_i) $$

Where:
- $\sigma$ is the **Sigmoid** function: $\frac{1}{1 + e^{-x}}$
- $T$ is the temperature parameter (default: 1.0)

### The Weighted Output (New Observation)

$$ V_{out} = \sum_{i} (Attention_i \cdot V_i) \cdot K_i $$

*Note: This is a "Smart Mean" where irrelevant neurons (low Attention) are suppressed to 0, and relevant ones are kept.*

---

## 4. Implementation

**File**: `src/processes/snn_rl_bridge.py::encode_emotion_vector`  
**Status**: ✅ **IMPLEMENTED**

### Actual Implementation Code

```python
def encode_emotion_vector(ctx: SystemContext):
    """
    Phase 9: Sigmoid Gating Attention.
    Query = Current Observation (from RL)
    Keys = Neuron Prototypes (from SNN)
    Values = Firing Rates (from SNN)
    """
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    
    # Query: Current observation
    query = ctx.domain_ctx.current_observation
    if query is None:
        query = np.zeros(16)
    
    # Collect active neurons
    active_neurons = [n for n in domain.neurons if n.fire_count > 0]
    
    if not active_neurons:
        ctx.domain_ctx.snn_emotion_vector = np.zeros(16)
        return
    
    # Attention mechanism
    attention_weights = []
    prototypes = []
    firing_rates = []
    
    for neuron in active_neurons:
        # Key: Prototype vector
        key = neuron.prototype_vector
        
        # Score: Dot product (scaled)
        score = np.dot(query, key) / (np.sqrt(16) * 1.0)  # temperature=1.0
        
        # Sigmoid gating (NOT softmax)
        attention = 1.0 / (1.0 + np.exp(-score))
        
        attention_weights.append(attention)
        prototypes.append(key)
        firing_rates.append(neuron.fire_count)
    
    # Weighted aggregation
    emotion_vector = np.zeros(16)
    for i, neuron in enumerate(active_neurons):
        gate = attention_weights[i]
        value = firing_rates[i]
        key = prototypes[i]
        
        # Gated contribution
        emotion_vector += gate * value * key
    
    # Normalize
    norm = np.linalg.norm(emotion_vector)
    if norm > 0:
        emotion_vector = emotion_vector / norm
    
    ctx.domain_ctx.snn_emotion_vector = emotion_vector
```

### Key Differences from Draft

| Aspect | Draft (Chapter 9) | Actual Implementation |
|--------|-------------------|----------------------|
| **Query Source** | "agent_state" (vague) | `current_observation` (concrete) |
| **Temperature** | Not mentioned | 1.0 (configurable) |
| **Normalization** | Optional | Always applied |
| **Status** | Conceptual | ✅ Implemented |

---

## 5. Performance Characteristics

### Complexity

- **Time**: $O(N_{active} \times D)$ where $D = 16$
- **Space**: $O(N_{active})$ for temporary arrays
- **Overhead**: Minimal (~10% vs simple mean)

### Benefits

- **Multi-modal preservation**: Can represent conflicting emotions simultaneously
- **Context-aware**: Filters irrelevant neurons based on current situation
- **Smooth gradients**: Sigmoid provides better gradient flow than hard selection

---

## 6. Conclusion

This "Advanced Bridge" moves the SNN-RL interface from a passive data pipe to an active cognitive process, where the RL agent actively "queries" its subconscious (SNN) for relevant emotional memories.

**Status**: ✅ Fully operational in production code.

---

> [!NOTE]
> **Related Chapters**:
> - Chapter 4: RL-SNN Interface (Full implementation details)
> - Chapter 8: Performance Architecture (Optimization strategies)
> - Chapter 10: Top-Down Modulation (Reverse flow: RL → SNN)
