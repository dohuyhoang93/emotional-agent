import json
import time
import torch
import random
import numpy as np
import pandas as pd
import argparse
import os
from typing import Dict, Any, List
from src.context import AgentContext
from src.process_registry import REGISTRY, ENVIRONMENT_AWARE_PROCESSES, SOCIAL_PROCESSES # Thêm SOCIAL_PROCESSES
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

def run_workflow(workflow_steps: list, context: AgentContext, environment: GridWorld, agent_id: int, all_contexts: List[AgentContext]):
    """
    Bộ máy thực thi (Workflow Engine) cho kiến trúc POP.
    Đã được sửa đổi để truyền agent_id và all_contexts (Blackboard).
    """
    for step_name in workflow_steps:
        if context.previous_observation is None and step_name == "record_consequences":
            continue

        process_func = REGISTRY.get(step_name)
        if not process_func:
            print(f"LỖI: Không tìm thấy process '{step_name}' trong REGISTRY.")
            continue

        # Truyền các tham số cần thiết cho các process nhận biết môi trường hoặc xã hội
        if step_name in ENVIRONMENT_AWARE_PROCESSES:
            context = process_func(context, environment, agent_id)
        elif step_name in SOCIAL_PROCESSES:
            context = process_func(context, all_contexts, agent_id)
        else:
            context = process_func(context)
    return context

def run_simulation(num_episodes: int, output_path: str, settings_override: Dict[str, Any], seed: int):
    """
    Chạy vòng lặp mô phỏng chính, đã được tái cấu trúc cho nhiều tác nhân.
    """
    print("--- BẮT ĐẦU CHƯƠNG TRÌNH MÔ PHỎNG ĐA TÁC NHÂN ---")

    # 1. Tải cấu hình
    with open("configs/settings.json", "r") as f:
        settings = json.load(f)
    with open("configs/agent_workflow.json", "r") as f:
        workflow = json.load(f)

    if settings_override:
        settings = recursive_update(settings, settings_override)
    
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

    # 2. Khởi tạo Môi trường và các Tác nhân
    environment = GridWorld(settings)
    num_agents = environment.num_agents
    print(f"Khởi tạo {num_agents} tác nhân.")

    # Chuyển đổi logical_switches một lần
    processed_switch_locations = {}
    if 'environment_config' in settings and 'logical_switches' in settings['environment_config']:
        for s in settings['environment_config']['logical_switches']:
            processed_switch_locations[s['id']] = tuple(s['pos'])
    settings['switch_locations'] = processed_switch_locations

    # Khởi tạo danh sách contexts (một cho mỗi agent)
    contexts = [AgentContext(settings) for _ in range(num_agents)]
    for i, context in enumerate(contexts):
        context.max_steps = environment.max_steps
        n_dim = len(settings['initial_needs'])
        b_dim = 6
        m_dim = 1
        e_dim = len(settings['initial_emotions'])
        context.emotion_model = EmotionCalculatorMLP(n_dim, b_dim, m_dim, e_dim)
        context.emotion_optimizer = torch.optim.Adam(context.emotion_model.parameters(), lr=settings['mlp_learning_rate'])

    episode_data = []

    # 3. Chạy vòng lặp mô phỏng
    for episode in range(num_episodes):
        if settings['visual_mode']:
            print(f"\n{'='*10} Bắt đầu Episode {episode + 1}/{num_episodes} {'='*10}")
        
        all_observations = environment.reset()
        for i, context in enumerate(contexts):
            context.current_observation = all_observations[i]
            context.previous_observation = None
            context.td_error = 0.0
            context.last_reward = {'extrinsic': 0.0, 'intrinsic': 0.0}

        # Các biến theo dõi cho episode
        episode_total_rewards = {i: 0 for i in range(num_agents)}
        cycle_times = []

        while not environment.is_done():
            if settings['visual_mode']:
                environment.render()
                print(f"Episode {episode + 1} | Step {environment.current_step}")
            
            # Cho mỗi agent thực hiện một lượt trong một bước của môi trường
            for agent_id, context in enumerate(contexts):
                # Nếu agent này đã đến đích hoặc episode đã kết thúc, bỏ qua
                if tuple(environment.agent_positions[agent_id]) == environment.goal_pos or environment.is_done():
                    continue

                if settings['visual_mode']:
                    print(f"  Agent {agent_id} turn...")
                
                start_time = time.time()
                # "Blackboard" (tấm bảng đen) chính là toàn bộ danh sách `contexts`
                context = run_workflow(workflow['steps'], context, environment, agent_id, contexts)
                end_time = time.time()
                
                cycle_time = end_time - start_time
                context.last_cycle_time = cycle_time
                cycle_times.append(cycle_time)
                
                episode_total_rewards[agent_id] += context.last_reward['extrinsic'] + context.last_reward['intrinsic']

            environment.current_step += 1 # Tăng step count một lần cho mỗi vòng lặp while

            if settings['visual_mode']:
                time.sleep(0.01)

        #Xác định trạng thái thành công
        is_successful = any(tuple(pos) == environment.goal_pos for pos in environment.agent_positions.values())

        if settings['visual_mode']:
            environment.render()
            if is_successful:
                print(f"*** THÀNH CÔNG! Một tác nhân đã đến đích sau {environment.current_step} bước. ***")
            else:
                print(f"--- THẤT BẠI! Không tác nhân nào đến được đích sau {environment.max_steps} bước. ---")
            time.sleep(0.1)
        
        # Ghi log (tạm thời chỉ lấy dữ liệu của agent 0 cho file CSV)
        avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0
        log_data_for_csv = {
            'episode': episode + 1,
            'success': is_successful,
            'steps': environment.current_step,
            'total_reward': episode_total_rewards.get(0, 0), # Log của agent 0
            'final_exploration_rate': contexts[0].policy['exploration_rate'], # Log của agent 0
            'avg_cycle_time': avg_cycle_time,
            'max_steps_env': contexts[0].max_steps
        }
        episode_data.append(log_data_for_csv)

        # --- Cập nhật cho Social Learning ---
        # Lưu kết quả vào bộ nhớ dài hạn của TẤT CẢ các agent để chúng có thể học hỏi lẫn nhau
        for i, context in enumerate(contexts):
            if 'episode_results' not in context.long_term_memory:
                context.long_term_memory['episode_results'] = []
            
            # Mỗi agent sẽ lưu lại kết quả chung của episode
            context.long_term_memory['episode_results'].append({
                'episode': episode + 1,
                'success': is_successful,
                'steps': environment.current_step
            })
        # ------------------------------------


    print(f"\n--- KẾT THÚC CHƯƠNG TRÌNH MÔ PHỎNG sau {num_episodes} episodes ---")
    
    if output_path:
        df = pd.DataFrame(episode_data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Đã lưu kết quả mô phỏng vào: {output_path}")

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
    parser.add_argument("--num-episodes", type=int, default=None, help="Số lượng episode để chạy.")
    parser.add_argument("--output-path", type=str, default=None, help="Đường dẫn để lưu file CSV kết quả.")
    parser.add_argument("--settings-override", type=str, default="{}", help="JSON string để ghi đè các thiết lập.")
    parser.add_argument("--seed", type=int, default=None, help="Seed ngẫu nhiên.")
    args = parser.parse_args()

    with open("configs/settings.json", "r") as f:
        default_settings = json.load(f)
    
    num_episodes = args.num_episodes if args.num_episodes is not None else default_settings.get("num_episodes", 10)
    settings_override_dict = json.loads(args.settings_override)
    run_simulation(num_episodes, args.output_path, settings_override_dict, args.seed)

if __name__ == "__main__":
    main()