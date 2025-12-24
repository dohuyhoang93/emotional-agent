# Chương 05: Cơ chế Nâng cao & Thông minh Tập thể (Advanced Mechanics & Collective Intelligence) - Consolidated

Chương này tổng hợp các cơ chế giúp SNN vượt qua giới hạn của mạng nơ-ron tĩnh, tích hợp cả cơ chế cá thể, tập thể và khả năng tưởng tượng.

---

## 5.1 Độ trễ Thời gian & Bộ nhớ (Temporal Delays)
*   **Nguyên lý:** "Delay là Bộ nhớ". Mạng lưu trữ thông tin về trình tự thời gian thông qua độ dài dây thần kinh.
*   **Cài đặt:** Sử dụng **Circular Time Buckets** ($O(1)$) thay vì Priority Queue để quản lý hàng triệu sự kiện trễ.

## 5.2 Ức chế Bên & Làm nét (Lateral Inhibition & WTA)
*   **Nguyên lý:** Các neuron cạnh tranh nhau để tạo ra tín hiệu sắc nét.
*   **Cài đặt:** Mỗi neuron có **Vùng ức chế cục bộ** (Local Inhibition Zone). Khi một neuron bắn, nó gửi tín hiệu ức chế (-V) tới hàng xóm.
*   **Tối ưu:** Sử dụng **Spatial Hashing** để tìm hàng xóm trong $O(1)$.

## 5.3 Thuyết Tiến hóa Thần kinh (Neural Darwinism)
*   **Cơ chế:**
    *   **Pruning (Đào thải):** Xóa các synapse có `utility_score` thấp (không tham gia dự báo đúng).
    *   **Neurogenesis (Sinh trưởng):** Khi Agent gặp "Ngạc nhiên" (Error cao), bơm thêm neuron mới vào vùng vỏ não tương ứng để tăng khả năng học.

---

## 5.4 Học Tập Xã hội & Thông minh Tập thể (Collective Intelligence)

### 5.4.1 Viral Learning (Học lây nhiễm)
*   Thay vì cộng trung bình trọng số, Agent trao đổi **"Gói Gen Synapse"** (các kết nối hiệu quả nhất).
*   Tri thức lan truyền như virus, nhưng Agent giữ hệ miễn dịch riêng.

### 5.4.2 Mỏ neo Văn hóa (Cultural Anchor)
*   **Ancestor Agent:** Một tác tử ảo học cực chậm, lưu giữ tri thức cốt lõi của quần thể.
*   Giúp các Agent trẻ "Reset" khi bị lạc lối (Catastrophic Forgeting).

### 5.4.3 Cộng hưởng Cảm xúc (Neural Resonance)
*   Tín hiệu cảm xúc của đám đông (Panic, Joy) tác động trực tiếp lên ngưỡng kích hoạt ($V_{th}$) của cá nhân.

---

## 5.5 Giải quyết Xung đột Kiến trúc (Conflict Resolutions)

### 5.5.1 Sandbox Ký sinh (The Parasitic Sandbox)
*   *Vấn đề:* Xung đột giữa Tri thức rắn (Internal Commitment) và Tri thức xã hội (External Viral).
*   *Giải pháp:* Gen ngoại lai chạy trong môi trường **Sandbox** với tư cách là **Shadow Synapse** (Bóng ma).
    *   Nó đưa ra dự đoán song song nhưng không điều khiển hành động.
    *   Chỉ khi Shadow Synapse chứng minh độ chính xác vượt trội liên tục, nó mới được phép "Đảo chính" (Revoke tri thức cũ).

### 5.5.2 Tách biệt Không - Thời gian (Spatiotemporal Decoupling)
*   *Vấn đề:* Kết hợp Vector Spike (Không gian) và STDP (Thời gian).
*   *Giải pháp:* Tách quá trình học làm 2 luồng:
    1.  **Spatial Learning (Unsupervised Clustering):** Xoay `Prototype Vector` để khớp với mẫu hình học của Input.
    2.  **Temporal Learning (Hebbian STDP):** Tăng giảm trọng số vô hướng $w$ dựa trên quan hệ nhân quả thời gian.

---

## 5.6 Vòng lặp Tưởng tượng (The Imagination Loop)

Cơ chế kỹ thuật để SNN tự mô phỏng và rút ra bài học chiến lược.

### 5.6.1 Quy trình Mô phỏng (Simulation Process)
1.  **Detach:** Ngắt kết nối Sensor Input.
2.  **Seed:** Kích hoạt một mẫu neuron ngẫu nhiên (hoặc dựa trên ký ức gần nhất) tại lớp Input.
3.  **Propagate:** Để mạng tự do lan truyền tín hiệu (theo các đường mòn synapse đã học).
4.  **Observe:** Quan sát kết quả tại lớp Cảm xúc (Emotion Layer).

### 5.6.2 Rút trích & Áp dụng Chiến thuật (Extraction & Modulation)
*   **Trường hợp 1: Nightmare (Tưởng tượng ra Cảnh Sợ hãi)**
    *   Kết quả: Neuron `FEAR` bắn mạnh.
    *   **Hành động:** Truy vết ngược (Backtrace) xem neuron nào đã kích hoạt FEAR? Gọi là `Neo_Pre_Fear`.
    *   **Chiến thuật:** Tạo một liên kết ức chế mạnh (Strong Inhibition) từ `Neo_Pre_Fear` tới `Action_Go`.
    *   *Hiệu quả:* Lần sau khi thức, nếu `Neo_Pre_Fear` kích hoạt (dấu hiệu báo trước), nó sẽ tự động khóa hành động nguy hiểm lại.

*   **Trường hợp 2: Fantasy (Tưởng tượng ra Phần thưởng)**
    *   Kết quả: Neuron `JOY` bắn mạnh.
    *   **Hành động:** Xác định `Neo_Pre_Joy`.
    *   **Chiến thuật:** Tăng độ nhạy (Boost Base Threshold) cho `Neo_Pre_Joy`.
    *   *Hiệu quả:* Agent trở nên nhạy bén hơn trong việc săn tìm cơ hội này.

Đây chính là cơ chế **"Học trong Mơ" (Dream Learning)**, giúp Agent thông minh hơn sau mỗi giấc ngủ.
