# src/process_registry.py

# from src.processes.p1_observation import observe
from src.processes.p2_belief_update import update_belief
from src.processes.p3_emotion_calc import calculate_emotions
from src.processes.p4_reward_calc import calculate_rewards
from src.processes.p5_policy_adjust import p5_policy_adjust
from src.processes.p6_action_select import select_action
from src.processes.p7_execution import execute_action
from src.processes.p8_consequence import record_consequences

# Sổ đăng ký quy trình (Process Registry)
# Ánh xạ một chuỗi tên tới một đối tượng hàm (function object).
REGISTRY = {
    # "p1_observation": observe, # Đã xóa
    "p2_belief_update": update_belief,
    "p3_emotion_calc": calculate_emotions,
    "p4_reward_calc": calculate_rewards,
    "p5_policy_adjust": p5_policy_adjust,
    "p6_action_select": select_action,
    "p7_execution": execute_action,
    "p8_consequence": record_consequences,
}

# Danh sách các process cần truy cập vào môi trường
ENVIRONMENT_AWARE_PROCESSES = [
    "p7_execution",
    # "p1_observation", # Đã xóa
]
