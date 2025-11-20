# src/process_registry.py

# from src.processes.p1_observation import observe
from src.processes.p2_belief_update import update_belief
from src.processes.p3_emotion_calc import calculate_emotions
from src.processes.p5_adjust_exploration import adjust_exploration
from src.processes.p6_action_select import select_action
from src.processes.p7_execution import execute_action
from src.processes.p8_consequence import record_consequences
from src.processes.p9_social_learning import social_learning # Import process mới

# Sổ đăng ký quy trình (Process Registry)
# Ánh xạ một chuỗi tên tới một đối tượng hàm (function object).
REGISTRY = {
    # "p1_observation": observe, # Đã xóa
    "p2_belief_update": update_belief,
    "p3_emotion_calc": calculate_emotions,
    "p5_adjust_exploration": adjust_exploration,
    "p6_action_select": select_action,
    "p7_execution": execute_action,
    "p8_consequence": record_consequences,
    "p9_social_learning": social_learning, # Thêm process học hỏi xã hội
}

# Danh sách các process cần truy cập vào môi trường
ENVIRONMENT_AWARE_PROCESSES = [
    "p7_execution",
    # "p1_observation", # Đã xóa
]

# Danh sách các process cần truy cập vào context của các agent khác (Blackboard)
SOCIAL_PROCESSES = [
    "p9_social_learning",
]
