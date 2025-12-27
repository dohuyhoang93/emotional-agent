"""
Gated Integration Network
==========================
PyTorch model kết hợp Observation và SNN Emotion qua AttentionMechanism.

Author: Do Huy Hoang
Date: 2025-12-27
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class AttentionBlock(nn.Module):
    """
    Sub-feature Cross Attention Block.
    Allow Emotion (Query) to attend to different subspaces of Observation (Key/Value).
    """
    def __init__(self, hidden_dim: int, num_heads: int = 4, temperature: float = 1.0):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.num_heads = num_heads
        self.head_dim = hidden_dim // num_heads
        self.temperature = temperature
        
        assert hidden_dim % num_heads == 0, "Hidden dim must be divisible by num_heads"
        
        # Projections
        self.q_proj = nn.Linear(hidden_dim, hidden_dim)
        self.k_proj = nn.Linear(hidden_dim, hidden_dim)
        self.v_proj = nn.Linear(hidden_dim, hidden_dim)
        
        self.out_proj = nn.Linear(hidden_dim, hidden_dim)
        self.scale = self.head_dim ** -0.5
        
    def forward(self, query: torch.Tensor, key_value: torch.Tensor) -> torch.Tensor:
        """
        Args:
            query: Emotion Vector [Batch, Hidden]
            key_value: Observation Vector [Batch, Hidden]
        """
        batch_size = query.size(0)
        
        # Project & Reshape to [Batch, Num_Heads, Seq_Len=1, Head_Dim]
        # Treat the input vectors as single-token sequences
        q = self.q_proj(query).view(batch_size, self.num_heads, 1, self.head_dim)
        k = self.k_proj(key_value).view(batch_size, self.num_heads, 1, self.head_dim)
        v = self.v_proj(key_value).view(batch_size, self.num_heads, 1, self.head_dim)
        
        # We want to ATTEND to features.
        # Standard Dot-Product Attention (Q @ K^T) over Seq=1 is trivial (Always 1.0).
        # TRICK: We use "Subspace Attention" logic.
        # We want the Q to re-weight the V based on alignment.
        # But if Seq=1, alignment is scalar.
        
        # Improvement: "Feature-wise Attention" / Gating
        # Calculate unnormalized scores: Q * K (Element-wise)
        # We want to know if specific Emotion HEAD matches Observation HEAD.
        
        # Score: [Batch, Num_Heads, 1, Head_Dim]
        # This is element-wise interaction.
        # We can sum over Head_Dim to get scalar relevance per head.
        
        # Score per Head: (Q * K).sum(dim=-1) -> [Batch, Num_Heads, 1]
        raw_scores = (q * k).sum(dim=-1, keepdim=True) * self.scale
        
        # Apply Temperature
        raw_scores = raw_scores / self.temperature
        
        # Stability: Clamp scores to avoid Sigmoid saturation
        raw_scores = torch.clamp(raw_scores, min=-10.0, max=10.0)
        
        # Activation: Sigmoid (Gating) instead of Softmax (Selection)
        # Because we only have 1 item, Softmax is always 1.
        attn_weights = torch.sigmoid(raw_scores) # [Batch, Num_Heads, 1, 1]
        
        # Apply weights to Value
        # [Batch, Num_Heads, 1, Head_Dim] * [Batch, Num_Heads, 1, 1]
        out = v * attn_weights
        
        # Recombine
        out = out.reshape(batch_size, self.hidden_dim)
        return self.out_proj(out), attn_weights


class GatedIntegrationNetwork(nn.Module):
    """
    Revised Gated Integration Network: Using Cross-Attention.
    
    New Architecture:
    - Obs Encoder -> h_obs
    - Emo Encoder -> h_emo
    - Attention(Q=h_emo, KV=h_obs) -> context
    - Fusion: h_obs + context (Residual)
    - Q-Head -> Actions
    """
    
    def __init__(
        self,
        obs_dim: int = 10,
        emotion_dim: int = 16,
        hidden_dim: int = 64,
        action_dim: int = 4
    ):
        super().__init__()
        
        self.obs_dim = obs_dim
        self.emotion_dim = emotion_dim
        self.hidden_dim = hidden_dim
        self.action_dim = action_dim
        
        # === Encoders ===
        self.obs_encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        self.emotion_encoder = nn.Sequential(
            nn.Linear(emotion_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # === Attention Mechanism ===
        # Replaces simple Sigmoid Gating
        self.attention = AttentionBlock(hidden_dim, num_heads=4, temperature=1.0)
        
        # === Fusion Stabilization ===
        self.ln_fusion = nn.LayerNorm(hidden_dim)
        
        # === Q-value Head ===
        self.q_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
        
        # Layer Norm for stability (Anti-Imbalance)
        self.ln_obs = nn.LayerNorm(hidden_dim)
        self.ln_emo = nn.LayerNorm(hidden_dim)
    
    def forward(
        self,
        observation: torch.Tensor,
        emotion_vector: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.
        """
        # Handle single sample
        if observation.dim() == 1:
            observation = observation.unsqueeze(0)
        if emotion_vector.dim() == 1:
            emotion_vector = emotion_vector.unsqueeze(0)
        
        # Encode
        h_obs = self.obs_encoder(observation)
        h_emo = self.emotion_encoder(emotion_vector)
        
        # Normalize (Crucial for Attention)
        h_obs = self.ln_obs(h_obs)
        h_emo = self.ln_emo(h_emo)
        
        # Cross-Attention: Emotion acts as Query to filter Observation
        # "Contextual Focus": Which parts of Observation align with current Emotion?
        # context: [Batch, Hidden]
        context, _ = self.attention(query=h_emo, key_value=h_obs)
        
        # Residual Fusion
        # We start with Observation (Rational), and add Emotional Context
        # Output = Obs + Attention(Obs given Emotion)
        h_fused = h_obs + context
        
        # Stabilization (Option 3 from Feedback)
        h_fused = self.ln_fusion(h_fused)
        
        # Q-values
        q_values = self.q_head(h_fused)
        
        # Squeeze if needed
        if q_values.shape[0] == 1:
            q_values = q_values.squeeze(0)
        
        return q_values
    
    def get_attention_weights(
        self,
        observation: torch.Tensor,
        emotion_vector: torch.Tensor
    ) -> torch.Tensor:
        """Get attention weights [Batch, Num_Heads]"""
        if observation.dim() == 1:
            observation = observation.unsqueeze(0)
        if emotion_vector.dim() == 1:
            emotion_vector = emotion_vector.unsqueeze(0)
            
        h_obs = self.ln_obs(self.obs_encoder(observation))
        h_emo = self.ln_emo(self.emotion_encoder(emotion_vector))
        
        _, weights = self.attention(h_emo, h_obs)
        # weights: [Batch, Num_Heads, 1, 1]
        # FIX: Use view ensures batch dimension is preserved even if batch_size=1
        return weights.view(weights.size(0), self.attention.num_heads)


# Keep Trainer class as is
class GatedIntegrationTrainer:
    def __init__(
        self,
        model: GatedIntegrationNetwork,
        learning_rate: float = 1e-3,
        device: str = 'cpu'
    ):
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
    
    def train_step(self, observation, emotion_vector, target_q) -> float:
        observation = observation.to(self.device)
        emotion_vector = emotion_vector.to(self.device)
        target_q = target_q.to(self.device)
        
        pred_q = self.model(observation, emotion_vector)
        loss = self.criterion(pred_q, target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        
        # Stability: Gradient Clipping (Added as per Final Review)
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
        
        self.optimizer.step()
        return loss.item()
