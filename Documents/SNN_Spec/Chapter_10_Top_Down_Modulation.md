# Chapter 10: Top-Down Modulation (RL → SNN Control)

> **Status:** Draft / Implementation
> **Target Phase:** Phase 10 (Closed Loop Control)
> **Reference Component:** `src/processes/snn_rl_bridge.py` (`modulate_snn_attention`)

## 1. Concept: Closing the Cognitive Loop

In previous chapters (4 & 9), the SNN acted as a "subconscious" feed that projected emotional states vectors **up** to the RL Agent (Bottom-Up).
This chapter defines the reverse path: The RL Agent exerting **Top-Down** control to influence the sensitivity of the SNN network.

### The "Focus" Metaphor
- **Bottom-Up (Attention):** "Hey, I (SNN) noticed something scary here."
- **Top-Down (Modulation):** "I (RL) am deciding to fight. SNN, become hyper-sensitive to 'Aggression' patterns and ignore 'Fear'."

## 2. Mechanism: Threshold Modulation

We control the SNN not by injecting spikes (which is sensory input), but by adjusting the **parameters** of neurons, specifically the **Firing Threshold**.

### The Logic
1.  **Action Mapping**: The RL Agent selects an Action (e.g., `UP`, `ATTACK`).
2.  **Sensitivity Boost**: Neurons associated with that action's concept receive a **decrease** in threshold.
3.  **Result**: These neurons fire more easily (requires less input potential), effectively "lowering the barrier" for expected stimuli.

$$ Threshold_{new} = Threshold_{current} \cdot (1 - \delta) $$

Where $\delta \approx 0.1$ (10% ease).

## 3. Dynamics & Stability (The "Elasticity" Principle)

A critical requirement for Top-Down modulation is that it must be **Transient** (temporary) and **Elastic**. If modulation is permanent, the network will permanently drift into a biased state ("Seizure" or "Obsession").

### 3.1 The Tug of War
We introduce two opposing forces:

1.  **Modulation Force (Fast)**: Driven by RL Steps. Pushes thresholds **down** rapidly to facilitate immediate action execution.
2.  **Restoration Force (Slow)**: Driven by Homeostasis. Pushes thresholds **up** back towards the `Initial Baseline`.

$$ \Delta Threshold_{restore} = \alpha \cdot (Threshold_{target} - Threshold_{current}) $$

This ensures that if the RL stops "paying attention" (stops performing the action), the neurons naturally relax back to their neutral state.

## 4. Risks & Safeguards

### 4.1 Confirmation Bias (The Echo Chamber)
-   **Risk**: RL generates "Fight" action -> SNN amplifies "Aggression" neurons -> RL sees more "Aggression" signal -> RL chooses "Fight" again.
-   **Mitigation**: The **Restoration Force** must be strong enough to prevent infinite looping. Additionally, **Novelty** rewards (Chapter 2) must remain active to encourage breaking out of loops.

### 4.2 Threshold Collapse (Seizure)
-   **Risk**: Repeated modulation without restoration drives thresholds to 0. Neurons fire at every timestep (Max Fire Rate), conveying zero information (Entropy = 0).
-   **Mitigation**: Hard clamp `Threshold_min` (e.g., 0.1) and enforce the Restoration Force in every SNN cycle.

### 4.3 Action-Neuron Coupling
-   **Risk**: Hardcoded mapping (e.g., `Neuron 0-25` = `Action 0`) is fragile.
-   **Future**: Use a learnable **Influence Matrix** or **Tagging** system where neurons "sign up" for specific action modulation via Hebbian association, rather than fixed indices.

## 5. Implementation Specification

### Function: `modulate_snn_attention`
-   **Input**: `last_action` (Int), `snn_context` (Context).
-   **Operation**: Identify target neurons indices. Multiply their `threshold` tensor by `0.9`.

### Function: `restore_snn_attention`
-   **Input**: `snn_context`.
-   **Operation**: Apply elastic restoration to **ALL** neurons.
-   **Formula**: `param += (target - param) * rate`.

## 6. Conclusion
Top-Down modulation transforms the Agent from a passive learner to an **Active Perceiver**, capable of tuning its own perception to align with its goals. It mimics the biological "efferent" control of sensory organs.
