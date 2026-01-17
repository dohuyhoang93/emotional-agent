
import re
from datetime import datetime
import statistics

def calculate_speed(log_path):
    print(f"Analyzing log: {log_path}")
    
    # Regex to match: 14:19:35 - INFO - Episode   0: agents=5 R=-11.91
    pattern = re.compile(r'(\d{2}:\d{2}:\d{2}) - INFO - Episode\s+(\d+):')
    
    timestamps = []
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                time_str = match.group(1)
                episode_num = int(match.group(2))
                # Assuming current day, only care about time difference
                t = datetime.strptime(time_str, "%H:%M:%S")
                timestamps.append((episode_num, t))
    
    if len(timestamps) < 2:
        print("Not enough episode logs found to calculate speed.")
        return

    intervals = []
    for i in range(1, len(timestamps)):
        prev = timestamps[i-1]
        curr = timestamps[i]
        
        diff = (curr[1] - prev[1]).total_seconds()
        
        # Handle day wrap around (unlikely for sanity check but good practice)
        if diff < 0:
            diff += 24 * 3600
            
        intervals.append(diff)
        print(f"Ep {prev[0]} -> Ep {curr[0]}: {diff:.2f}s")

    avg_speed = statistics.mean(intervals)
    median_speed = statistics.median(intervals)
    
    print("-" * 30)
    print(f"Total Episodes Analyzed: {len(timestamps)}")
    print(f"Average Time per Episode: {avg_speed:.2f} seconds")
    print(f"Median Time per Episode:  {median_speed:.2f} seconds")
    print("-" * 30)
    
    baseline = 12.0
    improvement = (baseline - avg_speed) / baseline * 100
    print(f"Baseline (Theus v2):      {baseline:.2f} seconds")
    print(f"Improvement:              {improvement:.1f}% faster")

if __name__ == "__main__":
    calculate_speed("full_log.txt")
