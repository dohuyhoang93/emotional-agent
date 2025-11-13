from src.context import AgentContext

def execute_action(context: AgentContext, environment) -> AgentContext:
    print("  [P] 7. Executing action...")
    extrinsic_reward = environment.perform_action(context.selected_action)
    context.last_reward['extrinsic'] = extrinsic_reward
    print(f"    > Phần thưởng ngoại sinh nhận được: {extrinsic_reward}")
    return context
