# Chapter 9: Advanced Bridge - Attention Mechanism (Phase 9)

> **Status:** Draft / Conceptual
> **Target Phase:** Phase 9 (Advanced Bridge)
> **Reference Model:** `src/models/gated_integration.py` (GatedIntegrationNetwork)

## 1. Problem Statement: The Limits of Mean Aggregation

### Current Approach (Population Coding)
In `snn_rl_bridge.py`, the translation from SNN activity to RL observation is done via **Averaging**:

$$ V_{emotion} = \frac{1}{N_{active}} \sum_{i \in Active} V_{prototype}^{(i)} $$

### The "Aliasing" Problem
Function `mean()` destroys structural information when dealing with orthogonal or conflicting vectors.
- **Scenario:** Agent feels **Fear** (Vector A) AND **Curiosity** (Vector B).
- **Result:** $V_{mix} = 0.5A + 0.5B$.
- **Issue:** The resulting `V_mix` might point to a completely unrelated region in the high-dimensional space (e.g., "Boredom"), or simply zero out if they are opposites. The RL agent loses the nuance that *both* distinct emotions are present.

## 2. Conceptual Solution: Sigmoid Gated Attention

Instead of mixing everything into a single soup, we use an **Attention Mechanism** to allow the RL Agent to "looks at" specific active neurons based on its current context.

Influenced by the project's **Gated Integration Network**, we choose **Sigmoid Activation** over Softmax.

### Why Sigmoid (Gating) vs Softmax (Selection)?
- **Softmax** is competitive: $\sum P_i = 1$. If Fear is high, Curiosity *must* be low. This forces a "Winner-Takes-All" dynamic.
- **Sigmoid** is independent: $P_i \in [0, 1]$. We can have High Fear ($0.9$) AND High Curiosity ($0.8$) simultaneously. This preserves the multi-modal nature of the SNN's internal state.

## 3. Mathematical Model

### Definition
- **Query ($Q$)**: The RL Agent's Context Vector (e.g., derived from current Observation or internal LSTM state).
- **Key ($K_i$)**: The static `prototype_vector` (16-dim) of Neuron $i$.
- **Value ($V_i$)**: The dynamic `activation` (firing rate or potential) of Neuron $i$.

### The Attention Formula

For each active neuron $i$:

$$ Score_i = \frac{Q \cdot K_i}{\sqrt{d_k}} $$

$$ Attention_i = \sigma(Score_i) $$

Where $\sigma$ is the **Sigmoid** function: $\frac{1}{1 + e^{-x}}$.

### The Weighted Output (New Observation)

$$ V_{out} = \sum_{i} (Attention_i \cdot V_i) \cdot K_i $$

*Note: Unlike standard Transformer which sums values, here we might want to keep them distinct or channel-wise. However, for a single vector output, this weighted sum is a "Smart Mean" where irrelevant neurons (low Attention) are suppressed to 0, and relevant ones are kept.*

## 4. Integration Strategy

The implementation will replace the simple loop in `snn_rl_bridge.py`.

### Current Code
```python
# Old: Simple Mean
if active_vectors:
    emotion_vector = np.mean(active_vectors, axis=0)
```

### Future Code (Phase 9)
```python
# New: Attention-based Aggregation
# Q comes from ctx.domain_ctx.agent_state
context_vector = np.zeros_like(prototype)

for neuron in neurons:
    # 1. Similarity (Dot Product)
    score = np.dot(query, neuron.prototype_vector)
    
    # 2. Gating (Sigmoid)
    gate = 1 / (1 + np.exp(-score))
    
    # 3. Aggregate
    # info = Gate * Firing_Rate * Prototype
    context_vector += gate * neuron.fire_count * neuron.prototype_vector

# Normalize capability
emotion_vector = normalize(context_vector)
```

## 5. Conclusion
This "Advanced Bridge" moves the SNN-RL interface from a passive data pipe to an active cognitive process, where the RL agent actively "queries" its subconscious (SNN) for relevant emotional memories.
