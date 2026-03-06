import json
from datetime import datetime
import statistics

filepath = r"c:\Users\dohoang\projects\EmotionAgent\results\multi_agent_complex_maze\metrics.jsonl"

try:
    with open(filepath, "r") as f:
        lines = f.readlines()
        
    last_20 = lines[-20:]
    
    eps = []
    timestamps = []
    
    for line in last_20:
        d = json.loads(line)
        eps.append(d.get("episode"))
        # Parse timestamp string like "2026-03-05T09:39:43.149831"
        ts_str = d.get("timestamp")
        timestamps.append(datetime.fromisoformat(ts_str))
        
    durations = []
    for i in range(1, len(timestamps)):
        diff = (timestamps[i] - timestamps[i-1]).total_seconds()
        durations.append(diff)
        
    print(f"=== THỜI GIAN THỰC THI (TẬP {eps[1]} ĐẾN {eps[-1]}) ===")
    print(f"Thời gian trung bình mỗi tập: {statistics.mean(durations):.2f} giây")
    print(f"Thời gian ngắn nhất: {min(durations):.2f} giây")
    print(f"Thời gian dài nhất: {max(durations):.2f} giây")
    print(f"Tổng thời gian cho 19 tập: {sum(durations):.2f} giây ({sum(durations)/60:.2f} phút)")
    
except Exception as e:
    print(f"Lỗi: {e}")
