import json
filepath = r'C:\Users\dohoang\projects\EmotionAgent\results\multi_agent_complex_maze\metrics.jsonl'
with open(filepath, 'r') as f:
    for line in f:
        if line.strip():
            print(json.dumps(json.loads(line), indent=2))
            break
