import json
import statistics
import sys
from pathlib import Path

def analyze_metrics(file_path):
    episodes = []
    rewards = []
    success_rates = []
    epsilons = []
    maturities = []
    
    # SNN metrics
    firing_rates = []
    synapses = []
    spike_queues = []
    
    # MLP metrics
    losses = []
    q_preds = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line.strip())
                ep = data.get("episode", 0)
                m = data.get("metrics", {})
                
                episodes.append(ep)
                rewards.append(m.get("avg_reward", 0))
                success_rates.append(m.get("success_rate", 0))
                epsilons.append(m.get("epsilon", 0))
                maturities.append(m.get("maturity", 0))
                
                firing_rates.append(m.get("avg_firing_rate", 0))
                synapses.append(m.get("debug_total_synapses", 0))
                spike_queues.append(m.get("debug_spike_queue_size", 0))
                
                losses.append(m.get("neural_loss_avg", 0))
                q_preds.append(m.get("avg_q_predicted", 0))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return
        
    total_episodes = len(episodes)
    if total_episodes == 0:
        print("No data found.")
        return
        
    # Split into 4 quarters to see trends
    chunk_size = max(1, total_episodes // 4)
    
    print(f"--- PHÂN TÍCH HIỆU SUẤT TỔNG QUAN ({total_episodes} EPISODES) ---")
    print(f"Reward: Avg {statistics.mean(rewards):.2f}, Min {min(rewards):.2f}, Max {max(rewards):.2f}")
    if any(s > 0 for s in success_rates):
        print(f"Success Rate: Avg {statistics.mean(success_rates):.4f}, Max {max(success_rates):.4f}")
    else:
        print("Success Rate: 0.0 (Chưa đạt được mục tiêu nào)")
    
    print("\n--- XU HƯỚNG THEO THỜI GIAN (CHIA 4 GIAI ĐOẠN) ---")
    headers = ["Giai đoạn", "Reward", "Success", "Epsilon", "SNN Firing", "SNN Synapse", "MLP Loss", "MLP Q-Pred"]
    print(f"{headers[0]:<12} | {headers[1]:<8} | {headers[2]:<7} | {headers[3]:<7} | {headers[4]:<10} | {headers[5]:<11} | {headers[6]:<8} | {headers[7]:<10}")
    print("-" * 85)
    
    for i in range(4):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < 3 else total_episodes
        chunk_r = rewards[start:end]
        chunk_s = success_rates[start:end]
        chunk_eps = epsilons[start:end]
        chunk_fr = firing_rates[start:end]
        chunk_syn = synapses[start:end]
        chunk_loss = losses[start:end]
        chunk_q = q_preds[start:end]
        
        name = f"Q{i+1} ({start}-{end-1})"
        print(f"{name:<12} | "
              f"{statistics.mean(chunk_r):8.2f} | "
              f"{statistics.mean(chunk_s):7.4f} | "
              f"{statistics.mean(chunk_eps):7.4f} | "
              f"{statistics.mean(chunk_fr):10.4f} | "
              f"{int(statistics.mean(chunk_syn)):11d} | "
              f"{statistics.mean(chunk_loss):8.4f} | "
              f"{statistics.mean(chunk_q):10.4f}")
              
    print("\n--- PHÂN TÍCH SỨC KHỎE SNN ---")
    print(f"Firing Rate: Phân bổ từ {min(firing_rates):.4f} đến {max(firing_rates):.4f} (Trung bình: {statistics.mean(firing_rates):.4f})")
    print(f"Synapses: Dao động từ {min(synapses)} đến {max(synapses)} (Trung bình: {int(statistics.mean(synapses))})")
    print(f"Spike Queue: Tối đa {max(spike_queues)}, Trung bình {statistics.mean(spike_queues):.1f} (Cảnh báo nếu quá cao gây nghẽn)")
    
    stdev_fr = statistics.stdev(firing_rates) if len(firing_rates) > 1 else 0
    if stdev_fr < 0.01:
        print("Trạng thái SNN: Rất ổn định (độ lệch chuẩn firing rate thấp).")
    elif stdev_fr > 0.1:
        print("Trạng thái SNN: CẢNH BÁO Bất ổn định (firing rate dao động mạnh).")
    else:
        print("Trạng thái SNN: Tương đối ổn định.")
    
    print("\n--- PHÂN TÍCH SỨC KHỎE MLP ---")
    print(f"Loss: Trung bình {statistics.mean(losses):.4f}, Max {max(losses):.4f}")
    if max(losses) > 1000:
        print("  -> CẢNH BÁO: Xuất hiện spike trong loss đột biến!")
        
    print(f"Q-Predicted: Phân bổ từ {min(q_preds):.4f} đến {max(q_preds):.4f}")
    q_trend = statistics.mean(q_preds[-chunk_size:]) - statistics.mean(q_preds[:chunk_size])
    if q_trend > 0:
        print("  -> Q-Values có xu hướng tăng: Model đang học được giá trị/trạng thái tốt hơn.")
    else:
        print("  -> Q-Values có xu hướng giảm hoặc đi ngang: Model có thể chưa tìm được lối đi tốt/kẹt điểm mù.")

if __name__ == '__main__':
    metrics_path = Path(r"C:\Users\dohoang\projects\EmotionAgent\results\multi_agent_complex_maze\metrics.jsonl")
    analyze_metrics(metrics_path)
