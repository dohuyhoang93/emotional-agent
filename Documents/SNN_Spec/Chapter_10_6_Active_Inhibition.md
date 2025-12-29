# Chapter 10.6: Active Inhibition (Top-Down Suppression)

> **Status:** Proposal / Draft
> **Target Phase:** Phase 11 (Advanced Control)
> **Reference Component:** Future update to `snn_rl_bridge.py`

## 1. Concept: The Power to "Ignore"

While **Attention Modulation (Chapter 10)** allows the Agent to "Spotlight" what it wants to see (Excitatory), **Active Inhibition** gives it the power to "Filter Out" what it wants to ignore (Inhibitory).

This mimics the biological ability to "suppress fear" or "ignore distractions" to focus on a high-stakes task.

### Mechanism
-   **Current (Spotlight):** `Threshold *= 0.9` (Easier to fire).
-   **Proposed (Suppression):** `Threshold *= 1.2` (Harder to fire).

## 2. Interaction with Lateral Inhibition

Currently, the system relies on **Lateral Inhibition** (Chapter 7) for suppression:
> "If I see A clearly, I passively suppress B."

Active Inhibition adds a **Pre-emptive** layer:
> "I don't need to see A to suppress B. I am actively deciding to suppress B regardless of A."

This decouples suppression from competition. The Agent can be "Calm" (suppressing everything) without needing to be "Hyper-focused" on one thing.

## 3. Impact Analysis (Positive)

1.  **Emotional Regulation ("Calmness")**:
    -   The Agent can dampen "Panic" or "Fear" neurons during dangerous but necessary maneuvers (e.g., crossing a trap).
    -   Prevents "Hysteria" loops where fear feeds on fear.

2.  **Noise Filtering**:
    -   In high-entropy environments, the Agent can suppress entire categories of sensory inputs (e.g., "Ignore visual noise, focus on motion").

3.  **Energy Efficiency**:
    -   By preventing irrelevant neurons from firing, the SNN consumes less computational resources (sparsity increases).

## 4. Risk Analysis (Negative)

1.  **Sensory Blinding ( The "Hubris" Risk)**:
    -   **Description**: The Agent suppresses "Danger" signals to pursue a reward.
    -   **Result**: It walks directly into a trap because it literally "refused to see" it.
    -   **Mitigation**: "Pain" signals (negative reward) must bypass Top-Down inhibition (Bottom-Up override).

2.  **Cognitive Stiffness**:
    -   **Description**: If the Agent suppresses alternative solutions, it becomes rigid.
    -   **Result**: It fails to adapt when the primary plan fails because the "Backup Plan" neurons were suppressed.

3.  **Oscillation (The "Flicker" Effect)**:
    -   **Description**: RL suppresses Neuron A $\to$ Neuron A falls silent $\to$ RL thinks threat is gone $\to$ RL stops suppressing $\to$ Neuron A fires $\to$ RL panics and suppresses again.
    -   **Result**: Thresholds fluctuate wildly.
    -   **Mitigation**: Damping/Hysteresis in the control signal.

## 5. Implementation Strategy

To implement this safely, we will extend `modulate_snn_attention` to accept a **Signed Control Signal**:
-   `Action_Excite`: Indices to Boost (`* 0.9`).
-   `Action_Inhibit`: Indices to Suppress (`* 1.1`).

This requires expending the Action Space or using a multi-head RL output.
