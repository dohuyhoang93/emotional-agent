from src.experiment_context import OrchestrationContext
from src.plotting import plot_all_experiment_results
from src.logger import log, log_error # Import the new logger

def p_plot_results(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để vẽ các biểu đồ tổng hợp từ dữ liệu đã tổng hợp.
    """
    log(context, "info", "  [Orchestration] Plotting aggregated results...")

    experiments_data_for_plotting = {
        exp_def.name: exp_def.aggregated_data
        for exp_def in context.experiments
        if not exp_def.aggregated_data.empty
    }

    if experiments_data_for_plotting:
        plot_all_experiment_results(experiments_data_for_plotting, context.global_output_dir)
    else:
        log(context, "info", "    [Plotting] Không có dữ liệu tổng hợp để vẽ biểu đồ.")

    return context
