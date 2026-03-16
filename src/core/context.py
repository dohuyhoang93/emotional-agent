import torch
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field

# THEUS V2 SDK Migration
from theus.context import BaseGlobalContext, BaseDomainContext, BaseSystemContext

@dataclass
class GlobalContext(BaseGlobalContext):
    """
    Global Context: Chứa cấu hình tĩnh, hằng số, và tham số môi trường bất biến.
    Đây là dữ liệu READ-ONLY trong suốt vòng đời của Workflow.
    """
    
    # --- Experiment Settings ---
    initial_needs: List[float] = field(default_factory=list)
    initial_emotions: List[float] = field(default_factory=list)
    total_episodes: int = 1
    max_steps: int = 200
    seed: int = 42
    log_level: str = "info"

    # --- Hyperparameters ---
    initial_exploration_rate: float = 1.0
    exploration_decay: float = 0.995
    min_exploration: float = 0.05
    learning_rate: float = 0.1
    discount_factor: float = 0.95
    intrinsic_reward_weight: float = 0.1
    emotional_boost_factor: float = 0.5
    assimilation_rate: float = 0.1
    fatigue_growth_rate: float = 0.001
    short_term_memory_limit: int = 100
    
    # --- Feature Flags ---
    use_dynamic_curiosity: bool = False
    use_adaptive_fatigue: bool = False

    # --- Environment Config ---
    switch_locations: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    
    # --- Output Setting ---
    output_path: str = "results"
    
    # --- Persistence & Monitoring (Phase 15) ---
    enable_recorder: bool = False
    checkpoint_freq: int = 50
    
    # --- Model Configuration (Phase 2) ---
    # Centralized config for Model Params (Network dims, etc.)
    model_config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DomainContext(BaseDomainContext):
    """
    Domain Context: Chứa trạng thái nghiệp vụ của hệ thống (Agent State).
    Đây là dữ liệu MUTABLE, nhưng chỉ được thay đổi bởi Process thông qua Contract.
    """

    # --- Identification ---
    agent_id: int = 0
    env_adapter: Any = None # Added for Process access compatibility

    # --- GridWorld State ---
    position: List[int] = field(default_factory=lambda: [0, 0])
    has_key: bool = False
    is_at_goal: bool = False
    last_action: int = -1
    
    # --- Emotion ---
    emotion_state: Any = None # Numpy array (Legacy compat with RLAgent?)

    # --- Internal State (Vectors) ---
    N_vector: Optional[torch.Tensor] = None # Needs
    heavy_E_vector: Optional[torch.Tensor] = None # Emotions
    
    # --- SNN Integration (Phase 5) ---
    # [HEAVY ZONE] - Entire SNN subsystem is large, skip shadow copy
    heavy_snn_context: Any = None  # SNNSystemContext (nested context)
    heavy_snn_emotion_vector: Optional[torch.Tensor] = None  # Emotion từ SNN
    heavy_previous_snn_emotion_vector: Optional[torch.Tensor] = None # Emotion cũ (t-1)
    heavy_snn_state_vector: Optional[torch.Tensor] = None # SNN firing traces/state
    heavy_previous_snn_state_vector: Optional[torch.Tensor] = None # SNN firing traces cũ (t-1)
    intrinsic_reward: float = 0.0  # Novelty signal từ SNN
    
    # Property alias for backward compatibility
    @property
    def snn_context(self):
        return self.heavy_snn_context
    
    @snn_context.setter
    def snn_context(self, value):
        self.heavy_snn_context = value
    
    # --- Belief State ---
    believed_switch_states: Dict[str, bool] = field(default_factory=dict)
    
    # --- Knowledge (Memory & Models) ---
    # [HEAVY ZONE] Prefix 'heavy_' instructions Theus Engine to SKIP shadow copying (optimization).
    # This prevents MemoryError/QuotaPanic for large structures.
    
    # NOTE: heavy_q_table is DEPRECATED in V3 (Neural Brain). Use heavy_gated_network instead.
    heavy_q_table: Dict[str, List[float]] = field(default_factory=dict)
    short_term_memory: List[Any] = field(default_factory=list)
    long_term_memory: Dict[str, Any] = field(default_factory=dict)
    
    # --- ML Models (Mutable Objects) ---
    emotion_model: Any = None # Torch Model (Legacy)
    emotion_optimizer: Any = None # Torch Optimizer (Legacy)
    
    # --- Integration Models (Phase 2 Upgrade) ---
    heavy_gated_network: Any = None # GatedIntegrationNetwork
    heavy_gated_optimizer: Any = None # Optimizer for Gated Net
    heavy_last_q_values: Optional[torch.Tensor] = None # Last Q snapshot (Tensor)
    
    # --- Dynamic Parameters ---
    current_exploration_rate: float = 1.0
    base_exploration_rate: float = 1.0  # Decays over time
    
    # --- Ephemeral State (Per Cycle) ---
    current_observation: Any = None
    previous_observation: Any = None
    selected_action: Optional[str] = None
    last_reward: Dict[str, float] = field(default_factory=lambda: {'extrinsic': 0.0, 'intrinsic': 0.0})
    td_error: float = 0.0
    
    # --- Progression State ---
    current_episode: int = 0
    current_step: int = 0
    total_steps_in_episode: int = 0
    
    # Metric tracking
    metrics: Dict[str, Any] = field(default_factory=dict)
    last_cycle_time: float = 0.0
    
    # --- SNN Recorder (Phase 15 - POP Refactor) ---
    # [HEAVY ZONE] Buffer is large and shouldn't be deep copied per step
    heavy_recorder_buffer: List[Any] = field(default_factory=list)
    recorder_config: Optional[Dict[str, Any]] = None
    
    # Alias for backward compatibility (Process expects 'recorder_buffer')
    # property setter/getter? No, dataclass field best. 
    # Process uses domain_ctx.recorder_buffer. 
    # Theus checks "heavy_" prefix for avoiding copy. 
    # If we name it 'heavy_recorder_buffer', process MUST use that name. 
    # Let's map it:
    
    @property
    def recorder_buffer(self) -> List[Any]:
        return self.heavy_recorder_buffer
        
    @recorder_buffer.setter
    def recorder_buffer(self, value):
        self.heavy_recorder_buffer = value

@dataclass
class SystemContext(BaseSystemContext):
    """
    System Context: Wrapper quản lý toàn bộ hệ thống.
    """
    # Note: BaseSystemContext already defines global_ctx and domain_ctx as fields.
    # We re-declare them here with narrowed types if we want, OR just rely on instance passing.
    # Dataclasses don't strictly enforce type narrowing in __init__ unless user-defined.
    # BaseSystemContext has: global_ctx: BaseGlobalContext, domain_ctx: BaseDomainContext
    
    # Casting for intellisense
    global_ctx: Optional[GlobalContext] = None
    domain_ctx: Optional[DomainContext] = None
    
    # System Runtime State (not domain logic)
    cycle_count: int = 0
    is_running: bool = True

