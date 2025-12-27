"""
Sleep Cycle Manager
===================
Orchestrates the Biological Sleep phase for all agents.

Author: Theus Agent
Date: 2025-12-27
"""
from src.logger import log

def run_sleep_cycle(coordinator, duration: int = 100):
    """
    Execute sleep cycle for all agents.
    
    Args:
        coordinator: MultiAgentCoordinator
        duration: Number of internal simulation steps
    """
    log(None, "info", f"💤 ENTERING SLEEP CYCLE (Duration: {duration} steps)...")
    
    # 1. Enter Sleep Mode
    for agent in coordinator.agents:
        if hasattr(agent, 'start_sleep'):
            agent.start_sleep()
            
    # 2. Dream Loop
    for t in range(duration):
        # Optional: Log progress
        # if t % 20 == 0: print(f"  ... Dream Step {t}")
        
        for agent in coordinator.agents:
            if hasattr(agent, 'dream_step'):
                agent.dream_step(t)
                
    # 3. Wake Up
    for agent in coordinator.agents:
        if hasattr(agent, 'wake_up'):
            agent.wake_up()
            
    log(None, "info", "🌅 WAKING UP! Sleep cycle complete.")
