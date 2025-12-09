import torch
from unittest.mock import MagicMock
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.core.engine import POPEngine
from src.adapters.environment_adapter import EnvironmentAdapter

# Import all processes
from src.processes.p1_perception import perception
from src.processes.p2_belief_update import update_belief
from src.processes.p3_emotion_calc import calculate_emotions
from src.processes.p5_adjust_exploration import adjust_exploration
from src.processes.p6_action_select import select_action
from src.processes.p7_execution import execute_action
from src.processes.p8_consequence import record_consequences

def test_bulk_migration():
    # 1. Setup Mock Env
    mock_env = MagicMock()
    # Mock sequence of observations for 2 steps (Initial -> After Action)
    mock_env.get_observation.side_effect = [
        {'agent_pos': (0, 0), 'step_count': 0}, # P1
        {'agent_pos': (0, 1), 'step_count': 1}, # P7 (legacy update)
        {'agent_pos': (0, 1), 'step_count': 1}  # P8 or Next Cycle
    ]
    mock_env.perform_action.return_value = -0.1 # Reward
    
    adapter = EnvironmentAdapter(mock_env)
    
    # 2. Setup Context
    global_ctx = GlobalContext(
        initial_needs=[0.5], initial_emotions=[0.0],
        total_episodes=1, max_steps=100, seed=42,
        switch_locations={'S1': (5,5)},
        initial_exploration_rate=0.5 # Wait, Global has this immutable? No, defaults to 1.0 in definition.
        # But our test needs to check update.
    )
    
    domain_ctx = DomainContext(
        N_vector=torch.tensor([0.5]), E_vector=torch.tensor([0.5, 0.5]), # Conf=0.5
        believed_switch_states={'S1': False}, q_table={}, short_term_memory=[], long_term_memory={},
        base_exploration_rate=0.8
    )
    system_ctx = SystemContext(global_ctx, domain_ctx)
    
    # 3. Setup Engine
    engine = POPEngine(system_ctx)
    engine.register_process("p1", perception)
    engine.register_process("p2", update_belief)
    engine.register_process("p3", calculate_emotions)
    engine.register_process("p5", adjust_exploration)
    engine.register_process("p6", select_action)
    engine.register_process("p7", execute_action)
    engine.register_process("p8", record_consequences)
    
    # 4. Run Cycle
    print("--- Step 1: Perception ---")
    engine.run_process("p1", env_adapter=adapter, agent_id=0)
    print(f"Obs: {domain_ctx.current_observation}")
    
    print("--- Step 2: Belief ---")
    engine.run_process("p2")
    
    print("--- Step 3: Emotion ---")
    engine.run_process("p3")
    print(f"E_vector: {domain_ctx.E_vector}")
    
    print("--- Step 5: Exploration ---")
    engine.run_process("p5")
    print(f"Exploration Rate: {domain_ctx.current_exploration_rate}")
    
    print("--- Step 6: Action Select ---")
    engine.run_process("p6")
    print(f"Selected Action: {domain_ctx.selected_action}")
    
    print("--- Step 7: Execution ---")
    engine.run_process("p7", env_adapter=adapter, agent_id=0)
    print(f"Last Reward: {domain_ctx.last_reward}")
    print(f"Current Obs (after P7): {domain_ctx.current_observation}")
    
    print("--- Step 8: Learn ---")
    engine.run_process("p8")
    print(f"Q-Table size: {len(domain_ctx.q_table)}")
    print(f"Memory size: {len(domain_ctx.short_term_memory)}")
    
    # Assertions
    assert len(domain_ctx.short_term_memory) == 1
    assert len(domain_ctx.q_table) > 0 # Should learn something
    
    # Check Logic Correctness:
    # 1. Base rate MUST decay
    assert domain_ctx.base_exploration_rate < 0.8
    # 2. Current rate accounts for boost (0.8*0.995 + 0.5*0.5 ~ 1.046)
    assert domain_ctx.current_exploration_rate > 0.8 
    
    print(">>> BULK MIGRATION TEST PASSED! <<<")

if __name__ == "__main__":
    test_bulk_migration()
