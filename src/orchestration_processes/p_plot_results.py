from src.experiment_context import OrchestrationContext
from src.plotting import plot_all_experiment_results

def p_plot_results(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để vẽ các biểu đồ tổng hợp từ dữ liệu đã tổng hợp.
    """
    print("  [Orchestration] Plotting aggregated results...")

    experiments_data_for_plotting = {
        exp_def.name: exp_def.aggregated_data
        for exp_def in context.experiments
        if not exp_def.aggregated_data.empty
    }

    if experiments_data_for_plotting:
        plot_all_experiment_results(experiments_data_for_plotting, context.global_output_dir)
    else:
        print("    [Plotting] Không có dữ liệu tổng hợp để vẽ biểu đồ.")

    return context
