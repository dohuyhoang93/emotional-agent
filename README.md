# EmotionAgent: Prototype Tác nhân AI Nhận thức-Cảm xúc với Hệ thống Thử nghiệm Tự động

Dự án này là một prototype hoạt động, hiện thực hóa các ý tưởng trong tài liệu `spec.md`. Nó mô phỏng một tác nhân AI học cách hoạt động trong môi trường "Thế giới Lưới" (Grid World) bằng kiến trúc nhận thức-cảm xúc tùy chỉnh.

Điểm nổi bật của dự án không chỉ nằm ở mô hình agent, mà còn ở **hệ thống dàn dựng thử nghiệm tự động**, cho phép cấu hình, thực thi và phân tích các kịch bản thử nghiệm phức tạp một cách khoa học và có hệ thống.

Mục tiêu chính của dự án là chứng minh và phân tích **Vòng lặp Tăng cường Trí tuệ-Cảm xúc**, nơi việc học hỏi (trí tuệ) và các trạng thái nội tại (cảm xúc máy) tương tác và ảnh hưởng lẫn nhau để định hình hành vi của tác nhân.

## 1. Kiến trúc Cốt lõi

Dự án được xây dựng dựa trên triết lý **Kiến trúc Hướng Quy trình (Process-Oriented Programming - POP)**, áp dụng cho cả mô hình agent và hệ thống dàn dựng thử nghiệm.

### a. Kiến trúc Tác nhân (Agent)

*   **Dữ liệu (Context):** Lớp `AgentContext` (`src/context.py`) là một cấu trúc dữ liệu "câm", chứa toàn bộ trạng thái của tác nhân.
*   **Hành vi (Processes):** Các hàm thuần túy trong `src/processes/`, mỗi hàm thực hiện một tác vụ duy nhất.
*   **Luồng hoạt động (Workflow):** Được định nghĩa trong `configs/agent_workflow.json`, quy định thứ tự các "process" được thực thi.
*   **Bộ máy thực thi (Engine):** Nằm trong `main.py`, đọc tệp workflow và thực thi các process tương ứng.

### b. Vòng lặp Tăng cường Trí tuệ-Cảm xúc

Đây là trái tim của tác nhân, mô phỏng sự tương tác giữa lý trí và cảm xúc:

1.  **Trí tuệ (Q-Learning):** Tác nhân học giá trị của các hành động để tối đa hóa phần thưởng. Quá trình này tạo ra tín hiệu "ngạc nhiên" (`td_error`).
2.  **Cảm xúc (MLP):** Một mạng nơ-ron nhỏ (`EmotionCalculatorMLP`) tạo ra Vector Cảm xúc Máy (`E_vector`) dựa trên trạng thái của tác nhân.
3.  **Sự kết nối:**
    *   **Ngạc nhiên → Thưởng nội sinh:** `td_error` được dùng để tính **phần thưởng nội sinh (`R_nội`)**, khuyến khích sự tò mò.
    *   **Thưởng nội sinh → Học hỏi:** `R_nội` ảnh hưởng đến quá trình cập nhật Q-table.
    *   **Cảm xúc → Hành vi:** `E_vector` điều chỉnh linh hoạt chính sách khám phá của tác nhân.

### c. Hệ thống Dàn dựng Thử nghiệm (Orchestrator)

Đây là một workflow POP thứ hai, chạy ở cấp độ cao hơn để quản lý các thử nghiệm.
*   **Dữ liệu:** `OrchestrationContext` (`src/experiment_context.py`) chứa toàn bộ cấu hình và kết quả của các thử nghiệm.
*   **Hành vi:** Các quy trình trong `src/orchestration_processes/` thực hiện các bước như tải cấu hình, chạy mô phỏng, tổng hợp dữ liệu, vẽ biểu đồ và phân tích.
*   **Luồng hoạt động:** Được định nghĩa trong `configs/orchestration_workflow.json`.
*   **Bộ máy thực thi:** `run_experiments.py` điều phối toàn bộ quá trình.

## 2. Cấu trúc Mã nguồn

```
EmotionAgent/
├── main.py                     # Worker: Chạy một lần mô phỏng
├── run_experiments.py          # Orchestrator: Dàn dựng và chạy các thử nghiệm
├── environment.py              # Môi trường mô phỏng GridWorld
│
├── experiments.json            # Cấu hình các kịch bản thử nghiệm
│
├── configs/
│   ├── agent_workflow.json       # Workflow cho Agent
│   ├── orchestration_workflow.json # Workflow cho Orchestrator
│   └── settings.json             # Siêu tham số mặc định
│
├── docs/                         # Chứa các tài liệu đặc tả, trạng thái
│   ├── spec.md
│   └── status.md
│
└── src/
    ├── context.py              # Định nghĩa AgentContext
    ├── experiment_context.py   # Định nghĩa OrchestrationContext
    ├── models.py               # Định nghĩa EmotionCalculatorMLP
    ├── plotting.py             # Module vẽ biểu đồ
    ├── process_registry.py     # Đăng ký các process của Agent
    │
    ├── processes/              # Các process của Agent (p1 -> p8)
    │   └── ...
    └── orchestration_processes/  # Các process của Orchestrator
        └── ...
```

## 3. Hướng dẫn Chạy chương trình

### a. Cài đặt thư viện cần thiết
```shell
pip install torch pandas matplotlib
```

### b. Chạy Kịch bản Thử nghiệm Tự động (Khuyến khích)

Đây là cách chạy chính để có được các kết quả đáng tin cậy.

1.  **Cấu hình thử nghiệm:** Mở và chỉnh sửa tệp `experiments.json`. Tại đây, bạn có thể định nghĩa nhiều thử nghiệm, mỗi thử nghiệm chạy nhiều lần với các tham số (`parameters`) khác nhau để ghi đè lên `configs/settings.json`.
2.  **Chạy bộ dàn dựng:**
    ```shell
    python run_experiments.py
    ```
3.  **Xem kết quả:** Kết quả, bao gồm các tệp CSV, biểu đồ tổng hợp, và báo cáo phân tích, sẽ được lưu vào thư mục được chỉ định trong `experiments.json` (trường `output_dir`).

### c. Chạy một lần mô phỏng đơn lẻ (Để gỡ lỗi)

Nếu bạn chỉ muốn chạy nhanh một lần mô phỏng để kiểm tra hoặc gỡ lỗi, bạn có thể chạy trực tiếp `main.py`.

1.  **Cấu hình:** Chỉnh sửa `configs/settings.json` để thiết lập các tham số mong muốn.
2.  **Chạy mô phỏng:**
    ```shell
    python main.py
    ```
    Lưu ý: Chế độ này sẽ không lưu kết quả ra tệp CSV hoặc vẽ biểu đồ.

## 4. Trạng thái Hiện tại và Hiểu biết Mới nhất

*   **Hoàn thành:** Đã hoàn thành **Bước 1 (Prototype Agent)** và **Bước 2 (Hệ thống Dàn dựng Thử nghiệm)**.
*   **Phát hiện chính:** Các thử nghiệm trên môi trường đơn giản (5x5) và phức tạp hơn (15x15) đều cho thấy một kết quả nhất quán và có phần phản trực giác: **agent có tính tò mò thấp (`Low_Curiosity`) cho hiệu suất tốt hơn agent có tính tò mò cao (`High_Curiosity`)**.
*   **Lý giải (Giả thuyết về sự "Xao lãng"):** Trong các môi trường có thể đoán trước được (deterministic), phần thưởng nội sinh dựa trên "sự ngạc nhiên" dường như hoạt động như một yếu tố gây xao lãng, khuyến khích agent khám phá những hành vi mới lạ nhưng không hiệu quả (như đâm vào tường) thay vì tập trung vào mục tiêu chính.
*   **Hướng đi tiếp theo:** Để thực sự kiểm chứng giá trị của sự tò mò, bước tiếp theo là đưa agent vào một môi trường **không thể đoán trước (stochastic)**, nơi hành động của agent có thể thất bại hoặc cho ra kết quả ngẫu nhiên. Trong một thế giới như vậy, khả năng mô hình hóa và hiểu được "sự bất ngờ" được kỳ vọng sẽ trở nên có giá trị hơn.
