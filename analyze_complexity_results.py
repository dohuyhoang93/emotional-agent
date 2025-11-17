import pandas as pd
import os
import numpy as np

def analyze_results(base_dir, optimal_steps):
    """
    Analyzes all run files to find the average episode number where the optimal path was first found.
    """
    experiment_types = ["Complex_NoCuriosity", "Complex_LowCuriosity", "Complex_MediumCuriosity"]
    results = {}

    for exp_type in experiment_types:
        exp_dir = os.path.join(base_dir, exp_type)
        if not os.path.isdir(exp_dir):
            print(f"Directory not found: {exp_dir}")
            continue
        
        convergence_episodes = []
        for i in range(1, 11):
            file_path = os.path.join(exp_dir, f"run_{i}.csv")
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                continue
            
            try:
                df = pd.read_csv(file_path)
                # Find the first occurrence of the optimal path
                optimal_runs = df[(df['success'] == True) & (df['steps'] == optimal_steps)]
                if not optimal_runs.empty:
                    first_occurrence_episode = optimal_runs['episode'].min()
                    convergence_episodes.append(first_occurrence_episode)
                else:
                    convergence_episodes.append(np.nan) # Append NaN if optimal path was never found
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
        
        results[exp_type] = convergence_episodes

    print("--- Convergence Analysis ---")
    for exp_type, episodes in results.items():
        valid_episodes = [e for e in episodes if not np.isnan(e)]
        if valid_episodes:
            average_convergence = np.mean(valid_episodes)
            print(f"  {exp_type}:")
            print(f"    - Average convergence episode: {average_convergence:.2f}")
            print(f"    - Individual run episodes: {valid_episodes}")
        else:
            print(f"  {exp_type}:")
            print("    - Optimal path never found in any run.")
    
    return results

if __name__ == "__main__":
    base_results_dir = "results/complex_curiosity_comparison"
    # The optimal path length is 8, as determined previously.
    optimal_path_length = 8
    analyze_results(base_results_dir, optimal_path_length)