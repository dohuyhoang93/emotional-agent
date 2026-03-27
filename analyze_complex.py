import json

filepath = 'results/multi_agent_complex_maze/metrics.jsonl'
sessions = []
current_session = []

try:
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get('episode') == 0 and current_session:
                    sessions.append(current_session)
                    current_session = []
                current_session.append(data)
            except: pass
        if current_session: sessions.append(current_session)
        
    if sessions:
        last = sessions[-1]
        print(f"Total Episodes in Current Run: {len(last)}")
        
        last_100 = last[-100:] if len(last) > 100 else last
        r = [float(d['metrics']['avg_reward']) for d in last_100 if 'avg_reward' in d['metrics']]
        s = [float(d['metrics']['success_rate']) for d in last_100 if 'success_rate' in d['metrics']]
        
        if r:
            avg_r = sum(r)/len(r)
            avg_s = sum(s)/len(s)
            print(f"Last 100 Ep Avg Reward: {avg_r:.4f}")
            print(f"Last 100 Ep Success Rate: {avg_s*100:.1f}%")
            print(f"Last Ep Epsilon: {last[-1]['metrics'].get('epsilon')}")
            print(f"Last Ep Avg Q-Predicted: {last[-1]['metrics'].get('avg_q_predicted')}")
        else: print("No metric data in last 100")
            
except Exception as e:
    print(f"Error reading file: {e}")
