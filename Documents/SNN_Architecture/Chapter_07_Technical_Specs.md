# Chương 07: Đặc tả Kỹ thuật (Technical Specifications) - Expanded

Chương này cung cấp hướng dẫn cài đặt chi tiết để chuyển hóa lý thuyết thành mã nguồn Python hiệu năng cao.

---

## 7.1 Cấu trúc Dữ liệu (In-Memory Database / ECS)

Chúng ta không dùng Object. Chúng ta dùng `Arrow` (Columnar) hoặc `Dictionary of Arrays` để tối ưu hóa Cache CPU. Ở phiên bản Python prototyp, ta dùng `Dataclass` + `Dict` làm Database giả lập.

```python
from dataclasses import dataclass
from typing import Dict, List, Set

# Loại dữ liệu ID (Alias cho int để rõ nghĩa)
NeuronID = int
SynapseID = int

@dataclass
class NeuronRecord:
    id: NeuronID
    layer_idx: int          # 0: Input, 1: Hidden, 2: Output
    potential: float        # Điện thế màng hiện tại (V)
    threshold: float        # Ngưỡng kích hoạt thích nghi (V_th)
    last_spike_time: int    # Thời gian bắn gần nhất (milisecond)
    spike_count: int        # Để tính Homeostasis
    
@dataclass
class SynapseRecord:
    id: SynapseID
    source_id: NeuronID
    target_id: NeuronID
    weight: float           # Trọng số nối (w)
    delay_ms: int           # Độ trễ truyền dẫn (Delta_t)
    last_active_time: int   # Thời điểm kích hoạt gần nhất (để tính STDP trace)

@dataclass
class SpikeEvent:
    trigger_time: int       # Thời điểm sự kiện sẽ tác động (arrival time)
    target_id: NeuronID
    signal_strength: float  # Giá trị tín hiệu (+w hoặc -w)

class SNNDatabase:
    neurons: Dict[NeuronID, NeuronRecord]
    synapses: Dict[SynapseID, SynapseRecord]
    # Index ngược để tìm nhanh các synapse xuất phát từ 1 neuron
    # Key: source_id, Value: List[SynapseID]
    outgoing_synapses: Dict[NeuronID, List[SynapseID]]
    # Index ngược để tìm các synapse đi vào 1 neuron (cho STDP ngược)
    incoming_synapses: Dict[NeuronID, List[SynapseID]]
    
    event_queue: List[SpikeEvent] # Nên dùng heapq (Priority Queue) để pop min time
```

## 7.2 Quy trình Xử lý (Process Workflow)

Sử dụng vòng lặp sự kiện chính xác đến mili-giây (ms).

### Process 1: Tích hợp Sự kiện (Integration Phase)

```python
def process_integrate(db: SNNDatabase, current_time: int):
    # 1. Lấy tất cả sự kiện đã đến giờ (trigger_time <= current_time)
    while db.event_queue and db.event_queue[0].trigger_time <= current_time:
        event = heapq.heappop(db.event_queue)
        
        # 2. Cộng điện thế vào neuron đích
        neuron = db.neurons[event.target_id]
        
        # Chỉ cộng nếu neuron chưa ra khỏi thời kỳ trơ (refractory check)
        if current_time - neuron.last_spike_time > REFRACTORY_PERIOD:
             neuron.potential += event.signal_strength
            
        # Rò rỉ điện thế (Leak) - có thể làm ở bước riêng hoặc lồng vào đây
        decay = calculate_leak(current_time, neuron.last_update_time)
        neuron.potential *= decay
```

### Process 2: Kích hoạt & Lan truyền (Fire & Propagate Phase)

```python
def process_fire(db: SNNDatabase, current_time: int) -> List[NeuronID]:
    spiked_neurons = []
    
    for neuron_id, neuron in db.neurons.items():
        # Kiểm tra ngưỡng (Chỉ quét các neuron active - Optimization needed here)
        if neuron.potential >= neuron.threshold:
            # FIRE!
            spiked_neurons.append(neuron_id)
            neuron.potential = 0.0  # Reset
            neuron.last_spike_time = current_time
            neuron.spike_count += 1
            
            # Homeostasis: Tăng ngưỡng nhẹ
            neuron.threshold += THRESHOLD_ADAPT_RATE
            
            # Lan truyền (Propagate)
            # Lấy tất cả các dây nối đi RA từ neuron này
            synapse_ids = db.outgoing_synapses[neuron_id]
            for syn_id in synapse_ids:
                syn = db.synapses[syn_id]
                
                # Tạo sự kiện mới trong tương lai
                new_event = SpikeEvent(
                    trigger_time = current_time + syn.delay_ms,
                    target_id = syn.target_id,
                    signal_strength = syn.weight
                )
                heapq.heappush(db.event_queue, new_event)
                
                # Cập nhật thời gian hoạt động của synapse (cho STDP)
                syn.last_active_time = current_time
                
    return spiked_neurons
```

### Process 3: Học Tập (Learning Phase - R-STDP)

```python
def process_learn(db: SNNDatabase, spiked_neurons: List[NeuronID], reward: float):
    if reward == 0: return # Không có gì để học nếu không có feedback
    
    for nid in spiked_neurons:
        # LTP (Long-term Potentiation): Tăng trọng số các dây ĐI VÀO neuron này
        # (Vì chúng nó vừa giúp neuron này bắn -> Chúng có công)
        incoming_syn_ids = db.incoming_synapses[nid]
        for syn_id in incoming_syn_ids:
            syn = db.synapses[syn_id]
            
            # Tính Delta t = Thời gian đích bắn - Thời gian nguồn kích hoạt
            delta_t = current_time - syn.last_active_time
            
            # Nếu nguồn vừa mới kích hoạt ngay trước đó (trong cửa sổ STDP)
            if 0 < delta_t < STDP_WINDOW:
                # Cập nhật trọng số theo Reward
                change = LEARNING_RATE * reward * math.exp(-delta_t / TAU)
                syn.weight += change
                syn.weight = clamp(syn.weight, MIN_W, MAX_W)
```

## 7.3 Tối ưu hóa Hiệu năng (Performance Tuning)

1.  **Spatial Hashing:** Để tìm synapse nhanh, Index `outgoing_synapses` là bắt buộc.
2.  **Lazy Leak:** Đừng trừ `potential * 0.9` cho mọi neuron ở mỗi bước giây. Chỉ trừ khi neuron đó *được truy cập* (nhận sự kiện mới).
    *   `V_new = V_old * decay^(current_time - last_update_time) + input`
    *   Đây là kỹ thuật quan trọng nhất để đạt O(Active) thay vì O(Total).
