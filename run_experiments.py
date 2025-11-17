import json
import argparse
from src.experiment_context import OrchestrationContext
from src.orchestration_processes.p_load_config import p_load_config
from src.orchestration_processes.p_run_simulations import p_run_simulations
from src.orchestration_processes.p_aggregate_results import p_aggregate_results
from src.orchestration_processes.p_plot_results import p_plot_results
from src.orchestration_processes.p_analyze_data import p_analyze_data
from src.orchestration_processes.p_save_summary import p_save_summary

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
            print(f"LỖI: Không tìm thấy process '{step_name}' trong ORCHESTRATION_REGISTRY.")
            continue
        
        print(f"\n--- Đang chạy Process: {step_name} ---")
        context = process_func(context)
        
        # Kiểm tra nếu có lỗi nghiêm trọng, dừng workflow
        if context.final_report and "LỖI" in context.final_report:
            print(f"LỖI NGHIÊM TRỌNG: Dừng workflow do lỗi trong process '{step_name}'.")
            break
            
    return context

def main():
    # --- Sửa lỗi: Thêm xử lý tham số dòng lệnh ---
    parser = argparse.ArgumentParser(description="Chạy quy trình dàn dựng thử nghiệm cho các agent cảm xúc.")
    parser.add_argument(
        '--config',
        type=str,
        default='experiments.json',
        help='Đường dẫn đến file JSON cấu hình thử nghiệm.'
    )
    args = parser.parse_args()
    # ---------------------------------------------

    print("--- BẮT ĐẦU QUY TRÌNH DÀN DỰNG THỬ NGHIỆM ---")
    print(f"--- Sử dụng file cấu hình: {args.config} ---")

    # 1. Khởi tạo OrchestrationContext với đường dẫn file cấu hình từ tham số
    context = OrchestrationContext(config_path=args.config)

    # 2. Tải định nghĩa workflow
    with open("configs/orchestration_workflow.json", "r", encoding="utf-8") as f:
        workflow_definition = json.load(f)

    # 3. Chạy workflow
    final_context = run_orchestration_workflow(workflow_definition['steps'], context)

    print("\n--- KẾT THÚC QUY TRÌNH DÀN DỰNG THỬ NGHIỆM ---")
    if final_context.final_report:
        print("\n" + final_context.final_report)

if __name__ == "__main__":
    main()