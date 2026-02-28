"""
SNN Context for Theus Framework
================================
Thiết kế Context cho SNN subsystem theo Theus architecture.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from theus.context import BaseGlobalContext, BaseDomainContext, BaseSystemContext


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
    initial_threshold: float = 0.6 # Lowered from 1.0 to increase activity
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
    target_fire_rate: float = 0.02  # 2%
    homeostasis_rate: float = 0.0001
    local_homeostasis_rate: float = 0.0005 # Faster local adaptation
    trace_decay: float = 0.999 # Slow decay for stable local average
    
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
    dream_noise_level: float = 0.1 # Noise level during dream
    
    # === Social Learning ===
    use_social_learning: bool = False  # Multi-agent only
    viral_top_k: int = 5
    shadow_confidence_threshold: float = 0.2
    # Added during Config Audit 2026-01-12
    social_elite_ratio: float = 0.2
    social_learner_ratio: float = 0.5
    social_synapses_per_transfer: int = 10
    
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
    revolution_window: int = 100  # Check every 100 episodes, cooldown period
    top_elite_percent: float = 0.1  # Top 10%
    current_episode: int = 0  # For cooldown tracking
    
    # === Bridge Configuration (SNN <-> RL) ===
    input_amplification_factor: float = 5.0 # Boost sensor [0,1] to potential
    modulation_excitation: float = 0.9      # Threshold multiplier (Focus)
    modulation_inhibition: float = 1.2      # Threshold multiplier (Ignore)
    restoration_rate: float = 0.05          # Elastic return to baseline
    
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
    
    # Phase 10.5: Derived Commitment
    solidity_ratio: float = 0.0  # 0.0 (Fluid) -> 1.0 (Solid)


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
    # [HEAVY ZONE] - Skip shadow copy (large object lists)
    heavy_neurons: List[NeuronState] = field(default_factory=list)
    heavy_synapses: List[SynapseState] = field(default_factory=list)
    
    # Property aliases for backward compatibility
    @property
    def neurons(self) -> List[NeuronState]:
        return self.heavy_neurons
    
    @neurons.setter
    def neurons(self, value):
        self.heavy_neurons = value
    
    @property
    def synapses(self) -> List[SynapseState]:
        return self.heavy_synapses
    
    @synapses.setter
    def synapses(self, value):
        self.heavy_synapses = value
    
    # === Temporal State ===
    current_time: int = 0
    spike_queue: Dict[int, List[int]] = field(default_factory=dict)
    
    # === PID State (Meta-Homeostasis) ===
    pid_state: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'threshold': {'error_integral': 0.0, 'error_prev': 0.0},
        'learning_rate': {'error_integral': 0.0, 'error_prev': 0.0}
    })
    
    # ===== Emotion Vectors (SNN-RL Bridge) =====
    heavy_snn_emotion_vector: Optional[torch.Tensor] = None  # Current emotion from SNN
    heavy_previous_snn_emotion_vector: Optional[torch.Tensor] = None  # Previous emotion (t-1)
    
    # ===== Metrics & Monitoring =====
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
    last_revolution_episode: int = -1000  # Cooldown tracker
    ancestor_baseline_reward: float = 0.0 # Baseline for Revolution (Reward vs Reward)
    
    # === FIX: Episode Tracking for Commitment ===
    # NOTE: Counter overflow fix - only update consecutive_correct/wrong once per episode
    last_commitment_update_episode: int = -1
    
    # === Optimization: Shadow Tensors (Phase 2) ===
    # Holds numpy arrays for vectorized computation:
    # - potentials: (N,)
    # - thresholds: (N,)
    # - weights: (N, N) - Connectivity matrix (0.0 if incomplete)
    # - prototypes: (N, D) - For vector matching
    # [HEAVY ZONE] - Skip shadow copy
    heavy_tensors: Dict[str, np.ndarray] = field(default_factory=dict)

    # === Phase 11: Robust Control (Safety) ===
    # Stores the current state of defense mechanisms
    safety_state: Dict[str, Any] = field(default_factory=lambda: {
        'emergency_override_steps': 0,  # If > 0, modulation is blocked
        'veto_active': False,           # Curiosity Veto
        'saccade_triggered': False,     # Context switch detected
        'last_action': -1               # Track for Saccade detection
    })


# ============================================================================
# System Context (Wrapper)
# ============================================================================

@dataclass
class SNNSystemContext(BaseSystemContext):
    """
    SNN System Context: Wrapper quản lý toàn bộ SNN.
    
    Kế thừa từ BaseSystemContext để tương thích với Theus Engine.
    """
    global_ctx: Optional[SNNGlobalContext] = None
    domain_ctx: Optional[SNNDomainContext] = None
    
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
            threshold=global_ctx.initial_threshold * np.random.uniform(0.95, 1.05),  # Birth variance
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


# ============================================================================
# Vectorization Helpers (Compute-Sync Strategy)
# ============================================================================

def ensure_heavy_tensors_initialized(ctx: SNNSystemContext):
    """
    Ensure shadow heavy_tensors exist and match object state.
    Call this at the start of Vectorized Process blocks.
    
    Creates:
    - potentials: (N,)
    - thresholds: (N,)
    - weights: (N, N)
    - prototypes: (N, D)
    """
    domain = ctx.domain_ctx
    neurons = domain.neurons
    N = len(neurons)
    
    # Initialize if missing or size mismatch
    if 'potentials' not in domain.heavy_tensors or domain.heavy_tensors['potentials'].shape[0] != N:
        # Potentials & Thresholds
        def _sf(x):
            try: return float(x)
            except: return 0.0
            
        domain.heavy_tensors['potentials'] = np.array([_sf(n.potential) for n in neurons], dtype=np.float32)
        domain.heavy_tensors['thresholds'] = np.array([_sf(n.threshold) for n in neurons], dtype=np.float32)
        
        # Last Fire Times (for Refractory)
        domain.heavy_tensors['last_fire_times'] = np.array([n.last_fire_time for n in neurons], dtype=np.int32)
        
        # Prototypes (N, D)
        D = neurons[0].vector_dim if N > 0 else 16
        prototypes = np.zeros((N, D), dtype=np.float32)
        for i, n in enumerate(neurons):
            prototypes[i] = n.prototype_vector
        domain.heavy_tensors['prototypes'] = prototypes
        
        # Potential Vectors (N, D) - Mutable State!
        pot_vecs = np.zeros((N, D), dtype=np.float32)
        for i, n in enumerate(neurons):
            pot_vecs[i] = n.potential_vector
        domain.heavy_tensors['potential_vectors'] = pot_vecs
        
        # Weights (N, N)
        # We assume sparse connectivity mapped to dense matrix for fast multiply
        # If N is large (>1000), sparse matrix is better. Here N=50-100.
        weights = np.zeros((N, N), dtype=np.float32)
        for s in domain.synapses:
            if s.pre_neuron_id < N and s.post_neuron_id < N:
                weights[s.pre_neuron_id, s.post_neuron_id] = s.weight
        domain.heavy_tensors['weights'] = weights
    
    # If heavy_tensors exist, we assume they are stale if we came from Object-logic land?
    # NO. The "Sync" strategy assumes Tensors are valid ONLY during compute burst.
    # But initialization should happen.
    # For robust Compute-Sync: Always overwrite Tensors from Objects OR 
    # keep them in sync.
    # "Load" step says: Sync Objects -> Tensors.
    
    # NEW: Add STDP traces tensor
    if 'traces' not in domain.heavy_tensors:
        domain.heavy_tensors['traces'] = np.zeros((N, N), dtype=np.float32)
        # Sync from synapses
        for syn in domain.synapses:
            if syn.pre_neuron_id < N and syn.post_neuron_id < N:
                domain.heavy_tensors['traces'][syn.pre_neuron_id, syn.post_neuron_id] = syn.trace
    
    # NEW: Add fitness tensor (for Neural Darwinism)
    if 'fitnesses' not in domain.heavy_tensors:
        domain.heavy_tensors['fitnesses'] = np.zeros((N, N), dtype=np.float32)
        for syn in domain.synapses:
            if syn.pre_neuron_id < N and syn.post_neuron_id < N:
                domain.heavy_tensors['fitnesses'][syn.pre_neuron_id, syn.post_neuron_id] = syn.fitness

    # NEW (Phase 7): Commitment Tensors
    if 'commit_states' not in domain.heavy_tensors:
        domain.heavy_tensors['commit_states'] = np.zeros((N, N), dtype=np.int8)
        domain.heavy_tensors['consecutive_correct'] = np.zeros((N, N), dtype=np.int16)
        domain.heavy_tensors['consecutive_wrong'] = np.zeros((N, N), dtype=np.int16)
        
        for syn in domain.synapses:
            if syn.pre_neuron_id < N and syn.post_neuron_id < N:
                domain.heavy_tensors['commit_states'][syn.pre_neuron_id, syn.post_neuron_id] = syn.commit_state
                domain.heavy_tensors['consecutive_correct'][syn.pre_neuron_id, syn.post_neuron_id] = syn.consecutive_correct
                domain.heavy_tensors['consecutive_correct'][syn.pre_neuron_id, syn.post_neuron_id] = syn.consecutive_correct
                domain.heavy_tensors['consecutive_wrong'][syn.pre_neuron_id, syn.post_neuron_id] = syn.consecutive_wrong

    # Phase 3: Vectorized Spike Buffer
    # Shape: (Buffer_Size, Num_Neurons)
    # Default buffer size 10ms is sufficient for most delays
    buffer_size = 10
    if 'spike_buffer' not in domain.heavy_tensors:
        domain.heavy_tensors['spike_buffer'] = np.zeros((buffer_size, N), dtype=np.int8)
        domain.heavy_tensors['use_vectorized_queue'] = True  # Flag to switch logic

    # NEW (Harmonic Homeostasis): Firing Traces
    if 'firing_traces' not in domain.heavy_tensors:
         domain.heavy_tensors['firing_traces'] = np.zeros(N, dtype=np.float32)

    # NEW (Phase 10.5): Derived Neuron Commitment
    if 'solidity_ratios' not in domain.heavy_tensors:
         domain.heavy_tensors['solidity_ratios'] = np.array([n.solidity_ratio for n in neurons], dtype=np.float32)

    # FULL SYNC (Objects -> Tensors)
    sync_to_heavy_tensors(ctx)

def sync_to_heavy_tensors(ctx: SNNSystemContext):
    """
    Sync Objects (Source of Truth) -> Tensors (Cache).
    """
    domain = ctx.domain_ctx
    neurons = domain.neurons
    N = len(neurons)
    if N == 0: return

    # 1. Potentials & Last Fire Times & Thresholds (Vectorized Sync)
    # Optimized: Use list comprehension is faster than direct loop for small objects
    domain.heavy_tensors['potentials'] = np.array([n.potential for n in neurons], dtype=np.float32)
    domain.heavy_tensors['last_fire_times'] = np.array([n.last_fire_time for n in neurons], dtype=np.int32)
    domain.heavy_tensors['thresholds'] = np.array([n.threshold for n in neurons], dtype=np.float32)
    
    # 2. Weights (Expensive! Only sync if missing to avoid O(S) loop)
    # We assume weights are primarily updated via Tensors (STDP) or valid if present.
    if 'weights' not in domain.heavy_tensors:
        weights = np.zeros((N, N), dtype=np.float32)
        for s in domain.synapses:
             if s.pre_neuron_id < N and s.post_neuron_id < N:
                  weights[s.pre_neuron_id, s.post_neuron_id] = s.weight
        domain.heavy_tensors['weights'] = weights
    
    # 3. Prototypes & Potential Vectors
    domain.heavy_tensors['prototypes'] = np.array([n.prototype_vector for n in neurons], dtype=np.float32)
    domain.heavy_tensors['potential_vectors'] = np.array([n.potential_vector for n in neurons], dtype=np.float32)
    domain.heavy_tensors['solidity_ratios'] = np.array([n.solidity_ratio for n in neurons], dtype=np.float32)

    # 4. Traces & Fitness (Avoid allocations if possible)
    # Check if heavy_tensors exist, otherwise create them. 
    # NOTE: Re-creating from scratch is O(S), ideally we assume heavy_tensors are authoritative during RUN.
    # But if objects are authoritative (e.g. after Load), we need to sync.
    # For now, we only sync if missing or explicitly triggered (this function is called explicitly).
    if 'traces' not in domain.heavy_tensors: 
        ensure_heavy_tensors_initialized(ctx) # Logic matches ensure_heavy_tensors
    else:
        # If heavy_tensors exist, we do NOT perform full sync from objects every step.
        # This function is meant for "Force Sync" or "Initialization".
        # During runtime loop, we trust heavy_tensors.
        pass

    # 5. Connectome Metadata (Phase 7)
    # Similar to weights, usually static structure unless Darwinism runs.


def sync_from_heavy_tensors(ctx: SNNSystemContext):
    """
    Sync Tensors (Cache) -> Objects (Source of Truth).
    Call this AFTER vectorized computation.
    """
    domain = ctx.domain_ctx
    if 'potentials' not in domain.heavy_tensors:
        return
        
    pots = domain.heavy_tensors['potentials']
    lfts = domain.heavy_tensors.get('last_fire_times', [])
    pvecs = domain.heavy_tensors.get('potential_vectors', [])
    pvecs = domain.heavy_tensors.get('potential_vectors', [])
    thresholds = domain.heavy_tensors.get('thresholds', [])
    solidity_ratios = domain.heavy_tensors.get('solidity_ratios', [])
    
    check_lft = len(lfts) > 0
    check_pvec = len(pvecs) > 0
    check_thresh = len(thresholds) > 0
    check_solidity = len(solidity_ratios) > 0
    
    # 1. Sync State Variables
    for i, neuron in enumerate(domain.neurons):
        # Update Potential
        neuron.potential = float(pots[i])
        
        # Update Last Fire Time
        if check_lft:
            neuron.last_fire_time = int(lfts[i])
            
        # Update Potential Vector
        if check_pvec:
             # COPY values, don't just assign reference if pvecs[i] is a view
             neuron.potential_vector[:] = pvecs[i]

        # Update Thresholds (Phase 7: Homeostasis/Hysteria)
        if check_thresh:
            neuron.threshold = float(thresholds[i])
            
        # Update Solidity Ratio (Phase 10.5)
        if check_solidity:
             neuron.solidity_ratio = float(solidity_ratios[i])
        
    # NOTE: We do NOT sync weights back yet because Vectorized STDP is not implemented.
    # If we vectorized STDP, we would sync weights back to domain.synapses.
    
    # NEW: Sync Traces & Fitness & Commitment Back (Partial Sync if they exist)
    if 'commit_states' in domain.heavy_tensors:
         traces = domain.heavy_tensors.get('traces')
         fitnesses = domain.heavy_tensors.get('fitnesses')
         
         # Commitment Tensors
         commit_states = domain.heavy_tensors.get('commit_states')
         consecutive_correct = domain.heavy_tensors.get('consecutive_correct')
         consecutive_wrong = domain.heavy_tensors.get('consecutive_wrong')
         
         N = len(domain.neurons)
         
         for synapse in domain.synapses:
             if synapse.pre_neuron_id < N and synapse.post_neuron_id < N:
                 u, v = synapse.pre_neuron_id, synapse.post_neuron_id
                 
                 if traces is not None:
                     synapse.trace = float(traces[u, v])
                 if fitnesses is not None:
                     synapse.fitness = float(fitnesses[u, v])
                     
                 if commit_states is not None:
                     synapse.commit_state = int(commit_states[u, v])
                     synapse.consecutive_correct = int(consecutive_correct[u, v])
                     synapse.consecutive_wrong = int(consecutive_wrong[u, v])


# ============================================================================
# Backward Compatibility Aliases
# ============================================================================

# Legacy name used in older tests
ensure_tensors_initialized = ensure_heavy_tensors_initialized
sync_from_tensors = sync_from_heavy_tensors
