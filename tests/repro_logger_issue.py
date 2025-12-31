import os
import json
import time
import threading
from datetime import datetime

# --- MOCK OF THE FLAWED LOGGER ---
# Copied from src/orchestrator/processes/p_initialize_experiment.py
class FlawedLogger:
    def __init__(self, output_dir, name="Logger"):
        self.name = name
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.metrics_file = os.path.join(output_dir, "metrics.json")
        self.episode_data = []
        
    def log_episode(self, episode, metrics):
        entry = {'episode': episode, 'metrics': metrics}
        self.episode_data.append(entry)
        
        # Simulate heavy data to exacerbate memory/IO
        # entry['payload'] = "x" * 1024 * 1024 # 1MB payload per episode to simulate accumulation
        
        start = time.time()
        # Append to file (or rewrite)
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.episode_data, f, indent=2)
        except Exception as e:
            print(f"{self.name}: Error logging metrics: {e}")
        
        duration = time.time() - start
        if duration > 0.1:
            print(f"{self.name}: Slow Write for Ep {episode}: {duration:.4f}s (List size: {len(self.episode_data)})")

# --- reproduction scenarios ---

def test_performance_hang():
    print("\n=== TEST 1: Performance Hang & Memory ===")
    logger = FlawedLogger("repro_logs/perf", "PerfLogger")
    
    print("Simulating 100 episodes...")
    for i in range(100):
        # Even with small payload, JSON dump of growing list gets slower
        logger.log_episode(i, {"score": i})
        if i % 20 == 0:
            print(f"Logged episode {i}")

def test_race_condition():
    print("\n=== TEST 2: Race Condition / Overwrite ===")
    # Simulate two runners (e.g., accidental restart or parallel agents) writing to same file
    # This explains "0, 1" -> "0, 2" if they share the file but NOT the memory state
    
    dir_path = "repro_logs/race"
    
    # Logger A starts and logs 0, 1
    loggerA = FlawedLogger(dir_path, "LoggerA")
    loggerB = FlawedLogger(dir_path, "LoggerB") # Re-initialized pointer to same file
    
    loggerA.log_episode(0, {"agent": "A"})
    loggerA.log_episode(1, {"agent": "A"})
    
    print("File content after Logger A (Ep 0, 1):")
    with open(os.path.join(dir_path, "metrics.json"), 'r') as f:
        print(f.read())
        
    # Logger B logs 0 (overwrite!), then 2 (skips 1?)
    # If Logger B was "reset" effectively
    print("\nLogger B writes Ep 0...")
    loggerB.log_episode(0, {"agent": "B"}) # Overwrites file with just [0]
    
    print("File content after Logger B (Ep 0):")
    with open(os.path.join(dir_path, "metrics.json"), 'r') as f:
        print(f.read())
        
    print("\nLogger B writes Ep 2...")
    loggerB.log_episode(2, {"agent": "B"}) # Overwrites file with [0, 2]
    
    print("File content after Logger B (Ep 2):")
    with open(os.path.join(dir_path, "metrics.json"), 'r') as f:
        print(f.read())
        
    print("\nResult: Episode 1 is completely LOST because Logger B didn't know about it and used 'w' mode.")

if __name__ == "__main__":
    test_performance_hang()
    test_race_condition()
