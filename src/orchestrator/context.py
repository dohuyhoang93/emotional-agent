from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd
from theus import BaseGlobalContext, BaseDomainContext, BaseSystemContext

@dataclass
class ExperimentRun:
    """Lưu trữ thông tin về một lần chạy mô phỏng duy nhất."""
    run_id: int
    seed: int
    parameters: Dict[str, Any]
    output_csv_path: str = ""
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    result_data: pd.DataFrame = field(default_factory=pd.DataFrame)

@dataclass
class ExperimentDefinition:
    """Lưu trữ cấu hình cho một thử nghiệm, bao gồm nhiều lần chạy."""
    name: str
    runs: int
    episodes_per_run: int
    parameters: Dict[str, Any]
    list_of_runs: List[ExperimentRun] = field(default_factory=list)
    aggregated_data: pd.DataFrame = field(default_factory=pd.DataFrame)
    log_level: str = "info"

@dataclass
class OrchestratorGlobalContext(BaseGlobalContext):
    """
    Global Context cho lớp Orchestration.
    Chứa các tham số đầu vào từ CLI (Immutable).
    """
    config_path: str
    cli_log_level: Optional[str] = None
    settings_override: Optional[str] = None

@dataclass
class OrchestratorDomainContext(BaseDomainContext):
    """
    Domain Context cho lớp Orchestration.
    Chứa trạng thái tiến trình chạy thử nghiệm (Mutable).
    """
    # Config loaded from file
    raw_config: Dict[str, Any] = field(default_factory=dict)
    output_dir: str = "results"
    
    # State
    experiments: List[ExperimentDefinition] = field(default_factory=list)
    active_experiment_idx: int = 0
    
    # Results
    analysis_summary: Dict[str, str] = field(default_factory=dict)
    final_report: str = ""
    
    # Runtime
    effective_log_level: str = "info"
    event_bus: Optional[Any] = None  # Reference to SignalBus

@dataclass
class OrchestratorSystemContext(BaseSystemContext):
    """
    Wrapper System Context cho lớp Orchestration.
    """
    global_ctx: OrchestratorGlobalContext
    domain_ctx: OrchestratorDomainContext
    
    @property
    def log_level(self) -> str:
        return self.domain_ctx.effective_log_level
        
    @log_level.setter
    def log_level(self, value: str):
        self.domain_ctx.effective_log_level = value
