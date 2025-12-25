"""
SNN Meta-Homeostasis: PID Controllers (FIXED VERSION)
=====================================================
Sửa lỗi logic:
1. Anti-windup mechanism (clamping + back-calculation)
2. Giảm PID gains xuống 1/100
3. Giảm scale factor xuống 1/1000
4. Giới hạn output
5. KHÔNG chạy cùng homeostasis thường

Author: Do Huy Hoang
Date: 2025-12-25
"""
from src.core.snn_context import SNNContext
import numpy as np


def pid_controller_with_antiwindup(
    error: float,
    kp: float,
    ki: float,
    kd: float,
    state: dict,
    max_integral: float = 5.0,
    max_output: float = 0.01
) -> float:
    """
    Bộ điều khiển PID với Anti-Windup đầy đủ.
    
    Anti-windup mechanisms:
    1. Clamping: Giới hạn integral term
    2. Back-calculation: Giảm integral khi output saturate
    
    Args:
        error: Sai số hiện tại (target - current)
        kp: Proportional gain
        ki: Integral gain
        kd: Derivative gain
        state: Dict chứa error_integral và error_prev
        max_integral: Giới hạn integral term
        max_output: Giới hạn output
    
    Returns:
        Control signal (điều chỉnh cần áp dụng)
    """
    # Proportional term
    p_term = kp * error
    
    # Integral term với clamping anti-windup
    state['error_integral'] += error
    state['error_integral'] = np.clip(
        state['error_integral'], 
        -max_integral, 
        max_integral
    )
    i_term = ki * state['error_integral']
    
    # Derivative term
    d_term = kd * (error - state['error_prev'])
    state['error_prev'] = error
    
    # Tổng hợp (trước khi saturate)
    control_raw = p_term + i_term + d_term
    
    # Giới hạn output
    control = np.clip(control_raw, -max_output, max_output)
    
    # Back-calculation anti-windup
    # NOTE: Nếu output bị saturate, giảm integral để tránh windup
    if abs(control_raw) > max_output and ki != 0:
        excess = control_raw - control
        state['error_integral'] -= excess / ki
        # Đảm bảo vẫn trong giới hạn
        state['error_integral'] = np.clip(
            state['error_integral'],
            -max_integral,
            max_integral
        )
    
    return control


def process_meta_homeostasis_fixed(ctx: SNNContext) -> SNNContext:
    """
    Quy trình Meta-Homeostasis FIXED.
    
    Thay đổi so với version cũ:
    1. Sử dụng PID với anti-windup
    2. Giảm gains xuống 1/100 (0.1 → 0.001)
    3. Giảm scale factor xuống 1/1000 (0.1 → 0.0001)
    4. Giới hạn output và integral
    5. Chỉ điều khiển threshold (bỏ learning rate)
    
    NOTE: Process này THAY THẾ homeostasis thường, không chạy cùng lúc.
    """
    # Lấy PID gains (ĐÃ GIẢM 100 LẦN)
    kp = ctx.params.get('meta_pid_kp', 0.001)   # 0.1 → 0.001
    ki = ctx.params.get('meta_pid_ki', 0.0001)  # 0.01 → 0.0001
    kd = ctx.params.get('meta_pid_kd', 0.0005)  # 0.05 → 0.0005
    
    # Lấy giới hạn
    max_integral = ctx.params.get('meta_max_integral', 5.0)
    max_output = ctx.params.get('meta_max_output', 0.01)
    
    # 1. Điều khiển Threshold (duy trì fire rate)
    target_fire_rate = ctx.params['target_fire_rate']
    current_fire_rate = ctx.metrics.get('fire_rate', 0.0)
    
    # Tính error
    fire_rate_error = target_fire_rate - current_fire_rate
    
    # Gọi PID controller với anti-windup
    threshold_adjustment = pid_controller_with_antiwindup(
        error=fire_rate_error,
        kp=kp,
        ki=ki,
        kd=kd,
        state=ctx.pid_state['threshold'],
        max_integral=max_integral,
        max_output=max_output
    )
    
    # Áp dụng điều chỉnh cho tất cả neuron (GIẢM SCALE 1000 LẦN)
    scale_factor = ctx.params.get('meta_scale_factor', 0.0001)  # 0.1 → 0.0001
    
    for neuron in ctx.neurons:
        neuron.threshold -= threshold_adjustment * scale_factor
        neuron.threshold = np.clip(neuron.threshold, 0.3, 3.0)
    
    # Ghi metrics để debug
    ctx.metrics['meta_threshold_adj'] = threshold_adjustment
    ctx.metrics['meta_integral'] = ctx.pid_state['threshold']['error_integral']
    ctx.metrics['meta_p_term'] = kp * fire_rate_error
    ctx.metrics['meta_i_term'] = ki * ctx.pid_state['threshold']['error_integral']
    ctx.metrics['meta_d_term'] = kd * (fire_rate_error - ctx.pid_state['threshold']['error_prev'])
    
    return ctx


def process_meta_homeostasis_adaptive(ctx: SNNContext) -> SNNContext:
    """
    Version nâng cao: Adaptive gains dựa trên fire rate variance.
    
    NOTE: Chỉ dùng khi version fixed đã ổn định.
    Tự động điều chỉnh gains dựa trên độ ổn định của mạng.
    """
    # Tính variance của fire rate (trong 100 steps gần nhất)
    # NOTE: Cần track history, chưa implement
    
    # Nếu variance cao → Giảm gains (mạng đang dao động)
    # Nếu variance thấp → Tăng gains (mạng ổn định, có thể phản ứng nhanh hơn)
    
    # Placeholder: Gọi version fixed
    return process_meta_homeostasis_fixed(ctx)
