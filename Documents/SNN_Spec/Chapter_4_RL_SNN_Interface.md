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

## 4.5 The Neo-Cortex (Gated MLP)
**Process**: `GatedIntegrationNetwork`

Beyond strict Rules (Q-Table) and pure Intuition (SNN), the agent has a **Synthesizer**.

### Architecture (PyTorch Implementation)
*   **Dual Encoders**: Two parallel 2-layer MLPs transform inputs into a shared latent space (`hidden_dim=64`).
    *   `Obs_Encoder`: `Input(10) -> Linear -> ReLU -> Linear -> Hidden(64)`
    *   `Emo_Encoder`: `Input(16) -> Linear -> ReLU -> Linear -> Hidden(64)`
*   **Element-wise Gating (The "Synthesizer")**:
    *   Unlike simple scalar gating, this uses a **Gate Vector** (size 64).
    *   `Gate = Sigmoid(Linear(Concatenate(Hidden_Obs, Hidden_Emo)))`
    *   **Fusion w/ Interpolation**: `H_Fused = Gate * H_Obs + (1 - Gate) * H_Emo`
    *   **Meaning**: The brain can choose to trust Logic for specific features (e.g., Position) while trusting Experience for others (e.g., Danger Level) *simultaneously*.
*   **Q-Head**: A final MLP maps the fused state to Action Values (`Action_Dim=4`).
*   **Significance**: The agent **learns when to trust its feelings vs. facts**.
    *   In stable environments, it might rely on facts (`Gate -> 1`).
    *   In chaotic/novel environments, it might fall back on intuition (`Gate -> 0`).
*   **Deep RL**: This network is trained via standard DQN (MSE Loss against temporal targets), allowing it to generalize beyond the tabular Q-learning limits.
