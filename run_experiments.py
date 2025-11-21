import json
import argparse
from src.experiment_context import OrchestrationContext
from src.orchestration_processes.p_load_config import p_load_config
from src.orchestration_processes.p_run_simulations import p_run_simulations
from src.orchestration_processes.p_aggregate_results import p_aggregate_results
from src.orchestration_processes.p_plot_results import p_plot_results
from src.orchestration_processes.p_analyze_data import p_analyze_data
from src.orchestration_processes.p_save_summary import p_save_summary
from src.logger import log, log_error # Import the new logger

# Sổ đăng ký Quy trình (Process Registry) cho Orchestration Workflow
ORCHESTRATION_REGISTRY = {
    "p_load_config": p_load_config,
    "p_run_simulations": p_run_simulations,
    "p_aggregate_results": p_aggregate_results,
    "p_plot_results": p_plot_results,
    "p_analyze_data": p_analyze_data,
    "p_save_summary": p_save_summary,
}

def run_orchestration_workflow(workflow_steps: list, context: OrchestrationContext):
    """
    Bộ máy thực thi (Workflow Engine) cho quy trình dàn dựng thử nghiệm.
    """
    for step_name in workflow_steps:
        process_func = ORCHESTRATION_REGISTRY.get(step_name)
        if not process_func:
            log_error(context, f"Không tìm thấy process '{step_name}' trong ORCHESTRATION_REGISTRY.")
            continue
        
        log(context, "info", f"\n--- Đang chạy Process: {step_name} ---")
        context = process_func(context)
        
        # Kiểm tra nếu có lỗi nghiêm trọng, dừng workflow
        if context.final_report and "LỖI" in context.final_report:
            log_error(context, f"NGHIÊM TRỌNG: Dừng workflow do lỗi trong process '{step_name}'.")
            break
            
    return context

def main():
    parser = argparse.ArgumentParser(description="Chạy quy trình dàn dựng thử nghiệm cho các agent cảm xúc.")
    parser.add_argument(
        '--config',
        type=str,
        default='experiments.json',
        help='Đường dẫn đến file JSON cấu hình thử nghiệm.'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['silent', 'info', 'verbose'],
        default=None,
        help='Cấp độ ghi log (silent, info, verbose). Ghi đè cài đặt trong file cấu hình.'
    )
    args = parser.parse_args()

    # Initialize context with config_path. log_level will be default 'info' for now.
    context = OrchestrationContext(config_path=args.config)

    # 1. Tải định nghĩa workflow từ file JSON
    with open("configs/orchestration_workflow.json", "r", encoding="utf-8") as f:
        workflow_definition = json.load(f)

    # 2. Chạy p_load_config ĐẦU TIÊN để đọc cấu hình, bao gồm cả log_level từ file.
    # Thao tác này sẽ cập nhật context.log_level từ file config.
    context = ORCHESTRATION_REGISTRY["p_load_config"](context)

    # 3. Ghi đè log_level bằng tham số dòng lệnh nếu được cung cấp.
    if args.log_level:
        context.log_level = args.log_level
        log(context, "info", f"Cấp độ ghi log được ghi đè bởi dòng lệnh: {context.log_level}")

    log(context, "info", "--- BẮT ĐẦU QUY TRÌNH DÀN DỰNG THỬ NGHIỆM ---")
    log(context, "info", f"--- Sử dụng file cấu hình: {args.config} ---")
    log(context, "info", f"--- Cấp độ ghi log hiệu dụng: {context.log_level} ---")

    # 4. Chạy phần còn lại của workflow (bỏ qua p_load_config vì đã chạy ở trên).
    workflow_steps_after_load_config = [step for step in workflow_definition['steps'] if step != "p_load_config"]
    final_context = run_orchestration_workflow(workflow_steps_after_load_config, context)

    log(context, "info", "\n--- KẾT THÚC QUY TRÌNH DÀN DỰNG THỬ NGHIỆM ---")
    if final_context.final_report:
        log(context, "info", final_context.final_report)

if __name__ == "__main__":
    main()