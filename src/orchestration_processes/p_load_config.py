import json
import os
from src.experiment_context import OrchestrationContext, ExperimentDefinition, ExperimentRun
from typing import Dict, Any

def p_load_config(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để tải cấu hình thử nghiệm từ tệp JSON và khởi tạo OrchestrationContext.
    """
    print(f"  [Orchestration] Loading experiment configuration from {context.config_path}...")
    
    if not os.path.exists(context.config_path):
        print(f"LỖI: Không tìm thấy tệp cấu hình: {context.config_path}")
        context.final_report = f"LỖI: Không tìm thấy tệp cấu hình: {context.config_path}"
        return context # Dừng quy trình nếu không tìm thấy tệp

    with open(context.config_path, "r", encoding="utf-8") as f:
        raw_config = json.load(f)
    
    context.raw_config = raw_config
    context.global_output_dir = raw_config.get("output_dir", "results")

    # Tạo thư mục output chính nếu chưa có
    os.makedirs(context.global_output_dir, exist_ok=True)

    for exp_config in raw_config.get("experiments", []):
        exp_def = ExperimentDefinition(
            name=exp_config["name"],
            runs=exp_config["runs"],
            episodes_per_run=exp_config["episodes_per_run"],
            parameters=exp_config.get("parameters", {})
        )
        context.experiments.append(exp_def)
    
    print(f"  [Orchestration] Loaded {len(context.experiments)} experiments.")
    return context

# Helper function for recursive dict update, used by p_run_simulations
def recursive_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively update a dictionary."""
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d
