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

# Pipeline Function
def run_agent_step_pipeline(ctx: SystemContext):
    """
    Executes the full Agent Step Pipeline (SNN + RL).
    Order matches `workflows/agent_main.yaml`.
    """
    
    # 1. Perception
    perception(ctx)
    
    # 2. SNN Safety Checks
    monitor_safety_triggers(ctx)
    
    # 3. Attention Modulation
    restore_snn_attention(ctx)
    modulate_snn_attention(ctx)
    
    # 4. SNN Cycle (Composite)
    process_snn_cycle(ctx)
    
    # 5. Fast Homeostasis
    process_homeostasis(ctx)
    
    # 6. Advanced Features (Post-Cycle)
    process_commitment(ctx)
    process_neural_darwinism(ctx)
    process_assimilate_ancestor(ctx)
    
    # 7. RL Decision Making
    compute_intrinsic_reward_snn(ctx)
    select_action_gated(ctx)
    
    # 8. Social / Meta (Sandbox)
    process_inject_viral_with_quarantine(ctx)
    process_quarantine_validation(ctx)
    process_meta_homeostasis_fixed(ctx)
    process_periodic_resync(ctx)
    
    # 9. Execution & Learning
    execute_action_with_env(ctx)
    combine_rewards(ctx)
    update_q_learning(ctx)
    
    # 10. Recording
    process_record_snn_step(ctx)
