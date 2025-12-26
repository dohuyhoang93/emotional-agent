# Chapter 2: Mechanisms of Learning (Space & Time)

**Scope**: How the network evolves its structure based on experience.

## 2.1 Spatial Learning (Vector Clustering)
**Process**: `process_clustering`
**Goal**: To organize neurons into "Semantic Topics".

Unlike traditional SNNs where learning is only about connection weights, Theus SNNs adjust the **identity** of the neurons themselves.

### Algorithm (Vector Hebbian)
*   **Principle**: *"Neurons that fire together, align together."*
*   **Trigger**: When a `Pre-Neuron` causes a `Post-Neuron` to fire.
*   **Action**: The `Post-Neuron` rotates its `prototype_vector` slightly towards the `Pre-Neuron`'s prototype.
    ```python
    Direction = Spike_Vector - Post_Vector
    Post_Vector += Clustering_Rate * Direction
    Post_Vector = Normalize(Post_Vector)
    ```

### Result
*   Neurons receiving similar inputs will gradually drift their prototypes to form a **cluster centroid**.
*   The network automatically builds a "Map of Concepts" (e.g., a group of neurons specializing in "Danger", another in "Food").

## 2.2 Temporal Learning (3-Factor STDP)
**Process**: `process_stdp_3factor`
**Goal**: To learn Causal Relationships (Cause -> Effect) modulated by Value (Reward).

This is a **Reinforcement Learning** adaptation of STDP.

### The 3 Factors
1.  **Pre-synaptic Activity**: The "Cause" (stored in `Synapse.trace_fast`).
2.  **Post-synaptic Activity**: The "Effect" (triggering the update).
3.  **Dopamine (Neuromodulator)**: The "Value" (Global signal `td_error` from RL).

### Mechanism (Synaptic Tagging)
1.  **Tagging (The Wait)**:
    *   When `Pre` fires before `Post`: `Eligibility` trace increases.
    *   Weight does *not* change significantly yet. The synapse is just "Tagged" as potentially useful.
2.  **Consolidation (The Hit)**:
    *   When the RL engine produces a Reward (positive or negative `td_error`):
    *   `Dopamine = tanh(td_error)`
    *   `Delta_Weight = Learning_Rate * Eligibility * Dopamine`

### Capabilities
*   **Credit Assignment**: Solves the "msg" problem. Even if the reward comes 10 steps later, the `Eligibility` trace (slow decay) ensures the responsible synapses get credit.
*   **Inverted Learning**: If Dopamine is negative (Punishment), the same Hebbian event causes **LTD** (Weight decrease), effectively un-learning the bad habit.

## 2.3 Synaptic Insurance (The Commitment Layer)
**Process**: `process_commitment`

A mechanism to balance **Plasticity** (Learning) and **Stability** (Remembering).
*   **Mechanism**: A 3-State FSM for every synapse.
    1.  **FLUID (Liquid)**: Default. High Learning Rate.
    2.  **SOLID (Frozen)**:
        *   **Trigger**: Correct predictions > Threshold.
        *   **Effect**: Learning Rate drops to `10%`. Protected from noise.
    3.  **REVOKED (Dead)**:
        *   **Trigger**: Repeated errors on a SOLID synapse.
        *   **Effect**: Synapse Pruned.

## 2.4 Structural Learning (Neural Darwinism)
**Process**: `process_neural_darwinism`

The network is not static; it is a living ecosystem that evolves under selection pressure. This ensures efficient resource utilization and continuous adaptability.

### Level 1: Synaptic Selection (Pruning)
*   **Mechanism**: Survival of the fittest.
*   **Fitness Score**: Updated based on `td_error`. Success increases fitness; Failure decreases it. Fitness decays over time.
*   **Action**: Synapses with low fitness are **Pruned** (Deleted).
*   **Safeguard (The Solid Shield)**: Synapses in `SOLID` state are **Immune** to pruning, preserving critical long-term memories even if they haven't been used recently.

### Level 2: Neuron Recycling (Neurogenesis)
*   **Problem**: "Dead Neurons" (or Zombie Neurons) that never fire consume resources but contribute nothing.
*   **Detection**: A neuron is considered "Dead" if:
    1.  It has not fired for `> 2000` steps (`DEAD_THRESHOLD`).
    2.  It has NO `SOLID` connections (it holds no critical knowledge).
*   **Action (Reincarnation)**:
    1.  **Reset Vector**: Its `prototype_vector` is randomized to a new position in the latent space.
    2.  **Rewire**: Old synapses are removed, and new random synapses are generated.
    3.  **Result**: An old, useless unit is transformed into a "Fresh" unit, ready to capture new concepts (solving the capacity saturation problem).

## 2.5 Conclusion
The system learns in four dimensions:
*   **Spatial**: Clustering (What is this?)
*   **Temporal**: STDP (What follows this?)
*   **Stability**: Commitment (Is this true?)
*   **Structural**: Darwinism (Is this useful?)
