"""
Agent Step Pipeline
===================
Manual composition of the Agent Step workflow to bypass Engine overhead and nested loop issues.
This pipeline executes the Logic defined in `workflows/deprecated/agent_main.yaml` as specialized Python code.

Author: Theus Migration Assistant
Date: 2026-01-16
"""

from src.core.context import SystemContext
# Import Process Functions
from src.processes.p1_perception import perception
from src.processes.snn_rl_bridge import compute_intrinsic_reward_snn, restore_snn_attention, modulate_snn_attention
from src.processes.experimental.snn_safety_theus import monitor_safety_triggers
# from src.processes.snn_core_theus import restore_snn_attention, modulate_snn_attention # Moved to bridge
from src.processes.snn_composite_theus import process_snn_cycle
from src.processes.snn_homeostasis_theus import process_homeostasis, process_meta_homeostasis_fixed
from src.processes.snn_commitment_theus import process_commitment
from src.processes.snn_advanced_features_theus import process_neural_darwinism, process_assimilate_ancestor
from src.processes.rl_processes import select_action_gated, update_q_learning
from src.processes.snn_social_quarantine_theus import process_inject_viral_with_quarantine, process_quarantine_validation
from src.processes.snn_resync_theus import process_periodic_resync
from src.processes.rl_snn_integration import execute_action_with_env, combine_rewards
from src.processes.snn_recorder_process import process_record_snn_step
from theus.contracts import process

def _apply_delta(ctx: SystemContext, delta: dict):
    """
    Helper to manually merge process outputs into context.
    Correctly handles nested SNN context for SNN-specific metrics and state.
    """
    if not isinstance(delta, dict):
        return
        
    # Resolve SNN Context for nested updates
    snn_ctx = None
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context'):
        snn_ctx = ctx.domain_ctx.snn_context
        
    for k, v in delta.items():
        # Handle prefixed keys from Theus Engine style
        clean_k = k.replace('domain_ctx.', '').replace('snn_context.domain_ctx.', '')
        
        # Determine target: RL Domain or SNN Domain
        # SNN specific state: current_time, metrics, heavy_tensors, spike_queue
        snn_keys = ['current_time', 'metrics', 'heavy_tensors', 'spike_queue', 
                    'emotion_saturation_level', 'dampening_active']
        
        if snn_ctx and clean_k in snn_keys:
            # Update SNN Domain Context
            setattr(snn_ctx.domain_ctx, clean_k, v)
        else:
            # Update RL Domain Context
            setattr(ctx.domain_ctx, clean_k, v)

# Pipeline Function
@process(
    inputs=['domain_ctx', 'domain_ctx.snn_context', 'domain_ctx.env_adapter'],
    outputs=['domain_ctx', 'domain_ctx.snn_context'],
)
def run_agent_step_pipeline(ctx: SystemContext, env_adapter=None):
    """
    Executes the full Agent Step Pipeline (SNN + RL).
    Order matches `workflows/agent_main.yaml`.
    
    COMPOSITE PROCESS: This is now a single transaction to minimize Theus overhead.
    Returns: Combined delta of all sub-processes for the Engine to apply.
    """
    master_delta = {}

    def _execute_and_merge(proc_func, *args, **kwargs):
        delta = proc_func(ctx, *args, **kwargs)
        if delta:
            _apply_delta(ctx, delta)
            master_delta.update(delta)
        return delta

    # 1. Perception
    _execute_and_merge(perception, env_adapter=env_adapter)
    
    # 2. SNN Safety Checks
    _execute_and_merge(monitor_safety_triggers)
    
    # 3. Attention Modulation
    _execute_and_merge(restore_snn_attention)
    _execute_and_merge(modulate_snn_attention)
    
    # 4. SNN Cycle (Composite)
    _execute_and_merge(process_snn_cycle)
    
    # 5. Fast Homeostasis
    _execute_and_merge(process_homeostasis)
    
    # 6. Advanced Features (Post-Cycle)
    _execute_and_merge(process_commitment)
    _execute_and_merge(process_neural_darwinism)
    _execute_and_merge(process_assimilate_ancestor)
    
    # 7. RL Decision Making
    _execute_and_merge(compute_intrinsic_reward_snn)
    _execute_and_merge(select_action_gated)
    
    # 8. Social / Meta (Sandbox)
    _execute_and_merge(process_inject_viral_with_quarantine)
    _execute_and_merge(process_quarantine_validation)
    _execute_and_merge(process_meta_homeostasis_fixed)
    _execute_and_merge(process_periodic_resync)
    
    # 9. Recording
    _execute_and_merge(process_record_snn_step)

    # CRITICAL: Return the full objects to ensure nested mutations are persisted.
    # Theus Engine will merge these back into the agent's official state record.
    return {
        'domain_ctx': ctx.domain_ctx,
        'domain_ctx.snn_context': ctx.domain_ctx.snn_context
    }
