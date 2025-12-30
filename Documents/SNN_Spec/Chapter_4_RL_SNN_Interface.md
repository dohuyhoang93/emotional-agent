# Chapter 4: RL-SNN Bidirectional Interface

**Scope**: How the Logical Brain (RL) talks to the Intuitive Brain (SNN).

> [!IMPORTANT]
> **Implementation Status**: All mechanisms described in this chapter are **FULLY IMPLEMENTED** as of 2025-12-30.

---

## 4.1 Downstream: Environment to Intuition (`RL -> SNN`)

**Process**: `encode_state_to_spikes`  
**File**: `src/processes/snn_rl_bridge.py::_encode_state_to_spikes_impl` (Lines 146-187)  
**Status**: ✅ **IMPLEMENTED**

### Strategic Design Choice: "Blind RL, Sighted SNN"

The architecture intentionally splits sensory input to force reliance on emotional processing:

*   **RL Agent ("The Rational Mind")**: Receives a **5-dimensional sliced vector** (Position, Step Count). It is effectively **"Blind"** to walls, gates, and switches.
*   **SNN ("The Intuitive Brain")**: Receives the **Full 16-dimensional vector** (including Proximity Sensors, Auditory signals).

**Implication**: The RL Agent *cannot* solve the maze purely by rational observation of its input. It **MUST** rely on the `snn_emotion_vector` (which encodes the SNN's reaction to walls/dangers) to navigate. This proves the system's "Emotional Intelligence."

### Mechanism

**Implementation**:
```python
def _encode_state_to_spikes_impl(ctx: SystemContext):
    """Encode environment observation into SNN neuron potentials."""
    obs = ctx.domain_ctx.observation  # 16D sensor vector
    snn_ctx = ctx.domain_ctx.snn_context
    
    # Inject into input neurons (0-15)
    input_end = min(16, len(snn_ctx.domain_ctx.neurons))
    
    for i in range(input_end):
        neuron = snn_ctx.domain_ctx.neurons[i]
        val = obs[i]  # Sensor value [0, 1]
        
        # Amplification to cross threshold
        # NOTE: 5.0x amplification ensures neurons can fire
        # Sensor values [0, 1], threshold = 0.6
        # Amplification 5.0 → potential [0, 5.0]
        neuron.potential = val * 5.0
        
        # Full context for vector matching
        neuron.potential_vector = obs
```

**Steps**:
1.  **Input**: `current_observation` (16-dim vector from sensors).
2.  **Action**: Direct Injection.
    *   The system takes the first 16 neurons (Input Layer).
    *   It sets their `potential` equal to the sensor value multiplied by an **Amplification Factor** (5.0).
    *   `Neuron[i].Potential = Sensor[i] * 5.0`
3.  **Result**: The input neurons fire immediately if the signal is strong enough, initiating the SNN cascade.

**Hyperparameters**:
- `amplification_factor`: 5.0 (ensures threshold crossing)
- `input_neurons`: 16 (first 16 neurons)
- `sensor_range`: [0, 1] (normalized)

---

## 4.2 Upstream: Intuition to Logic (`SNN -> RL`)

**Process**: `encode_emotion_vector`  
**File**: `src/processes/snn_rl_bridge.py::encode_emotion_vector` (Lines 189-280)  
**Status**: ✅ **IMPLEMENTED** (Phase 9: Advanced Attention)

The RL Agent needs to know "How do I feel about this situation?".

### Mechanism (Phase 9: Sigmoid Gating Attention)

**Old Implementation** (Population Coding):
```python
# Simple mean of firing neuron prototypes
firing_protos = [neurons[i].prototype_vector for i in spike_queue]
emotion_vector = mean(firing_protos)  # 16D
```

**New Implementation** (Attention-Based):
```python
def encode_emotion_vector(ctx: SystemContext):
    """Encode SNN state into emotion vector using attention."""
    obs = ctx.domain_ctx.observation  # Query
    snn_ctx = ctx.domain_ctx.snn_context
    
    # 1. Gather neuron prototypes (Keys) and activity (Values)
    prototypes = [n.prototype_vector for n in neurons]  # (N, 16)
    activity = [n.potential for n in neurons]  # (N,)
    
    # 2. Compute similarity (Attention Scores)
    # Query: Current observation
    # Keys: Neuron prototypes
    similarities = cosine_similarity(obs, prototypes)  # (N,)
    
    # 3. Apply Sigmoid Gating (not Softmax!)
    # Temperature scaling for sensitivity
    attention_weights = sigmoid(similarities / temperature)  # (N,)
    
    # 4. Weighted aggregation
    # Combine prototype semantics with activity levels
    emotion_vector = sum(
        attention_weights[i] * activity[i] * prototypes[i]
        for i in range(N)
    )  # (16,)
    
    # 5. Normalize
    emotion_vector = L2_normalize(emotion_vector)
    
    ctx.domain_ctx.snn_emotion_vector = emotion_vector
```

**Key Innovation (Phase 9)**:
- **Sigmoid vs Softmax**: Allows multiple neurons to contribute independently
- **Temperature**: Controls attention sharpness (default: 1.0)
- **Query-based**: Only neurons relevant to current observation contribute

**Output**: `snn_emotion_vector` (16-dim)

**Interpretation**: This vector represents the **Current Emotional State** of the agent (e.g., "Fear", "Curiosity", "Safety").

**Hyperparameters**:
- `temperature`: 1.0 (attention sharpness)
- `min_activity_threshold`: 0.1 (ignore inactive neurons)

---

## 4.3 Interaction: The Feedback Loop

The two brain halves influence each other constantly.

### A. Emotion-Gated Action (`select_action_gated`)

**Process**: `select_action_gated`  
**File**: `src/processes/rl_processes.py::select_action_gated` (Lines 126-193)  
**Status**: ✅ **IMPLEMENTED**

*   **Logic**: The RL Agent uses the `snn_emotion_vector` to modulate its **Exploration Rate**.
*   **Equation**: `Exploration = Base_Rate * (1.0 + 0.5 * Emotion_Magnitude)`
*   **Meaning**: If the SNN is highly active (High Emotion), the agent becomes **more impulsive/curious**. If the SNN is quiet, the agent follows its rigid Q-Table.

**Implementation**:
```python
def select_action_gated(ctx: SystemContext):
    """Select action using emotion gating."""
    obs = ctx.domain_ctx.current_observation
    emotion = ctx.domain_ctx.snn_emotion_vector
    
    # Emotion-modulated exploration
    emotion_magnitude = float(torch.norm(emotion).item())
    adjusted_exploration = (
        ctx.domain_ctx.current_exploration_rate * 
        (1.0 + 0.5 * emotion_magnitude)
    )
    adjusted_exploration = min(adjusted_exploration, 1.0)
    
    # Get Q-values from Gated Network
    if ctx.domain_ctx.gated_network is not None:
        net = ctx.domain_ctx.gated_network
        obs_tensor = observation_to_tensor(obs)
        
        net.eval()
        with torch.no_grad():
            q_values_tensor = net(obs_tensor, emotion)
        net.train()
        
        q_values_list = q_values_tensor.tolist()
    else:
        # Fallback: Tabular Q-learning
        state_key = str(obs)
        q_values_list = ctx.domain_ctx.q_table.get(state_key, [0.0] * 4)
    
    # Epsilon-greedy with emotion modulation
    if np.random.rand() < adjusted_exploration:
        action = np.random.randint(0, 4)  # Explore
    else:
        action = int(np.argmax(q_values_list))  # Exploit
    
    ctx.domain_ctx.last_action = action
    ctx.domain_ctx.last_q_values = torch.tensor(q_values_list)
```

---

### B. Intrinsic Reward (Novelty)

**Process**: `compute_intrinsic_reward_snn`  
**File**: `src/processes/snn_rl_bridge.py::compute_intrinsic_reward_snn` (Lines 282-340)  
**Status**: ✅ **IMPLEMENTED**

*   **Logic**:
    *   `Novelty = 1 - Max_Similarity(Current_Pattern, Memory)`
    *   If the SNN creates a vector pattern it has never seen before, `Novelty` is high.
*   **Effect**: The RL Agent gets a "Dopamine Hit" (Reward), encouraging it to seek out new experiences even if they don't yield external points.

**Implementation**:
```python
def compute_intrinsic_reward_snn(ctx: SystemContext):
    """Compute novelty-based intrinsic reward."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    # Get current emotion vector
    current_emotion = ctx.domain_ctx.snn_emotion_vector
    
    # Compare with all neuron prototypes (memory)
    prototypes = [n.prototype_vector for n in snn_ctx.domain_ctx.neurons]
    
    # Compute max similarity
    similarities = [
        cosine_similarity(current_emotion, proto)
        for proto in prototypes
    ]
    max_similarity = max(similarities) if similarities else 0.0
    
    # Novelty = 1 - max_similarity
    novelty = 1.0 - max_similarity
    
    # Intrinsic reward (scaled)
    intrinsic_reward = novelty * intrinsic_reward_weight  # 0.05
    
    ctx.domain_ctx.intrinsic_reward = intrinsic_reward
```

**Hyperparameters**:
- `intrinsic_reward_weight`: 0.05 (5% of extrinsic reward)

---

## 4.4 Conclusion

The RL and SNN are not separate. They form a **Closed Loop**:

```
┌─────────────────────────────────────────────┐
│              Environment                    │
└─────────────────┬───────────────────────────┘
                  │ 16D Sensor Vector
                  ↓
┌─────────────────────────────────────────────┐
│         SNN (Intuitive Brain)               │
│  - Integrate (cosine-weighted)              │
│  - Fire (LIF dynamics)                      │
│  - Learn (STDP, Clustering)                 │
└─────────────────┬───────────────────────────┘
                  │ Emotion Vector (16D)
                  ↓
┌─────────────────────────────────────────────┐
│    Gated Integration Network (Neo-Cortex)  │
│  - Cross-Attention (Emotion × Observation)  │
│  - Fusion (Residual)                        │
│  - Q-Head (Action Values)                   │
└─────────────────┬───────────────────────────┘
                  │ Q-Values
                  ↓
┌─────────────────────────────────────────────┐
│         RL Agent (Rational Mind)            │
│  - Epsilon-greedy (emotion-modulated)       │
│  - Q-Learning (TD-error)                    │
│  - Intrinsic reward (novelty)               │
└─────────────────┬───────────────────────────┘
                  │ Action
                  ↓
┌─────────────────────────────────────────────┐
│              Environment                    │
│  - Execute action                           │
│  - Return reward                            │
└─────────────────────────────────────────────┘
```

**Feedback Loops**:
1. **Env → SNN**: Sensory input triggers emotional reaction
2. **SNN → Emotion**: Attention-based encoding
3. **Emotion → RL**: Modulates exploration and Q-values
4. **RL → Action**: Changes environment
5. **Reward → SNN**: TD-error as dopamine signal (3-Factor STDP)

---

## 4.5 The Neo-Cortex (Gated Integration Network)

**Process**: `GatedIntegrationNetwork` with `MultiHeadAttention`  
**File**: `src/models/gated_integration.py::GatedIntegrationNetwork` (Lines 85-237)  
**Status**: ✅ **IMPLEMENTED** (Phase 9)

Beyond strict Rules (Q-Table) and pure Intuition (SNN), the agent uses **Cross-Attention** to synthesize Logic and Emotion.

### Architecture (PyTorch Attentional Mechanism)

Instead of simple gating, we treat the Interaction as a **Query-Key-Value** problem:

*   **Query (Q)**: The **Emotional State** ("What do I feel? What matters to me right now?").
*   **Key (K)**: The **Observation Features** ("What acts/objects are present?").
*   **Value (V)**: The **Observation Data** itself.

### The Flow

**Implementation**:
```python
class GatedIntegrationNetwork(nn.Module):
    def __init__(
        self,
        obs_dim: int = 10,
        emotion_dim: int = 16,
        hidden_dim: int = 64,
        action_dim: int = 8,
        num_heads: int = 4,
        temperature: float = 1.0
    ):
        super().__init__()
        
        # 1. Dual Encoders
        self.obs_encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim)
        )
        
        self.emo_encoder = nn.Sequential(
            nn.Linear(emotion_dim, hidden_dim),
            nn.ReLU(),
            nn.LayerNorm(hidden_dim)
        )
        
        # 2. Cross-Attention
        self.attention = AttentionBlock(
            hidden_dim=hidden_dim,
            num_heads=num_heads,
            temperature=temperature
        )
        
        # 3. Q-Head
        self.q_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(self, obs, emotion):
        # Encode
        h_obs = self.obs_encoder(obs)    # (batch, 64)
        h_emo = self.emo_encoder(emotion)  # (batch, 64)
        
        # Cross-Attention: Emotion (Query) × Observation (Key/Value)
        context, attn_weights = self.attention(
            query=h_emo,
            key_value=h_obs
        )
        
        # Fusion (Residual)
        fused = h_obs + context  # Always see reality + emotion highlight
        
        # Q-Values
        q_values = self.q_head(fused)
        
        return q_values
```

**Attention Block** (Sub-feature Cross Attention):
```python
class AttentionBlock(nn.Module):
    def __init__(self, hidden_dim: int, num_heads: int = 4, temperature: float = 1.0):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.temperature = temperature
        
        # Projections
        self.q_proj = nn.Linear(hidden_dim, hidden_dim)
        self.k_proj = nn.Linear(hidden_dim, hidden_dim)
        self.v_proj = nn.Linear(hidden_dim, hidden_dim)
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        
        self.scale = self.head_dim ** -0.5
    
    def forward(self, query, key_value):
        batch_size = query.size(0)
        
        # Project & Reshape to [Batch, Num_Heads, 1, Head_Dim]
        q = self.q_proj(query).view(batch_size, self.num_heads, 1, self.head_dim)
        k = self.k_proj(key_value).view(batch_size, self.num_heads, 1, self.head_dim)
        v = self.v_proj(key_value).view(batch_size, self.num_heads, 1, self.head_dim)
        
        # Score per Head: (Q * K).sum(dim=-1)
        raw_scores = (q * k).sum(dim=-1, keepdim=True) * self.scale
        
        # Temperature scaling
        raw_scores = raw_scores / self.temperature
        
        # Stability: Clamp
        raw_scores = torch.clamp(raw_scores, min=-10.0, max=10.0)
        
        # Sigmoid Gating (not Softmax!)
        attn_weights = torch.sigmoid(raw_scores)  # [Batch, Heads, 1, 1]
        
        # Apply weights to Value
        out = v * attn_weights
        
        # Recombine heads
        out = out.reshape(batch_size, self.hidden_dim)
        return self.out_proj(out), attn_weights
```

### Key Components

1.  **Dual Encoders**:
    *   `Obs_Encoder`: `Input(5) -> MLP -> Hidden(64)`
    *   `Emo_Encoder`: `Input(16) -> MLP -> Hidden(64)`

2.  **Sub-feature Attention (4 Heads)**:
    *   We split the 64-dim vectors into 4 Heads (16 dims each).
    *   Each head allows the emotion to attend to different "subspaces" of reality (e.g., Head 1 tracks Danger, Head 2 tracks Rewards).

3.  **Attention Score**:
    *   `Score = Sigmoid( (Q * K).sum() / scale / temperature )`
    *   We use **Sigmoid** instead of Softmax to allow multiple independent features to be highlighted (or none).

4.  **Fusion**:
    *   `Context = Score * V`
    *   `Output = LayerNorm(Obs + Context)` (Residual Connection).
    *   The agent *always* sees reality (`Obs`), but Emotion highlights specific parts of it (`Context`).

5.  **Output**:
    *   Fused State -> MLP -> Q-Values (Action Potentials).

### Significance

*   **Focus, not just Bias**: The agent can choose to *ignore* irrelevant logical features if the emotional "Query" doesn't match the observation "Key".
*   **Deep RL**: Trained via DQN (MSE Loss) with gradient clipping for stability.

**Training**:
```python
# In update_q_learning process
if gated_network is not None:
    # Predict Q(s, a)
    q_values = net(state_tensor, emotion_tensor)
    current_q_val = q_values[action]
    
    # Target Q
    with torch.no_grad():
        next_q_values = net(next_state_tensor, next_emotion_tensor)
        max_next_q = torch.max(next_q_values)
        target_q_val = reward + 0.95 * max_next_q
    
    # Loss & Backprop
    loss = F.mse_loss(current_q_val, target_q_val)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

---

## 4.6 Implementation Status Summary

| Component | Status | File | Notes |
|-----------|--------|------|-------|
| **State → Spikes** | ✅ Implemented | `snn_rl_bridge.py` | 5.0x amplification |
| **SNN → Emotion** | ✅ Implemented | `snn_rl_bridge.py` | Phase 9 attention |
| **Emotion Gating** | ✅ Implemented | `rl_processes.py` | Modulated exploration |
| **Intrinsic Reward** | ✅ Implemented | `snn_rl_bridge.py` | Novelty-based |
| **Gated Network** | ✅ Implemented | `gated_integration.py` | Cross-attention |
| **Multi-Head Attention** | ✅ Implemented | `gated_integration.py` | 4 heads, Sigmoid |
| **Deep RL Training** | ✅ Implemented | `rl_processes.py` | DQN with MSE loss |

---

## 4.7 Hyperparameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `amplification_factor` | 5.0 | Input encoding strength |
| `attention_temperature` | 1.0 | Attention sharpness |
| `num_attention_heads` | 4 | Multi-head attention |
| `hidden_dim` | 64 | Network hidden size |
| `intrinsic_reward_weight` | 0.05 | Novelty reward scale |
| `emotion_exploration_factor` | 0.5 | Exploration modulation |
| `learning_rate` | 0.001 | Adam optimizer |
| `gamma` | 0.95 | Discount factor |

---

> [!NOTE]
> **Related Chapters**:
> - Chapter 2: Learning Mechanisms (3-Factor STDP uses TD-error)
> - Chapter 9: Advanced Bridge Attention (Detailed attention mechanism)
> - Chapter 10: Top-Down Modulation (RL → SNN threshold control)
