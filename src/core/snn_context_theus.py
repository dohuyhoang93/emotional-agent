"""
SNN Context for Theus Framework
================================
Thiết kế Context cho SNN subsystem theo Theus architecture.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any
from theus import BaseGlobalContext, BaseDomainContext, BaseSystemContext


# ============================================================================
# Commitment States (Phase 7)
# ============================================================================

COMMIT_STATE_FLUID = 0    # Learning freely
COMMIT_STATE_SOLID = 1    # Protected (slow learning)
COMMIT_STATE_REVOKED = 2  # Marked for deletion


# ============================================================================
# Global Context (Hyperparameters - READ-ONLY)
# ============================================================================

@dataclass
class SNNGlobalContext(BaseGlobalContext):
    """
    SNN Global Context: Hyperparameters và cấu hình tĩnh.
    
    READ-ONLY trong suốt experiment.
    Chứa tất cả hyperparameters cho SNN.
    """
    
    # === Network Architecture ===
    num_neurons: int = 100
    connectivity: float = 0.15  # 15% synapses
    vector_dim: int = 16
    
    # === Neuron Parameters ===
    tau_decay: float = 0.9  # Leaky decay (90% retention per step)
    refractory_period: int = 5  # ms
    initial_threshold: float = 1.0
    threshold_min: float = 0.3
    threshold_max: float = 3.0
    
    # === Learning Parameters ===
    learning_rate: float = 0.01
    clustering_rate: float = 0.001
    tau_trace: float = 0.9  # STDP trace decay (legacy 2-factor)
    weight_decay: float = 0.9999  # 0.01% decay per step
    
    # === Synaptic Tagging (Phase 6) ===
    use_synaptic_tagging: bool = True
    tau_trace_fast: float = 0.9      # Fast trace decay ~20ms
    tau_trace_slow: float = 0.9998   # Slow trace decay ~5000ms
    dopamine_learning_rate: float = 0.01  # Dopamine modulation strength
    
    # === Commitment Layer (Phase 7) ===
    use_commitment_layer: bool = True
    commitment_threshold: int = 10      # Correct streak to solidify
    revoke_threshold: int = 5           # Wrong streak to revoke
    prediction_error_threshold: float = 0.1  # Error tolerance
    solid_learning_rate_factor: float = 0.1  # 90% reduction for SOLID
    
    # === Homeostasis Parameters ===
    target_fire_rate: float = 0.02  # 2%
    homeostasis_rate: float = 0.0001
    
    # === Meta-Homeostasis (PID) ===
    # === Meta-Homeostasis (PID) ===
    use_meta_homeostasis: bool = True
    pid_kp: float = 0.001
    pid_ki: float = 0.0001
    pid_kd: float = 0.0005
    pid_max_integral: float = 5.0
    pid_max_output: float = 0.01
    pid_scale_factor: float = 0.0001
    
    # === Imagination Parameters ===
    use_imagination: bool = True
    imagination_interval: int = 500  # ms
    nightmare_threshold: float = 0.05  # Fire rate threshold
    
    # === Social Learning ===
    use_social_learning: bool = False  # Multi-agent only
    viral_top_k: int = 5
    shadow_confidence_threshold: float = 0.2
    
    # === Social Quarantine (Phase 8) ===
    use_social_quarantine: bool = True
    quarantine_duration: int = 100  # Steps in quarantine
    validation_threshold: float = 0.7  # Min score to promote
    max_influence_percent: float = 0.1  # Max 10% influence during quarantine
    
    # === Hysteria Dampener (Phase 9) ===
    use_hysteria_dampener: bool = True
    saturation_threshold: float = 0.9  # 90% neurons firing
    dampening_factor: float = 0.5  # 50% threshold increase
    recovery_rate: float = 0.01
    
    # === Lateral Inhibition (Phase 10) ===
    use_lateral_inhibition: bool = True
    inhibition_strength: float = 0.2
    wta_k: int = 5  # Top-k winners
    
    # === Neural Darwinism (Phase 11) ===
    use_neural_darwinism: bool = True
    selection_pressure: float = 0.1  # 10% die
    reproduction_rate: float = 0.05  # 5% reproduce
    fitness_decay: float = 0.99
    darwinism_interval: int = 100 # Run every 100 steps
    
    # === Revolution Protocol (Phase 12) ===
    use_revolution_protocol: bool = False  # Multi-agent only
    revolution_threshold: float = 0.6  # 60% outperform
    revolution_window: int = 1000
    top_elite_percent: float = 0.1  # Top 10%
    
    # === Experiment Settings ===
    seed: int = 42
    output_path: str = "results/snn"


# ============================================================================
# Domain Context (State - MUTABLE)
# ============================================================================

@dataclass
class NeuronState:
    """
    Neuron state (ECS-style, wrapped cho Theus).
    
    NOTE: Theus sẽ track changes vào neurons qua Delta Architecture.
    """
    neuron_id: int
    
    # Neuron state
    potential: float = 0.0
    threshold: float = 1.0
    last_fire_time: int = -1000
    fire_count: int = 0
    
    # Vector state (16-dim)
    potential_vector: np.ndarray = field(default_factory=lambda: np.zeros(16))
    prototype_vector: np.ndarray = field(default_factory=lambda: np.random.randn(16))
    
    # Lateral Inhibition (Phase 10)
    inhibition_received: float = 0.0
    
    # Metadata
    vector_dim: int = 16


@dataclass
class SynapseState:
    """
    Synapse state (ECS-style).
    """
    synapse_id: int
    pre_neuron_id: int
    post_neuron_id: int
    
    # Weights & Traces
    weight: float = 0.5
    trace: float = 0.0  # Legacy (2-factor STDP)
    delay: int = 1
    
    # Multi-timescale Traces (Phase 6: Synaptic Tagging)
    trace_fast: float = 0.0   # Decay ~20ms (tau=0.9)
    trace_slow: float = 0.0   # Decay ~5000ms (tau=0.9998)
    last_active_time: int = 0
    eligibility: float = 0.0  # trace_fast + trace_slow (for 3-factor learning)
    
    # Commitment Layer (Phase 7)
    commit_state: int = 0  # COMMIT_STATE_FLUID by default
    consecutive_correct: int = 0
    consecutive_wrong: int = 0
    
    # Social Quarantine (Phase 8)
    quarantine_time: int = 0  # Steps in quarantine
    validation_score: float = 0.0  # Performance score
    is_blacklisted: bool = False
    
    # Neural Darwinism (Phase 11)
    fitness: float = 0.5
    generation: int = 0
    
    # Social Learning (Phase 3)
    synapse_type: str = "native"  # "native" or "shadow"
    source_agent_id: int = -1
    confidence: float = 0.5
    prediction_error_accum: float = 0.0


@dataclass
class SNNDomainContext(BaseDomainContext):
    """
    SNN Domain Context: Trạng thái mạng SNN.
    
    MUTABLE - chỉ được thay đổi qua @process với contracts.
    Theus sẽ audit mọi thay đổi vào context này.
    """
    
    # === Identity ===
    agent_id: int = 0
    
    # === Network State (ECS Arrays) ===
    # NOTE: Theus sẽ track changes vào arrays này
    neurons: List[NeuronState] = field(default_factory=list)
    synapses: List[SynapseState] = field(default_factory=list)
    
    # === Temporal State ===
    current_time: int = 0
    spike_queue: Dict[int, List[int]] = field(default_factory=dict)
    
    # === PID State (Meta-Homeostasis) ===
    pid_state: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'threshold': {'error_integral': 0.0, 'error_prev': 0.0},
        'learning_rate': {'error_integral': 0.0, 'error_prev': 0.0}
    })
    
    # === Metrics (Ephemeral - per timestep) ===
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # === Imagination State ===
    last_imagination_time: int = 0
    nightmare_count: int = 0
    fantasy_count: int = 0
    
    # === Social Learning ===
    viral_synapses_received: int = 0
    shadow_synapses: List[SynapseState] = field(default_factory=list)
    
    # === Social Quarantine (Phase 8) ===
    blacklisted_sources: List[int] = field(default_factory=list)  # Agent IDs
    
    # === Hysteria Dampener (Phase 9) ===
    emotion_saturation_level: float = 0.0
    dampening_active: bool = False
    
    # === Revolution Protocol (Phase 12) ===
    ancestor_weights: Dict[int, float] = field(default_factory=dict)
    population_performance: List[float] = field(default_factory=list)
    revolution_triggered: bool = False


# ============================================================================
# System Context (Wrapper)
# ============================================================================

@dataclass
class SNNSystemContext(BaseSystemContext):
    """
    SNN System Context: Wrapper quản lý toàn bộ SNN.
    
    Kế thừa từ BaseSystemContext để tương thích với Theus Engine.
    """
    global_ctx: SNNGlobalContext
    domain_ctx: SNNDomainContext
    
    # System Runtime State
    cycle_count: int = 0
    is_running: bool = True


# ============================================================================
# Helper Functions
# ============================================================================

def create_snn_context_theus(
    num_neurons: int = 100,
    connectivity: float = 0.15,
    **kwargs
) -> SNNSystemContext:
    """
    Factory function để tạo SNN context với Theus.
    
    Args:
        num_neurons: Số lượng neurons
        connectivity: Tỷ lệ kết nối (0-1)
        **kwargs: Override global context params
    
    Returns:
        SNNSystemContext đã được khởi tạo
    """
    # Tạo Global Context
    global_params = {
        'num_neurons': num_neurons,
        'connectivity': connectivity,
        **kwargs
    }
    global_ctx = SNNGlobalContext(**global_params)
    
    # Tạo Domain Context
    domain_ctx = SNNDomainContext()
    
    # Khởi tạo neurons
    for i in range(num_neurons):
        # Normalize prototype vector
        prototype = np.random.randn(global_ctx.vector_dim)
        prototype = prototype / (np.linalg.norm(prototype) + 1e-8)
        
        neuron = NeuronState(
            neuron_id=i,
            threshold=global_ctx.initial_threshold,
            prototype_vector=prototype,
            vector_dim=global_ctx.vector_dim
        )
        domain_ctx.neurons.append(neuron)
    
    # Khởi tạo synapses (random connectivity)
    np.random.seed(global_ctx.seed)
    synapse_id = 0
    
    for pre_id in range(num_neurons):
        for post_id in range(num_neurons):
            if pre_id == post_id:
                continue
            
            if np.random.random() < connectivity:
                synapse = SynapseState(
                    synapse_id=synapse_id,
                    pre_neuron_id=pre_id,
                    post_neuron_id=post_id,
                    weight=np.random.uniform(0.3, 0.7)
                )
                domain_ctx.synapses.append(synapse)
                synapse_id += 1
    
    # Tạo System Context
    sys_ctx = SNNSystemContext(
        global_ctx=global_ctx,
        domain_ctx=domain_ctx
    )
    
    return sys_ctx
