import torch
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.core.engine import POPEngine, process

# 1. Define a dummy process
@process(inputs=['global.initial_exploration_rate'], outputs=['domain.current_exploration_rate'])
def dummy_process(ctx: SystemContext):
    # Logic: Reset exploration rate to base
    base = ctx.global_ctx.initial_exploration_rate
    ctx.domain_ctx.current_exploration_rate = base
    print(f"Process ran. Set exploration to {base}")

def test_pop_arch():
    # 2. Setup Context
    global_ctx = GlobalContext(
        initial_needs=[0.5, 0.5],
        initial_emotions=[0.0, 0.0],
        total_episodes=10,
        max_steps=100,
        seed=42,
        switch_locations={'A': (1,1)}
    )
    
    domain_ctx = DomainContext(
        N_vector=torch.tensor([0.5, 0.5]),
        E_vector=torch.tensor([0.0, 0.0]),
        believed_switch_states={'A': False},
        q_table={},
        short_term_memory=[],
        long_term_memory={}
    )
    
    system_ctx = SystemContext(global_ctx, domain_ctx)
    
    # 3. Setup Engine
    engine = POPEngine(system_ctx)
    engine.register_process("test_p1", dummy_process)
    
    # 4. Execute
    print("Before:", system_ctx.domain_ctx.current_exploration_rate)
    system_ctx.domain_ctx.current_exploration_rate = 0.5 # sabotage
    print("Sabotaged:", system_ctx.domain_ctx.current_exploration_rate)
    
    engine.run_process("test_p1")
    
    print("After:", system_ctx.domain_ctx.current_exploration_rate)
    
    assert system_ctx.domain_ctx.current_exploration_rate == 1.0
    print("POP Core Test Passed!")

if __name__ == "__main__":
    test_pop_arch()
