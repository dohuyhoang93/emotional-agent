import os
import glob
import re

processes_dir = os.path.join("src", "orchestrator", "processes")
files = glob.glob(os.path.join(processes_dir, "*.py"))

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    # Find outputs=[],  # ... or outputs=[]
    # Replace with outputs=['domain', 'domain_ctx', 'global_ctx', 'domain.metrics', 'domain.metrics_history', 'domain.sig_episode_counter', 'domain.sig_max_episodes', 'domain.active_experiment_episode_idx', 'domain.active_experiment_idx'],
    
    new_outputs = "outputs=['domain', 'domain_ctx', 'global_ctx', 'domain.metrics', 'domain.metrics_history', 'domain.sig_episode_counter', 'domain.sig_max_episodes', 'domain.active_experiment_episode_idx', 'domain.active_experiment_idx'],"
    
    # We use regex to find outputs=\[.*?\]
    content = re.sub(r'outputs=\[([^\]]*)\]', new_outputs, content)
    
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Patched {len(files)} process files.")
