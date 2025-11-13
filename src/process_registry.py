# src/process_registry.py

from src.processes.p1_observation import observe
from src.processes.p2_belief_update import update_belief
from src.processes.p3_emotion_calc import calculate_emotions
from src.processes.p4_reward_calc import calculate_rewards
from src.processes.p5_policy_adjust import adjust_policy
from src.processes.p6_action_select import select_action
from src.processes.p7_execution import execute_action
from src.processes.p8_consequence import record_consequences

REGISTRY = {
    "observe": observe,
    "update_belief": update_belief,
    "calculate_emotions": calculate_emotions,
    "calculate_rewards": calculate_rewards,
    "adjust_policy": adjust_policy,
    "select_action": select_action,
    "execute_action": execute_action,
    "record_consequences": record_consequences,
}

# Các process cần truy cập environment
ENVIRONMENT_AWARE_PROCESSES = {
    "observe",
    "execute_action"
}
