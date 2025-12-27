# Architecture Rationale: Emotion-Conditioned Sub-feature Gating Network

> [!NOTE]
> This document serves as the **Architecture Decision Record (ADR)** for the upgrade from Gated MLP to Attention-based Integration in the EmotionAgent.

## 1. Context and Problem Statement

The EmotionAgent operates on a hybrid architecture:
- **Rational Stream:** Processes raw observations (Logic).
- **Emotional Stream:** Processes SNN-derived emotion vectors (Feeling).

**Problem:** In the previous Gated MLP architecture, a simple scalar gate determined the influence of emotion. Empirical analysis and "Multimodal Imbalance" theory suggested that the high-dimensional, high-frequency Observation vector could structurally dominate the simpler Emotion vector, effectively ignoring the agent's internal state.

**Goal:** Create a mechanism where Emotion can dynamically "highlight" or "suppress" specific aspects of reality (Contextual Focus) without completely overriding the rational input.

## 2. Decision: Sub-feature Cross-Attention

We decided to implement a specific variation of Attention called **"Sub-feature Cross-Attention"** with **Sigmoid Gating**.

### 2.1 The Architecture
Instead of treating inputs as sequences (standard NLP), we treat them as global vectors composed of latent "subspaces".

$$
\text{Attention}(Q, K, V) = \text{Sigmoid}\left(\frac{Q \cdot K}{\sqrt{d_{head}} \cdot \tau}\right) \odot V
$$

Where:
- **Query (Q):** Emotion Vector (What I care about).
- **Key (K):** Observation Vector (What I see).
- **Value (V):** Observation Vector (Content).
- **Output:** Gated Observation + Original Observation (Residual).

### 2.2 Why Not Standard Transformer Attention?

Standard Transformer Attention uses `Softmax` and requires `Seq_Len > 1`.
We rejected this standard approach because:

1.  **No Sequence:** Our inputs are single global state vectors. Forcing a sequence structure (e.g., repeating vectors) introduces unnecessary computational overhead.
2.  **Independence vs. Competition:**
    - **Softmax** forces a "Winner-Take-All" distribution ($\sum p_i = 1$). If the agent pays attention to "Danger", it *must* ignore "Reward".
    - **Sigmoid** allows independent gating. The agent can attend to *both* Danger and Reward (if relevant), or *neither* (if neutral). This fits the "Modulation" paradigm better than "Routing".

### 2.3 Why Not Simple Dot-Product?

We partition the 64-dim hidden vector into **4 Heads** (16-dim each).
- **Reason:** A single global dot product is too coarse (Scalar).
- **Benefit:** Each head can learn to represent a semantic subspace (e.g., Head 1: Spatial, Head 2: Entity, Head 3: Threat). This allows "Mixed Feelings" to attend to "Mixed Reality".

## 3. Stabilization Measures (The "Paper-Ready" Fixes)

To ensure this non-standard attention remains stable during RL training (which is notoriously unstable), we implemented strict constraints:

1.  **Scaling:** $\frac{1}{\sqrt{d}}$ to normalize dot products.
2.  **Temperature ($\tau$):** Controls the "sharpness" of the sigmoid gate.
3.  **Clamping:** Hard-clamping scores to $[-10, 10]$ to prevent vanishing gradients in Sigmoid.
4.  **LayerNorm:** Applied post-fusion to prevent the "Gated" signal from overwhelming the "Residual" signal.
5.  **Gradient Clipping:** Enforced in the trainer to catch any sudden spikes.

## 4. Conclusion

This architecture is verified mathematically correct and is essentially an **Emotion-Conditioned Gating Network**. It provides the expressivity of Attention (dynamic weighting) without the baggage of Sequence Processing, making it highly efficient for this specific RL agent.
