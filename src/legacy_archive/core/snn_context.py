"""
SNN Context Data Structures (Phase 1: Scalar Core)
====================================================
Định nghĩa các cấu trúc dữ liệu ECS cho SNN.
Giai đoạn 1 chỉ hỗ trợ Scalar Spike (0/1), không có Vector.
"""
from dataclasses import dataclass, field
from typing import List, Dict
import numpy as np


@dataclass
class NeuronRecord:
    """
    Bản ghi Neuron (Vector Version - Phase 2).
    NOTE: Không có method. Đây là Pure Data Structure.
    """
    neuron_id: int
    
    # Scalar properties (giữ nguyên để tương thích ngược)
    potential: float = 0.0  # Điện thế màng tổng hợp (V)
    threshold: float = 1.0  # Ngưỡng kích hoạt
    last_fire_time: int = -1000  # Thời điểm bắn xung gần nhất
    fire_count: int = 0  # Số lần đã bắn (dùng cho Homeostasis)
    
    # Vector properties (Phase 2)
    vector_dim: int = 16  # Số chiều của vector
    potential_vector: np.ndarray = field(default_factory=lambda: np.zeros(16))  # Vector điện thế
    prototype_vector: np.ndarray = field(default_factory=lambda: np.random.randn(16))  # Vector mẫu (học được)


@dataclass
class SynapseRecord:
    """
    Bản ghi Synapse (Phase 3: Social Learning).
    """
    synapse_id: int
    pre_neuron_id: int  # ID neuron tiền synapse
    post_neuron_id: int  # ID neuron hậu synapse
    weight: float = 0.5  # Trọng số synapse
    trace: float = 0.0  # Dấu vết STDP (Eligibility Trace)
    delay: int = 1  # Độ trễ truyền xung (ms)
    
    # Phase 3: Social Learning
    synapse_type: str = "native"  # "native" hoặc "shadow" (Sandbox)
    source_agent_id: int = -1  # ID của agent nguồn (nếu là viral synapse)
    confidence: float = 0.5  # Độ tin cậy (dùng cho Commitment Layer)
    prediction_error_accum: float = 0.0  # Tích lũy lỗi dự đoán


@dataclass
class SNNContext:
    """
    Context Data cho toàn bộ mạng SNN (Phase 3: Multi-Agent).
    """
    # Identity
    agent_id: int = 0  # ID của agent này trong quần thể
    
    # Thời gian mô phỏng
    current_time: int = 0
    
    # Danh sách Neuron (ECS Style: Array of Structs)
    neurons: List[NeuronRecord] = field(default_factory=list)
    
    # Danh sách Synapse
    synapses: List[SynapseRecord] = field(default_factory=list)
    
    # Hàng đợi sự kiện (Event Queue)
    spike_queue: Dict[int, List[int]] = field(default_factory=dict)
    
    # Tham số toàn cục
    params: Dict[str, float] = field(default_factory=lambda: {
        'tau_decay': 0.9,
        'tau_trace': 0.95,
        'learning_rate': 0.01,
        'clustering_rate': 0.01,
        'target_fire_rate': 0.02,
        'homeostasis_rate': 0.001,
        # Phase 3: Meta-Homeostasis PID
        'pid_kp': 0.1,  # Proportional gain
        'pid_ki': 0.01,  # Integral gain
        'pid_kd': 0.05,  # Derivative gain
    })
    
    # Metrics (dùng cho giám sát)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Phase 3: Social Signals
    social_signals: Dict[str, float] = field(default_factory=lambda: {
        'fear': 0.0,
        'curiosity': 0.0,
        'stress': 0.0,
    })
    
    # Phase 3: PID State (cho Meta-Homeostasis)
    pid_state: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'threshold': {'error_integral': 0.0, 'error_prev': 0.0},
        'learning_rate': {'error_integral': 0.0, 'error_prev': 0.0},
    })


def create_snn_context(num_neurons: int, connectivity: float = 0.1) -> SNNContext:
    """
    Factory function để tạo SNN Context ban đầu.
    
    Args:
        num_neurons: Số lượng neuron
        connectivity: Tỷ lệ kết nối (0.1 = 10% neuron kết nối với nhau)
    
    Returns:
        SNNContext đã được khởi tạo
    """
    ctx = SNNContext()
    
    # Tạo neurons
    for i in range(num_neurons):
        ctx.neurons.append(NeuronRecord(
            neuron_id=i,
            threshold=1.0 + np.random.uniform(-0.1, 0.1)  # Ngưỡng ngẫu nhiên nhẹ
        ))
    
    # Tạo synapses (kết nối ngẫu nhiên)
    synapse_id = 0
    for pre_id in range(num_neurons):
        for post_id in range(num_neurons):
            if pre_id != post_id and np.random.rand() < connectivity:
                ctx.synapses.append(SynapseRecord(
                    synapse_id=synapse_id,
                    pre_neuron_id=pre_id,
                    post_neuron_id=post_id,
                    weight=np.random.uniform(0.3, 0.7),
                    delay=np.random.randint(1, 5)  # Delay 1-4ms
                ))
                synapse_id += 1
    
    return ctx
