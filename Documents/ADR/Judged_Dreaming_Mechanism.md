# ADR: RL-Judged Dreaming (Proposal)

**Status**: Proposed
**Date**: 2025-12-27
**Author**: Antigravity (AI Assistant)
**Context**: Phase 2 Dream Architecture (SNN-RL Hybrid)

## 1. The Problem: "Blind Coherence"
Currently, the Dream Cycle (Phase 13/14) uses a **Coherence Reward** mechanism:
*   **Metric**: `Active Ratio` (5% - 30% neurons firing).
*   **Logic**: If the network activity is stable (not too quiet, not epileptic), we assume it is "good" and reinforce the synapses via STDP (+0.1 reward).
*   **Flaw**: The brain rewards **Functionally Useless** stability. The agent can dream of "walking into a wall repeatedly" or "spinning in circles" comfortably. As long as the neural firing is smooth, it becomes a SOLID memory.
*   **Risk**: **Delusion** (Hoang Tuong). The agent learns wrong physics or bad policies simply because they are easy to simulate.

## 2. The Solution: "Judged Dreaming" (RL-SNN Bridge)
We propose injecting the **RL Q-Network** into the dream loop as a "Critic".

### Mechanism
1.  **Replay/Simulate**: The SNN runs its course (Dream Step), producing a `Spike Queue`.
2.  **Decode**: Convert `Spike Queue` -> `Reconstructed State (s')` (using Decoder).
3.  **Judge (The Critic)**:
    *   The RL Agent (Q-Network) evaluates the state `s'` based on its existing Q-Table (learned from Reality).
    *   It calculates the **Value** of the dreamed state: `V(s') = max Q(s', a)`.
4.  **Feedback**:
    *   **High Value (Good Dream)**: If `V(s')` is high (e.g., reaching goal), RL sends a **Positive Signal** (+1.0).
    *   **Low Value (Bad/Dangerous Dream)**: If `V(s')` is low (e.g., hitting wall, pain), RL sends a **Negative Signal** (-1.0).
5.  **Consolidation**:
    *   SNN uses this *Judge Signal* (instead of just Coherence) as `td_error` for STDP.
    *   **Result**: The agent "learns from its nightmares" to avoid them, and reinforces "success visualization".

## 3. Implementation Plan (Future Phase)
*   **New Process**: `process_dream_judgement`.
*   **Input**: `domain.snn_context`, `domain.q_table`.
*   **Output**: `domain.td_error`.
*   **Workflow**:
    ```yaml
    - process_inject_dream_stimulus
    - process_snn_cycle
    - process_decode_dream       # Existing
    - process_dream_judgement    # NEW: Overwrites td_error from Coherence
    - process_stdp_3factor       # Learns based on Judgement
    ```

## 4. Consequences
### Positive
*   **Grounding**: Dreams are tethered to reality (via Q-Table). Prevents hallucination of impossible/wrong physics.
*   **Planning**: Effectively implements Monte-Carlo Tree Search (MCTS) in sleep. The agent "thinks ahead" about possible futures and consolidates the best paths.

### Negative
*   **Loop**: If the Q-Table is wrong (early training), the agent will reinforce wrong dreams. Making the agent "stubborn".
*   **Cost**: decoding and querying Q-table every dream step is computationally expensive.

## 5. Decision
*   **Current State**: Use `Coherence Reward` for initialization (Baby Agent).
*   **Future Upgrade**: Switch to `Judged Dreaming` when Agent is mature (Adolescent Agent).
