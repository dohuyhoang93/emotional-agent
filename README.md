# EmotionAgent: Prototype Tác nhân AI Nhận thức-Cảm xúc

Dự án này là một prototype hoạt động, hiện thực hóa các ý tưởng trong tài liệu `spec.md`. Nó mô phỏng một tác nhân AI đơn lẻ học cách hoạt động trong một môi trường "Thế giới Lưới" (Grid World) bằng cách sử dụng một kiến trúc nhận thức-cảm xúc tùy chỉnh.

Mục tiêu chính của prototype này là chứng minh tính khả thi của **Vòng lặp Tăng cường Trí tuệ-Cảm xúc**, nơi việc học hỏi (trí tuệ) và các trạng thái nội tại (cảm xúc máy) tương tác và ảnh hưởng lẫn nhau để định hình hành vi của tác nhân.

## 1. Kiến trúc Cốt lõi

Dự án được xây dựng dựa trên hai nguyên tắc chính: Kiến trúc Hướng Quy trình (POP) và Vòng lặp Trí tuệ-Cảm xúc.

### a. Kiến trúc Hướng Quy trình (Process-Oriented Programming - POP)

Toàn bộ mã nguồn được tổ chức theo triết lý POP, với nguyên tắc cốt lõi là **tách biệt hoàn toàn giữa Dữ liệu và Hành vi**:

*   **Dữ liệu (Context):** Được định nghĩa trong `src/context.py`, lớp `AgentContext` là một cấu trúc dữ liệu "câm", chứa toàn bộ trạng thái của tác nhân (các vector N, E, Q-table, policy...) nhưng không có bất kỳ phương thức logic nào.
*   **Hành vi (Processes):** Được định nghĩa trong các tệp riêng lẻ trong `src/processes/`, mỗi tệp chứa một hàm thuần túy nhận `AgentContext` làm đầu vào, thực hiện một tác vụ duy nhất (ví dụ: quan sát, chọn hành động, học hỏi), và trả về `AgentContext` đã được cập nhật.
*   **Luồng hoạt động (Workflow):** Được định nghĩa trong `configs/agent_workflow.json`. Tệp này quy định thứ tự các "process" được thực thi trong một chu kỳ sống của tác nhân. Điều này cho phép thay đổi luồng logic mà không cần sửa mã.
*   **Bộ máy thực thi (Engine):** Nằm trong `main.py`, một engine đơn giản đọc tệp workflow, tra cứu các process tương ứng trong `src/process_registry.py`, và thực thi chúng.

### b. Vòng lặp Tăng cường Trí tuệ-Cảm xúc

Đây là trái tim của tác nhân, mô phỏng sự tương tác giữa lý trí và cảm xúc:

1.  **Trí tuệ (Học tăng cường - Q-Learning):**
    *   Tác nhân sử dụng một bảng Q (`q_table`) để học giá trị của từng cặp `(trạng thái, hành động)`.
    *   Mục tiêu là tìm ra con đường tối ưu để đến đích và tối đa hóa phần thưởng.
    *   Quá trình học này tạo ra một tín hiệu quan trọng: **lỗi chênh lệch thời gian (`td_error`)**, đại diện cho mức độ "ngạc nhiên" của tác nhân trước kết quả của một hành động.

2.  **Cảm xúc (Mô hình MLP - `EmotionCalculatorMLP`):**
    *   Một mạng nơ-ron nhỏ hoạt động như "bộ não cảm xúc".
    *   Nó nhận đầu vào là trạng thái của tác nhân (nhu cầu, quan sát môi trường) và tạo ra một **Vector Cảm xúc Máy (`E_vector`)**.
    *   Mô hình này được huấn luyện với **mục tiêu kép**:
        *   Một chiều của `E_vector` (ví dụ: `E_tin_cậy`) học cách dự đoán giá trị dài hạn của trạng thái.
        *   Một chiều khác (ví dụ: `E_tò_mò`) học cách phản ánh mức độ "ngạc nhiên" (`td_error`).

3.  **Sự kết nối trong Vòng lặp:**
    *   **Ngạc nhiên → Thưởng nội sinh:** Mức độ "ngạc nhiên" (`td_error`) được dùng để tính toán **phần thưởng nội sinh (`R_nội`)**. Điều này khuyến khích tác nhân khám phá những khu vực chưa biết hoặc có kết quả khó đoán.
    *   **Thưởng nội sinh → Học hỏi:** `R_nội` được cộng vào phần thưởng từ môi trường để cập nhật `q_table`. Do đó, "cảm xúc" tò mò trực tiếp thúc đẩy quá trình học hỏi của "trí tuệ".
    *   **Cảm xúc → Hành vi:** `E_vector` (đặc biệt là chiều `E_tin_cậy`) được sử dụng để điều chỉnh linh hoạt chính sách của tác nhân, cụ thể là `exploration_rate` (tỷ lệ khám phá). Nếu tác nhân "tự tin" vào kiến thức của mình, nó sẽ giảm khám phá và tăng cường khai thác.

## 2. Cấu trúc Mã nguồn

```
EmotionAgent/
├── main.py                 # Điểm khởi chạy chính, chứa Workflow Engine
├── environment.py          # Môi trường mô phỏng GridWorld
├── status.md               # Tệp ghi lại trạng thái và kết quả các lần thử nghiệm
├── spec.md                 # Tài liệu đặc tả tầm nhìn và kiến trúc tổng thể
│
├── configs/
│   ├── agent_workflow.json   # Định nghĩa luồng xử lý của tác nhân
│   └── settings.json         # Chứa các siêu tham số (hyperparameters)
│
└── src/
    ├── context.py          # Định nghĩa lớp AgentContext (dữ liệu)
    ├── models.py           # Định nghĩa lớp EmotionCalculatorMLP (kiến trúc model)
    ├── process_registry.py # Ánh xạ tên process tới hàm
    └── processes/
        ├── p1_observation.py
        ├── p2_belief_update.py
        ├── p3_emotion_calc.py
        ├── p4_reward_calc.py
        ├── p5_policy_adjust.py
        ├── p6_action_select.py
        ├── p7_execution.py
        └── p8_consequence.py
```

## 3. Hướng dẫn Chạy chương trình

1.  **Cài đặt thư viện cần thiết:**
    ```shell
    pip install torch
    ```

2.  **Chạy mô phỏng:**
    ```shell
    python main.py
    ```

3.  **Tùy chỉnh mô phỏng:**
    *   Bạn có thể thay đổi các siêu tham số như số lượng episodes, learning rate, kích thước môi trường... trong tệp `configs/settings.json`.

## 4. Trạng thái Hiện tại

Dự án đã hoàn thành việc triển khai một prototype hoạt động cho **Bước 1 (Tác nhân đơn lẻ)**.

*   **Điểm mạnh:** Kiến trúc cốt lõi đã được chứng minh là khả thi về mặt kỹ thuật. Vòng lặp Trí tuệ-Cảm xúc đã được kết nối và hoạt động.
*   **Vấn đề:** Trong lần chạy thử nghiệm gần nhất (xem `status.md`), việc bổ sung các cơ chế hoàn thiện đã làm giảm hiệu suất của tác nhân. Điều này cho thấy sự xung đột giữa các logic mới hoặc các siêu tham số chưa được tối ưu.
*   **Hướng tiếp theo:** Cần thực hiện các bước gỡ lỗi một cách có hệ thống (cô lập biến số) để xác định nguyên nhân gây sụt giảm hiệu suất và tinh chỉnh lại các cơ chế tương tác cho hài hòa.