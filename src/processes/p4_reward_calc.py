from src.context import AgentContext

def calculate_rewards(context: AgentContext) -> AgentContext:
    """
    Process tính toán phần thưởng nội sinh (R_nội).
    R_nội được tính dựa trên sự "ngạc nhiên" (td_error) từ bước trước.
    """
    print("  [P] 4. Calculating intrinsic reward...")
    
    # Phần thưởng nội sinh (R_nội) là sự "ngạc nhiên" từ bước trước
    # Nó khuyến khích agent khám phá những hành động dẫn đến kết quả bất ngờ
    reward_intrinsic = context.intrinsic_reward_weight * abs(context.td_error)
    context.last_reward['intrinsic'] = reward_intrinsic
    
    print(f"    > R_nội (từ ngạc nhiên): {reward_intrinsic:.4f}")
    
    return context