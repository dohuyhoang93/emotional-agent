from src.context import AgentContext

def observe(context: AgentContext, environment) -> AgentContext:
    print("  [P] 1. Observing environment...")
    # Lưu lại quan sát cũ trước khi có quan sát mới
    context.previous_observation = context.current_observation
    
    context.current_observation = environment.get_observation()
    print(f"    > Quan sát mới: {context.current_observation}")
    return context
