from dataclasses import dataclass, field
from typing import List, Dict, Any
import pandas as pd

@dataclass
class ExperimentRun:
    """Lưu trữ thông tin về một lần chạy mô phỏng duy nhất."""
    run_id: int
    seed: int
    parameters: Dict[str, Any]
    output_csv_path: str = ""
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    result_data: pd.DataFrame = field(default_factory=pd.DataFrame) # Để lưu dữ liệu thô của lần chạy

@dataclass
class ExperimentDefinition:
    """Lưu trữ cấu hình cho một thử nghiệm, bao gồm nhiều lần chạy."""
    name: str
    runs: int
    episodes_per_run: int
    parameters: Dict[str, Any]
    list_of_runs: List[ExperimentRun] = field(default_factory=list)
    aggregated_data: pd.DataFrame = field(default_factory=pd.DataFrame) # Để lưu dữ liệu tổng hợp của tất cả các lần chạy
    log_level: str = "info" # Cấp độ ghi log cho thử nghiệm này

@dataclass
class OrchestrationContext:
    """
    Đối tượng dữ liệu trung tâm cho quy trình dàn dựng thử nghiệm.
    Nó chứa toàn bộ trạng thái của quá trình, từ cấu hình ban đầu đến kết quả cuối cùng.
    """
    # --- Dữ liệu đầu vào và cấu hình ---
    config_path: str = "experiments.json"
    raw_config: Dict[str, Any] = field(default_factory=dict)
    global_output_dir: str = "results"
    log_level: str = "info" # Cấp độ ghi log mặc định cho toàn bộ quá trình điều phối
    
    # --- Dữ liệu xử lý ---
    experiments: List[ExperimentDefinition] = field(default_factory=list)
    
    # --- Dữ liệu đầu ra ---
    analysis_summary: Dict[str, str] = field(default_factory=dict)
    final_report: str = ""
