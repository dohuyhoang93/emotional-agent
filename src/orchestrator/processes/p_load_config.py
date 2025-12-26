import json
import os
from typing import Dict, Any

from theus import process
from src.orchestrator.context import OrchestratorSystemContext, ExperimentDefinition
from src.logger import log, log_error

def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

@process(
    inputs=['global.config_path', 'log_level', 'system.log_level', 'global.cli_log_level', 'global.settings_override', 'domain.output_dir', 'domain.experiments', 'domain.effective_log_level'],
    outputs=[
        'domain.raw_config',
        'domain.output_dir',
        'domain.effective_log_level',
        'domain.experiments',
        'domain.final_report'
    ],
    side_effects=['filesystem.read', 'filesystem.mkdir'],
    errors=['config_not_found']
)
def load_config(ctx: OrchestratorSystemContext):
    """
    Process: Tải cấu hình thử nghiệm từ tệp JSON.
    """
    config_path = ctx.global_ctx.config_path
    log(ctx, "info", f"  [Orchestration] Loading experiment configuration from {config_path}...")
    
    if not os.path.exists(config_path):
        error_msg = f"Không tìm thấy tệp cấu hình: {config_path}"
        log_error(ctx, error_msg)
        ctx.domain_ctx.final_report = f"LỖI: {error_msg}"
        return # Contract says we must returnCtx? Implicitly returns None which Engine ignores? No, engine returns ctx.
        # But we modify ctx in place.
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = json.load(f)
    except Exception as e:
        error_msg = f"Lỗi đọc JSON: {e}"
        log_error(ctx, error_msg)
        ctx.domain_ctx.final_report = f"LỖI: {error_msg}"
        return

    domain = ctx.domain_ctx
    domain.raw_config = raw_config
    domain.output_dir = raw_config.get("output_dir", "results")
    
    # Global Log Level overrides
    # Priority: CLI (Global) > Config (Raw).
    # But Global defaults to None if not set.
    cli_level = ctx.global_ctx.cli_log_level
    config_level = raw_config.get("log_level", "info")
    
    domain.effective_log_level = cli_level if cli_level else config_level

    # Create output dir
    os.makedirs(domain.output_dir, exist_ok=True)

    # Parse Overrides
    settings_override = {}
    if ctx.global_ctx.settings_override:
        try:
            settings_override = json.loads(ctx.global_ctx.settings_override)
            log(ctx, "info", f"  [Orchestration] Applying global settings override: {settings_override}")
        except json.JSONDecodeError as e:
             log_error(ctx, f"  [Orchestration] Failed to parse settings-override JSON: {e}")

    # Parse Experiments
    for exp_config in raw_config.get("experiments", []):
        base_params = exp_config.get("parameters", {})
        # Apply overrides
        if settings_override:
            recursive_update(base_params, settings_override)

        exp_def = ExperimentDefinition(
            name=exp_config["name"],
            runs=exp_config["runs"],
            episodes_per_run=exp_config["episodes_per_run"],
            parameters=base_params,
            log_level=exp_config.get("log_level", domain.effective_log_level)
        )
        domain.experiments.append(exp_def)
    
    log(ctx, "info", f"  [Orchestration] Loaded {len(domain.experiments)} experiments.")
