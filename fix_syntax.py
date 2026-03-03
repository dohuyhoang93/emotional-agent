import os
import glob

processes_dir = os.path.join("src", "orchestrator", "processes")
files = glob.glob(os.path.join(processes_dir, "*.py"))

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix double commas
    content = content.replace("],,", "],")
    
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Fixed {len(files)} process files.")
