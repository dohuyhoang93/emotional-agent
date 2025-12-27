# Chapter 4: RL-SNN Bidirectional Interface

**Scope**: How the Logical Brain (RL) talks to the Intuitive Brain (SNN).

## 4.1 Downstream: Environment to Intuition (`RL -> SNN`)
**Process**: `encode_state_to_spikes`

The SNN needs to "feel" what the agent sees.
1.  **Input**: `current_observation` (16-dim vector from sensors).
2.  **Action**: Direct Injection.
    *   The system takes the first 16 neurons (Input Layer).
    *   It sets their `potential` equal to the sensor value multiplied by an **Amplification Factor** (5.0).
    *   `Neuron[i].Potential = Sensor[i] * 5.0`
3.  **Result**: The input neurons fire immediately if the signal is strong enough, initiating the SNN cascade.

## 4.2 Upstream: Intuition to Logic (`SNN -> RL`)
**Process**: `encode_emotion_vector`

The RL Agent needs to know "How do I feel about this situation?".
1.  **Mechanism (Population Coding)**:
    *   The system scans all neurons that fired in the current tick.
    *   It collects their `prototype_vectors` (their semantic meaning).
    *   It calculates the **Mean Vector** (The "General Vibe").
2.  **Output**: `snn_emotion_vector` (16-dim).
3.  **Interpretation**: This vector represents the **Current Emotional State** of the agent (e.g., "Fear", "Curiosity", "Safety").

## 4.3 Interaction: The Feedback Loop
The two brain halves influence each other constantly.

### A. Emotion-Gated Action (`select_action_gated`)
*   **Logic**: The RL Agent uses the `snn_emotion_vector` to modulate its **Exploration Rate**.
*   **Equation**: `Exploration = Base_Rate * (1.0 + 0.5 * Emotion_Magnitude)`
*   **Meaning**: If the SNN is highly active (High Emotion), the agent becomes **more impulsive/curious**. If the SNN is quiet, the agent follows its rigid Q-Table.

### B. Intrinsic Reward (Novelty)
*   **Process**: `compute_intrinsic_reward_snn`
*   **Logic**:
    *   `Novelty = 1 - Max_Similarity(Current_Pattern, Memory)`
    *   If the SNN creates a vector pattern it has never seen before, `Novelty` is high.
*   **Effect**: The RL Agent gets a "Dopamine Hit" (Reward), encouraging it to seek out new experiences even if they don't yield external points.

## 4.4 Conclusion
The RL and SNN are not separate. They form a **Closed Loop**:
*   Env -> SNN (Reaction)
*   SNN -> Emotion (Feeling)
*   Emotion -> RL (Bias)
*   RL -> Action (Change Env)

## 4.5 The Neo-Cortex (Cross-Attention Network)
**Process**: `GatedIntegrationNetwork` with `MultiHeadAttention`

Beyond strict Rules (Q-Table) and pure Intuition (SNN), the agent uses **Cross-Attention** to synthesize Logic and Emotion.

### Architecture (PyTorch Attentional Mechanism)

Instead of simple gating, we treat the Interaction as a **Query-Key-Value** problem:
*   **Query (Q)**: The **Emotional State** ("What do I feel? What matters to me right now?").
*   **Key (K)**: The **Observation Features** ("What acts/objects are present?").
*   **Value (V)**: The **Observation Data** itself.

### The Flow
1.  **Dual Encoders**:
    *   `Obs_Encoder`: `Input(5) -> MLP -> Hidden(64)`
    *   `Emo_Encoder`: `Input(16) -> MLP -> Hidden(64)`
2.  **Sub-feature Attention (4 Heads)**:
    *   We split the 64-dim vectors into 4 Heads (16 dims each).
    *   Each head allows the emotion to attend to different "subspaces" of reality (e.g., Head 1 tracks Danger, Head 2 tracks Rewards).
3.  **Attention Score**:
    *   `Score = Sigmoid( (Q @ K.T) / scale )`
    *   We uses **Sigmoid** instead of Softmax to allow multiple independent features to be highlighted (or none).
4.  **Fusion**:
    *   `Context = Score * V`
    *   `Output = LayerNorm(Obs + Context)` (Residual Connection).
    *   The agent *always* sees reality (`Obs`), but Emotion highlights specific parts of it (`Context`).
5.  **Output**:
    *   Fused State -> MLP -> Q-Values (Action Potentials).

### Significance
*   **Focus, not just Bias**: The agent can choose to *ignore* irrelevant logical features if the emotional "Query" doesn't match the observation "Key".
*   **Deep RL**: Trained via DQN (MSE Loss) with gradient clipping for stability.
