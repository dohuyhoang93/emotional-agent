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
        'global', 
        'global.config_path',
        'global.cli_log_level',
        'global.settings_override',
        'domain',
        'log_level'
    ],
    outputs=[
        'domain.raw_config',
        'domain.output_dir',
        'domain.effective_log_level',
        'domain.experiments',
        'domain.sig_total_experiments',
        'domain.sig_experiment_active_idx',
        'domain.final_report'
    ],
    side_effects=['filesystem.read', 'filesystem.mkdir'],
    errors=['config_not_found']
)
def load_config(ctx: OrchestratorSystemContext):
    """
    Process: Load experiment configuration from JSON file.
    Initializes Signals for Flux Control Flow.
    """
    global_ctx = getattr(ctx, 'global')
    config_path = global_ctx.get('config_path') or global_ctx['config_path']
    log(ctx, "info", f"  [Orchestration] Loading experiment configuration from {config_path}...")
    
    # Error case
    if not os.path.exists(config_path):
        error_msg = f"Config file not found: {config_path}"
        log_error(ctx, error_msg)
        return {
             'domain.final_report': f"ERROR: {error_msg}"
        }
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = json.load(f)
    except Exception as e:
        error_msg = f"JSON parse error: {e}"
        log_error(ctx, error_msg)
        return {
             'domain.final_report': f"ERROR: {error_msg}"
        }
        
    output_dir = raw_config.get("output_dir", "results")
    cli_level = global_ctx.get('cli_log_level')
    config_level = raw_config.get("log_level", "info")
    effective_log_level = cli_level if cli_level else config_level
    
    os.makedirs(output_dir, exist_ok=True)
    
    settings_override = {}
    settings_override_str = global_ctx.get('settings_override')
    if settings_override_str:
        try:
            settings_override = json.loads(settings_override_str)
        except:
            pass
            
    # Parse experiments
    experiments = []
    for exp_config in raw_config.get("experiments", []):
        base_params = exp_config.get("parameters", {}).copy()
        if settings_override:
            recursive_update(base_params, settings_override)
            
        final_episodes = exp_config["episodes_per_run"]
        if settings_override and 'max_episodes' in settings_override:
            final_episodes = int(settings_override['max_episodes'])
            
        exp_def = ExperimentDefinition(
            name=exp_config["name"],
            runs=exp_config["runs"],
            episodes_per_run=final_episodes,
            parameters=base_params,
            log_level=exp_config.get("log_level", "info")
        )
        experiments.append(exp_def)
    
    # Initialize Signals
    total_experiments = len(experiments)
    
    log(ctx, "info", f"  [Orchestration] Loaded {total_experiments} experiments.")
    
    # Return Delta dict instead of mutating (POP Copy-on-Write)
    return {
        'domain.raw_config': raw_config,
        'domain.output_dir': output_dir,
        'domain.effective_log_level': effective_log_level,
        'domain.experiments': experiments,
        'domain.sig_total_experiments': total_experiments,
        'domain.sig_experiment_active_idx': 0
    }
