import json

filepath = r'c:\Users\dohoang\projects\EmotionAgent\results\multi_agent_complex_maze\metrics.jsonl'
success_count = 0
total_episodes = 0
successful_episodes = []

try:
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            try:
                data = json.loads(line)
                total_episodes += 1
                metrics = data.get('metrics', {})
                # Check if any agent succeeded
                if any(metrics.get('agent_success', [False])):
                    success_count += 1
                    successful_episodes.append(data.get('episode'))
            except Exception as e:
                # print(f"Error at line {i+1}: {e}")
                pass

    print(f"Total valid JSON lines: {total_episodes}")
    print(f"Actual Success Count: {success_count}")
    if successful_episodes:
        print(f"First 5 successful episodes: {successful_episodes[:5]}")
        print(f"Last 5 successful episodes: {successful_episodes[-5:]}")
except Exception as e:
    print(f"Error reading file: {e}")
