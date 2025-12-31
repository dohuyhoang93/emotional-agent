"""
SNN Homeostasis Processes for Theus Framework
==============================================
Homeostasis processes: Regular & Meta-Homeostasis với Theus @process decorator.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus.contracts import process
from src.core.snn_context_theus import SNNSystemContext, ensure_tensors_initialized, sync_from_tensors


@process(
    inputs=[
        'domain_ctx.neurons',
        'domain_ctx.metrics', # Allow reading dict
        'domain_ctx.metrics.fire_rate',
        'global_ctx.target_fire_rate',
        'global_ctx.homeostasis_rate',
        'global_ctx.threshold_min',
        'global_ctx.threshold_max',
        'domain_ctx.tensors' # NEW
    ],
    outputs=[
        'domain_ctx.neurons',  # threshold updated
        'domain_ctx.tensors'   # NEW
    ],
    side_effects=[]
)
def process_homeostasis(ctx: SNNSystemContext):
    """
    Quy trình Homeostasis thường - điều chỉnh threshold (VECTORIZED).
    
    Mục tiêu: Duy trì fire rate gần target_fire_rate.
    
    Logic:
    - Fire rate cao → Tăng threshold (khó bắn hơn)
    - Fire rate thấp → Giảm threshold (dễ bắn hơn)
    """
    domain = ctx.domain_ctx
    global_ctx = ctx.global_ctx
    
    current_fire_rate = domain.metrics.get('fire_rate', 0.0)
    target_fire_rate = global_ctx.target_fire_rate
    homeostasis_rate = global_ctx.homeostasis_rate
    
    # Tính error
    error = current_fire_rate - target_fire_rate
    
    # === VECTORIZED UPDATE ===
    # 1. Ensure tensors exist
    ensure_tensors_initialized(ctx)
    t = domain.tensors
    
    # 2. Vectorized calculation
    t['thresholds'] += error * homeostasis_rate
    
    # 3. Clip
    np.clip(
        t['thresholds'],
        global_ctx.threshold_min,
        global_ctx.threshold_max,
        out=t['thresholds'] # Update in-place
    )

    # === EMERGENCY RESCUE (SNN Death Spiral Protection) ===
    # If firing rate is critically low (e.g. < 1e-5), the network is "dead".
    # Standard homeostasis is too slow. We need a "defibrillator".
    if current_fire_rate < 1e-5:
        # 1. Hard Reset Thresholds to Min for ALL neurons
        t['thresholds'].fill(global_ctx.threshold_min)
        
        # 2. Inject Massive Noise into Potentials (Kickstart)
        # Add random value [0, threshold_min] to potentials
        noise = np.random.uniform(0, global_ctx.threshold_min, size=t['thresholds'].shape)
        t['potentials'] += noise
        
        # 3. Mark Metrics
        domain.metrics['emergency_rescue_triggered'] = True
        domain.metrics['rescue_noise_magnitude'] = float(np.mean(noise))
        print(f"⚠️  [Homeostasis] EMERGENCY RESCUE TRIGGERED! Noise injected. Fire Rate: {current_fire_rate}")
    
    # 4. Sync back to objects (Risk #9 Mitigation)
    sync_from_tensors(ctx)


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
    PID Controller với anti-windup.
    """
    # Proportional
    p_term = kp * error
    
    # Integral (với clamping)
    state['error_integral'] += error
    state['error_integral'] = np.clip(
        state['error_integral'],
        -max_integral,
        max_integral
    )
    i_term = ki * state['error_integral']
    
    # Derivative
    d_term = kd * (error - state['error_prev'])
    state['error_prev'] = error
    
    # PID output
    output = p_term + i_term + d_term
    
    # Saturation
    output_saturated = np.clip(output, -max_output, max_output)
    
    # Back-calculation anti-windup
    # Nếu output bị saturate, giảm integral
    if abs(output) > max_output:
        saturation_error = output - output_saturated
        state['error_integral'] -= saturation_error / ki if ki != 0 else 0
    
    return output_saturated


@process(
    inputs=[
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.domain_ctx.pid_state',
        'domain.snn_context.global_ctx.target_fire_rate',
        'domain.snn_context.global_ctx.pid_kp',
        'domain.snn_context.global_ctx.pid_ki',
        'domain.snn_context.global_ctx.pid_kd',
        'domain.snn_context.global_ctx.pid_max_integral',
        'domain.snn_context.global_ctx.pid_max_output',
        'domain.snn_context.global_ctx.pid_scale_factor',
        'domain.snn_context.global_ctx.threshold_min',
        'domain.snn_context.global_ctx.threshold_max',
        'domain.snn_context.domain_ctx.tensors' # NEW
    ],
    outputs=[
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.pid_state',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.domain_ctx.tensors' # NEW
    ],
    side_effects=[]
)
def process_meta_homeostasis_fixed(ctx: SNNSystemContext):
    """
    Quy trình Meta-Homeostasis với PID anti-windup (VECTORIZED).
    """
    # Handle context nesting (RL -> SNN)
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context
        domain = snn_ctx.domain_ctx
        global_ctx = snn_ctx.global_ctx
    else:
        # Standalone SNN context
        snn_ctx = ctx
        domain = ctx.domain_ctx
        global_ctx = ctx.global_ctx
    
    current_fire_rate = domain.metrics.get('fire_rate', 0.0)
    target_fire_rate = global_ctx.target_fire_rate
    
    # Tính error
    fire_rate_error = target_fire_rate - current_fire_rate
    
    # === PID CONTROLLER CHO THRESHOLD ===
    threshold_adjustment = pid_controller_with_antiwindup(
        error=fire_rate_error,
        kp=global_ctx.pid_kp,
        ki=global_ctx.pid_ki,
        kd=global_ctx.pid_kd,
        state=domain.pid_state['threshold'],
        max_integral=global_ctx.pid_max_integral,
        max_output=global_ctx.pid_max_output
    )
    
    # === VECTORIZED UPDATE ===
    # 1. Ensure tensors
    ensure_tensors_initialized(snn_ctx)
    t = domain.tensors

    # 2. Vectorized Update
    # NOTE: Giảm threshold khi fire_rate thấp (error > 0)
    t['thresholds'] -= threshold_adjustment * global_ctx.pid_scale_factor
    
    # 3. Clip
    np.clip(
         t['thresholds'],
         global_ctx.threshold_min,
         global_ctx.threshold_max,
         out=t['thresholds']
    )
    
    # 4. Sync back
    sync_from_tensors(snn_ctx)
    
    # Cập nhật metrics để audit
    domain.metrics['meta_threshold_adj'] = threshold_adjustment
    domain.metrics['meta_integral'] = domain.pid_state['threshold']['error_integral']
    domain.metrics['meta_fire_rate_error'] = fire_rate_error
