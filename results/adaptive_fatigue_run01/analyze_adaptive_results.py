import pandas as pd
import os

# Define path to CSV
csv_path = 'ComplexMaze_AdaptiveFatigue_Run01/run_1.csv'
output_file = 'analysis_output.txt'

def analyze_run(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    df = pd.read_csv(file_path)
    
    # Overall stats
    total_episodes = len(df)
    success_rate = df['success'].mean() * 100
    avg_steps_success = df[df['success'] == True]['steps'].mean()
    avg_reward = df['total_reward'].mean()
    avg_exploration = df['final_exploration_rate'].mean()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"--- ANALYSIS REPORT ---\n")
        f.write(f"Total Episodes: {total_episodes}\n")
        f.write(f"Overall Success Rate: {success_rate:.2f}%\n")
        f.write(f"Avg Steps (Success): {avg_steps_success:.2f}\n")
        f.write(f"Avg Total Reward: {avg_reward:.2f}\n")
        f.write(f"Avg Exploration Rate: {avg_exploration:.4f}\n\n")
        
        f.write("--- TREND ANALYSIS (Per 1000 Episodes) ---\n")
        # Chunk analysis
        chunk_size = 1000
        for i in range(0, total_episodes, chunk_size):
            chunk = df.iloc[i:i+chunk_size]
            chunk_success = chunk['success'].mean() * 100
            chunk_steps = chunk[chunk['success'] == True]['steps'].mean()
            chunk_reward = chunk['total_reward'].mean()
            chunk_exploration = chunk['final_exploration_rate'].mean()
            
            f.write(f"Episodes {i}-{i+chunk_size}:\n")
            f.write(f"  Success Rate: {chunk_success:.2f}%\n")
            f.write(f"  Avg Steps: {chunk_steps:.2f}\n")
            f.write(f"  Avg Reward: {chunk_reward:.2f}\n")
            f.write(f"  Avg Exploration: {chunk_exploration:.4f}\n")

if __name__ == "__main__":
    analyze_run(csv_path)
    print(f"Analysis complete. Results saved to {output_file}")
