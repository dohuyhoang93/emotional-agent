"""
SNN Safety & Robustness Layer (Phase 11)
========================================
Processes for "Defense-in-Depth":
- Monitor Safety Triggers (Pain, Novelty, Context Switch)
- Activate/Deactivate Overrides

Author: Do Huy Hoang
Date: 2025-12-29
"""
from theus.contracts import process
from src.core.context import SystemContext

@process(
    inputs=['domain_ctx', 'domain', 
        'domain.td_error',
        'domain.snn_context', 
        'domain.intrinsic_reward',
        'domain.last_action'
    ],
    outputs=['domain', 'domain_ctx', 'domain.snn_context'],
    side_effects=[]
)
def monitor_safety_triggers(ctx: SystemContext):
    """
    Monitor system metrics to trigger safety mechanisms.
    
    1. Bottom-Up Override (Emergency Brake): High TD-Error.
    2. Saccadic Reset: Action change.
    3. Curiosity Veto: High Intrinsic Reward.
    """
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    safety = domain.safety_state
    
    # === 1. Bottom-Up Override (Emergency Brake) ===
    # Trigger: High negative prediction error (Pain) or extreme surprise
    td_error = ctx.domain_ctx.td_error
    
    # Thresholds (Should be in GlobalContext, hardcoded for now)
    PAIN_THRESHOLD = 2.0  # High error
    EMERGENCY_DURATION = 5 # Steps
    
    if abs(td_error) > PAIN_THRESHOLD:
        safety['emergency_override_steps'] = EMERGENCY_DURATION
        # print("DEBUG: Emergency Override Triggered!")
        
    # Decrement timer
    if safety['emergency_override_steps'] > 0:
        safety['emergency_override_steps'] -= 1
        
    # === 2. Saccadic Reset (Context Switch) ===
    # Trigger: Action changed from previous step
    current_action = ctx.domain_ctx.last_action
    last_action = safety['last_action']
    
    # Detect change (ignore None/Initial)
    if current_action is not None and last_action != -1 and current_action != last_action:
        safety['saccade_triggered'] = True
    else:
        safety['saccade_triggered'] = False
        
    # Update tracker
    if current_action is not None:
        safety['last_action'] = int(current_action)
        
    # === 3. Curiosity Veto ===
    # Trigger: High novelty (intrinsic reward)
    intrinsic = ctx.domain_ctx.intrinsic_reward
    VETO_THRESHOLD = 0.8  # Very novel
    
    if intrinsic > VETO_THRESHOLD:
        safety['veto_active'] = True
    else:
        safety['veto_active'] = False

