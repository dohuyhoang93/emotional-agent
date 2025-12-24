# Chương 04: Phân tích & Phản biện (Critical Analysis) - Revised

---

## 4.1 So sánh Chiến lược: Không phải thay thế, mà là Bổ khuyết

Khác với các tài liệu cũ thường phủ nhận Deep Learning (DL), chúng ta thừa nhận sức mạnh của DL hiện đại (Transformers, Continual Learning).

| Tiêu chí | Modern DL (Sparse Transformers) | Computational Hebbian SNN (Our Approach) |
| :--- | :--- | :--- |
| **Mục tiêu** | Hiểu biết sâu, Tổng quát hóa, Big Data. | **Thích nghi sinh tồn, Phản xạ nhanh, Small Data.** |
| **Kiến trúc** | Global Attention ($O(N^2)$ hoặc $O(N \log N)$). | **Local Causality ($O(K)$).** |
| **Học tập** | Offline / Batch / Continual Learning (vẫn phức tạp). | **Always-on Online Learning (Tự nhiên).** |
| **Vai trò** | **Cortex (Vỏ não cấp cao).** | **Limbic System (Hệ viền/Hạch hạnh nhân).** |

**Kết luận:** Chúng ta không xây dựng một "Bộ não tốt hơn Transformer". Chúng ta xây dựng phần "Hệ viền" (Limbic System) mà Transformer còn thiếu để trở thành một thực thể sống thực sự.

## 4.2 Các Vấn đề mở rộng & Giải pháp

### 4.2.1 Bài toán Gán tín dụng tầm xa (Long-term Credit Assignment)
*   *Phản biện:* STDP thông thường chỉ nhớ được 20ms. Làm sao con chuột nhớ hành động cách đây 1 phút?
*   *Giải pháp:* **Synaptic Tagging & Capture.** Sử dụng biến `slow_trace` phân rã cực chậm (phút/giờ) để "đánh dấu" các synapse tiềm năng. Khi Reward đến muộn, nó sẽ kích hoạt các Tag này.

### 4.2.2 Bài toán Giao tiếp Đa chiều (High-Bandwidth Communication)
*   *Phản biện:* Giao tiếp bằng 1 con số vô hướng là quá nghèo nàn.
*   *Giải pháp:* **Population Coding & Top-down Modulation.**
    *   SNN nói với RL bằng vector mật độ cao.
    *   RL nói với SNN bằng tín hiệu điều biến (ức chế/kích thích) cụ thể từng vùng.

## 4.3 Đánh giá lại Rủi ro
Sự phức tạp của hệ thống đã tăng lên đáng kể với việc thêm Synaptic Tagging và Top-down Control.
*   **Rủi ro mới:** Quá tải tham số (Parameter Explosion). Việc tinh chỉnh các hằng số thời gian (`tau_fast`, `tau_slow`) sẽ khó khăn hơn.
*   **Biện pháp:** Sử dụng Meta-Learning (Genetic Algorithm đơn giản) để tìm bộ tham số tối ưu cho từng vùng não, thay vì chỉnh tay.
