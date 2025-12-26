"""
Dream Validation & Reward Injection
===================================
Validates decoded dream states against World Model (Beliefs).
Injects synthetic rewards (Dopamine) for STDP.
Part of Semantic Dream Learning (Phase 13).

Author: Do Huy Hoang
Date: 2025-12-26
"""
from theus import process
from src.core.context import SystemContext

@process(
    inputs=[
        'domain_ctx.metrics',          # Read dream_state_x, y
        'domain_ctx.believed_switch_states', # World Model
        'domain_ctx.td_error'          # Write synthetic reward here
    ],
    outputs=[
        'domain_ctx.td_error',
        'domain_ctx.metrics'
    ],
    side_effects=[]
)
def process_validate_and_reward(ctx: SystemContext):
    """
    Thẩm định & Thưởng phạt.
    
    Logic:
    1. Đọc trạng thái mơ (x, y).
    2. Kiểm tra tính hợp lý (Validity Check).
    3. Bơm TD-Error (Synthetic Reward).
    
    Rewards:
    - INVALID (Vô lý/Nguy hiểm): -1.0 (Punish)
    - VALID & NOVEL (Hợp lý & Mới): +0.5 (Reinforce)
    - NEUTRAL: 0.0
    """
    domain = ctx.domain_ctx
    snn_domain = domain.snn_context.domain_ctx
    
    # 1. Get Decoded State
    x = snn_domain.metrics.get('dream_state_x')
    y = snn_domain.metrics.get('dream_state_y')
    
    if x is None or y is None:
        return

    # 2. Validation Logic (The World Model)
    # ---------------------------------------------------------
    # Rule 1: Switch Consistency
    # Nếu vị trí này là một cái công tắc (theo Global Config),
    # thì niềm tin của Agent về nó phải "Rõ ràng" (True/False).
    # Nếu Agent mơ thấy đi qua công tắc mà không biết nó bật/tắt -> Mơ hồ -> Phạt nhẹ.
    
    # (Mockup Logic for demo implementation w/o full map access)
    is_valid = True
    punishment = 0.0
    reward = 0.0
    
    # --- HEURISTIC RULES (Phase 13 Lite) ---
    
    # A. Phạt "Ảo giác biên" (Boundary Hallucination)
    # Nếu giải mã ra tọa độ kỳ lạ (mặc dù argmax 0-7 safe, nhưng giả sử logic khác)
    if x < 0 or x > 7 or y < 0 or y > 7:
        is_valid = False
        punishment = -0.5
        
    # B. Phạt "Vùng Nguy Hiểm" (Lava Zone - Giả định tại 3,3)
    # Đây là cách dạy Agent tránh xa vùng này ngay trong mơ
    if x == 3 and y == 3:
        is_valid = False
        punishment = -1.0 # Logic Punishment (Anti-Hebbian)
        # Do NOT set 'nightmare' here, otherwise Sanity Check will clear queue 
        # and prevent STDP from learning this punishment.
        
    # C. Thưởng "Vùng Khám Phá" (Novelty)
    # Nếu mơ thấy vùng biên (thường ít đi tới)
    if (x == 0 or x == 7 or y == 0 or y == 7) and is_valid:
        reward = 0.5
        
    # 3. Inject Synthetic Reward (TD Error)
    # -------------------------------------
    # STDP uses 'td_error' input to calculate Dopamine.
    # Normal Q-learning writes to this. In dream, WE write to this.
    
    synthetic_error = reward + punishment
    
    # Overwrite TD Error for the STDP process coming next
    domain.td_error = synthetic_error
    
    # Log validity
    snn_domain.metrics['dream_validity'] = 1.0 if is_valid else 0.0
    snn_domain.metrics['dream_reward'] = synthetic_error
