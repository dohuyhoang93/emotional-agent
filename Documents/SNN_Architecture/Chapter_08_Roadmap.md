# Chương 08: Lộ trình Triển khai Gia tăng (Incremental Roadmap) - Revised V2

*Phản hồi cho bản Phân tích Phản biện Lần 2 (Incremental Validation Strategy).*

Chúng ta từ bỏ chiến lược "Big Bang" (Làm tất cả cùng lúc). Thay vào đó, áp dụng chiến lược **"Crawl - Walk - Run"** để kiểm soát độ phức tạp.

---

## 8.1 Giai đoạn 1: MVM - The Scalar Core (Crawl)
**Mục tiêu:** Xác thực động lực học cơ bản của SNN mà không bị nhiễu bởi Vector hay Social.
*   **Neuron:** Scalar Spike (0/1).
*   **Learning:** Basic STDP (2-factor).
*   **Control:** Simple Homeostasis (Adaptive Threshold).
*   **Kiểm thử:**
    *   Cho chạy bài toán đơn giản (ví dụ: CartPole).
    *   Chứng minh mạng tự cân bằng được Firing Rate (không chết/động kinh).

## 8.2 Giai đoạn 2: The Vector Upgrade (Walk)
**Mục tiêu:** Nâng cấp khả năng biểu diễn ngữ nghĩa.
*   **Neuron:** Chuyển sang **Vector Spike** (16-dim).
*   **Learning:** Kích hoạt Spatiotemporal Decoupling (STDP cho $w$ + Clustering cho Prototype).
*   **Interface:** Kết nối với RL Agent qua Gated Integration.
*   **Kiểm thử:**
    *   Bài toán Maze (Cần nhớ đường đi).
    *   Đo lường sự cải thiện của RL khi có thêm SNN vector support.

## 8.3 Giai đoạn 3: The Social & Meta Layer (Run)
**Mục tiêu:** Kích hoạt trí tuệ tập thể và tự động hóa vận hành.
*   **Collective:** Viral Synapses + Cultural Anchor.
*   **Stability:** Meta-Homeostasis (PID Controllers cho tham số).
*   **Conflict:** Parasitic Sandbox.
*   **Kiểm thử:**
    *   Multi-agent Environment.
    *   Thử nghiệm "Echo Chamber": Bơm virus và xem hệ thống có tự lọc được không.

## 8.4 Giai đoạn 4: The Resilience & Imagination (Fly)
**Mục tiêu:** Đạt trạng thái Anti-fragile và khả năng dự báo.
*   **Resilience:** Periodic Resync + Brain Biopsy Tool.
*   **Imagination:** Dream Loop (Offline Learning).
*   **Protection:** Social Quarantine + Hysteria Dampener.
*   **Kiểm thử:**
    *   Stress Test: Tắt 30% neuron ngẫu nhiên.
    *   Chaos Engineering: Bơm nhiễu cực đại vào tín hiệu.

---

## 8.5 Kết luận

Việc chia nhỏ lộ trình giúp chúng ta gỡ rối bài toán "Gỡ lỗi phức tạp".
*   Nếu Giai đoạn 1 thất bại -> Sai ở STDP cơ bản.
*   Nếu Giai đoạn 2 thất bại -> Sai ở Vector Math.
*   Không bao giờ phải đoán lỗi đến từ đâu trong một mớ bòng bong.

**Tiếp theo:** Chúng ta sẽ bắt đầu code **Giai đoạn 1 (Scalar Core)** tại `src/core/snn_context.py`.
