import json
import time
import torch
from src.context import AgentContext
from src.process_registry import REGISTRY, ENVIRONMENT_AWARE_PROCESSES
from environment import GridWorld
from src.models import EmotionCalculatorMLP

def run_workflow(workflow_steps: list, context: AgentContext, environment: GridWorld):
    """
    Bộ máy thực thi (Workflow Engine) cho kiến trúc POP.
    """
    for step_name in workflow_steps:
        # Bỏ qua process 'record_consequences' ở bước đầu tiên của episode
        if context.previous_observation is None and step_name == "record_consequences":
            continue

        process_func = REGISTRY.get(step_name)
        if not process_func:
            print(f"LỖI: Không tìm thấy process '{step_name}' trong REGISTRY.")
            continue

        if step_name in ENVIRONMENT_AWARE_PROCESSES:
            context = process_func(context, environment)
        else:
            context = process_func(context)
    return context

def main():
    """
    Điểm khởi chạy chính của chương trình.
    """
    print("--- BẮT ĐẦU CHƯƠNG TRÌNH MÔ PHỎNG TÁC NHÂN HỌC TẬP ---")

    # 1. Tải cấu hình
    with open("configs/settings.json", "r") as f:
        settings = json.load(f)
    with open("configs/agent_workflow.json", "r") as f:
        workflow = json.load(f)

    # 2. Khởi tạo Môi trường, Tác nhân và Model (CHỈ MỘT LẦN)
    environment = GridWorld(settings)
    context = AgentContext(settings)
    
    n_dim = len(settings['initial_needs'])
    b_dim = 2
    m_dim = 1
    e_dim = len(settings['initial_emotions'])
    emotion_model = EmotionCalculatorMLP(n_dim, b_dim, m_dim, e_dim)
    optimizer = torch.optim.Adam(emotion_model.parameters(), lr=settings['mlp_learning_rate'])
    
    context.emotion_model = emotion_model
    context.emotion_optimizer = optimizer

    # 3. Chạy vòng lặp mô phỏng theo từng episode
    num_episodes = settings.get("num_episodes", 10)
    all_episode_steps = []

    for episode in range(num_episodes):
        print(f"\n{'='*10} Bắt đầu Episode {episode + 1}/{num_episodes} {'='*10}")
        
        # Reset môi trường và các trạng thái tạm thời của context
        context.current_observation = environment.reset()
        context.previous_observation = None
        context.td_error = 0.0

        while not environment.is_done():
            environment.render()
            print(f"Episode {episode + 1} | Step {environment.current_step}")
            print(f"Trạng thái tác nhân:\n{context}")
            
            context = run_workflow(workflow['steps'], context, environment)
            
            time.sleep(0.01) # Giảm thời gian chờ để chạy nhanh hơn

        environment.render()
        if tuple(environment.agent_pos) == environment.goal_pos:
            print(f"*** THÀNH CÔNG! Tác nhân đã đến đích sau {environment.current_step} bước. ***")
        else:
            print(f"--- THẤT BẠI! Tác nhân không đến được đích sau {environment.max_steps} bước. ---")
        
        all_episode_steps.append(environment.current_step)
        # time.sleep(0.1) # Giảm thời gian chờ

    print("\n--- KẾT THÚC CHƯƠNG TRÌNH MÔ PHỎNG ---")
    successful_episodes = sum(1 for s in all_episode_steps if s < settings['max_steps_per_episode'])
    print(f"Tỷ lệ thành công: {successful_episodes / num_episodes * 100:.1f}%")
    if successful_episodes > 0:
        avg_steps_on_success = sum(s for s in all_episode_steps if s < settings['max_steps_per_episode']) / successful_episodes
        print(f"Số bước trung bình cho các episode thành công: {avg_steps_on_success:.2f}")


if __name__ == "__main__":
    main()
