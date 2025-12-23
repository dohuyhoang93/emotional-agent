# Chương 05: Cơ chế Nâng cao & Giải thuật (Advanced Mechanics & Algorithms) - Expanded

Chương này chuyển hóa các khái niệm trừu tượng (Delay, Inhibition) thành **Cấu trúc dữ liệu cụ thể** để code.

---

## 5.1 Giải thuật Quản lý Sự kiện Trễ (Delay Implementation)

Làm sao quản lý hàng triệu sự kiện trễ mà không tốn O(N) để insert?

### Cấu trúc: Circular Time Buckets (Vòng tròn Thời gian)
Thay vì dùng `PriorityQueue` (Heap) tốn $O(\log N)$, ta dùng một mảng vòng tròn (Circular Buffer) đại diện cho thời gian tương lai.

*   **Thời gian tối đa:** $T_{max} = 1000ms$ (1 giây).
*   **Buckets:** Mảng `buckets` có kích thước 1000. `buckets[i]` chứa danh sách các sự kiện sẽ xảy ra tại $ms = i$.
*   **Con trỏ:** `current_tick` chạy từ 0 đến 999.

```python
class TemporalEngine:
    def __init__(self, max_delay=1000):
        self.buckets = [[] for _ in range(max_delay)]
        self.current_tick = 0
        self.max_delay = max_delay

    def schedule_event(self, event, delay_ms):
        # Tính vị trí bucket tương lai (Modulo arithmetic)
        target_tick = (self.current_tick + delay_ms) % self.max_delay
        self.buckets[target_tick].append(event) # O(1)

    def process_current_step(self):
        # Lấy tất cả sự kiện O(1)
        events = self.buckets[self.current_tick]
        self.buckets[self.current_tick] = [] # Clear bucket
        
        # Xử lý events...
        
        # Nhích đồng hồ
        self.current_tick = (self.current_tick + 1) % self.max_delay
```
*   **Hiệu năng:** Constant Time $O(1)$ cho cả việc thêm sự kiện và lấy sự kiện. Nhanh hơn Heap rất nhiều.

## 5.2 Giải thuật Ức chế Bên (Lateral Inhibition)

Làm sao tìm "hàng xóm" của một neuron để ức chế trong O(1)?

### Cấu trúc: Spatial Partitioning (Phân không gian)
Giả sử neuron có tọa độ 3D hoặc 2D ảo `(x, y)`. Ta chia không gian thành lưới (Grid).

*   **Grid Size:** Chia không gian thành các ô $10 \times 10$.
*   **Lookup Table:** `grid[(x,y)] -> List[NeuronID]`.

**Thuật toán Local WTA:**
1.  Khi neuron A tại $(x_A, y_A)$ bắn xung.
2.  Tra cứu `grid[(x_A, y_A)]` để lấy danh sách hàng xóm.
3.  Gửi tín hiệu ức chế ngay lập tức (-50mV) tới hàng xóm.
4.  Để tránh ức chế bản thân, kiểm tra `if neighbor_id != self_id`.

```python
def process_lateral_inhibition_fast(db, spiked_neurons):
    for nid in spiked_neurons:
        coords = db.neurons[nid].coords
        # Lấy danh sách hàng xóm từ cache O(1)
        neighbors = db.spatial_grid.get_neighbors(coords)
        
        for neighbor_id in neighbors:
            if neighbor_id == nid: continue
            # Dập tắt ngay lập tức (Hard Inhibition)
            db.neurons[neighbor_id].potential = 0 
            # Đi vào trạng thái trơ cưỡng bức
            db.neurons[neighbor_id].refractory_end = current_time + 10
```

## 5.3 Giải thuật Sinh trưởng (Neurogenesis Strategy)

Chúng ta dùng chiến lược **"Tiêm ngẫu nhiên, Chọn lọc tự nhiên"**.

### Quy trình:
1.  **Trigger:** Khi `Average_Reward_Last_100_Steps` giảm đột ngột (Agent đang gặp khó khăn/Ngạc nhiên).
2.  **Injection:** Sinh ra 100 neuron mới.
    *   **Vị trí:** Ngẫu nhiên hoặc gần các neuron đang hoạt động mạnh (nơi có vấn đề).
    *   **Kết nối Input:** Kết nối ngẫu nhiên tới 10% neuron lớp trước.
    *   **Kết nối Output:** Kết nối ngẫu nhiên tới 10% neuron lớp sau.
    *   **Trọng số:** Khởi tạo rất nhỏ (gần 0) để không gây nhiễu mạng ngay lập tức ("Silent Synapses").
3.  **Maturation (Trưởng thành):** Trong 1000 bước đầu, neuron mới có tính dẻo (Learning Rate) cao gấp 10 lần.
4.  **Selection:** Sau thời gian trưởng thành, nếu `utility_score` vẫn thấp -> Xóa.

Điều này đảm bảo mạng có khả năng "Thử nghiệm giả thuyết mới" mà không phá vỡ cấu trúc cũ đang chạy tốt.
