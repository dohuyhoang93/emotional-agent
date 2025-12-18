import torch
from typing import Dict, List, Tuple, Any, Optional
import sys
import os
from dataclasses import dataclass, field

# THEUS V2 SDK Migration
from theus import BaseGlobalContext, BaseDomainContext, BaseSystemContext

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

@dataclass
class DomainContext(BaseDomainContext):
    """
    Domain Context: Chứa trạng thái nghiệp vụ của hệ thống (Agent State).
    Đây là dữ liệu MUTABLE, nhưng chỉ được thay đổi bởi Process thông qua Contract.
    """

    # --- Internal State (Vectors) ---
    N_vector: Optional[torch.Tensor] = None # Needs
    E_vector: Optional[torch.Tensor] = None # Emotions
    
    # --- Belief State ---
    believed_switch_states: Dict[str, bool] = field(default_factory=dict)
    
    # --- Knowledge (Memory & Models) ---
    q_table: Dict[str, List[float]] = field(default_factory=dict)
    short_term_memory: List[Any] = field(default_factory=list)
    long_term_memory: Dict[str, Any] = field(default_factory=dict)
    
    # --- ML Models (Mutable Objects) ---
    emotion_model: Any = None # Torch Model
    emotion_optimizer: Any = None # Torch Optimizer
    
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
    last_cycle_time: float = 0.0

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
    global_ctx: GlobalContext
    domain_ctx: DomainContext
    
    # System Runtime State (not domain logic)
    cycle_count: int = 0
    is_running: bool = True

