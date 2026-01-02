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
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.metrics',
        'domain.snn_context.domain_ctx.metrics.fire_rate', # Current Global Rate
        'domain.snn_context.global_ctx.target_fire_rate',
        'domain.snn_context.global_ctx.homeostasis_rate',
        'domain.snn_context.global_ctx.local_homeostasis_rate', # NEW
        'domain.snn_context.global_ctx.trace_decay',             # NEW
        'domain.snn_context.global_ctx.threshold_min',
        'domain.snn_context.global_ctx.threshold_max',
        'domain.snn_context.domain_ctx.tensors'
    ],
    outputs=[
        'domain.snn_context.domain_ctx.neurons',
        'domain.snn_context.domain_ctx.tensors'
    ],
    side_effects=[]
)
def process_homeostasis(ctx: SNNSystemContext):
    """
    Quy trình Harmonic Homeostasis (Elastic Anchoring).
    
    Triết lý: Threshold = (1-S)*Global + S*Local
    - Neuron non trẻ (S~0): Tuân theo Global (Ổn định)
    - Neuron trưởng thành (S~1): Tự chủ Local (Đa dạng)
    """
    from src.logger import log, log_error
    import traceback
    
    try:
        # Handle context nesting (RL -> SNN)
        if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
            snn_ctx = ctx.domain_ctx.snn_context
        else:
            # Standalone SNN context
            snn_ctx = ctx
            
        snn_domain = snn_ctx.domain_ctx
        snn_global = snn_ctx.global_ctx
        
        # 1. Inputs
        target_fire_rate = snn_global.target_fire_rate
        rate_global = snn_global.homeostasis_rate
        rate_local = snn_global.local_homeostasis_rate
        decay = snn_global.trace_decay
        
        t = snn_domain.tensors
        
        thresholds = t['thresholds']
        firing_traces = t['firing_traces']
        
        # Solidity Ratio
        if 'solidity_ratios' in t:
            # Clamp solidity to [0, 1] to prevent numerical errors (negative scale)
            solidity = np.clip(t['solidity_ratios'], 0.0, 1.0)
        else:
            solidity = np.zeros_like(thresholds)
        
        # 2. Update Vectorized Firing Traces
        current_time = snn_domain.current_time
        last_fire_times = t['last_fire_times']
        
        spikes = (last_fire_times == current_time).astype(np.float32)
        firing_traces[:] = decay * firing_traces + (1.0 - decay) * spikes
        
        # 3. Calculate Errors
        current_global_rate = np.mean(firing_traces) 
        error_global = current_global_rate - target_fire_rate
        error_local = firing_traces - target_fire_rate
        
        # 4. Harmonic Blending (Elastic Anchoring)
        base_local_influence = 0.2
        w_local = solidity + (1.0 - solidity) * base_local_influence
        w_global = 1.0 - w_local
        
        adjustment_global = error_global * rate_global
        adjustment_local = error_local * rate_local
        
        delta = w_global * adjustment_global + w_local * adjustment_local
        
        # 6. Adaptive Noise (Sinh - Lão - Bệnh)
        noise_scale = 0.0001 * (1.0 - solidity)
        adaptive_noise = np.random.normal(0, noise_scale, size=delta.shape)
        delta += adaptive_noise
        
        # 7. Apply Update
        thresholds += delta
        
        # 8. Clip
        np.clip(
            thresholds,
            snn_global.threshold_min,
            snn_global.threshold_max,
            out=thresholds
        )
        
        # === EMERGENCY RESCUE ===
        if current_global_rate < 1e-6:
            # RESET with variance to avoid "Dead Zone" uniformity
            # Triết lý: Khi chết, hồi sinh ở mức thấp + sự đa dạng để không chết lại đồng loạt
            rescue_base = snn_global.threshold_min
            rescue_noise = np.random.uniform(0.0, 0.1, size=thresholds.shape)
            
            thresholds[:] = rescue_base + rescue_noise
            
            # Boost potentials too
            noise_pot = np.random.uniform(0, rescue_base, size=thresholds.shape)
            t['potentials'] += noise_pot
            
            snn_domain.metrics['emergency_rescue_triggered'] = True
            # print(f"⚠️ [Harmonic] RESCUE TRIGGERED! Rate: {current_global_rate}")
    
        # 9. Audit Metrics
        snn_domain.metrics['fire_rate'] = float(current_global_rate)
        snn_domain.metrics['avg_threshold'] = float(np.mean(thresholds))
        snn_domain.metrics['std_threshold'] = float(np.std(thresholds))
        
        # 10. Sync Back (CRITICAL FIX)
        # Must sync tensors -> objects immediately, otherwise next cycle's 
        # sync_to_tensors will overwrite these changes with stale object data!
        from src.core.snn_context_theus import sync_from_tensors
        sync_from_tensors(snn_ctx)
        
    except Exception as e:
        log_error(ctx, f"CRITICAL ERROR in process_homeostasis: {e}")
        log_error(ctx, traceback.format_exc())
        raise e


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
