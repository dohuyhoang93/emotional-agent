from src.core.engine import process
from src.orchestrator.context import OrchestratorSystemContext
from src.plotting import plot_all_experiment_results
from src.logger import log

@process(
    inputs=['domain.experiments', 'domain.output_dir', 'log_level'],
    outputs=[],
    side_effects=['plotting.plot_all', 'filesystem.write'],
    errors=['plotting_error']
)
def plot_results(ctx: OrchestratorSystemContext):
    """
    Process: Vẽ biểu đồ từ dữ liệu đã tổng hợp.
    """
    log(ctx, "info", "  [Orchestration] Plotting aggregated results...")
    domain = ctx.domain_ctx
    
    experiments_data_for_plotting = {
        exp_def.name: exp_def.aggregated_data
        for exp_def in domain.experiments
        if not exp_def.aggregated_data.empty
    }

    if experiments_data_for_plotting:
        try:
            plot_all_experiment_results(experiments_data_for_plotting, domain.output_dir)
        except Exception as e:
            log(ctx, "info", f"LỖI khi vẽ biểu đồ: {e}") 
            # We don't bubble error to stop workflow, just log? Contract errors allows exceptions.
    else:
        log(ctx, "info", "    [Plotting] Không có dữ liệu tổng hợp để vẽ biểu đồ.")
