# Hebbian Learning
---
Tính đến thời điểm tháng 1/2025, lĩnh vực **Hebbian Learning (Học Hebbian)** trong **Spiking Neural Networks (SNN)** đang trải qua một giai đoạn chuyển mình mạnh mẽ. Các nghiên cứu không còn chỉ dừng lại ở quy tắc STDP (Spike-Timing-Dependent Plasticity) cổ điển mà đang tập trung vào việc làm sao để quy tắc học cục bộ này có thể huấn luyện được các mạng sâu (Deep SNNs) và ứng dụng trên phần cứng tiết kiệm năng lượng.

Dưới đây là tổng hợp các xu hướng và công trình nghiên cứu mới nhất, nổi bật nhất từ năm 2023 đến đầu năm 2025:

### 1. Kết hợp Hebbian Learning với Backpropagation (Hybrid Learning)
Đây là xu hướng mạnh mẽ nhất hiện nay. Các nhà nghiên cứu nhận ra rằng STDP thuần túy khó đạt độ chính xác cao trên các tập dữ liệu phức tạp (như ImageNet), trong khi Backpropagation (BP) lại tốn kém năng lượng.
*   **Surrogate Gradient + Hebbian:** Các công trình mới đề xuất sử dụng Hebbian learning để khởi tạo trọng số (pre-training) hoặc để tinh chỉnh cục bộ (fine-tuning) sau khi đã huấn luyện bằng Surrogate Gradient.
*   **Local Error Propagation:** Thay vì truyền lỗi ngược toàn cục (global backprop), các nghiên cứu mới (ví dụ: các biến thể của *e-prop* hoặc *DECOLLE*) sử dụng các quy tắc giống Hebbian để xấp xỉ gradient tại mỗi nơ-ron, giúp việc học có thể diễn ra "online" và cục bộ.

### 2. Quy tắc 3 yếu tố (Three-Factor Hebbian Learning / Reward-Modulated STDP)
Mô hình Hebbian truyền thống là "2 yếu tố" (pre-synaptic và post-synaptic). Các nghiên cứu mới nhất tập trung vào **yếu tố thứ 3** (như dopamine trong não bộ), đóng vai trò là tín hiệu thưởng (reward) hoặc tín hiệu lỗi toàn cục.
*   **Reinforcement Learning trong SNN:** Sử dụng quy tắc 3 yếu tố để huấn luyện SNN chơi game hoặc điều khiển robot. Các công trình gần đây đã chứng minh R-STDP (Reward-modulated STDP) có thể giải quyết các bài toán điều khiển liên tục với năng lượng cực thấp.
*   **Ứng dụng:** Điều khiển cánh tay robot thích nghi, drone tự hành tránh vật cản sử dụng chip Neuromorphic (như Intel Loihi 2).

### 3. Học liên tục (Continual Learning) và Chống lãng quên (Catastrophic Forgetting)
SNN với Hebbian Learning có ưu thế tự nhiên trong việc học liên tục (học nhiệm vụ mới mà không quên nhiệm vụ cũ) so với ANN truyền thống.
*   **Metaplasticity:** Các công trình năm 2023-2024 tập trung vào việc mô phỏng "độ dẻo của độ dẻo" (plasticity of plasticity). Tức là khả năng thay đổi tốc độ học của khớp thần kinh dựa trên lịch sử hoạt động, giúp bảo vệ các ký ức quan trọng.
*   **Sleep-like consolidation:** Một số nghiên cứu mô phỏng giai đoạn "ngủ" trong SNN, sử dụng Hebbian learning không giám sát để củng cố các trọng số quan trọng, giúp mạng ổn định hơn.

### 4. Triển khai trên phần cứng Memristor và Neuromorphic
Hebbian learning là chìa khóa cho việc học "On-chip" (học ngay trên chip) vì nó chỉ cần thông tin cục bộ.
*   **Memristive SNNs:** Các công trình mới nhất tập trung vào việc ánh xạ trực tiếp quy tắc STDP lên đặc tính vật lý của **Memristor** (ReRAM, PCRAM). Khi xung điện đi qua, điện trở thay đổi tự nhiên theo quy tắc Hebbian mà không cần mạch điều khiển phức tạp.
*   **Hiệu quả năng lượng:** Các thiết kế chip mới (2024) chứng minh khả năng học on-chip với mức tiêu thụ năng lượng chỉ vài nanojoules cho mỗi lần cập nhật trọng số.

### 5. Các biến thể hiện đại của STDP
Không chỉ là STDP cơ bản, các nhà nghiên cứu đang đề xuất các hàm toán học phức tạp hơn để mô phỏng sinh học tốt hơn và tăng hiệu suất:
*   **Triplet-STDP:** Xem xét bộ 3 xung (thay vì 2) để xác định trọng số, giúp mô hình học được các mẫu tần số cao tốt hơn.
*   **Voltage-dependent Synaptic Plasticity:** Cập nhật trọng số dựa trên điện thế màng (emembrane potential) tại thời điểm hiện tại thay vì chỉ dựa vào thời điểm phát xung. Điều này giúp giải quyết vấn đề "dead neurons" (nơ-ron không bao giờ phát xung nên không bao giờ học).

### Các nhóm nghiên cứu và dự án tiêu biểu (cập nhật đến 2025)
Nếu bạn muốn tìm đọc các paper cụ thể, hãy tìm kiếm các tác giả và từ khóa từ các nhóm sau:
1.  **ETH Zurich (Nhóm của Giacomo Indiveri):** Chuyên về mạch neuromorphic analog và các quy tắc học lấy cảm hứng sinh học (bio-inspired learning rules).
2.  **TU Graz (Nhóm của Wolfgang Maass):** Tác giả của *e-prop*, tiếp tục phát triển các thuật toán học cục bộ mạnh mẽ cho SNN tái phát (Recurrent SNN).
3.  **Intel Labs (Dự án Loihi):** Các công trình về việc triển khai quy tắc học Hebbian tùy chỉnh trên chip Loihi 2.
4.  **Kaushik Roy (Purdue University):** Các nghiên cứu về STDP trên nền tảng phần cứng Spintronics và Memristors.

### Tổng kết từ khóa để tìm kiếm (Keywords for Search):
*   *Online learning in Deep SNNs*
*   *Three-factor rules SNN reinforcement learning*
*   *Memristive STDP implementation 2024*
*   *Surrogate gradient with local plasticity*
*   *Few-shot learning in SNN using Hebbian rules*

Xu hướng chung của giai đoạn này là **"Làm cho Hebbian Learning trở nên thực dụng"**: không chỉ mô phỏng não bộ cho vui, mà phải giải quyết được các bài toán AI hiện đại (nhận diện giọng nói, xử lý ảnh động event-camera) với chi phí năng lượng thấp hơn nhiều so với Deep Learning truyền thống.