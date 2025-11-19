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


---

### Chạy thử lần 6 (Ngày 15/11/2025): Thử nghiệm "Mê cung Logic Đa tầng" (4x4)

*   **Mục tiêu:** Thử nghiệm quyết định nhằm xác định giá trị của sự tò mò trong một môi trường có độ phức tạp logic cao, bao gồm cả cổng AND và XOR.
*   **Thiết lập Môi trường:** Môi trường 15x15 với 4 công tắc và 4 tường động, yêu cầu tác nhân phải học và thực hiện một chuỗi logic phụ thuộc lẫn nhau (ví dụ: (A và B) -> qua C, (C xor D) -> qua D).
*   **Thiết lập Thử nghiệm:** 5 nhóm tác nhân với mức độ tò mò tăng dần từ 0 (không tò mò) đến 4 (rất tò mò). 3 lần chạy, 4000 episode/lần.
*   **Kết quả:**

| Mức độ Tò mò | Tỷ lệ Thành công | Số bước Trung bình (khi thành công) |
| :--- | :--- | :--- |
| 0 (Không) | **100.00%** | **8.87** |
| 1 (Thấp) | 100.00% | 10.60 |
| 2 (Vừa) | 100.00% | 16.28 |
| 3 (Cao) | 99.98% | 35.32 |
| 4 (Rất cao) | 99.62% | 123.56 |

*   **Phân tích:**
    1.  **Giả thuyết cuối cùng đã bị bác bỏ:** Kết quả không thể rõ ràng hơn. Ngay cả trong môi trường phức tạp nhất, tác nhân không có sự tò mò vẫn là tác nhân hiệu quả nhất.
    2.  **Sự tò mò là một sự xao lãng có thể định lượng:** Có một mối tương quan trực tiếp, gần như tuyến tính trên thang log, giữa việc tăng độ tò mò và tăng số bước cần thiết để giải quyết vấn đề. Tác nhân tò mò nhất đã lãng phí tài nguyên gấp ~14 lần so với tác nhân không tò mò.
    3.  **Bản chất của vấn đề:** Tác nhân tò mò dành quá nhiều thời gian để "hiểu" các quy tắc. Nó bị thu hút bởi sự bất ngờ của các cổng logic và thực hiện các thí nghiệm lặp đi lặp lại để xây dựng một mô hình nội tại hoàn chỉnh. Trong khi đó, tác nhân không tò mò chỉ cần tìm ra một chuỗi hành động hiệu quả một cách tình cờ và khai thác nó mãi mãi.

---

## KẾT LUẬN TOÀN BỘ DỰ ÁN

Sau một loạt các thử nghiệm được thiết kế và thực thi một cách có hệ thống, từ các môi trường đơn giản đến các mê cung logic đa tầng phức tạp, chúng ta có thể rút ra một kết luận vững chắc, mặc dù nó trái với giả thuyết ban đầu của dự án:

**Trong bối cảnh một tác nhân đơn lẻ hoạt động trong một môi trường có quy tắc ẩn nhưng cố định, với một mục tiêu đã được xác định rõ ràng, thì sự tò mò (được định nghĩa là một cơ chế tìm kiếm sự bất ngờ và được tưởng thưởng nội tại) là một trở ngại, làm giảm hiệu suất và lãng phí tài nguyên.**

Dự án đã thành công trong việc:
1.  Xây dựng một kiến trúc hướng quy trình (POP) mạnh mẽ để dàn dựng các thử nghiệm khoa học về AI.
2.  Triển khai một tác nhân học tăng cường với "cảm xúc máy" có thể đo lường và có tác động đến hành vi.
3.  Kiểm chứng và bác bỏ một cách thuyết phục "Giả thuyết về giá trị của sự tò mò" trong các điều kiện đã nêu.

Kết quả này không làm giảm giá trị của sự tò mò nói chung, mà nó giúp chúng ta xác định rõ hơn những điều kiện mà ở đó sự tò mò thực sự cần thiết và có giá trị. Các hướng đi trong tương lai nên tập trung vào các môi trường có đặc tính khác, chẳng hạn như:
*   **Môi trường có quy tắc thay đổi liên tục (non-stationary).**
*   **Môi trường có nhiều tác nhân cạnh tranh/hợp tác.**
*   **Các nhiệm vụ không có mục tiêu cụ thể ngoài việc khám phá và lập bản đồ thế giới.**

Dự án EmotionAgent, với kết quả này, đã hoàn thành sứ mệnh của nó là trả lời một câu hỏi khoa học cụ thể.

---

### Phân tích Bổ sung: Tốc độ Tìm ra Lời giải Tối ưu

Để hiểu rõ hơn về tác động của sự tò mò, chúng ta đã phân tích số episode đầu tiên mà mỗi tác nhân tìm thấy con đường ngắn nhất (8 bước) trong bất kỳ lần chạy nào.

| Mức độ Tò mò | Episode đầu tiên đạt 8 bước (Tổng thể) |
| :--- | :--- |
| 0 (Không) | **30** |
| 1 (Thấp) | **23** |
| 2 (Vừa) | 67 |
| 3 (Cao) | 513 |
| 4 (Rất cao) | 869 |

**Diễn giải:**

*   **Tác nhân tò mò thấp học nhanh hơn:** Tác nhân `Lvl_1` (tò mò thấp) là tác nhân đầu tiên tìm thấy con đường tối ưu (8 bước) chỉ sau **23 episode** trong một lần chạy. Tác nhân `Lvl_0` (không tò mò) cũng khá nhanh, với 30 episode.
*   **Tò mò quá cao làm chậm quá trình học:** Khi mức độ tò mò tăng lên, số episode cần thiết để lần đầu tiên tìm thấy con đường tối ưu cũng tăng lên đáng kể. Tác nhân `Lvl_4` (rất tò mò) phải mất tới **869 episode** trong lần chạy tốt nhất của nó, và thậm chí trong một lần chạy khác, nó không bao giờ tìm thấy con đường 8 bước.
*   **Sự "xao lãng" ngay từ đầu:** Điều này cho thấy rằng sự tò mò cao không chỉ làm giảm hiệu quả sau khi học, mà còn làm chậm quá trình học ban đầu. Tác nhân tò mò cao có thể bị phân tâm bởi quá nhiều "sự bất ngờ" nhỏ nhặt trong môi trường, khiến nó mất nhiều thời gian hơn để tập trung vào việc giải quyết vấn đề chính.

Phân tích này củng cố mạnh mẽ kết luận rằng sự tò mò, trong môi trường này, là một yếu tố gây xao lãng. Nó không chỉ làm tăng số bước trung bình mà còn làm chậm đáng kể thời gian cần thiết để tác nhân lần đầu tiên tìm thấy giải pháp tối ưu.

---

### Chạy thử lần 7 (Ngày 17/11/2025): So găng trực tiếp Lvl_0 vs Lvl_1
*   **Mục tiêu:** Kiểm chứng lại kết quả bất thường từ "Phân tích Bổ sung" của lần chạy 6, nơi tác nhân Lvl_1 (tò mò thấp) tìm ra lời giải tối ưu nhanh hơn Lvl_0 (không tò mò).
*   **Thiết lập Môi trường:** Giữ nguyên môi trường "Mê cung Logic Đa tầng" (4x4).
*   **Thiết lập Thử nghiệm:**
    *   NoCuriosity_vs_Low_Lvl_0: Tác nhân không tò mò.
    *   NoCuriosity_vs_Low_Lvl_1: Tác nhân tò mò thấp.
    *   3 lần chạy cho mỗi tác nhân, 1000 episode/lần.
*   **Kết quả Phân tích Chi tiết (Tốc độ tìm ra lời giải tối ưu):**

| Tác nhân | Lần chạy | Số bước Tối ưu | Episode đầu tiên đạt Tối ưu |
| :--- | :--- | :--- | :--- |
| **Lvl_0 (Không tò mò)** | Run 1 | **8** | 43 |
| | Run 2 | **8** | **28** |
| | Run 3 | **8** | 69 |
| **Lvl_1 (Tò mò ít)** | Run 1 | **8** | 109 |
| | Run 2 | **8** | 53 |
| | Run 3 | **8** | 68 |

*   **Phân tích:**
    1.  **Kết quả bất thường đã bị bác bỏ:** Thử nghiệm lặp lại và có kiểm soát này cho thấy kết quả từ lần chạy 6 chỉ là một sự may mắn ngẫu nhiên (statistical anomaly).
    2.  **Tác nhân không tò mò nhanh hơn một cách nhất quán:** Trong cả 3 lần chạy so găng trực tiếp, tác nhân **Không Tò mò (Lvl_0)** đều tìm ra con đường tối ưu (8 bước) nhanh hơn so với tác nhân **Tò mò Ít (Lvl_1)**. Lần chạy nhanh nhất của Lvl_0 là ở episode 28, trong khi lần chạy nhanh nhất của Lvl_1 là ở episode 53.
    3.  **Củng cố kết luận chính:** Phân tích này củng cố mạnh mẽ hơn kết luận cuối cùng của dự án: trong môi trường có quy tắc cố định, sự tò mò (dù chỉ ở mức thấp) cũng làm chậm quá trình hội tụ đến giải pháp hiệu quả nhất. Tác nhân tập trung hoàn toàn vào việc khai thác sẽ chiến thắng.

---

## Giai đoạn 4: Mở rộng Trạng thái Tác nhân và Sửa lỗi Logic Mê cung (Ngày 17/11/2025)

### 4.1. Vấn đề
Các thử nghiệm trước đây trên "Mê cung Logic Đa tầng" (Chạy thử lần 6 và 7) cho thấy tác nhân không tò mò luôn vượt trội hơn tác nhân có tò mò, ngay cả khi môi trường yêu cầu suy luận logic. Điều này chỉ ra một lỗi cơ bản trong cách tác nhân hiểu và học về môi trường có các công tắc logic. Cụ thể, tác nhân không thể phân biệt được các trạng thái môi trường giống nhau về vị trí nhưng khác nhau về trạng thái công tắc.

### 4.2. Nguyên nhân gốc rễ
Q-table của tác nhân chỉ sử dụng vị trí `(y, x)` làm trạng thái, điều này không đủ cho môi trường có các bức tường động được điều khiển bởi các công tắc ẩn. Tác nhân không có "niềm tin" về trạng thái của các công tắc này, dẫn đến việc nó không thể học được mối quan hệ nhân-quả giữa việc kích hoạt công tắc và sự thay đổi của môi trường.

### 4.3. Giải pháp
Mở rộng định nghĩa trạng thái của tác nhân để bao gồm niềm tin về trạng thái của các công tắc logic. Trạng thái mới sẽ là một bộ `(agent_pos_y, agent_pos_x, switch_A_state, switch_B_state, switch_C_state, switch_D_state)`.

Các thay đổi đã thực hiện:
1.  **`src/context.py`:** Thêm `believed_switch_states` (niềm tin về trạng thái công tắc) và `get_composite_state` (hàm tạo trạng thái phức hợp).
2.  **`main.py`:** Truyền thông tin vị trí các công tắc từ cấu hình môi trường vào `AgentContext`.
3.  **`src/processes/p2_belief_update.py`:** Cập nhật logic để suy luận và điều chỉnh `believed_switch_states` dựa trên việc tác nhân đi qua các vị trí công tắc. Đồng thời, đảm bảo cập nhật Q-table sử dụng trạng thái phức hợp.
4.  **`src/processes/p6_action_select.py`:** Sửa đổi để sử dụng trạng thái phức hợp khi truy cập Q-table để chọn hành động.
5.  **`src/processes/p8_consequence.py`:** Sửa đổi để sử dụng trạng thái phức hợp khi cập nhật Q-table và ghi log vào bộ nhớ ngắn hạn.

### 4.4. Tổng kết Giai đoạn 4
Lỗi logic cơ bản trong việc học của tác nhân đã được khắc phục bằng cách mở rộng trạng thái của nó. Tác nhân giờ đây có khả năng phân biệt các trạng thái môi trường dựa trên niềm tin về các công tắc ẩn, cho phép nó học chính xác hơn về động lực của mê cung logic.

---

### Chạy thử lần 8 (Ngày 17/11/2025): Xác minh Sửa lỗi Logic Mê cung

*   **Mục tiêu:** Xác minh rằng việc mở rộng trạng thái tác nhân và sửa đổi các quy trình liên quan đã khắc phục lỗi logic trong môi trường mê cung có công tắc.
*   **Thiết lập Môi trường:** Môi trường "Mê cung Logic Đa tầng" (4x4) tương tự như Chạy thử lần 6 và 7.
*   **Thiết lập Thử nghiệm:**
    *   NoCuriosity_vs_Low_Lvl_0: Tác nhân không tò mò.
    *   NoCuriosity_vs_Low_Lvl_1: Tác nhân tò mò thấp.
    *   3 lần chạy cho mỗi tác nhân, 1000 episode/lần.
*   **Kết quả Tổng hợp:**

| Thử nghiệm | Tỷ lệ Thành công (Trung bình) | Số bước Trung bình (khi thành công) | Tỷ lệ khám phá cuối cùng trung bình |
| :--- | :--- | :--- | :--- |
| **NoCuriosity_vs_Low_Lvl_0** | **100.00%** | **10.12** | 0.0500 |
| **NoCuriosity_vs_Low_Lvl_1** | **100.00%** | 12.36 | 0.2021 |

*   **Kết quả Phân tích Chi tiết (Tốc độ tìm ra lời giải tối ưu - 8 bước):**

| Tác nhân | Lần chạy | Episode đầu tiên đạt 8 bước |
| :--- | :--- | :--- |
| **NoCuriosity_vs_Low_Lvl_0** | Run 1 | 41 |
| | Run 2 | 14 |
| | Run 3 | 32 |
| **Trung bình** | | **29** |
| **NoCuriosity_vs_Low_Lvl_1** | Run 1 | 49 |
| | Run 2 | 49 |
| | Run 3 | 97 |
| **Trung bình** | | **65** |

*   **Phân tích:**
    1.  **Khắc phục hoàn toàn lỗi logic:** Cả hai tác nhân đều đạt tỷ lệ thành công 100%, cho thấy chúng đã có thể giải quyết mê cung logic một cách nhất quán. Điều này xác nhận rằng việc mở rộng trạng thái tác nhân để bao gồm niềm tin về công tắc đã giải quyết được vấn đề cốt lõi.
    2.  **Tác nhân không tò mò hiệu quả hơn:** Tác nhân `NoCuriosity_vs_Low_Lvl_0` (không tò mò) tìm thấy đường đi tối ưu (8 bước) sớm hơn đáng kể (trung bình 29 episode) so với tác nhân `NoCuriosity_vs_Low_Lvl_1` (tò mò thấp, trung bình 65 episode). Điều này củng cố kết luận trước đó: trong môi trường có quy tắc cố định, ngay cả khi phức tạp, sự tò mò vẫn là một yếu tố gây xao lãng và làm chậm quá trình học.
    3.  **Không còn sự bất thường:** Kết quả này nhất quán và không còn cho thấy sự bất thường nào như trong "Chạy thử lần 6" (nơi Lvl_1 dường như nhanh hơn Lvl_0).

*   **Hướng đi tiếp theo:** Với việc lỗi logic cơ bản đã được khắc phục, các thử nghiệm trong tương lai có thể tập trung vào các môi trường thực sự phi xác định hoặc có quy tắc thay đổi động để khám phá giá trị thực sự của sự tò mò.

### Chạy thử độc lập main.py lần 1 (Ngày 17/11/2025)

Quan sát khi chạy debug visual_mode : true với logic belief_update và maze mới -> confidence nhanh chóng -> 0.0 và uncertainty -> 1.0

---

## Giai đoạn 5: Thử nghiệm Mê cung Cân bằng và Phân tích Sâu (Ngày 19/11/2025)

### 5.1. Bối cảnh
Sau khi khắc phục các lỗi logic cơ bản, các thử nghiệm trước đây vẫn cho thấy tác nhân không tò mò vượt trội trong các môi trường có quy tắc cố định. Tuy nhiên, các môi trường đó có thể chưa đủ phức tạp hoặc có những sai sót trong thiết kế (ví dụ: tạo ra các "lồng" không thể thoát ra). Giai đoạn này tập trung vào việc thiết kế một mê cung mới, phức tạp hơn nhưng được đảm bảo là có thể giải được ("Balanced Maze v2") và thực hiện một loạt phân tích sâu để hiểu rõ hành vi của các agent.

### 5.2. Quá trình Thử nghiệm và Gỡ lỗi
1.  **Thiết kế "Balanced Maze v2":** Một mê cung 25x25 mới được tạo ra bằng script `generate_config.py` với các hành lang được xác định rõ ràng, các cổng động được đặt một cách chiến lược và các công tắc có thể truy cập. Thiết kế này đã được xác minh trực quan bằng script `verify_environment.py` để đảm bảo không có khu vực nào bị cô lập hoàn toàn.
2.  **Xác minh khả năng học cốt lõi:** Một thử nghiệm trên mê cung 5x5 tĩnh đơn giản đã được thực hiện, cho thấy agent có thể học với tỷ lệ thành công 78%, khẳng định thuật toán Q-learning cốt lõi không bị lỗi.
3.  **Thử nghiệm ngắn (100 episode):**
    *   **Mục tiêu:** Xác minh nhanh rằng "Balanced Maze v2" có thể giải được.
    *   **Kết quả:** Lần đầu tiên, các agent đã đạt được tỷ lệ thành công khác 0 trong một mê cung phức tạp. `LowCuriosity` đạt 41%, `MediumCuriosity` đạt 38%, và `NoCuriosity` đạt 32%.
    *   **Phân tích bất ngờ:** Agent `NoCuriosity` là agent duy nhất tìm thấy đường đi tối ưu (354 bước) tại episode 48, trong khi các agent tò mò hơn thì không. Điều này cho thấy `NoCuriosity` có thể "ăn may" nhưng các agent tò mò lại học một cách ổn định hơn (số bước trung bình có xu hướng giảm).

### 5.3. Chạy thử lần 9: Thử nghiệm Dài hạn (1000 episode)
*   **Mục tiêu:** Quan sát các xu hướng dài hạn và xác định xem sự học hỏi bền vững của các agent tò mò có vượt qua sự "ăn may" của agent không tò mò hay không.
*   **Thiết lập:** "Balanced Maze v2", 1 lần chạy cho mỗi agent, 1000 episode/lần, `visual_mode` được tắt để tăng tốc độ.
*   **Kết quả:**

| Thử nghiệm | Tỷ lệ Thành công | Số bước Trung bình (khi thành công) | Tìm thấy đường đi tối ưu (99 bước)? |
| :--- | :--- | :--- | :--- |
| **NoCuriosity** | 2.40% | 326.46 | **Có (tại episode 833)** |
| **LowCuriosity** | 2.90% | 353.79 | Không |
| **MediumCuriosity** | **3.70%** | **299.03** | Không |

*   **Phân tích:**
    1.  **Phát hiện đường đi tối ưu mới:** Một đường đi ngắn hơn nhiều (99 bước) đã được phát hiện trong lần chạy dài này (được xác định bằng `analyze_complexity_results.py`), cho thấy tầm quan trọng của việc cho agent đủ thời gian để khám phá.
    2.  **Sự đánh đổi giữa Tò mò và Hiệu quả:**
        *   **Agent `MediumCuriosity`** nổi lên là agent hiệu quả nhất về tổng thể: tỷ lệ thành công cao nhất và số bước trung bình để thành công là thấp nhất. Nó học được cách giải quyết vấn đề một cách ổn định và hiệu quả, mặc dù không tìm ra con đường ngắn nhất tuyệt đối.
        *   **Agent `NoCuriosity`** một lần nữa tìm thấy đường đi tối ưu, nhưng rất muộn (episode 833) và có tỷ lệ thành công chung rất thấp. Điều này củng cố giả thuyết rằng nó phụ thuộc vào may mắn và không có chiến lược học tập ổn định.
    3.  **Kết luận cuối cùng (tạm thời):** Sự tò mò (đặc biệt ở mức độ vừa phải) giúp agent học một cách bền vững và đạt được hiệu suất trung bình tốt hơn trong các môi trường phức tạp. Việc không có tò mò khiến agent dễ bị mắc kẹt và chỉ có thể thành công một cách ngẫu nhiên.

### 5.4. Hướng đi tiếp theo
Các kết quả từ một lần chạy duy nhất rất hứa hẹn nhưng có thể bị nhiễu. Để có kết luận khoa học cuối cùng, bước tiếp theo là thực hiện một thử nghiệm đầy đủ với nhiều lần chạy (ví dụ: 5 lần) để lấy kết quả trung bình và đảm bảo tính nhất quán của các xu hướng đã quan sát.
