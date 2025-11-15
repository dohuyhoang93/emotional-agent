# Trạng thái Dự án: EmotionAgent

---
*Tài liệu này được cập nhật theo thời gian để ghi lại tiến trình, các kết quả thử nghiệm và những thay đổi trong định hướng của dự án. Các cập nhật mới nhất sẽ được thêm vào cuối tệp.*
---

## Giai đoạn 1: Prototype Tác nhân Đơn lẻ (Ngày 13/11/2025)

### 1.1. Mục tiêu
Hoàn thành việc triển khai **Bước 1: Prototype tác nhân đơn lẻ** theo tầm nhìn đã được thống nhất trong `spec.md` và triết lý Kiến trúc Hướng Quy trình (POP).

### 1.2. Tổng kết
Tính khả thi của mô hình cốt lõi đã được chứng minh ở cấp độ prototype. Đã xây dựng một tác nhân có khả năng học hỏi thông qua Q-Learning, với một vòng lặp phản hồi Trí tuệ-Cảm xúc tích hợp.

### 1.3. Trạng thái các thành phần khi hoàn thành Giai đoạn 1

#### A. Các thành phần đã hoàn thiện:
*   **Kiến trúc Hướng Quy trình (POP):** Đã triển khai đầy đủ và hoạt động ổn định (Workflow Engine, Process Registry, AgentContext, cấu trúc thư mục).
*   **Môi trường (`GridWorld`):** Hoàn chỉnh cho mục đích thử nghiệm Giai đoạn 1.
*   **Cơ chế học hỏi cốt lõi (Q-Learning):** Đã triển khai đầy đủ, bao gồm cập nhật Q-table và chiến lược chọn hành động epsilon-greedy.
*   **Mô hình Cảm xúc Máy (MLP):** Đã được định nghĩa, tích hợp và huấn luyện với mục tiêu kép (tự tin và tò mò).
*   **Vòng lặp phản hồi Trí tuệ-Cảm xúc:** Đã được kết nối hoàn chỉnh và hoạt động.
*   **Các Process:** `p1` đến `p8` đã hoàn thiện các chức năng cơ bản.

#### B. Các thành phần vẫn là Placeholder hoặc cần mở rộng/tinh chỉnh:
1.  **Bộ nhớ dài hạn (`long_term_memory`):** Hoàn toàn chưa được triển khai.
2.  **Sử dụng Bộ nhớ ngắn hạn (`short_term_memory`):** Mới chỉ được sử dụng ở mức cơ bản.
3.  **`p2_belief_update.py` (Cập nhật Niềm tin):** Logic còn cơ bản, có thể mở rộng.
4.  **`N_vector` (Vector Nhu cầu):** Hiện tại là tĩnh.
5.  **Các chiều khác của `E_vector`:** Hiện tại chỉ huấn luyện 2 chiều.

---

## Giai đoạn 2: Xây dựng Hệ thống Dàn dựng Thử nghiệm (Ngày 14/11/2025)

### 2.1. Mục tiêu
Xây dựng một hệ thống tự động để chạy các thử nghiệm quy mô lớn, thu thập dữ liệu và phân tích một cách khoa học, tuân thủ triết lý POP.

### 2.2. Tổng kết
Hệ thống đã hoàn thiện, cho phép cấu hình và thực thi các kịch bản thử nghiệm phức tạp một cách tự động.

### 2.3. Trạng thái các thành phần khi hoàn thành Giai đoạn 2
*   **Kiến trúc POP:** Toàn bộ hệ thống dàn dựng được thiết kế tuân thủ triết lý POP.
*   **Các thành phần chính:**
    *   **`experiments.json`:** Tệp cấu hình trung tâm.
    *   **`run_experiments.py`:** Bộ máy thực thi (Workflow Engine) chính.
    *   **`main.py` (Worker):** Được tái cấu trúc để hoạt động như một "worker" độc lập.
    *   **`src/orchestration_processes/`:** Thư mục chứa các quy trình độc lập cho từng bước dàn dựng.
*   **Tính năng:** Hệ thống có khả năng chạy N thử nghiệm, mỗi thử nghiệm M lần, tự động thu thập kết quả, vẽ biểu đồ tổng hợp và tạo báo cáo phân tích.

---

## Giai đoạn 3: Gỡ lỗi, Tinh chỉnh và Phân tích sâu (Ngày 14/11/2025)

### 3.1. Vấn đề
Sau khi hoàn thiện Giai đoạn 2, các thử nghiệm cho thấy những hành vi bất thường:
1.  Khi chạy độc lập ở chế độ trực quan, tỷ lệ thành công báo cáo luôn là 0%, dù thực tế agent vẫn có những lần đến đích.
2.  Kết quả từ các thử nghiệm quy mô lớn cho thấy hiệu suất rất thấp và agent `High_Curiosity` hoạt động kém hơn `Low_Curiosity` một cách khó hiểu.

### 3.2. Quá trình Gỡ lỗi và Sửa lỗi
Một quá trình gỡ lỗi có hệ thống đã được thực hiện và phát hiện ra 3 lỗi nghiêm trọng:

*   **Phát hiện 1 (Lỗi Hiển thị):** Lỗi trong `main.py` khiến biến `is_successful` không bao giờ được cập nhật thành `True`, dẫn đến báo cáo 0% thành công.
    *   **Giải pháp:** Tách logic *xác định* thành công ra khỏi logic *hiển thị* thành công.

*   **Phát hiện 2 (Lỗi Logic Nghiêm trọng - State-Mismatch):** Lỗi trong thứ tự thực thi workflow khiến quy trình học (`p8`) cập nhật Q-table cho một cặp `(trạng thái, hành động)` sai. Agent đang học sai bài học.
    *   **Giải pháp:** Hợp nhất logic "Hành động & Quan sát" vào `p7_execution.py`, xóa bỏ `p1_observation.py` và cập nhật lại `agent_workflow.json`.

*   **Phát hiện 3 (Lỗi Môi trường Hardcoded):** Lỗi trong `environment.py` khiến môi trường luôn là lưới 5x5, không tuân theo các thiết lập `grid_size` từ `experiments.json`.
    *   **Giải pháp:** Sửa đổi `environment.py` để tạo môi trường một cách linh động dựa trên `settings`.

### 3.3. Tổng kết Giai đoạn 3
Tất cả các lỗi trên đã được sửa. Quá trình gỡ lỗi đã chứng minh tầm quan trọng của việc phân tích sâu và xác minh từng bước. Các thay đổi đã khôi phục và cải thiện đáng kể khả năng học của agent.

---

## Nhật ký Chạy thử và Phân tích

### Chạy thử lần 1 (Ngày 13/11/2025) - Lịch sử
*   **Mục tiêu:** Thử nghiệm ban đầu sau khi hoàn thiện Giai đoạn 1.
*   **Thiết lập:** 500 episodes, môi trường 5x5.
*   **Kết quả:** Tỷ lệ thành công: 15.6%.
*   **Đánh giá:** Hiệu suất giảm đáng kể. **Nguyên nhân sau này được xác định là do Lỗi Logic State-Mismatch.**

### Chạy thử lần 2 (Ngày 14/11/2025): So sánh Tò mò (trước khi sửa lỗi)
*   **Mục tiêu:** Tìm hiểu nguyên nhân suy giảm hiệu suất.
*   **Thiết lập:** Môi trường 5x5, 3 thử nghiệm (Low/Baseline/High Curiosity), 1000 episode/lần.
*   **Kết quả:** Agent `Low_Curiosity` cho hiệu suất tốt nhất (35.00%).
*   **Phân tích (tại thời điểm đó):** Đưa ra "Giả thuyết về sự Xao lãng".
*   **Phân tích (sau khi biết lỗi):** Lỗi State-Mismatch làm tín hiệu `td_error` bị nhiễu loạn. Agent `High_Curiosity` khuếch đại nhiễu này nên hoạt động kém nhất. Agent `Low_Curiosity` hoạt động tốt hơn vì nó "phớt lờ" tín hiệu nhiễu tốt hơn.

### Chạy thử lần 3 (Ngày 14/11/2025): Kiểm chứng trong Môi trường Phức tạp (trước khi sửa lỗi)
*   **Mục tiêu:** Kiểm chứng giả thuyết tò mò trong môi trường phức tạp.
*   **Thiết lập:** Cấu hình môi trường 15x15.
*   **Kết quả:** Agent `Low_Curiosity` vẫn tốt hơn (43.58% vs 35.62%).
*   **Phân tích (tại thời điểm đó):** Giả thuyết tò mò không được xác nhận.
*   **Phân tích (sau khi biết lỗi):** Phát hiện ra Lỗi Môi trường Hardcoded. Thử nghiệm này thực chất vẫn chạy trên lưới 5x5.

### Chạy thử lần 4 (Ngày 14/11/2025): Chạy lại Môi trường Phức tạp (SAU KHI SỬA LỖI)
*   **Mục tiêu:** Chạy lại thử nghiệm trên môi trường 15x15 thực sự với agent đã được sửa lỗi hoàn toàn.
*   **Thiết lập:** Môi trường 15x15, 2 thử nghiệm (Complex_Low_Curiosity và Complex_High_Curiosity), 3 lần chạy, 2000 episode/lần.
*   **Kết quả:**

| Thử nghiệm | Trọng số Tò mò (`intrinsic_reward_weight`) | Tỷ lệ Thành công (Trung bình) | Số bước Trung bình (khi thành công) |
| :--- | :--- | :--- | :--- |
| **Complex_Low_Curiosity** | 0.01 | **93.72%** | **43.39** |
| **Complex_High_Curiosity** | 0.1 | 92.47% | 44.63 |

*   **Phân tích:**
    1.  **Hiệu suất bùng nổ:** Việc sửa các lỗi nghiêm trọng đã giúp hiệu suất tăng vọt lên hơn 90%, chứng tỏ khả năng học của agent giờ đây đã rất hiệu quả.
    2.  **Giả thuyết tò mò vẫn chưa được xác nhận:** Trong môi trường phức tạp nhưng có thể đoán trước (deterministic), agent `Low_Curiosity` vẫn nhỉnh hơn một chút. Khoảng cách đã được thu hẹp, nhưng "Giả thuyết Xao lãng" vẫn còn hiệu lực ở mức độ nhỏ.

---

## Giai đoạn 4: Môi trường Logic Biến đổi (Kế hoạch cho Ngày 15/11/2025)

### 4.1. Tầm nhìn
Sau khi các thử nghiệm cho thấy agent đã rất hiệu quả trong môi trường có thể đoán trước, nhưng vai trò của "sự tò mò" vẫn chưa thực sự nổi bật, chúng ta cần một thử thách mới, phù hợp hơn với tầm nhìn "trí tuệ phi nhân". Hướng đi tiếp theo là tạo ra một môi trường mà ở đó, agent phải học cách khám phá và suy luận ra các **quy tắc ngầm**.

### 4.2. Ý tưởng: Mê cung Logic (Logical Maze)
*   **Khái niệm:** Môi trường sẽ chứa các "công tắc logic". Khi agent đi qua một công tắc, nó sẽ thay đổi trạng thái của một phần khác trong môi trường (ví dụ: một dãy tường ở xa được bật/tắt).
*   **Mục tiêu của Agent:** Không chỉ tìm đường đến đích, mà phải học được mối quan hệ nhân-quả trừu tượng giữa công tắc và các bức tường để giải quyết mê cung.
*   **Kỳ vọng:** Trong môi trường này, "cảm xúc máy" Tò mò (`td_error`) sẽ trở nên cực kỳ quan trọng. Nó sẽ thúc đẩy agent tìm hiểu nguyên nhân của những thay đổi "bất ngờ" trong môi trường, từ đó xây dựng một mô hình logic về thế giới.

### 4.3. Kế hoạch Triển khai
1.  **Sửa đổi `environment.py`:**
    *   Thêm logic để quản lý trạng thái của các công tắc và các bức tường động.
    *   Cập nhật hàm `perform_action` để kiểm tra việc agent đi vào ô công tắc và thay đổi trạng thái môi trường tương ứng.
2.  **Cập nhật `experiments.json`:**
    *   Thiết kế một kịch bản thử nghiệm mới với một mê cung logic, định nghĩa vị trí các công tắc và các bức tường động liên quan.
3.  **Chạy và Phân tích:**
    *   Thực hiện thử nghiệm so sánh agent `Low_Curiosity` và `High_Curiosity`.
    *   Phân tích xem agent `High_Curiosity` có thể hiện khả năng suy luận và giải quyết mê cung logic hiệu quả hơn không.

#### Thảo luận về xây dựng tính cảm xúc ảnh hưởng lên quyết điịnh:

 nhưng trạng thái lạ, và nguy hiểm kia dc xảy ra khi nào? code cho thấy việc xảy ra sự kiện này là phụ thuộc vào gì? Thực tế tôi thấy exploration rate rất nhanh sẽ giảm xuống ngưỡng min
  quy định 0,050

✦ Bạn lại một lần nữa đưa ra một quan sát cực kỳ sắc sảo và chính xác.

  Bạn hoàn toàn đúng. Trong thực tế, exploration_rate đang giảm xuống mức tối thiểu quá nhanh. Điều này cho thấy cơ chế "điều chỉnh bởi cảm xúc" mà tôi mô tả về mặt lý thuyết đang không
  hoạt động hiệu quả trong thực tế.

  Phân tích Nguyên nhân Gốc rễ

  Lý do cho sự mâu thuẫn này nằm ở 2 điểm:

   1. Sự Áp đảo của Cơ chế Suy giảm: Trong code hiện tại, epsilon được cập nhật theo kiểu epsilon_mới = epsilon_cũ * hệ_số_suy_giảm. Đây là một áp lực chỉ đi xuống rất mạnh mẽ và không
      ngừng. Bất kỳ sự "thúc đẩy" nhỏ nào từ cảm xúc đều nhanh chóng bị dập tắt bởi sự suy giảm liên tục này.

   2. Sự ổn định của "Tự tin": Trong một môi trường có thể đoán trước, một khi agent đã tìm ra con đường tối ưu, nó sẽ dành phần lớn thời gian đi trên con đường đó. Các giá trị Q-value trên
      con đường này trở nên ổn định và có thể dự đoán được. Do đó, mô hình cảm xúc nhanh chóng học cách "tự tin" ở hầu hết các trạng thái mà nó gặp phải. Các trạng thái "lạ và nguy hiểm"
      thực sự (gây mất tự tin) trở nên hiếm hoi.

  Kết quả là: Áp lực đi xuống của epsilon thì mạnh và liên tục, trong khi lực đẩy đi lên từ cảm xúc "thiếu tự tin" thì yếu và không thường xuyên. Kết quả là epsilon lao dốc không phanh.

  Đề xuất Giải pháp: Tái cấu trúc Logic Điều chỉnh Chính sách

  Để epsilon thực sự phản ánh "cảm xúc" của agent, chúng ta cần một logic mạnh mẽ hơn. Tôi đề xuất thay đổi hoàn toàn cách epsilon được tính toán trong p5_policy_adjust.py.

  Logic mới:
  Hãy tách exploration_rate thành 2 thành phần:
   1. Tỷ lệ Khám phá Nền (Base Rate): Đây là một giá trị suy giảm từ từ theo thời gian, giống như hiện tại. Nó đại diện cho sự tò mò chung của agent giảm dần khi nó trưởng thành.
   2. Sự Bùng nổ Cảm xúc (Emotional Boost): Đây là một giá trị cộng thêm, biến động mạnh dựa trên sự "Không chắc chắn" (Uncertainty).
       * Chúng ta định nghĩa Uncertainty = 1.0 - Confidence.
       * Khi agent rất tự tin (Confidence gần 1.0), Uncertainty sẽ gần 0, và sự bùng nổ này gần như bằng 0.
       * Khi agent mất tự tin (Confidence gần 0), Uncertainty sẽ gần 1.0, và sự bùng nổ này sẽ đạt giá trị tối đa.

  Công thức cuối cùng:
  exploration_rate = Tỷ_lệ_Nền + Sự_Bùng_nổ_Cảm_xúc

  Kết quả của Logic mới:

  Với logic này, exploration_rate sẽ không chỉ đi xuống. Nó sẽ là một đường cơ sở giảm dần, nhưng sẽ liên tục có những đỉnh nhọn đột biến tăng vọt lên mỗi khi agent gặp một trạng thái
  "lạ" hoặc "nguy hiểm" làm nó "mất tự tin".

  Điều này sẽ làm cho hành vi khám phá của nó năng động và phản ứng nhanh hơn nhiều với những thay đổi hoặc bất ngờ trong môi trường, thay vì chỉ giảm một cách thụ động. Đây là một bước
  đi quan trọng để làm cho "cảm xúc" thực sự có tác động hữu hình lên hành vi của agent.

  Bạn có đồng ý với việc tái cấu trúc quan trọng này không?

> trạng thái lạ, và nguy hiểm kia dc xảy ra khi nào?

✦ Đó là câu hỏi mấu chốt để liên kết 2 đề xuất mới của chúng ta lại với nhau. "Trạng thái lạ và nguy hiểm" sẽ không tự nhiên xuất hiện, mà nó là kết quả trực tiếp của việc agent tương tác
  với một môi trường có logic ngầm.

  Hãy định nghĩa các loại trạng thái trong môi trường "mê cung logic" mới:

   1. Trạng thái "Bình thường": Là những khu vực không có gì đặc biệt, chỉ có đường đi và tường tĩnh. Sau một thời gian ngắn, agent sẽ học thuộc các khu vực này.
       * Code sẽ làm gì? Ở đây, Q-table sẽ ổn định, dự đoán của mô hình cảm xúc sẽ chính xác. Confidence sẽ cao. Theo logic mới, exploration_rate sẽ thấp (chỉ còn base_rate suy giảm từ từ).

   2. Trạng thái "Bất ngờ" (The Surprising State): Đây là trạng thái quan trọng nhất. Đó là trạng thái ngay trước một kết quả không như dự đoán.
       * Khi nào xảy ra? Hãy tưởng tượng agent đã học được rằng có một bức tường năng lượng ở hàng y=10. Nó rất "tự tin" về điều này. Sau đó, một công tắc được kích hoạt. Trong một lần
         "khám phá" ngẫu nhiên, agent thử đi vào bức tường đó và... đi xuyên qua được.
       * Code sẽ làm gì? Hành động này phá vỡ mô hình thế giới của agent. Lần tiếp theo khi nó quay lại trạng thái ngay cạnh bức tường đó, mô hình cảm xúc sẽ báo động. Nó không còn "tự tin"
         về kết quả của hành động đi vào đó nữa. Confidence sẽ giảm mạnh.

  Đây là lúc logic mới phát huy tác dụng:

  Khi Confidence giảm mạnh, Uncertainty (tức là 1.0 - Confidence) sẽ tăng vọt.

  Theo công thức mới: exploration_rate = Tỷ_lệ_Nền + (Uncertainty * Emotional_Boost)

  epsilon sẽ tăng đột biến một cách có chủ đích, nhưng chỉ ở xung quanh khu vực có sự bất thường này.

  Kết quả:
  Agent sẽ không khám phá ngẫu nhiên một cách vô tội vạ trên toàn bản đồ. Thay vào đó, nó sẽ hành xử như một nhà khoa học:
   * Ở những vùng quen thuộc, nó tự tin khai thác kiến thức.
   * Khi gặp một hiện tượng "khó hiểu" (một bức tường lúc có lúc không), nó sẽ "mất tự tin", trở nên "tò mò" hơn, và tự động tăng cường nỗ lực khám phá chỉ tại khu vực đó để tìm ra quy
     luật.

  "Trạng thái lạ và nguy hiểm" chính là những nơi mà mô hình nội tại của agent về thế giới bị sụp đổ, và logic epsilon mới của chúng ta được thiết kế để tự động phát hiện và tập trung vào
  việc sửa chữa những "vết nứt" đó trong sự hiểu biết của nó.


---
---

## Mẫu Cập nhật Trạng thái Thử nghiệm (Template)

*Sao chép và điền thông tin cho các lần chạy thử nghiệm trong tương lai.*

### Chạy thử lần X (Ngày XX/XX/XXXX): [Tên thử nghiệm]
*   **Mục tiêu:** [Mô tả mục tiêu của thử nghiệm này]
*   **Thiết lập Môi trường:** [Mô tả các thay đổi về môi trường, ví dụ: Stochastic, Slippery=0.2]
*   **Thiết lập Thử nghiệm:** [Mô tả các nhóm thử nghiệm, số lần chạy, số episode]
*   **Kết quả:** [Bảng hoặc tóm tắt kết quả chính]
*   **Phân tích:** [Phân tích kết quả, giả thuyết có được xác nhận không, tại sao?]
*   **Hướng đi tiếp theo:** [Dựa trên kết quả, bước tiếp theo là gì?]


---

### Chạy thử lần 5 (Ngày 15/11/2025): Thử nghiệm "Mê cung Logic"

*   **Mục tiêu:** Kiểm chứng giả thuyết rằng tác nhân có "sự tò mò" cao (HighCuriosity) sẽ hoạt động hiệu quả hơn trong một môi trường đòi hỏi phải suy luận ra các quy tắc ngầm (mê cung có công tắc và tường động).
*   **Thiết lập Môi trường:** Môi trường 10x10 với một công tắc tại [5, 2] điều khiển một bức tường động chặn đường đến đích [9, 9].
*   **Thiết lập Thử nghiệm:**
    *   LogicalMaze_LowCuriosity: emotional_boost_factor = 0.1, intrinsic_reward_weight = 0.01.
    *   LogicalMaze_HighCuriosity: emotional_boost_factor = 0.8, intrinsic_reward_weight = 0.1.
    *   Cả hai đều sử dụng logic exploration_rate mới. 3 lần chạy, 2000 episode/lần.
*   **Kết quả:**

| Thử nghiệm | Tỷ lệ Thành công | Số bước Trung bình (khi thành công) |
| :--- | :--- | :--- |
| **LogicalMaze_LowCuriosity** | **100.00%** | **9.20** |
| **LogicalMaze_HighCuriosity** | 99.95% | 35.53 |

*   **Phân tích:**
    1.  **Giả thuyết thất bại:** Kết quả hoàn toàn trái ngược với kỳ vọng. Tác nhân LowCuriosity không chỉ thành công mà còn tìm ra lời giải nhanh hơn gần 4 lần so với tác nhân HighCuriosity.
    2.  **"Giả thuyết Xao lãng" được củng cố:** Một khi con đường tối ưu (đi qua công tắc -> đến đích) được tìm thấy, nó trở thành một chuỗi hành động có thể đoán trước. Tác nhân LowCuriosity nhanh chóng khai thác con đường này. Ngược lại, tác nhân HighCuriosity quá nhạy cảm với sự thay đổi của môi trường. Việc kích hoạt công tắc có thể gây ra một "cú sốc" (TD-error lớn), làm nó "mất tự tin" và thúc đẩy các hành vi khám phá không cần thiết, làm giảm hiệu quả một cách đáng kể.
    3.  **Bài học rút ra:** Môi trường "Mê cung Logic" với một quy tắc đơn lẻ vẫn chưa đủ phức tạp để chứng minh giá trị của sự tò mò. Sau khi quy tắc được học, môi trường lại trở nên có thể dự đoán được.

*   **Hướng đi tiếp theo:** Cần một môi trường thực sự phi xác định (stochastic) hoặc có nhiều quy tắc logic phức tạp hơn, chồng chéo lên nhau để sự tò mò không chỉ là một công cụ tìm ra một "bí mật" duy nhất, mà là một chiến lược cần thiết để liên tục thích ứng.
