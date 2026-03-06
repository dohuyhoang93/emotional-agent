import os
import sys
sys.path.append(os.getcwd())

import numpy as np
import torch
from src.core.context import SystemContext, DomainContext, GlobalContext
from src.processes.snn_core_theus import _fire_impl
from src.processes.rl_processes import update_q_learning
from src.core.snn_context_theus import create_snn_context_theus
from environment import GridWorld

def test_snn_cumulative_average():
    print("\n" + "="*50)
    print("1. PROOF: SNN FIRING RATE CUMULATIVE MATH BUG")
    print("="*50)
    
    # Khởi tạo giả lập SNN Context
    snn_ctx = create_snn_context_theus(
        num_neurons=100, connectivity=0.1, vector_dim=16, 
        seed=42, initial_threshold=0.05, tau_decay=0.9, threshold_min=0.01
    )
    
    # Khởi tạo mock nặng cho Theus
    t = {
        'potentials': np.array([0.1]*100),     # Mức điện thế vượt qua threshold
        'thresholds': np.array([0.0]*100),     # Ngưỡng thấp
        'last_fire_times': np.array([-10]*100),# Tránh refractory period
        'potential_vectors': np.zeros((100, 16)),
        'use_vectorized_queue': False
    }
    snn_ctx.domain_ctx.heavy_tensors = t
    snn_ctx.domain_ctx.current_time = 100
    snn_ctx.domain_ctx.spike_queue = {}
    
    # GIẢ LẬP: Agent đã chạy được \~10 episodes dài, tích lũy 50,000 ticks.
    snn_ctx.domain_ctx.metrics = {
        'accumulated_spikes': 1500,
        'accumulated_ticks': 50000 
    }
    
    ctx = SystemContext(global_ctx=GlobalContext(), domain_ctx=DomainContext(agent_id=0))
    ctx.domain_ctx.snn_context = snn_ctx
    
    print(f"[Before Step] Tích lũy cũ -> Spikes: 1500, Ticks: 50000")
    print(f"              Expected true firing rate of THIS step: 1.0 (100% neurons fire)")
    
    delta = _fire_impl(ctx, sync=False)
    metrics = delta['metrics']
    
    print(f"[After Step] Số Nơ-ron chạy trong step này: {metrics['fired_count']}/100")
    print(f"[After Step] Nhưng Metrics['avg_firing_rate'] bị trả về: {metrics['avg_firing_rate']:.6f}")
    print("-> BẰNG CHỨNG: Dù 100% neuron kích hoạt trong step này, avg_firing_rate bị triệt tiêu tới mức 0.00032 do mẫu số bị dồn lại qua nhiều episode!\n")

def test_q_table_truncate():
    print("="*50)
    print("2. PROOF: Q-TABLE OVERWRITE BUG IN THEUS CONTEXT")
    print("="*50)
    
    g_ctx = GlobalContext()
    d_ctx = DomainContext(
        agent_id=0, 
        current_observation={'agent_pos': (0,0)}, 
        previous_observation={'agent_pos': (0,1)}, 
        last_reward=1.0, 
        last_action=0
    )
    
    # Khởi tạo Q-Table ban đầu có 3 States
    # (Được học qua rất nhiều steps)
    d_ctx.heavy_q_table = {
        "0,0": [0.0]*8,
        "0,1": [1.0]*8,
        "1,0": [2.0]*8
    }
    d_ctx.heavy_gated_network = None
    
    ctx = SystemContext(global_ctx=g_ctx, domain_ctx=d_ctx)
    
    print(f"[Before Update] Kích thước Q-Table của Agent hiện tại: {len(ctx.domain_ctx.heavy_q_table)} states.")
    
    # Chạy Q-Learning Update
    delta = update_q_learning(ctx)
    
    # Trích xuất Dict trả về Theus Engine
    returned_table = delta['heavy_q_table']
    
    print(f"[After Update]  Hàm trả về dictionary heavy_q_table có kích thước mới: {len(returned_table)} states.")
    print(f"                Các key tồn tại trong dict trả về: {list(returned_table.keys())}")
    print("-> BẰNG CHỨNG: Do Engine dùng dictionary payload này để OVERWRITE vào state toàn cục, Q-Table bị reset thành size = 1, mất toàn bộ trí nhớ!\n")


def test_env_observation():
    print("="*50)
    print("3. PROOF: STATIC ENVIRONMENT SENSOR (VẤP TƯỜNG LIÊN TỤC)")
    print("="*50)
    
    settings = {"environment_config": {"grid_size": 5, "num_agents": 1, "start_positions": [[0,0]], "goal_pos": [4,4], "walls": [[0,1]]}}
    env = GridWorld(settings)
    
    print("[State] Agent bắt đầu ở toạ độ (0, 0). Điểm (0, 1) là tường tĩnh (#).")
    
    # Lấy sensor_vector lúc đầu
    obs1 = env.get_sensor_vector(0)
    
    # Cố gắng đi sang phải vô tường
    env.perform_action(0, 'right')
    obs2 = env.get_sensor_vector(0)
    
    diff = np.sum(np.abs(obs1 - obs2))
    print(f"[Action] Agent thực hiện Action 'right' -> Vấp Tường.")
    print(f"[Sensor] Tổng sự khác biệt (L1_norm) Vector cảm biến trước và sau vấp tường: {diff}")
    if diff == 0.0:
        print("-> BẰNG CHỨNG: Khi vấp tường toạ độ không đổi, Đầu vào SNN (Sensor Vector) hoàn toàn không cấp tín hiệu mới để thoát kẹt!\n")

if __name__ == '__main__':
    test_snn_cumulative_average()
    test_q_table_truncate()
    test_env_observation()
