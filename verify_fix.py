import os
import pandas as pd
from main import run_simulation

def verify_fix():
    output_path = "results/verification/verify_fix.csv"
    num_episodes = 20
    
    # Run simulation with 20 episodes
    # If fix works, Finisher activates at 0.9 * 20 = 18
    # If fix fails, Finisher activates at 0.9 * 100 = 90 (default) -> won't activate
    # Wait, if fix fails, total_episodes=100. 0.9*100=90.
    # Current episode will be 1..20.
    # 20 < 90. So Finisher won't activate in EITHER case if I use 20 episodes.
    
    # I need a number where:
    # If fixed: threshold = 0.9 * N. Current > threshold.
    # If broken: threshold = 90. Current < 90.
    
    # Example: N=20. Threshold=18.
    # Check episode 19.
    # If fixed: 19 > 18 -> Finisher ON (Exploration=0).
    # If broken: 19 < 90 -> Finisher OFF (Exploration>0).
    
    # So logic is reversed:
    # Fixed -> Exploration = 0 at ep 19.
    # Broken -> Exploration > 0 at ep 19.
    print(f"Running simulation with {num_episodes} episodes...")
    run_simulation(num_episodes, output_path, {}, seed=42, log_level="silent")
    
    if not os.path.exists(output_path):
        print("Error: Output file not found.")
        return

    df = pd.read_csv(output_path)
    
    # Check episode 19
    # If fixed: 19 > 0.9*20=18 -> Finisher ON -> Exploration = 0.0
    # If broken: 19 < 0.9*100=90 -> Finisher OFF -> Exploration > 0.0
    row_check = df[df['episode'] == 19]
    
    if row_check.empty:
        print("Error: Episode 19 not found in results.")
        return

    exploration_rate = row_check['final_exploration_rate'].values[0]
    print(f"Exploration rate at episode 19: {exploration_rate}")
    
    if exploration_rate == 0.0:
        print("SUCCESS: Exploration rate is 0 at episode 19. Finisher activated correctly (based on N=20).")
    else:
        print("FAILURE: Exploration rate is > 0 at episode 19. Finisher did NOT activate (it thinks total is 100).")

if __name__ == "__main__":
    verify_fix()
