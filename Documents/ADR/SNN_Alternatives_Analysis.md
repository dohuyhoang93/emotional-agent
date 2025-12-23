# Phân Tích So Sánh: Các Hướng Tiếp Cận Mô Hình Hóa Cảm Xúc

Tài liệu này phân tích các phương pháp thay thế để xây dựng trí tuệ và cảm xúc cho Agent, đối chiếu chúng với chiến lược **Computational Hebbian POP (Lập trình Hướng Quy trình)** mà chúng ta đã chọn.

---

## 1. Hệ Phái Thống Trị: Deep Learning Tiêu Chuẩn (ANN/MLP/Transformers)

Đây là cách tiếp cận "dòng chính" (được dùng trong DQN, PPO của DeepMind). Nó coi bộ não Agent là một hàm xấp xỉ liên tục, được tối ưu hóa bằng Lan truyền ngược (Backpropagation) toàn cục.

*   **Cơ chế:** `Vector Đầu vào -> Nhân Ma trận Đặc (Layers) -> Vector Đầu ra`.
*   **Huấn luyện:** Lan truyền ngược sai số toàn cục (Gradient Descent).

| Đặc điểm | ANN/Deep Learning | Hướng Tiếp Cận Của Chúng Ta (Hebbian POP) |
| :--- | :--- | :--- |
| **Độ chính xác (Benchmarks)** | **Vượt trội** trên dữ liệu tĩnh (ImageNet). Đỉnh cao về độ chính xác thô. | Thấp hơn về độ chính xác thô. Tốt hơn về khả năng *thích nghi*. |
| **Chi phí Huấn luyện** | **Khổng lồ.** Cần GPU, batch lớn, hàng triệu lượt chạy. Độ phức tạp $O(N^2)$. | **Tối thiểu.** Học online, cập nhật cục bộ. Chỉ neuron hoạt động mới tính toán. Độ phức tạp $O(N_{active})$. |
| **Sự Minh bạch** | **Hộp đen.** Không thể giải thích tại sao `weight[1024] = 0.5`. | **Nhân quả.** "Synapse A->B mạnh lên vì Sự kiện A xảy ra trước Sự kiện B 5 lần." |
| **Thích nghi (Online)** | **Kém.** Dễ bị "Quên thảm khốc" (Catastrophic Forgetting) nếu không có replay buffer lớn. | **Tự nhiên.** Được thiết kế để học liên tục cả đời mà không quên các quy luật cũ. |
| **Kiến trúc** | Các lớp (Layer) cứng nhắc. | Cấu trúc động (Neurogenesis - Tự sinh neuron). |

**Kết luận:** ANN tốt hơn để *giải một game cụ thể* một cách hoàn hảo. SNN tốt hơn để *sinh tồn và tiến hóa* trong một thế giới chưa biết và luôn thay đổi.

---

## 2. Hướng Tiếp Cận "Hàn Lâm": Surrogate Gradient Descent (BPTT)

Đây là xu hướng nghiên cứu hiện đại cho SNN (các thư viện như `snntorch`, `spikingjelly`). Nó cố gắng ép SNN hoạt động giống ANN để có thể dùng Backpropagation.

*   **Cơ chế:** Trải phẳng SNN theo thời gian (Time-steps) và dùng đạo hàm "giả" (Surrogate Gradient) để vượt qua tính chất không khả vi của xung điện.
*   **Huấn luyện:** Vẫn dùng Lan truyền ngược theo thời gian (BPTT).

| Đặc điểm | Surrogate Gradient SNN | Hướng Tiếp Cận Của Chúng Ta (Hebbian POP) |
| :--- | :--- | :--- |
| **Triết lý** | "Sửa SNN để nó chạy được với PyTorch." | "Dùng SNN cho những gì nó giỏi nhất (Luật Cục bộ)." |
| **Bộ nhớ** | **Cao.** Phải lưu lịch sử điện thế màng của *tất cả* neuron qua *tất cả* thời gian để tính đạo hàm. | **Thấp.** Chỉ lưu trạng thái hiện tại và thời gian xung nổ cuối cùng. Không cần bộ nhớ lịch sử. |
| **Tính Sinh học** | Thấp. Não bộ không thực hiện Backpropagation ngược thời gian. | Cao. Hebbian/STDP là cơ chế thực sự của sinh học. |
| **Phần cứng** | Tốt nhất cho GPU. | Tốt nhất cho Hệ thống Hướng Sự kiện (Event-driven) / Phần cứng Neuromorphic / CPU thường (với xử lý thưa). |

**Kết luận:** BPTT rất tuyệt để đạt điểm cao trên MNIST/CIFAR bằng SNN. Nhưng nó **KHÔNG PHÙ HỢP** với mục tiêu tạo ra Agent nhẹ, tự tiến hóa của chúng ta vì nó mang theo gánh nặng của thuật toán Backpropagation.

---

## 3. Hướng Tiếp Cận "Hỗn Loạn": Reservoir Computing (LSM/ESN)

Liquid State Machines (LSM) sử dụng một "nồi súp" các neuron kết nối ngẫu nhiên, hỗn loạn (Reservoir) và không bao giờ huấn luyện nồi súp này. Chỉ có một lớp đọc (readout layer) ở cuối là được huấn luyện.

*   **Cơ chế:** `Input -> [Nồi súp Xung ngẫu nhiên] -> Bộ phân loại Tuyến tính -> Output`.
*   **Huấn luyện:** Chỉ train lớp cuối cùng. "Bộ não" bên trong là cố định.

| Đặc điểm | Reservoir Computing | Hướng Tiếp Cận Của Chúng Ta (Hebbian POP) |
| :--- | :--- | :--- |
| **Tốc độ Train** | **Nhanh nhất.** Chỉ lớp cuối cùng học. | Nhanh (Học phân tán). |
| **Khả năng Kiểm soát** | **Bằng không.** Động lực bên trong là ngẫu nhiên. Hy vọng một mẫu hình hữu ích sẽ tự nảy sinh. | **Cao.** Chúng ta có thể thanh tra và xây dựng các quy luật nhân quả bên trong. |
| **Độ phức tạp** | Cài đặt cực dễ nếu chấp nhận "Hộp đen". | Phức tạp trong việc cài đặt các quy tắc dẻo (STDP) cụ thể. |
| **Trí nhớ Dài hạn** | Kém. Reservoir thường có "Trí nhớ phai dần" (Fading Memory). | Tốt. Các Synapse mạnh sẽ tồn tại vĩnh viễn (Long-term Potentiation). |

**Kết luận:** Reservoir computing thú vị cho việc nhận dạng mẫu thời gian nhưng thất bại trong việc xây dựng một "Mô hình Thế giới" (World Model) hay "Logic Nhân quả" có cấu trúc, vì bên trong nó là ngẫu nhiên, không phải do học mà thành.

---

## 4. Tại sao cách tiếp cận "POP Hebbian" của chúng ta khác biệt?

Chúng ta đang chọn **"Con đường Kỹ thuật Trung đạo"**:

1.  **Từ chối sự cồng kềnh:** Chúng ta từ chối Backpropagation (Cách 1 & 2) vì nó quá nặng và phi sinh học cho một Agent phải học *trong lúc* sống.
2.  **Từ chối sự ngẫu nhiên:** Chúng ta từ chối Reservoir Computing (Cách 3) vì chúng ta muốn cấu trúc bên trong của Agent biểu diễn các Quy luật Nhân quả đã học, chứ không phải tiếng vọng ngẫu nhiên.
3.  **Đón nhận Nhân quả:** Chúng ta tập trung vào **Học Nhân quả Cục bộ (STDP)** được triển khai qua **Kiến trúc Hướng Quy trình (POP)**.
    *   *Lợi thế:* Mỗi synapse đại diện cho một giả thuyết: "Nếu A xảy ra, B có khả năng xảy ra."
    *   *Lợi thế:* Minh bạch. Cấu trúc dữ liệu *chính là* logic.
    *   *Lợi thế:* Hiệu năng. Chúng ta xử lý Sự kiện, không xử lý Ma trận.

**Tổng kết sự Đánh đổi (Trade-offs):**
*   **Chúng ta hy sinh:** Khả năng giải quyết bài toán ImageNet hay chơi cờ Go ở mức siêu nhân ngay lập tức (thứ mà Deep Learning làm tốt).
*   **Chúng ta đạt được:** Một Agent biết "Lửa thì nóng" sau khi chạm vào lửa một lần (Học một lần - One-shot learning), thích nghi với luật chơi mới ngay tức khắc (Online learning), và có một "tâm trí" mà chúng ta có thể đọc hiểu như đọc một cơ sở dữ liệu.
