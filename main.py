import json
import time
import torch
import random
import numpy as np
import pandas as pd
import argparse
import os
from typing import Dict, Any
from src.context import AgentContext
from src.process_registry import REGISTRY, ENVIRONMENT_AWARE_PROCESSES
from environment import GridWorld
from src.models import EmotionCalculatorMLP

def recursive_update(d, u):
    """Recursively update a dictionary."""
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = recursive_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

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

def run_simulation(num_episodes: int, output_path: str, settings_override: Dict[str, Any], seed: int):
    """
    Chạy vòng lặp mô phỏng chính của tác nhân.
    """
    print("--- BẮT ĐẦU CHƯƠNG TRÌNH MÔ PHỎNG TÁC NHÂN HỌC TẬP ---")

    # 1. Tải cấu hình mặc định
    with open("configs/settings.json", "r") as f:
        settings = json.load(f)
    with open("configs/agent_workflow.json", "r") as f:
        workflow = json.load(f)

    # Áp dụng ghi đè cấu hình từ tham số
    if settings_override:
        settings = recursive_update(settings, settings_override)
        print(f"Đã áp dụng ghi đè cấu hình: {settings_override}")
    print(f"DEBUG: Settings after override: {settings}")

    # Áp dụng seed
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        print(f"Đã đặt seed ngẫu nhiên: {seed}")

    # 2. Khởi tạo Môi trường, Tác nhân và Model (CHỈ MỘT LẦN)
    environment = GridWorld(settings)
    
    # Chuyển đổi logical_switches từ list of dicts sang dict {id: pos}
    processed_switch_locations = {}
    if 'environment_config' in settings and 'logical_switches' in settings['environment_config']:
        for s in settings['environment_config']['logical_switches']:
            processed_switch_locations[s['id']] = tuple(s['pos'])
    settings['switch_locations'] = processed_switch_locations

    context = AgentContext(settings)
    
    n_dim = len(settings['initial_needs'])
    b_dim = 6 # agent_pos (y, x) + 4 believed_switch_states
    m_dim = 1 # m_vector is currently a placeholder, so 1 dimension
    e_dim = len(settings['initial_emotions'])
    emotion_model = EmotionCalculatorMLP(n_dim, b_dim, m_dim, e_dim)
    optimizer = torch.optim.Adam(emotion_model.parameters(), lr=settings['mlp_learning_rate'])
    
    context.emotion_model = emotion_model
    context.emotion_optimizer = optimizer

    episode_data = [] # Danh sách để lưu dữ liệu của từng episode

    # 3. Chạy vòng lặp mô phỏng theo từng episode
    for episode in range(num_episodes):
        if settings['visual_mode']:
            print(f"\n{'='*10} Bắt đầu Episode {episode + 1}/{num_episodes} {'='*10}")
        
        # Reset môi trường và các trạng thái tạm thời của context
        environment.reset()
        context.current_observation = environment.get_observation() # Lấy quan sát ban đầu sau reset
        context.previous_observation = None
        context.td_error = 0.0
        context.last_reward = {'extrinsic': 0.0, 'intrinsic': 0.0} # Reset rewards for new episode
        
        episode_total_reward = 0
        is_successful = False

        while not environment.is_done():
            if settings['visual_mode']:
                environment.render()
                print(f"Episode {episode + 1} | Step {environment.current_step}")
                print(f"Trạng thái tác nhân:\n{context}")
            
            context = run_workflow(workflow['steps'], context, environment)
            episode_total_reward += context.last_reward['extrinsic'] + context.last_reward['intrinsic']
            
            if settings['visual_mode']:
                time.sleep(0.01) # Giảm thời gian chờ để chạy nhanh hơn

        # Xác định trạng thái thành công bất kể visual mode
        if tuple(environment.agent_pos) == environment.goal_pos:
            is_successful = True

        # Hiển thị kết quả nếu ở chế độ trực quan
        if settings['visual_mode']:
            environment.render()
            if is_successful:
                print(f"*** THÀNH CÔNG! Tác nhân đã đến đích sau {environment.current_step} bước. ***")
            else:
                print(f"--- THẤT BẠI! Tác nhân không đến được đích sau {environment.max_steps} bước. ---")
            time.sleep(0.1) # Giảm thời gian chờ
        
        # Lưu dữ liệu của episode (với giá trị 'success' đã đúng)
        episode_data.append({
            'episode': episode + 1,
            'success': is_successful,
            'steps': environment.current_step,
            'total_reward': episode_total_reward,
            'final_exploration_rate': context.policy['exploration_rate']
        })

    print(f"\n--- KẾT THÚC CHƯƠNG TRÌNH MÔ PHỎNG sau {num_episodes} episodes ---")
    
    # Lưu dữ liệu vào CSV nếu output_path được cung cấp
    if output_path:
        df = pd.DataFrame(episode_data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Đã lưu kết quả mô phỏng vào: {output_path}")

    # In ra tóm tắt cuối cùng nếu ở chế độ trực quan
    if settings.get('visual_mode', False):
        successful_episodes = sum(1 for d in episode_data if d['success'])
        num_episodes_run = len(episode_data)
        
        print("\n--- TÓM TẮT KẾT QUẢ ---")
        if num_episodes_run > 0:
            success_rate = successful_episodes / num_episodes_run * 100
            print(f"Tỷ lệ thành công: {success_rate:.1f}% ({successful_episodes}/{num_episodes_run})")
            
            if successful_episodes > 0:
                avg_steps_on_success = sum(d['steps'] for d in episode_data if d['success']) / successful_episodes
                print(f"Số bước trung bình cho các episode thành công: {avg_steps_on_success:.2f}")
        else:
            print("Không có episode nào được chạy.")


def main():
    parser = argparse.ArgumentParser(description="Chạy mô phỏng tác nhân học tập cảm xúc.")
    parser.add_argument("--num-episodes", type=int, default=None,
                        help="Số lượng episode để chạy. Mặc định lấy từ settings.json.")
    parser.add_argument("--output-path", type=str, default=None,
                        help="Đường dẫn để lưu file CSV kết quả của mỗi episode.")
    parser.add_argument("--settings-override", type=str, default="{}",
                        help="JSON string để ghi đè các thiết lập trong settings.json.")
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed ngẫu nhiên để đảm bảo khả năng tái lập.")

    args = parser.parse_args()

    # Tải cấu hình mặc định để lấy giá trị num_episodes nếu không được cung cấp qua CLI
    with open("configs/settings.json", "r") as f:
        default_settings = json.load(f)
    
    num_episodes = args.num_episodes if args.num_episodes is not None else default_settings.get("num_episodes", 10)
    
    settings_override_dict = json.loads(args.settings_override)

    run_simulation(num_episodes, args.output_path, settings_override_dict, args.seed)

if __name__ == "__main__":
    main()
