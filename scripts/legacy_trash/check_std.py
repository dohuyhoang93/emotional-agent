import json

try:
    data = []
    with open('results/Optimization_Sanity_Check_checkpoints/metrics.jsonl', 'r') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except:
                pass

    if not data:
        print("No data found")
        exit(1)

    print(f"Total episodes: {len(data)}")
    for d in data[-5:]:
        ep = d.get('episode')
        metrics = d.get('metrics', {})
        std = metrics.get('std_threshold', 0.0)
        avg = metrics.get('avg_threshold', 0.0)
        success = metrics.get('success', False)
        print(f"Ep {ep}: std={std:.5f}, avg={avg:.5f}, success={success}")
        
except Exception as e:
    print(f"Error: {e}")
