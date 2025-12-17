import torch
from typing import Dict, List, Tuple, Any, Optional
import sys
import os
from pydantic import BaseModel, ConfigDict, Field

# Import from Independent SDK
# Add SDK path to sys.path to ensure it can be imported
sdk_path = os.path.join(os.getcwd(), 'python_pop_sdk')
if sdk_path not in sys.path:
    sys.path.append(sdk_path)

# from pop import BaseGlobalContext, BaseDomainContext, BaseSystemContext 
# Note: Dropping inheritance from SDK Base Contexts to avoid Metaclass conflicts with Pydantic.
# We implement the schema structure directly.

class GlobalContext(BaseModel):
    """
    Global Context: Chứa cấu hình tĩnh, hằng số, và tham số môi trường bất biến.
    Đây là dữ liệu READ-ONLY trong suốt vòng đời của Workflow.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # --- Experiment Settings ---
    initial_needs: List[float]
    initial_emotions: List[float]
    total_episodes: int
    max_steps: int
    seed: int
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
    switch_locations: Dict[str, Tuple[int, int]] = Field(default_factory=dict)
    
    # --- Output Setting ---
    output_path: str = "results"

class DomainContext(BaseModel):
    """
    Domain Context: Chứa trạng thái nghiệp vụ của hệ thống (Agent State).
    Đây là dữ liệu MUTABLE, nhưng chỉ được thay đổi bởi Process thông qua Contract.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # --- Internal State (Vectors) ---
    N_vector: torch.Tensor  # Needs
    E_vector: torch.Tensor  # Emotions
    # Confidence is derived from E_vector usually, but if tracked separately:
    # We keep strict data. If confidence is E_vector[0], logic should assume that.
    
    # --- Belief State ---
    believed_switch_states: Dict[str, bool]
    
    # --- Knowledge (Memory & Models) ---
    q_table: Dict[str, List[float]] # State -> Q-values
    short_term_memory: List[Any]
    long_term_memory: Dict[str, Any]
    
    # --- ML Models (Mutable Objects) ---
    emotion_model: Any = None # Torch Model
    emotion_optimizer: Any = None # Torch Optimizer
    
    # --- Dynamic Parameters ---
    current_exploration_rate: float = 1.0
    base_exploration_rate: float = 1.0  # Decays over time
    
    # --- Ephemeral State (Per Cycle) ---
    current_observation: Any = None
    previous_observation: Any = None
    selected_action: Optional[str] = None # Changed from last_action_id for compatibility
    last_reward: Dict[str, float] = Field(default_factory=lambda: {'extrinsic': 0.0, 'intrinsic': 0.0})
    td_error: float = 0.0
    
    # --- Progression State ---
    current_episode: int = 0
    current_step: int = 0
    total_steps_in_episode: int = 0
    
    # Metric tracking
    last_cycle_time: float = 0.0

class SystemContext(BaseModel):
    """
    System Context: Wrapper quản lý toàn bộ hệ thống.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    global_ctx: GlobalContext
    domain_ctx: DomainContext
    
    # System Runtime State (not domain logic)
    cycle_count: int = 0
    is_running: bool = True
    
    # Mocking lock manager for compatibility if Engine tries to set it
    # We can just ignore it or store it privately
    _lock_manager: Any = None
    
    def set_lock_manager(self, manager):
        self._lock_manager = manager
