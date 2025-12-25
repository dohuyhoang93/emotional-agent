"""
Gated Integration Network
==========================
PyTorch model kết hợp Observation và SNN Emotion qua Gating.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class GatedIntegrationNetwork(nn.Module):
    """
    Gated Integration Network: Kết hợp Observation và Emotion.
    
    Architecture:
    - Observation Encoder: obs → h_obs
    - Emotion Encoder: emotion → h_emo
    - Gating Mechanism: gate = σ(W[h_obs; h_emo])
    - Fusion: h = gate ⊙ h_obs + (1-gate) ⊙ h_emo
    - Q-value Head: h → Q(s,a)
    
    NOTE: Có side effects (gradient computation) nhưng đây là ML model,
    không phải process nên không cần @process decorator.
    """
    
    def __init__(
        self,
        obs_dim: int = 10,
        emotion_dim: int = 16,
        hidden_dim: int = 64,
        action_dim: int = 4
    ):
        """
        Initialize network.
        
        Args:
            obs_dim: Observation dimension
            emotion_dim: Emotion vector dimension (từ SNN)
            hidden_dim: Hidden layer dimension
            action_dim: Number of actions
        """
        super().__init__()
        
        self.obs_dim = obs_dim
        self.emotion_dim = emotion_dim
        self.hidden_dim = hidden_dim
        self.action_dim = action_dim
        
        # === Observation Encoder ===
        self.obs_encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # === Emotion Encoder ===
        self.emotion_encoder = nn.Sequential(
            nn.Linear(emotion_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # === Gating Mechanism ===
        self.gate_network = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Sigmoid()  # Gate values [0, 1]
        )
        
        # === Q-value Head ===
        self.q_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(
        self,
        observation: torch.Tensor,
        emotion_vector: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            observation: [batch, obs_dim] or [obs_dim]
            emotion_vector: [batch, emotion_dim] or [emotion_dim]
        
        Returns:
            q_values: [batch, action_dim] or [action_dim]
        """
        # Handle single sample (no batch)
        if observation.dim() == 1:
            observation = observation.unsqueeze(0)
        if emotion_vector.dim() == 1:
            emotion_vector = emotion_vector.unsqueeze(0)
        
        # Encode observation
        h_obs = self.obs_encoder(observation)
        
        # Encode emotion
        h_emo = self.emotion_encoder(emotion_vector)
        
        # Concatenate
        h_concat = torch.cat([h_obs, h_emo], dim=-1)
        
        # Compute gate
        gate = self.gate_network(h_concat)
        
        # Gated fusion
        h_fused = gate * h_obs + (1 - gate) * h_emo
        
        # Q-values
        q_values = self.q_head(h_fused)
        
        # Remove batch dim if single sample
        if q_values.shape[0] == 1:
            q_values = q_values.squeeze(0)
        
        return q_values
    
    def get_gate_values(
        self,
        observation: torch.Tensor,
        emotion_vector: torch.Tensor
    ) -> torch.Tensor:
        """
        Get gate values (for analysis).
        
        Args:
            observation: [batch, obs_dim] or [obs_dim]
            emotion_vector: [batch, emotion_dim] or [emotion_dim]
        
        Returns:
            gate: [batch, hidden_dim] or [hidden_dim]
        """
        # Handle single sample
        if observation.dim() == 1:
            observation = observation.unsqueeze(0)
        if emotion_vector.dim() == 1:
            emotion_vector = emotion_vector.unsqueeze(0)
        
        # Encode
        h_obs = self.obs_encoder(observation)
        h_emo = self.emotion_encoder(emotion_vector)
        
        # Concatenate
        h_concat = torch.cat([h_obs, h_emo], dim=-1)
        
        # Gate
        gate = self.gate_network(h_concat)
        
        # Remove batch dim if single sample
        if gate.shape[0] == 1:
            gate = gate.squeeze(0)
        
        return gate


class GatedIntegrationTrainer:
    """
    Trainer cho Gated Integration Network.
    
    NOTE: Có side effects (model updates, optimizer steps).
    """
    
    def __init__(
        self,
        model: GatedIntegrationNetwork,
        learning_rate: float = 1e-3,
        device: str = 'cpu'
    ):
        """
        Initialize trainer.
        
        Args:
            model: Gated integration network
            learning_rate: Learning rate
            device: 'cpu' or 'cuda'
        """
        self.model = model.to(device)
        self.device = device
        
        # Optimizer
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=learning_rate
        )
        
        # Loss function
        self.criterion = nn.MSELoss()
    
    def train_step(
        self,
        observation: torch.Tensor,
        emotion_vector: torch.Tensor,
        target_q: torch.Tensor
    ) -> float:
        """
        Single training step.
        
        Args:
            observation: [batch, obs_dim]
            emotion_vector: [batch, emotion_dim]
            target_q: [batch, action_dim]
        
        Returns:
            loss: Scalar loss value
        """
        # Move to device
        observation = observation.to(self.device)
        emotion_vector = emotion_vector.to(self.device)
        target_q = target_q.to(self.device)
        
        # Forward
        pred_q = self.model(observation, emotion_vector)
        
        # Loss
        loss = self.criterion(pred_q, target_q)
        
        # Backward
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def predict(
        self,
        observation: torch.Tensor,
        emotion_vector: torch.Tensor
    ) -> torch.Tensor:
        """
        Predict Q-values (no gradient).
        
        Args:
            observation: [obs_dim]
            emotion_vector: [emotion_dim]
        
        Returns:
            q_values: [action_dim]
        """
        self.model.eval()
        
        with torch.no_grad():
            observation = observation.to(self.device)
            emotion_vector = emotion_vector.to(self.device)
            
            q_values = self.model(observation, emotion_vector)
        
        self.model.train()
        
        return q_values.cpu()
