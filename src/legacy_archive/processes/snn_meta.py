"""
SNN Meta-Homeostasis: PID Controllers
======================================
Tự động điều chỉnh tham số hệ thống để duy trì ổn định.
"""
from src.core.snn_context import SNNContext
import numpy as np


def pid_controller(
    error: float,
    kp: float,
    ki: float,
    kd: float,
    state: dict
) -> float:
    """
    Bộ điều khiển PID chuẩn.
    
    Args:
        error: Sai số hiện tại (target - current)
        kp, ki, kd: Hệ số PID
        state: Dict chứa error_integral và error_prev
    
    Returns:
        Control signal (điều chỉnh cần áp dụng)
    """
    # Proportional
    p_term = kp * error
    
    # Integral (tích lũy sai số)
    state['error_integral'] += error
    i_term = ki * state['error_integral']
    
    # Derivative (tốc độ thay đổi)
    d_term = kd * (error - state['error_prev'])
    state['error_prev'] = error
    
    # Tổng hợp
    control = p_term + i_term + d_term
    
    return control


def process_meta_homeostasis(ctx: SNNContext) -> SNNContext:
    """
    Quy trình Meta-Homeostasis: Tự động điều chỉnh tham số toàn cục.
    
    Điều khiển:
    1. Threshold (dựa trên fire rate)
    2. Learning Rate (dựa trên prediction error)
    """
    # Lấy PID gains
    kp = ctx.params['pid_kp']
    ki = ctx.params['pid_ki']
    kd = ctx.params['pid_kd']
    
    # 1. Điều khiển Threshold (duy trì fire rate)
    target_fire_rate = ctx.params['target_fire_rate']
    current_fire_rate = ctx.metrics.get('fire_rate', 0.0)
    
    fire_rate_error = target_fire_rate - current_fire_rate
    
    threshold_adjustment = pid_controller(
        error=fire_rate_error,
        kp=kp,
        ki=ki,
        kd=kd,
        state=ctx.pid_state['threshold']
    )
    
    # Áp dụng điều chỉnh cho tất cả neuron
    for neuron in ctx.neurons:
        neuron.threshold -= threshold_adjustment * 0.1  # Scale down
        neuron.threshold = np.clip(neuron.threshold, 0.3, 3.0)
    
    # 2. Điều khiển Learning Rate (dựa trên prediction error)
    # NOTE: Nếu error cao -> Tăng learning rate để học nhanh hơn
    avg_prediction_error = ctx.metrics.get('avg_prediction_error', 0.0)
    target_error = 0.1  # Mục tiêu
    
    learning_error = avg_prediction_error - target_error
    
    learning_adjustment = pid_controller(
        error=learning_error,
        kp=kp * 0.5,  # Nhẹ hơn
        ki=ki * 0.5,
        kd=kd * 0.5,
        state=ctx.pid_state['learning_rate']
    )
    
    # Điều chỉnh learning rate
    ctx.params['learning_rate'] += learning_adjustment * 0.001
    ctx.params['learning_rate'] = np.clip(ctx.params['learning_rate'], 0.001, 0.1)
    
    # Ghi metrics
    ctx.metrics['meta_threshold_adj'] = threshold_adjustment
    ctx.metrics['meta_learning_adj'] = learning_adjustment
    
    return ctx
