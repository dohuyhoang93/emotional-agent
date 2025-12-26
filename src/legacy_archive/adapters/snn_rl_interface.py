"""
SNN-RL Interface Layer
======================
Interface giữa SNN và RL Agent với Theus framework.

CRITICAL: Side-effects handling cho environment interaction.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
import torch
from theus import process
from src.core.context import SystemContext  # RL Agent context
from src.core.snn_context_theus import SNNSystemContext


class SNNRLInterface:
    """
    Interface giữa SNN và RL Agent.
    
    CRITICAL: Xử lý side-effects khi giao tiếp với environment.
    
    Responsibilities:
    - SNN → RL: Population Code (emotion vector)
    - RL → SNN: State Encoding (observation → spikes)
    - RL → SNN: Top-down Modulation (attention control)
    - SNN → RL: Intrinsic Reward (novelty signal)
    """
    
    def __init__(self, snn_ctx: SNNSystemContext):
        """
        Initialize interface.
        
        Args:
            snn_ctx: SNN system context
        """
        self.snn = snn_ctx
    
    # ===================================================================
    # SNN → RL: Population Code (Emotion Vector)
    # ===================================================================
    
    @staticmethod
    @process(
        inputs=[
            'snn_ctx.domain_ctx.neurons'
        ],
        outputs=[
            'rl_ctx.domain_ctx.snn_emotion_vector'
        ],
        side_effects=[]  # Pure function - no external calls
    )
    def encode_emotion_vector(
        snn_ctx: SNNSystemContext,
        rl_ctx: SystemContext
    ):
        """
        Trích xuất emotion vector từ SNN output neurons.
        
        Population Code: Đọc prototype vectors từ emotion layer.
        
        NOTE: Pure function - chỉ đọc SNN state, ghi RL context.
        
        Args:
            snn_ctx: SNN context
            rl_ctx: RL context
        """
        # Emotion layer: neurons 84-99 (16 neurons)
        emotion_start = 84
        emotion_end = 100
        emotion_dim = 16
        
        emotion_vector = np.zeros(emotion_dim)
        
        # Extract prototype vectors từ emotion neurons
        for i, nid in enumerate(range(emotion_start, emotion_end)):
            if nid < len(snn_ctx.domain_ctx.neurons):
                neuron = snn_ctx.domain_ctx.neurons[nid]
                # Lấy first component của prototype vector
                emotion_vector[i] = neuron.prototype_vector[0]
        
        # Normalize
        norm = np.linalg.norm(emotion_vector)
        if norm > 0:
            emotion_vector = emotion_vector / norm
        
        # Convert to PyTorch tensor
        emotion_tensor = torch.tensor(
            emotion_vector,
            dtype=torch.float32
        )
        
        # Update RL context
        rl_ctx.domain_ctx.snn_emotion_vector = emotion_tensor
    
    # ===================================================================
    # RL → SNN: State Encoding (Observation → Spikes)
    # ===================================================================
    
    @staticmethod
    @process(
        inputs=[
            'rl_ctx.domain_ctx.current_observation'
        ],
        outputs=[
            'snn_ctx.domain_ctx.neurons'  # potential_vector injected
        ],
        side_effects=[]  # Pure function - no external calls
    )
    def encode_state_to_spikes(
        rl_ctx: SystemContext,
        snn_ctx: SNNSystemContext
    ):
        """
        Encode RL observation thành spike pattern cho SNN.
        
        Spatial Encoding: Position → Spike pattern.
        
        NOTE: Pure function - chỉ đọc RL state, ghi SNN neurons.
        
        Args:
            rl_ctx: RL context
            snn_ctx: SNN context
        """
        obs = rl_ctx.domain_ctx.current_observation
        
        # Extract agent position
        x, y = obs['agent_pos']
        
        # Spatial encoding (16-dim pattern)
        pattern = np.zeros(16)
        pattern[x % 8] = 1.0
        pattern[8 + (y % 8)] = 1.0
        
        # Normalize
        norm = np.linalg.norm(pattern)
        if norm > 0:
            pattern = pattern / norm
        
        # Inject vào input neurons (0-15)
        input_end = min(16, len(snn_ctx.domain_ctx.neurons))
        
        for i in range(input_end):
            neuron = snn_ctx.domain_ctx.neurons[i]
            # Set potential_vector
            neuron.potential_vector = pattern * 2.0
            # Set scalar potential (vượt threshold để bắn)
            neuron.potential = 2.0
    
    # ===================================================================
    # RL → SNN: Top-down Modulation (Attention Control)
    # ===================================================================
    
    @staticmethod
    @process(
        inputs=[
            'rl_ctx.domain_ctx.td_error'
        ],
        outputs=[
            'snn_ctx.domain_ctx.neurons'  # threshold modulated
        ],
        side_effects=[]  # Pure function
    )
    def modulate_attention(
        rl_ctx: SystemContext,
        snn_ctx: SNNSystemContext,
        region: str,
        strength: float
    ):
        """
        Điều chỉnh threshold của một vùng neurons (attention).
        
        Top-down Modulation: RL điều khiển SNN focus.
        
        NOTE: Pure function - chỉ thay đổi thresholds.
        
        Args:
            rl_ctx: RL context
            snn_ctx: SNN context
            region: Vùng cần modulate ('fear', 'joy', 'curiosity')
            strength: Độ mạnh modulation [-1, 1]
        """
        # Region map
        region_map = {
            'fear': (50, 60),
            'joy': (60, 70),
            'curiosity': (70, 80),
            'anger': (80, 84)
        }
        
        if region not in region_map:
            return
        
        start, end = region_map[region]
        
        # Modulate thresholds
        for nid in range(start, end):
            if nid < len(snn_ctx.domain_ctx.neurons):
                neuron = snn_ctx.domain_ctx.neurons[nid]
                
                # Strength > 0: Giảm threshold (tăng attention)
                # Strength < 0: Tăng threshold (giảm attention)
                neuron.threshold -= strength * 0.2
                
                # Clamp
                neuron.threshold = np.clip(
                    neuron.threshold,
                    snn_ctx.global_ctx.threshold_min,
                    snn_ctx.global_ctx.threshold_max
                )
    
    # ===================================================================
    # SNN → RL: Intrinsic Reward (Novelty Signal)
    # ===================================================================
    
    @staticmethod
    @process(
        inputs=[
            'snn_ctx.domain_ctx.neurons',
            'snn_ctx.domain_ctx.metrics',
            'snn_ctx.domain_ctx.current_time'
        ],
        outputs=[
            'rl_ctx.domain_ctx.intrinsic_reward'
        ],
        side_effects=[]  # Pure function - read-only
    )
    def compute_intrinsic_reward(
        snn_ctx: SNNSystemContext,
        rl_ctx: SystemContext
    ):
        """
        Tính intrinsic reward từ SNN novelty.
        
        Novelty Detection: Dựa trên clustering similarity.
        
        NOTE: Pure function - chỉ đọc SNN state, ghi RL reward.
        
        Args:
            snn_ctx: SNN context
            rl_ctx: RL context
        """
        domain = snn_ctx.domain_ctx
        
        # Tính novelty từ clustering similarity
        similarities = []
        
        for neuron in domain.neurons:
            # Chỉ xét neurons vừa bắn
            if neuron.last_fire_time == domain.current_time:
                # Similarity giữa potential_vector và prototype
                pot_norm = np.linalg.norm(neuron.potential_vector)
                proto_norm = np.linalg.norm(neuron.prototype_vector)
                
                if pot_norm > 0 and proto_norm > 0:
                    sim = np.dot(
                        neuron.potential_vector,
                        neuron.prototype_vector
                    ) / (pot_norm * proto_norm)
                    similarities.append(sim)
        
        # Tính novelty
        if not similarities:
            novelty = 0.0
        else:
            avg_similarity = np.mean(similarities)
            # Novelty = 1 - similarity
            # High similarity → Low novelty
            # Low similarity → High novelty
            novelty = 1.0 - avg_similarity
        
        # Clip [0, 1]
        novelty = np.clip(novelty, 0.0, 1.0)
        
        # Update RL context
        rl_ctx.domain_ctx.intrinsic_reward = novelty
