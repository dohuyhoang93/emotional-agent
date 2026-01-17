import json
import os

from theus.contracts import process
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
    inputs=[
        'global_ctx', 
        'global_ctx.config_path',
        'global_ctx.cli_log_level',
        'global_ctx.settings_override',
        'domain_ctx'
    ],
    outputs=[],  # Empty outputs - using legacy mutation pattern for v2 compatibility
    side_effects=['filesystem.read', 'filesystem.mkdir'],
    errors=['config_not_found']
)
def load_config(ctx: OrchestratorSystemContext):
    """
    Process: Load experiment configuration from JSON file.
    
    NOTE: Using v2-compatible mutation pattern due to OrchestratorSystemContext
    being a Python dataclass (not Rust State). outputs=[] to avoid Engine mapping.
    """
    config_path = ctx.global_ctx.config_path
    log(ctx, "info", f"  [Orchestration] Loading experiment configuration from {config_path}...")
    
    domain = ctx.domain_ctx
    
    # Error case: config not found
    if not os.path.exists(config_path):
        error_msg = f"Config file not found: {config_path}"
        log_error(ctx, error_msg)
        domain.final_report = f"ERROR: {error_msg}"
        return
    
    # Parse JSON
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = json.load(f)
    except Exception as e:
        error_msg = f"JSON parse error: {e}"
        log_error(ctx, error_msg)
        domain.final_report = f"ERROR: {error_msg}"
        return
    
    # Update domain context (v2 mutation pattern)
    domain.raw_config = raw_config
    domain.output_dir = raw_config.get("output_dir", "results")
    
    # Log Level Priority: CLI (Global) > Config (Raw)
    cli_level = ctx.global_ctx.cli_log_level
    config_level = raw_config.get("log_level", "info")
    domain.effective_log_level = cli_level if cli_level else config_level
    
    # Create output dir (side effect - declared in contract)
    os.makedirs(domain.output_dir, exist_ok=True)
    
    # Parse settings override
    settings_override = {}
    if ctx.global_ctx.settings_override:
        try:
            settings_override = json.loads(ctx.global_ctx.settings_override)
            log(ctx, "info", f"  [Orchestration] Applying global settings override: {settings_override}")
        except json.JSONDecodeError as e:
            log_error(ctx, f"  [Orchestration] Failed to parse settings-override JSON: {e}")
    
    # Parse experiments
    for exp_config in raw_config.get("experiments", []):
        base_params = exp_config.get("parameters", {}).copy()
        
        # Apply overrides
        if settings_override:
            recursive_update(base_params, settings_override)
        
        # Apply top-level overrides
        final_episodes = exp_config["episodes_per_run"]
        if settings_override and 'max_episodes' in settings_override:
            final_episodes = int(settings_override['max_episodes'])
        
        exp_def = ExperimentDefinition(
            name=exp_config["name"],
            runs=exp_config["runs"],
            episodes_per_run=final_episodes,
            parameters=base_params,
            log_level=exp_config.get("log_level", domain.effective_log_level)
        )
        domain.experiments.append(exp_def)
    
    log(ctx, "info", f"  [Orchestration] Loaded {len(domain.experiments)} experiments.")
