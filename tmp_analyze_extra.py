import json
import statistics

filepath = r"c:\Users\dohoang\projects\EmotionAgent\results\multi_agent_complex_maze\metrics.jsonl"

try:
    with open(filepath, "r") as f:
        lines = f.readlines()
        
    last_19 = lines[-19:]
    
    eps = []
    mems = []
    spikes = []
    epsilons = []
    maturities = []
    
    for line in last_19:
        d = json.loads(line)
        m = d.get("metrics", {})
        eps.append(d.get("episode"))
        mems.append(m.get("debug_process_memory_mb", 0))
        spikes.append(m.get("debug_spike_queue_size", 0))
        epsilons.append(m.get("epsilon", 0))
        maturities.append(m.get("maturity", 0))
        
    print(f"=== CÁC CHỈ SỐ KHÁC TỪ TẬP {eps[0]} ĐẾN {eps[-1]} ===")
    print(f"Memory (MB): Trung bình {statistics.mean(mems):.2f} (Min: {min(mems):.2f}, Max: {max(mems):.2f})")
    print(f"Spike Queue Size: Trung bình {statistics.mean(spikes):.2f} (Min: {min(spikes)}, Max: {max(spikes)})")
    print(f"Epsilon (khám phá): Giảm từ {epsilons[0]:.4f} xuống {epsilons[-1]:.4f}")
    print(f"Maturity (trưởng thành): Tăng từ {maturities[0]:.2f} lên {maturities[-1]:.2f}")
    
except Exception as e:
    print(f"Lỗi: {e}")
