# Chapter 10: Top-Down Modulation (RL → SNN Control)

> [!IMPORTANT]
> **Implementation Status**: 
> - **Basic Modulation**: ✅ FULLY IMPLEMENTED
> - **Derived Commitment**: ✅ FULLY IMPLEMENTED  
> - **Active Inhibition**: ⚠️ PARTIALLY IMPLEMENTED

**Target Phase:** Phase 10-11 (Closed Loop Control)  
**Reference Components:** 
- `src/processes/snn_rl_bridge.py::modulate_snn_attention`, `restore_snn_attention`
- `src/processes/snn_commitment_theus.py::process_commitment_derived`

---

## 10.1 Concept: Closing the Cognitive Loop

In previous chapters (4 & 9), the SNN acted as a "subconscious" feed that projected emotional states vectors **up** to the RL Agent (Bottom-Up).

This chapter defines the reverse path: The RL Agent exerting **Top-Down** control to influence the sensitivity of the SNN network.

### The "Focus" Metaphor
- **Bottom-Up (Attention):** "Hey, I (SNN) noticed something scary here."
- **Top-Down (Modulation):** "I (RL) am deciding to fight. SNN, become hyper-sensitive to 'Aggression' patterns and ignore 'Fear'."

---

## 10.2 Basic Mechanism: Threshold Modulation (Excitation)

**Status**: ✅ **IMPLEMENTED**

We control the SNN not by injecting spikes (which is sensory input), but by adjusting the **parameters** of neurons, specifically the **Firing Threshold**.

### The Logic
1.  **Action Mapping**: The RL Agent selects an Action (e.g., `UP`, `ATTACK`).
2.  **Sensitivity Boost**: Neurons associated with that action's concept receive a **decrease** in threshold.
3.  **Result**: These neurons fire more easily (requires less input potential), effectively "lowering the barrier" for expected stimuli.

$$ Threshold_{new} = Threshold_{current} \cdot (1 - \delta) $$

Where $\delta \approx 0.1$ (10% ease).

### Dynamics & Stability (The "Elasticity" Principle)

A critical requirement for Top-Down modulation is that it must be **Transient** (temporary) and **Elastic**. If modulation is permanent, the network will permanently drift into a biased state ("Seizure" or "Obsession").

#### The Tug of War
We introduce two opposing forces:

1.  **Modulation Force (Fast)**: Driven by RL Steps. Pushes thresholds **down** rapidly to facilitate immediate action execution.
2.  **Restoration Force (Slow)**: Driven by Homeostasis. Pushes thresholds **up** back towards the `Initial Baseline`.

$$ \Delta Threshold_{restore} = \alpha \cdot (Threshold_{target} - Threshold_{current}) $$

This ensures that if the RL stops "paying attention" (stops performing the action), the neurons naturally relax back to their neutral state.

### Implementation

**Function**: `modulate_snn_attention`
-   **Input**: `last_action` (Int), `snn_context` (Context).
-   **Operation**: Identify target neurons indices. Multiply their `threshold` tensor by `0.9`.

**Function**: `restore_snn_attention`
-   **Input**: `snn_context`.
-   **Operation**: Apply elastic restoration to **ALL** neurons.
-   **Formula**: `param += (target - param) * rate`.

---

## 10.3 Advanced: Derived Neuron Commitment (Safe Modulation)

**Status**: ✅ **IMPLEMENTED**  
**Process**: `process_commitment_derived`

### Problem: The Granularity Mismatch

-   **Synaptic Commitment (Chapter 2)**: Operates at the connection level (`Synapse`). A synapse becomes `SOLID` when it consistently predicts correctly.
-   **Neuron Modulation (Section 10.2)**: Operates at the unit level (`Neuron`). The RL agent boosts the sensitivity of entire neurons.

**The Logic Gap**: We want to apply modulation *only* to stable, mature concepts ("Solid Neurons") to avoid amplifying noise (Novelty Masking risk). However, the system relies on Synaptic Solidity. A neuron might have 10 incoming synapses, where 1 is Solid and 9 are Fluid. Is the neuron "Solid"?

### Solution: Derived Solidity Ratio

We introduce a **Derived State** for neurons, calculated from the bottom-up aggregation of their dendritic tree (incoming synapses).

#### Definition
The `solidity_ratio` ($\rho$) of a neuron $j$ is the fraction of its valid incoming synapses that are in the `SOLID` state.

$$ \rho_j = \frac{\sum_{i \in Inputs} \mathbb{1}(Synapse_{i \to j} == SOLID)}{Total\_Incoming\_Synapses_j} $$

#### Classification
-   **Fluid Identity ($\rho < 0.5$)**: The neuron is still forming its concept. It is dominated by plastic connections. *Modulation should be weak or disabled.*
-   **Solid Identity ($\rho \ge 0.5$)**: The neuron represents a stable, validated concept. *Modulation is fully enabled.*

### Implementation Logic

#### Data Structure
-   **NeuronState**: Add `solidity_ratio: float` (Range 0.0 - 1.0).
-   **Tensors**: Add `solidity_ratios` (Shape `[N]`).

#### Calculation Process (`process_commitment_derived`)
1.  **Update Synapses**: Existing logic updates `commit_state` (Fluid/Solid/Revoked).
2.  **Aggregate**:
    -   For each neuron, count `Incoming_Solid`.
    -   Count `Incoming_Total`.
    -   Compute $\rho$.
3.  **Vectorization Strategy**:
    -   Use `commit_states` matrix (`[N, N]`).
    -   Mask `solid_mask = (commit_states == 1)`.
    -   `solid_counts = solid_mask.sum(axis=0)` (Sum columns → incoming).
    -   `total_counts` can be derived from `weights > 0` or a separate adjacency mask.

#### Filtering Application (`modulate_snn_attention`)
-   **Input**: `solidity_ratios` tensor.
-   **Mask**: `ModulationMask = (ActionTarget) & (solidity_ratios > 0.5)`.
-   **Action**: Apply threshold reduction only to `ModulationMask`.

### Benefit
This mechanism bridges the gap between low-level plasticity (Synapses) and high-level control (Neurons), allowing the RL agent to confidently manipulate "Concepts" without accidentally distorting the learning process of new memories.

---

## 10.4 Advanced: Active Inhibition (Top-Down Suppression)

**Status**: ⚠️ **PARTIALLY IMPLEMENTED** - Field exists, logic incomplete

### Concept: The Power to "Ignore"

While **Excitation (Section 10.2)** allows the Agent to "Spotlight" what it wants to see, **Active Inhibition** gives it the power to "Filter Out" what it wants to ignore.

This mimics the biological ability to "suppress fear" or "ignore distractions" to focus on a high-stakes task.

#### Mechanism
-   **Excitation (Current):** `Threshold *= 0.9` (Easier to fire).
-   **Inhibition (Proposed):** `Threshold *= 1.2` (Harder to fire).

### Interaction with Lateral Inhibition

Currently, the system relies on **Lateral Inhibition** (Chapter 5) for suppression:
> "If I see A clearly, I passively suppress B."

Active Inhibition adds a **Pre-emptive** layer:
> "I don't need to see A to suppress B. I am actively deciding to suppress B regardless of A."

This decouples suppression from competition. The Agent can be "Calm" (suppressing everything) without needing to be "Hyper-focused" on one thing.

### Impact Analysis

#### Positive
1.  **Emotional Regulation ("Calmness")**:
    -   The Agent can dampen "Panic" or "Fear" neurons during dangerous but necessary maneuvers (e.g., crossing a trap).
    -   Prevents "Hysteria" loops where fear feeds on fear.

2.  **Noise Filtering**:
    -   In high-entropy environments, the Agent can suppress entire categories of sensory inputs (e.g., "Ignore visual noise, focus on motion").

3.  **Energy Efficiency**:
    -   By preventing irrelevant neurons from firing, the SNN consumes less computational resources (sparsity increases).

#### Negative (Risks)
1.  **Sensory Blinding (The "Hubris" Risk)**:
    -   **Description**: The Agent suppresses "Danger" signals to pursue a reward.
    -   **Result**: It walks directly into a trap because it literally "refused to see" it.
    -   **Mitigation**: "Pain" signals (negative reward) must bypass Top-Down inhibition (Bottom-Up override).

2.  **Cognitive Stiffness**:
    -   **Description**: If the Agent suppresses alternative solutions, it becomes rigid.
    -   **Result**: It fails to adapt when the primary plan fails because the "Backup Plan" neurons were suppressed.

3.  **Oscillation (The "Flicker" Effect)**:
    -   **Description**: RL suppresses Neuron A → Neuron A falls silent → RL thinks threat is gone → RL stops suppressing → Neuron A fires → RL panics and suppresses again.
    -   **Result**: Thresholds fluctuate wildly.
    -   **Mitigation**: Damping/Hysteresis in the control signal.

### Implementation Strategy

To implement this safely, we will extend `modulate_snn_attention` to accept a **Signed Control Signal**:
-   `Action_Excite`: Indices to Boost (`* 0.9`).
-   `Action_Inhibit`: Indices to Suppress (`* 1.1`).

This requires expanding the Action Space or using a multi-head RL output.

---

## 10.5 Risks & Safeguards

### Confirmation Bias (The Echo Chamber)
-   **Risk**: RL generates "Fight" action → SNN amplifies "Aggression" neurons → RL sees more "Aggression" signal → RL chooses "Fight" again.
-   **Mitigation**: The **Restoration Force** must be strong enough to prevent infinite looping. Additionally, **Novelty** rewards (Chapter 2) must remain active to encourage breaking out of loops.

### Threshold Collapse (Seizure)
-   **Risk**: Repeated modulation without restoration drives thresholds to 0. Neurons fire at every timestep (Max Fire Rate), conveying zero information (Entropy = 0).
-   **Mitigation**: Hard clamp `Threshold_min` (e.g., 0.1) and enforce the Restoration Force in every SNN cycle.

### Action-Neuron Coupling
-   **Risk**: Hardcoded mapping (e.g., `Neuron 0-25` = `Action 0`) is fragile.
-   **Future**: Use a learnable **Influence Matrix** or **Tagging** system where neurons "sign up" for specific action modulation via Hebbian association, rather than fixed indices.

---

## 10.6 Implementation Status Summary

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| **Threshold Modulation (Excitation)** | ✅ Implemented | `snn_rl_bridge.py` | Basic boost mechanism |
| **Elastic Restoration** | ✅ Implemented | `snn_rl_bridge.py` | Prevents permanent drift |
| **Derived Solidity Ratio** | ✅ Implemented | `snn_commitment_theus.py` | Safe modulation filter |
| **Active Inhibition (Suppression)** | ⚠️ Partial | `snn_rl_bridge.py` | Field exists, needs RL action expansion |

---

## 10.7 Conclusion

Top-Down modulation transforms the Agent from a passive learner to an **Active Perceiver**, capable of tuning its own perception to align with its goals. It mimics the biological "efferent" control of sensory organs.

The three-tier system provides:
1. **Basic Control** (10.2): Excitation via threshold modulation
2. **Safety Filter** (10.3): Only modulate mature neurons
3. **Advanced Control** (10.4): Inhibition for active suppression (planned)

---

> [!NOTE]
> **Related Chapters**:
> - Chapter 2: Learning Mechanisms (Commitment states)
> - Chapter 4: RL-SNN Interface (Bottom-up flow)
> - Chapter 5: Safety & Homeostasis (Lateral inhibition)
> - Chapter 9: Advanced Bridge Attention (Sigmoid gating)
