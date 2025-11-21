# Trạng thái Dự án: EmotionAgent

*Tài liệu này được cập nhật theo thời gian để ghi lại tiến trình, các kết quả thử nghiệm và những thay đổi trong định hướng của dự án. Các cập nhật mới nhất sẽ được thêm vào cuối tệp.*

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

## Giai đoạn 3: Gỡ lỗi, Tinh chỉnh và Phân tích sâu
(Ngày 14/11/2025)

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

#### Thảo luận về xây dựng tính cảm xúc ảnh hưởng lên quyết định:

✦ Trạng thái *"lạ và nguy hiểm"* kia xảy ra khi nào? Thực tế quan sát khi `visual_mode: true` (chế độ in và kết xuất trên terminal) cho thấy `exploration rate` rất nhanh sẽ giảm xuống ngưỡng quy định `0,050`
##### Phân tích:

Trong thực tế, exploration_rate đang giảm xuống mức tối thiểu quá nhanh. Điều này cho thấy cơ chế "điều chỉnh bởi cảm xúc" đang không hoạt động hiệu quả trong thực tế.

  **Phân tích Nguyên nhân Gốc rễ**

  > Lý do chỉ số khám phá `exloration_rate` nhanh chóng giảm xuống mức tối thiểu.

   1. Sự Áp đảo của Cơ chế Suy giảm: Trong code hiện tại, epsilon được cập nhật theo kiểu epsilon_mới = epsilon_cũ * hệ_số_suy_giảm. Đây là một áp lực chỉ đi xuống rất mạnh mẽ và không
      ngừng. Bất kỳ sự "thúc đẩy" nhỏ nào từ cảm xúc đều nhanh chóng bị dập tắt bởi sự suy giảm liên tục này.

   2. Sự ổn định của "Tự tin": Trong một môi trường có thể đoán trước, một khi agent đã tìm ra con đường tối ưu, nó sẽ dành phần lớn thời gian đi trên con đường đó. Các giá trị Q-value trên
      con đường này trở nên ổn định và có thể dự đoán được. Do đó, mô hình cảm xúc nhanh chóng học cách "tự tin" ở hầu hết các trạng thái mà nó gặp phải. Các trạng thái "lạ và nguy hiểm"
      thực sự (gây mất tự tin) trở nên hiếm hoi.

  Kết quả là: Áp lực đi xuống của epsilon thì mạnh và liên tục, trong khi lực đẩy đi lên từ cảm xúc "thiếu tự tin" thì yếu và không thường xuyên. Kết quả là epsilon lao dốc không phanh.

  **📌 Đề xuất Giải pháp: Tái cấu trúc Logic Điều chỉnh Chính sách**

  Để epsilon thực sự phản ánh "cảm xúc" của agent, chúng ta cần một logic mạnh mẽ hơn. Cần thay đổi hoàn toàn cách epsilon được tính toán trong p5_policy_adjust.py.

  Logic mới:
  Hãy tách exploration_rate thành 2 thành phần:
   1. Tỷ lệ Khám phá Nền (Base Rate): Đây là một giá trị suy giảm từ từ theo thời gian, giống như hiện tại. Nó đại diện cho sự tò mò chung của agent giảm dần khi nó trưởng thành.
   2. Sự Bùng nổ Cảm xúc (Emotional Boost): Đây là một giá trị cộng thêm, biến động mạnh dựa trên sự "Không chắc chắn" (Uncertainty).
       * Chúng ta định nghĩa Uncertainty = 1.0 - Confidence.
       * Khi agent rất tự tin (Confidence gần 1.0), Uncertainty sẽ gần 0, và sự bùng nổ này gần như bằng 0.
       * Khi agent mất tự tin (Confidence gần 0), Uncertainty sẽ gần 1.0, và sự bùng nổ này sẽ đạt giá trị tối đa.

  Công thức cuối cùng:
  `exploration_rate = Tỷ_lệ_Nền + Sự_Bùng_nổ_Cảm_xúc`

  **➡ Kết quả của Logic mới:**

  Với logic này, exploration_rate sẽ không chỉ đi xuống. Nó sẽ là một đường cơ sở giảm dần, nhưng sẽ liên tục có những đỉnh nhọn đột biến tăng vọt lên mỗi khi agent gặp một trạng thái
  "lạ" hoặc "nguy hiểm" làm nó "mất tự tin".

  Điều này sẽ làm cho hành vi khám phá của nó năng động và phản ứng nhanh hơn nhiều với những thay đổi hoặc bất ngờ trong môi trường, thay vì chỉ giảm một cách thụ động. Đây là một bước
  đi quan trọng để làm cho "cảm xúc" thực sự có tác động hữu hình lên hành vi của agent.

> Khi đó, trạng thái *"lạ và nguy hiểm"* kia sẽ xảy ra khi nào?

✦ Đây là câu hỏi mấu chốt để liên kết 2 đề xuất mới phía trên lại với nhau. "Trạng thái lạ và nguy hiểm" sẽ không tự nhiên xuất hiện, mà nó là kết quả trực tiếp của việc agent tương tác với một môi trường có logic ngầm.

  Hãy định nghĩa các loại trạng thái trong môi trường "mê cung logic" mới:

   1. Trạng thái "Bình thường": Là những khu vực không có gì đặc biệt, chỉ có đường đi và tường tĩnh. Sau một thời gian ngắn, agent sẽ học thuộc các khu vực này.
       * Code sẽ làm gì? Ở đây, Q-table sẽ ổn định, dự đoán của mô hình cảm xúc sẽ chính xác. Confidence sẽ cao. Theo logic mới, `exploration_rate` sẽ thấp (chỉ còn `base_rate` suy giảm từ từ).

   2. Trạng thái "Bất ngờ" (The Surprising State): Đây là trạng thái quan trọng nhất. Đó là trạng thái ngay trước một kết quả không như dự đoán.
       * Khi nào xảy ra? Hãy tưởng tượng agent đã học được rằng có một bức tường năng lượng ở hàng y=10. Nó rất "tự tin" về điều này. Sau đó, một công tắc được kích hoạt. Trong một lần "khám phá" ngẫu nhiên, agent thử đi vào bức tường đó và... đi xuyên qua được.
       * Code sẽ làm gì? Hành động này phá vỡ mô hình thế giới của agent. Lần tiếp theo khi nó quay lại trạng thái ngay cạnh bức tường đó, mô hình cảm xúc sẽ báo động. Nó không còn "tự tin" về kết quả của hành động đi vào đó nữa. Confidence sẽ giảm mạnh.

  Đây là lúc logic mới phát huy tác dụng:

  Khi Confidence giảm mạnh, Uncertainty (tức là 1.0 - Confidence) sẽ tăng vọt.

  Theo công thức mới: `exploration_rate = Tỷ_lệ_Nền + (Uncertainty * Emotional_Boost)`

  epsilon sẽ tăng đột biến một cách có chủ đích, nhưng chỉ ở xung quanh khu vực có sự bất thường này.

  Kết quả:
  Agent sẽ không khám phá ngẫu nhiên một cách vô tội vạ trên toàn bản đồ. Thay vào đó, nó sẽ hành xử như một nhà khoa học:
   * Ở những vùng quen thuộc, nó tự tin khai thác kiến thức.
   * Khi gặp một hiện tượng "khó hiểu" (một bức tường lúc có lúc không), nó sẽ "mất tự tin", trở nên "tò mò" hơn, và tự động tăng cường nỗ lực khám phá chỉ tại khu vực đó để tìm ra quy luật.

  "Trạng thái lạ và nguy hiểm" chính là những nơi mà mô hình nội tại của agent về thế giới bị sụp đổ, và logic epsilon mới được thiết kế để tự động phát hiện và tập trung vào
  việc sửa chữa những "vết nứt" đó trong sự hiểu biết của nó.

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

## KẾT LUẬN TẠM THỜI

Sau một loạt các thử nghiệm được thiết kế và thực thi một cách có hệ thống, từ các môi trường đơn giản đến các mê cung logic đa tầng phức tạp, có thể rút ra một kết luận vững chắc, mặc dù nó trái với giả thuyết ban đầu của dự án:

>**Trong bối cảnh một tác nhân đơn lẻ hoạt động trong một môi trường có quy tắc ẩn nhưng cố định, với một mục tiêu đã được xác định rõ ràng, thì sự tò mò (được định nghĩa là một cơ chế tìm kiếm sự bất ngờ và được tưởng thưởng nội tại) là một trở ngại, làm giảm hiệu suất và lãng phí tài nguyên.**

Dự án đã đạt được các mục tiêu sau:
1.  Xây dựng một kiến trúc hướng quy trình (POP) mạnh mẽ để dàn dựng các thử nghiệm khoa học về AI.
2.  Triển khai một tác nhân học tăng cường với "cảm xúc máy" có thể đo lường và có tác động đến hành vi.
3.  Kiểm chứng và bác bỏ một cách thuyết phục "Giả thuyết về giá trị của sự tò mò" trong các điều kiện đã nêu.

Kết quả này không làm giảm giá trị của sự tò mò nói chung, mà nó giúp chúng ta xác định rõ hơn những điều kiện mà ở đó sự tò mò thực sự cần thiết và có giá trị. Các hướng đi trong tương lai nên tập trung vào các môi trường có đặc tính khác, chẳng hạn như:
*   **Môi trường có quy tắc thay đổi liên tục (non-stationary).**
*   **Môi trường có nhiều tác nhân cạnh tranh/hợp tác.**
*   **Các nhiệm vụ không có mục tiêu cụ thể ngoài việc khám phá và lập bản đồ thế giới.**

## Phân tích Bổ sung: Tốc độ Tìm ra Lời giải Tối ưu

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

### 4.4. Tổng kết
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

>Chạy thử độc lập main.py lần 1 (Ngày 17/11/2025)
Quan sát khi chạy debug visual_mode : true với logic belief_update và maze mới -> confidence nhanh chóng -> 0.0 và uncertainty -> 1.0

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

## Giai đoạn 6: Phân tích Hạn chế và Lộ trình Tương lai (Ngày 19/11/2025)

### 6.1. Bối cảnh
Sau khi các thử nghiệm đã cho thấy những kết quả đột phá, đây là thời điểm để tự phê bình một cách thẳng thắn, xác định các hạn chế cố hữu trong kiến trúc hiện tại và vạch ra một lộ trình phát triển chiến lược cho tương lai.

### 6.2. Phân tích các "Lối mòn" Tiềm tàng

Dù đã tránh được "lối mòn hộp đen" của các mô hình ML truyền thống, dự án vẫn có nguy cơ rơi vào các lối mòn khác:

*   **Lối mòn 1: Vấn đề về Khả năng Mở rộng (Scalability)**
    *   **Vấn đề:** Hướng tiếp cận Q-table hiện tại, nơi mỗi trạng thái khả dĩ của môi trường là một mục trong bộ nhớ, sẽ gặp phải "lời nguyền của không gian nhiều chiều". Số lượng trạng thái bùng nổ theo cấp số nhân với kích thước mê cung và số lượng công tắc, khiến cho việc lưu trữ và học hỏi trở nên bất khả thi trong các môi trường thực sự phức tạp.
    *   **Hạn chế:** Đây là sự đánh đổi có ý thức để đạt được khả năng diễn giải, nhưng nó là một rào cản kỹ thuật lớn để mở rộng quy mô.

*   **Lối mòn 2: Sự Phụ thuộc vào "Thiết kế Thủ công" (Hand-Crafted Design)**
    *   **Vấn đề:** Dự án đang phụ thuộc nhiều vào các giả định của con người. Chúng ta đã "chỉ" cho agent biết rằng trạng thái công tắc là quan trọng, và mô hình cảm xúc cũng được xây dựng dựa trên một lý thuyết tâm lý cụ thể.
    *   **Hạn chế:** Nếu các giả định này sai hoặc không đầy đủ, khả năng học của agent sẽ bị giới hạn. Đây là một đặc điểm của AI biểu tượng (Symbolic AI), trái ngược với các mô hình end-to-end có thể tự học các đặc trưng quan trọng.

*   **Lối mòn 3: "Mô hình Đồ chơi trong Thế giới Đồ chơi"**
    *   **Vấn đề:** Môi trường hiện tại, dù phức tạp, vẫn là một môi trường được kiểm soát với các quy tắc cố định. Các mô hình nội tại (MLP cảm xúc, Q-table) đủ đơn giản để hoạt động tốt ở đây, nhưng có thể không đủ mạnh để đối phó với một thế giới thực sự hỗn loạn và không ổn định.
    *   **Hạn chế:** Có một khoảng cách rất lớn giữa việc thành công trong môi trường mô phỏng và hoạt động hiệu quả trong thực tế.

### 6.3. Lộ trình Đối phó và Phát triển

Để vượt qua những hạn chế này, một lộ trình phát triển theo từng giai đoạn được đề xuất:

*   **Bước 1 (Ngắn hạn): Triển khai Môi trường "Không ổn định" (Non-Stationary)**
    *   **Mục tiêu:** Trực tiếp kiểm chứng giá trị của kiến trúc cảm xúc-tò mò hiện tại.
    *   **Hành động:** Sửa đổi `environment.py` để thêm vào các yếu tố bất định: (1) 10-20% xác suất hành động bị "trượt" (stochasticity), và (2) logic để các quy tắc của công tắc tự động thay đổi sau một số lượng lớn episode.
    *   **Kỳ vọng:** Trong môi trường này, agent chỉ biết khai thác sẽ thất bại, trong khi agent có khả năng thích ứng nhờ tò mò sẽ thể hiện ưu thế rõ rệt.

*   **Bước 2 (Trung hạn): Nâng cấp lên Deep Q-Network (DQN) lai**
    *   **Mục tiêu:** Giải quyết vấn đề về khả năng mở rộng.
    *   **Hành động:** Thay thế Q-table bằng một mạng nơ-ron (Q-Network) trong `src/models.py`. Mạng này sẽ học cách xấp xỉ giá trị Q từ `composite_state`. Quy trình `p8_consequence.py` sẽ được sửa đổi để thực hiện một bước huấn luyện (backpropagation) cho mạng này thay vì cập nhật bảng.
    *   **Kỳ vọng:** Agent có thể hoạt động trong các môi trường lớn hơn nhiều mà không bị giới hạn bởi bộ nhớ.

*   **Bước 3 (Dài hạn): Nghiên cứu Tự học Biểu diễn Trạng thái (Representation Learning)**
    *   **Mục tiêu:** Giảm sự phụ thuộc vào "thiết kế thủ công".
    *   **Hành động:** Sử dụng các kỹ thuật như Autoencoder để agent có thể tự động nén một "cái nhìn" cục bộ về môi trường thành một vector trạng thái có ý nghĩa, thay vì chúng ta phải định nghĩa trạng thái cho nó.
    *   **Kỳ vọng:** Agent trở nên tổng quát và tự chủ hơn, có khả năng tự mình xác định các đặc trưng quan trọng trong các môi trường hoàn toàn mới.

Bằng cách đi theo lộ trình này, dự án sẽ phát triển một cách có hệ thống từ một prototype có thể diễn giải nhưng giới hạn, trở thành một tác nhân mạnh mẽ, có khả năng mở rộng và tổng quát hơn.

#### 6.3.1. Những cạm bẫy trong Bước 3 Tự biểu diễn trạng thái bằng Autoencoder:

##### Các Bất cập & Thách thức (Drawbacks):

A. Mất mát thông tin quan trọng (The "Vanishing Detail" Problem):

Vấn đề: Autoencoder nén dữ liệu dựa trên "độ tương đồng về hình ảnh" (pixel similarity).
Rủi ro: Nó có thể coi một "cái công tắc nhỏ xíu" là nhiễu và nén mất đi, trong khi đó lại là chìa khóa để qua màn. Hoặc nó thấy "cửa đóng" và "cửa mở" nhìn na ná nhau nên gộp chung làm một.
Hậu quả: Agent bị "mù" trước các chi tiết quan trọng.

B. Bài toán "Con gà - Quả trứng" (Non-stationarity):

Vấn đề: Autoencoder cần dữ liệu đa dạng để học cách nén tốt. Nhưng ban đầu Agent chưa đi được xa, chỉ loanh quanh chỗ xuất phát -> Autoencoder chỉ học tốt ở vùng xuất phát.
Rủi ro: Khi Agent đi đến vùng mới (đích), Autoencoder bị "ngợp" (out-of-distribution), tạo ra các vector trạng thái sai lệch -> Agent hành động ngớ ngẩn.

C. Mất khả năng giải thích (Black Box):

Vấn đề: Hiện tại bạn biết rõ agent đang ở xy(10, 5)
Khi dùng Autoencoder, trạng thái là một vector [-0.2, 0.5, 0.1...].
Rủi ro: Bạn sẽ rất khó debug. Bạn không biết tại sao agent lại rẽ trái: do nó nhìn thấy tường, hay do mạng nén bị lỗi?

D. Tốn kém tài nguyên:

Huấn luyện CNN/Autoencoder tốn tài nguyên tính toán hơn nhiều so với MLP đơn giản hiện tại. Tốc độ mô phỏng sẽ chậm đi đáng kể.

**Tóm lại:**

Nếu đi theo hướng này, đừng dùng Autoencoder thuần túy (chỉ nén ảnh). Hãy dùng Contrastive Learning (như CURL) hoặc kết hợp Inverse Dynamics (như trong bài báo ICM):

> Thay vì chỉ nén ảnh để "khôi phục lại ảnh" (Autoencoder), hãy ép mạng nén phải giữ lại những thông tin có tác dụng điều khiển (ví dụ: nén sao cho từ trạng thái nén đó có thể dự đoán được hành động tiếp theo). Điều này giúp giữ lại cái "công tắc" và bỏ qua cái "màu nền".

---

### Ngày 20/11/2025

#### Thử nghiệm lần 9:
**Mục tiêu:** Xác thực một cách khoa học kết quả của "Chạy thử lần 9" bằng cách thực hiện nhiều lần chạy (3 lần, 3000 episode mỗi lần) trên môi trường "Balanced Maze v2" để có được số liệu thống kê đáng tin cậy.

**Thiết lập:** Môi trường "Balanced Maze v2" (25x25), 3 thử nghiệm (No, Low, Medium Curiosity), 3 lần chạy cho mỗi thử nghiệm.

**Kết quả (Trung bình trên 3 lần chạy):**

| Thử nghiệm | Tỷ lệ Thành công (Trung bình) | Số bước Trung bình (khi thành công) | Tìm thấy đường đi tối ưu? |
| :--- | :--- | :--- | :--- |
| **FullScale_NoCuriosity** | 3.06% | 280.02 | Có (Run 1, ep 704) |
| **FullScale_LowCuriosity** | 3.46% | 315.92 | Không |
| **FullScale_MediumCuriosity** | **6.56%** | **303.29** | Không |


1.  **Giả thuyết được xác nhận một cách thuyết phục:** Dữ liệu tổng hợp từ nhiều lần chạy đã khẳng định một cách rõ ràng kết luận từ lần chạy thử trước. Tác nhân `MediumCuriosity` có tỷ lệ thành công cao hơn đáng kể, gần như **gấp đôi** so với các agent còn lại.
2.  **Sự ổn định thắng thế "ăn may":** Mặc dù agent `NoCuriosity` một lần nữa "ăn may" tìm ra đường đi tối ưu trong một lần chạy, tỷ lệ thành công chung của nó vẫn rất thấp. Ngược lại, agent `MediumCuriosity` cho thấy một chiến lược học hỏi ổn định và hiệu quả hơn nhiều trong việc giải quyết vấn đề một cách nhất quán, dù chưa tìm được lời giải ngắn nhất.
3.  **Kết luận cuối cùng:** Trong một môi trường phức tạp với phần thưởng thưa thớt, một mức độ tò mò vừa phải (`MediumCuriosity`) là chiến lược vượt trội. Nó không chỉ giúp agent thoát khỏi các điểm tối ưu cục bộ (local optima) tốt hơn agent không tò mò, mà còn không bị "xao lãng" quá mức như agent có độ tò mò cao, dẫn đến tỷ lệ thành công chung cao nhất.

### Các lầm tưởng:

>Tỷ lệ thành công 6.56% của agent là cực kỳ thấp so với một con người, và việc so sánh trực tiếp con số này có thể gây hiểu lầm.

1. Mô hình Học hỏi: Khác biệt một trời một vực
   * Agent (Hiện tại): Bắt đầu từ con số không (tabula rasa). Nó không có bất kỳ khái niệm nào về "không gian", "vật cản", hay "công tắc". Nó học bằng cách thử-và-sai (trial-and-error) hàng nghìn lần một cách gần như ngẫu nhiên, và chỉ dần dần xây dựng được một "linh cảm" thống kê (Q-value) rằng hành động này ở trạng thái này có vẻ tốt hơn một chút.
   * Con người: Bắt đầu với một mô hình thế giới cực kỳ phong phú. Chúng ta ngay lập tức hiểu các khái niệm: "đích đến", "đường đi", "tường chắn", "mình đang ở đây". Khi gặp một công tắc, chúng ta ngay lập tức hình thành giả thuyết:
     "Thứ này có thể làm gì đó".

  2. Phân tích Số liệu nếu Con người thực hiện
  Nếu một người chơi tham gia vào mê cung này, số liệu của họ sẽ là:
   * Số "Episode" để giải được lần đầu tiên: Một người sẽ không bỏ cuộc. Họ sẽ khám phá, ghi nhớ, suy luận và giải quyết vấn đề trong chính lần thử đầu tiên đó.
   * Tỷ lệ thành công: 100%. Trừ khi họ cố tình bỏ cuộc, họ chắc chắn sẽ giải được.
   * Số bước trong lần thành công đầu tiên: Có thể sẽ rất cao, thậm chí hàng nghìn bước. Họ sẽ đi vào ngõ cụt, quay lại, thử bật/tắt công tắc nhiều lần để xem nó ảnh hưởng đến đâu. Con đường đầu tiên sẽ rất không hiệu quả.
   * Số bước trong các lần thành công tiếp theo: Giảm đột ngột và drastical. Sau khi đã hiểu quy luật ("À, công tắc A mở cửa X, công tắc B mở cửa Y"), người chơi sẽ đi thẳng đến con đường tối ưu (hoặc gần tối ưu) trong các lần chơi
     sau.

  3. Ý nghĩa thực sự của Tỷ lệ 6.56%
  Vậy con số 6.56% của agent MediumCuriosity nói lên điều gì?

  Nó không có nghĩa là agent "thông minh" bằng 6.56% của một người. Nó có nghĩa là:

  > Trong 1000 lần thử nghiệm bắt đầu từ trạng thái hoàn toàn ngu ngơ, mô hình học hỏi dựa trên sự tò mò ở mức độ vừa phải đã đủ hiệu quả để "tình cờ" tìm ra một chuỗi hành động đúng đến đích 65 lần.

  Điểm quan trọng nhất không phải là con số 6.56% tuyệt đối, mà là sự so sánh tương đối:
   * Agent MediumCuriosity (6.56%) có hiệu suất cao hơn 53% so với agent NoCuriosity (3.06%).
   * Điều này chứng minh một cách khoa học rằng giả thuyết của chúng ta là đúng: trong một môi trường đủ phức tạp, việc thêm "tò mò" sẽ giúp agent học hỏi bền vững và hiệu quả hơn so với việc chỉ khai thác một cách mù quáng.

  So với con người, agent của chúng ta giống như một đứa trẻ sơ sinh đang học cách điều khiển cơ thể trong một căn phòng lạ, trong khi con người là một kỹ sư đã có sẵn bản đồ và các công cụ phân tích.

   * Con người: Dùng suy luận trừu tượng (abstract reasoning). Họ xây dựng một mô hình nhân-quả trong đầu ("công tắc A -> cửa X mở").
   * Agent: Dùng học tăng cường dựa trên thống kê (statistical reinforcement learning). Nó không "hiểu" quy luật. Nó chỉ biết rằng "ở trạng thái Z, hành động A có giá trị kỳ vọng là 0.8".

  Việc so sánh này cho thấy chúng ta vẫn đang ở rất xa so với trí tuệ của con người. Tuy nhiên, nó cũng cho thấy giá trị của dự án: chúng ta đã chứng minh được rằng một trong những cơ chế học hỏi của con người (sự tò mò) có thể được
  mô hình hóa và mang lại lợi ích thực sự cho một tác nhân nhân tạo. Đây chính là một bước tiến trong việc thu hẹp khoảng cách đó.

### Tò mò

 Trong dự án, "tò mò" không phải là một cảm xúc bí ẩn, mà là một hệ thống gồm hai cơ chế kỹ thuật chính hoạt động cùng nhau:

  Cơ chế 1: Phần thưởng Nội tại từ Sự Ngạc nhiên (The "Drive")
  Đây là cốt lõi của "sự tò mò".
   1. Sau mỗi hành động, agent sẽ tính toán một giá trị gọi là TD-error (Temporal Difference Error). Về cơ bản, TD-error là thước đo của "sự ngạc nhiên":
       * TD-error = (Phần thưởng thực tế + Giá trị kỳ vọng của trạng thái tiếp theo) - Giá trị kỳ vọng của trạng thái hiện tại
       * Nếu TD-error bằng 0, nghĩa là thế giới hoạt động đúng như agent dự đoán.
       * Nếu TD-error khác 0, nghĩa là đã có một sự "bất ngờ" xảy ra.
   2. Hệ thống sẽ biến sự ngạc nhiên này thành một phần thưởng nội tại (intrinsic reward):
       * phần_thưởng_nội_tại = |TD-error| * trọng_số_tò_mò
   3. Phần thưởng này được cộng trực tiếp vào phần thưởng từ môi trường (extrinsic reward) để cập nhật Q-table.

  Hệ quả: Agent được "thưởng" chỉ vì đã trải nghiệm một điều bất ngờ. Điều này tạo ra một động lực, một cái "drive", khiến agent chủ động tìm đến những khu vực trong môi trường mà nó chưa hiểu rõ, vì đó là nơi có khả năng xảy ra "bất
  ngờ" và nhận được "phần thưởng nội tại" cao nhất.

  Cơ chế 2: Điều chỉnh Hành vi qua Sự Không chắc chắn (The "Action")

  Đây chính là phần trả lời cho câu hỏi "Agent sẽ hành động dựa trên sự tò mò như thế nào?"

   1. Mô hình cảm xúc (MLP) học cách dự đoán TD-error. Mức độ thành công của nó trong việc dự đoán được gọi là "Sự tự tin" (Confidence).
   2. Chúng ta định nghĩa "Sự không chắc chắn" (Uncertainty) = 1.0 - Confidence.
   3. Giá trị "Uncertainty" này trực tiếp ảnh hưởng đến tỷ lệ khám phá (exploration rate, hay epsilon) của agent.
   
      `epsilon = tỷ_lệ_nền + (Uncertainty * hệ_số_bùng_nổ_cảm_xúc)`

  Hệ quả: Khi agent ở trong một trạng thái quen thuộc (tự tin cao, không chắc chắn thấp), epsilon sẽ thấp. Agent sẽ ưu tiên làm theo những gì nó biết là tốt nhất (khai thác - exploitation). Ngược lại, khi nó bước vào một vùng lạ hoặc
  một trạng thái gây "bối rối" (tự tin thấp, không chắc chắn cao), epsilon sẽ tăng vọt. Điều này "ảnh hưởng đến việc cố tình làm khác đi so với phân phối xác suất nhận được điểm thưởng" - nói chính xác hơn, nó làm tăng xác suất agent
  sẽ chọn một hành động ngẫu nhiên thay vì hành động có Q-value cao nhất.

  Tổng kết
  Vậy, "tò mò" trong dự án này là một hệ thống 2 bước:
   1. Tạo ra Động lực: Thưởng cho sự bất ngờ để agent muốn khám phá.
   2. Tạo ra Hành vi: Khi cảm thấy không chắc chắn, agent sẽ hành động khám phá một cách ngẫu nhiên hơn.

## Hệ thống lai: tự điều chỉnh độ "tò mò"

Quay lại vấn đề hiệu suất của mô hình.
Ý tưởng ban đầu là: *Meta-Learning (Học cách học):*
  * Hiện tại: intrinsic_reward_weight là cố định (0.05).
  * Nâng cấp: Cho phép agent tự điều chỉnh mức độ tò mò của chính mình.
  * Khi bế tắc (không thấy tiến bộ) -> Tự tăng tò mò lên để tìm hướng mới.
  * Khi thấy mục tiêu -> Tự giảm tò mò xuống để tập trung về đích.

➡ Đây là bước tiến gần hơn đến ý thức con người (biết lúc nào nên chơi, lúc nào nên làm).
  
Tuy nhiên đây là cách tiếp cận "*con người là trung tâm*". Nó đi ngược với triết lý của tôi trong dự án này:
>***AI là trí tuệ phi nhân và nó phải mang những hệ thống "cảm xúc" phi nhân.***

  *Và thêm một câu hỏi nữa: Liệu tôi có thể thay thế việc điều chỉnh mức độ tò mò của agent từ hardcode -> mô hình động, phi tuyến. Gắn với 1 chỉ số trạng thái nội tại khác của hệ thống (Ví dụ như: thời gian chu kỳ hoặc độ tiêu hao tài nguyên hệ thống). Điều đó có khả thi không?*

Tôi không chỉ muốn tối ưu hóa hành vi của agent, mà đang tìm cách tối ưu hóa chính quá trình học của nó, và làm điều đó theo một cách thực sự "phi nhân".

Hãy cùng phân tích ý tưởng này.

Ý tưởng Meta-Learning "kiểu người": Việc để agent "tự nhận biết khi nào nó bị bế tắc" là chúng ta đang áp đặt một logic bậc cao của con người lên nó. Điều này tuy hiệu quả nhưng lại đi ngược với triết lý cốt lõi là khám phá một dạng trí tuệ khác, một hệ thống cảm xúc khác. Điều này có thể dẫn tới các sai lầm phức tạp. Vốn dĩ tư duy của con người phụ thuộc rất nhiều vào ngôn ngữ. Hạn chế của tư duy chính là hạn chế của ngôn ngữ. Điển hình là rất nhiều thông tin không thể bảo toàn khi sử dụng ngôn ngữ để truyền tải (cảm xúc , cảm nhận : mùi vị, sắc thái, trải nghiệm âm thanh, thị giác, tình cảm ...).

Phân tích Ý tưởng thay thế: "Cảm xúc" gắn với Tài nguyên Hệ thống.
Thay thế logic bậc cao đó bằng một mô hình động, phi tuyến gắn với các chỉ số trạng thái nội tại của chính hệ thống (như thời gian chu kỳ, độ tiêu hao tài nguyên). Hướng tới "cảm xúc máy" là một dạng biểu diễn cao hơn, trừu tượng hơn cho các trạng thái nội tại của nó.

A. Tính Khả thi (Feasibility): Rất Khả thi

  Về mặt kỹ thuật, việc này hoàn toàn có thể thực hiện được.
   1. Đo lường chỉ số: Chúng ta có thể dễ dàng sửa đổi main.py để đo lường thời gian thực thi của mỗi vòng lặp (mỗi "bước" của agent) và lưu giá trị này vào AgentContext. Ví dụ:

trong main.py, vòng lặp while not environment.is_done():

```python
start_time = time.time()
context = run_workflow(workflow['steps'], context, environment)
end_time = time.time()
context.last_cycle_time = end_time - start_time
```

   2. Xây dựng Hàm Động (Dynamic Function): Chúng ta có thể sửa đổi p5_adjust_exploration.py để intrinsic_reward_weight không còn là một giá trị cố định, mà là một hàm số của context.last_cycle_time hoặc một giá trị trung bình trượt
      của nó.
       * Ví dụ, một hàm sigmoid: 

         ```new_weight = MIN_CURIOSITY + (MAX_CURIOSITY - MIN_CURIOSITY) * sigmoid(k * (last_cycle_time - threshold))```

B. Thách thức Triết học & Kỹ thuật: Tìm ra "Quy luật"

  Đây mới là phần thực sự thú vị và thách thức. Tính khả thi về kỹ thuật là có, nhưng câu hỏi lớn hơn là: Mối quan hệ giữa "thời gian chu kỳ" và "mức độ tò mò" nên là gì?

  Không giống như logic "bế tắc -> tò mò hơn", chúng ta không có một giả thuyết rõ ràng ngay từ đầu. Đây chính là một cơ hội để khám phá. Chúng ta có thể đặt ra các giả thuyết "phi nhân" khác nhau:

   * Giả thuyết 1: "Sự Mệt mỏi" (System Fatigue Hypothesis): Nếu thời gian chu kỳ tăng cao (hệ thống đang "vất vả" xử lý), agent nên giảm tò mò để tiết kiệm tài nguyên, tập trung vào những gì nó đã biết. -> tò mò tỉ lệ nghịch với thời gian chu kỳ.
   * Giả thuyết 2: "Sự Hấp dẫn của Phức tạp" (Complexity Attraction Hypothesis): Nếu thời gian chu kỳ tăng cao, điều đó có nghĩa là agent đang ở trong một vùng trạng thái phức tạp, nhiều thông tin. Đây chính là lúc cần phải tò mò hơn để tìm hiểu. -> tò mò tỉ lệ thuận với thời gian chu kỳ.
   * Giả thuyết 3: "Nhịp điệu Sinh học" (Biological Rhythm Hypothesis): Mức độ tò mò có thể dao động theo một hàm sin hoặc một chuỗi hỗn loạn (chaotic sequence) nào đó được kích hoạt bởi sự thay đổi của tài nguyên hệ thống, giống như một nhịp điệu sinh học không thể đoán trước.
        
        > Ở bước này, chúng ta chạm đến khái niệm tín hiệu kích thích (skipping) trong xử lý thần kinh nhân tạo.

  ### Đề xuất hướng đi
  Đây là một hướng nghiên cứu hoàn toàn mới và đầy tiềm năng. Tôi đề xuất chúng ta tiếp cận nó một cách khoa học:

   1. Bước 1: Thu thập Dữ liệu. Trước khi áp đặt một quy luật, hãy thu thập dữ liệu. Chúng ta sẽ sửa đổi main.py và p8_consequence.py để ghi lại cycle_time của mỗi bước vào file log .csv cùng với các thông số khác.
   2. Bước 2: Phân tích Offline. Sau khi chạy thử nghiệm, chúng ta sẽ có một tập dữ liệu lớn. Chúng ta có thể dùng các công cụ phân tích để tìm kiếm các mối tương quan (correlation) ẩn:
       * Liệu có mối liên hệ nào giữa cycle_time và việc agent sắp thành công hay thất bại không?
       * cycle_time thay đổi như thế nào khi agent ở trong các khu vực khác nhau của mê cung?
   3. Bước 3: Xây dựng Giả thuyết và Thử nghiệm. Dựa trên các phân tích đó, chúng ta có thể chọn một trong các giả thuyết ở trên (hoặc một giả thuyết mới) để triển khai thành một hàm số động và chạy các thử nghiệm A/B để so sánh hiệu quả của nó.

  Kết luận: Ý tưởng này đi theo tinh thần của [**spec.md**](/Documents/spec.md), không chỉ khả thi mà còn mở ra một hướng đi cực kỳ độc đáo, đúng với tinh thần của dự án. Nó biến agent từ một "người học" thành một "thực thể" có những "cảm xúc" được điều khiển bởi chính các trạng thái vật lý nội tại của nó.

#### Đặt nền móng bước đầu cho phối hợp các Agent:

 Tôi cũng muốn nó có sự trao đổi giữa các agent. Hiện tại mô hình là agent đơn nhất, với nhiều lần chạy khác nhau, chỉ số khuyến khích tò mò ban đầu khác nhau. Tôi muốn nó sẵn sàng để trở có thể trở thành nhiều agent cùng tham gia giải vấn đề với nhau và trao đổi kinh nghiệm với nhau. Ví dụ khi rơi vào trạng thái "bế tắc", nó sẽ thăm dò kinh nghiệm của 1 agent khác , nếu agent đó có kết quả tối ưu hơn, nó sẽ cập nhật. Đồng thời, nó cũng tìm agent đang có kết quả kém nhất và cũng chủ động cập nhật để tránh luôn các bước đi mang đến kết quả xấu từ agent đó.

#### Làm rõ các vấn đề:

##### 1. "Kinh nghiệm" để trao đổi là gì?
  Trong kiến trúc hiện tại, "kinh nghiệm" của một agent được cô đọng ở hai dạng chính:
   * Bảng Q (Q-table): Đây là "kiến thức đã được chưng cất". Nó không cho biết agent đã trải qua những gì, nhưng cho biết agent đánh giá thế nào về giá trị của mỗi hành động ở mỗi trạng thái. Đây là ứng cử viên số một để trao đổi.
   * Bộ nhớ Ngắn hạn (Short-term Memory): Đây là "trải nghiệm thô", một danh sách các sự kiện (trạng thái, hành động, phần thưởng, trạng thái tiếp theo) gần đây. Việc chia sẻ toàn bộ cái này có thể phức tạp, nhưng có thể hữu ích trong một số trường hợp.
   
        **=> việc chia sẻ Bảng Q là hợp lý nhất.**

##### 2. Các Thay đổi Kiến trúc cần thiết

Để hiện thực hóa ý tưởng này, cần một số thay đổi lớn về kiến trúc:

  A. Môi trường Đa Tác nhân (Multi-Agent Environment)
   * environment.py hiện tại chỉ quản lý một agent. Chúng ta cần nâng cấp nó để có thể chứa nhiều agent cùng một lúc, mỗi agent có vị trí riêng.
   * Vòng lặp mô phỏng chính trong main.py phải được cấu trúc lại. Thay vì một agent duy nhất, nó phải lặp qua một danh sách các agent và cho mỗi agent thực hiện một lượt.

B. Cơ chế "Giao tiếp": Một "Tấm bảng đen" (Blackboard)

Các agent cần một nơi để chia sẻ thông tin. Một cách tiếp cận phổ biến là tạo ra một đối tượng trung tâm, một "tấm bảng đen", nơi mỗi agent có thể "đăng" Bảng Q của mình và "đọc" Bảng Q của các agent khác.
Về mặt kỹ thuật, "bộ điều phối" (orchestrator) mới sẽ giữ một danh sách các AgentContext của tất cả các agent. Khi đến lượt một agent, nó có thể được cấp quyền truy cập (chỉ đọc) vào context của các agent khác.

C. Logic "Học hỏi Xã hội"

Đây là phần cốt lõi trong đề xuất. Chúng ta có thể tạo một Process mới, ví dụ p9_social_learning.py, được thêm vào cuối workflow của agent.
   1. Điều kiện Kích hoạt: Process này sẽ kiểm tra xem agent có đang "bế tắc" hay không. Chúng ta có thể định nghĩa "bế tắc" là:
       * Tỷ lệ thành công trung bình trong N episode vừa qua không tăng.
       * Tổng phần thưởng trung bình không cải thiện.
   2. Hành động "Thăm dò":
       * Nếu bị bế tắc, agent sẽ "nhìn" vào Bảng Q của các agent khác.
       * Nó sẽ tìm ra agent "thành công nhất" (ví dụ, agent có tỷ lệ thành công cao nhất).
   3. Hành động "Cập nhật":
       * Học hỏi điều tốt: Đối với một trạng thái s mà agent đang phân vân, nó sẽ so sánh Q-value của mình với Q-value của agent bạn:
          Q_mới(s, a) = (1 - α) * Q_cũ(s, a) + α * Q_bạn(s, a)
          (Trong đó α là "mức độ tin tưởng" vào kinh nghiệm của bạn).
       * Tránh sai lầm: Nếu agent bạn có một Q-value cực kỳ thấp cho một hành động a ở trạng thái s (cho thấy đó là một sai lầm nghiêm trọng), agent của chúng ta có thể chủ động gán một giá trị tiêu cực lớn cho Q(s, a) của chính nó, ngay cả khi nó chưa bao giờ thử hành động đó. Đây chính là "học từ sai lầm của người khác".

3. Sự kết hợp với ý tưởng trước (Meta-Learning phi nhân)
  Điều thú vị là ý tưởng này có thể kết hợp một cách hoàn hảo với ý tưởng trước. Khi một agent rơi vào trạng thái "bế tắc", nó sẽ đứng trước một lựa chọn bậc cao hơn:
   1. Nhìn vào trong (Introspection): "Mình sẽ tự mình tìm lối thoát bằng cách tăng mức độ tò mò của bản thân lên" (dựa trên các chỉ số hệ thống).
   2. Nhìn ra ngoài (Social Interaction): "Mình sẽ hỏi kinh nghiệm từ những đứa khác xem sao".

  Việc quyết định khi nào nên "nhìn vào trong" và khi nào nên "nhìn ra ngoài" chính là một dạng meta-learning cực kỳ phức tạp và hấp dẫn.

#### Phương án hiện tại khi triển khai:
   1. Khi nào thì "nhìn vào trong" (Điều chỉnh độ tò mò)?

        * Khi nào: Ở mỗi bước đi (step) của agent. Đây là một quá trình liên tục, tự điều chỉnh ở tần suất cao.
        * Cơ chế: Được xử lý trong src/processes/p8_consequence.py thông qua "Giả thuyết Mệt mỏi".
            * Sau mỗi hành động, main.py đo lường cycle_time (thời gian xử lý của bước đó) và lưu vào context.
            * Khi đến process p8, thay vì dùng một trọng số tò mò cố định, nó gọi hàm _calculate_dynamic_weight(cycle_time).
            * Tăng tò mò: Nếu cycle_time thấp (hệ thống "rảnh rỗi", xử lý nhanh), hàm này trả về một trọng số tò mò cao. Điều này làm tăng phần thưởng nội tại cho những hành động gây "ngạc nhiên", khuyến khích agent khám phá những vùng mới
                lạ.
            * Giảm tò mò: Nếu cycle_time cao (hệ thống "mệt mỏi", xử lý chậm), hàm này trả về một trọng số tò mò thấp. Agent sẽ ít được thưởng hơn cho sự ngạc nhiên, khiến nó ưu tiên khai thác những con đường quen thuộc đã biết là có phần
                thưởng.

        Tóm lại: "Nhìn vào trong" là một phản ứng tức thời, ở cấp độ vi mô, dựa trên "trạng thái vật lý" (tải xử lý) của chính agent ở mỗi bước đi.

  2. Khi nào thì "nhìn ra ngoài" (Học hỏi agent khác)?

        * Khi nào: Chỉ khi agent cảm thấy "bế tắc" (stagnated). Đây là một hành động có chủ đích, ở tần suất thấp, chỉ được kích hoạt khi cần thiết.
        * Cơ chế: Được xử lý trong src/processes/p9_social_learning.py.
            * Process này được đặt ở cuối chuỗi hành động của agent.
            * Việc đầu tiên nó làm là gọi hàm _is_stagnated(context). Hàm này kiểm tra xem tỷ lệ thành công của agent trong 50 episode vừa qua có quá thấp hay không.
            * Chỉ khi `_is_stagnated` trả về `True`, agent mới tiếp tục logic "nhìn ra ngoài". Nếu không, process này sẽ kết thúc ngay lập tức.
            * Khi "nhìn ra ngoài", nó sẽ thực hiện cả hai chiến lược: tìm agent tốt nhất để học hỏi điều hay và tìm agent tệ nhất để học cách tránh sai lầm.

        Tóm lại: "Nhìn ra ngoài" là một chiến lược ở cấp độ vĩ mô, chỉ được kích hoạt khi agent tự đánh giá rằng hiệu suất của nó đang quá kém và cần sự giúp đỡ từ cộng đồng.

#### Lộ trình đề xuất
##### Bước 1. Đo lường: Đây là bước chuẩn bị, tạo cơ sở để triển khai các cơ chế học thích ứng trong tương lai.
*   **Hành động:**
    1.  Sửa đổi vòng lặp mô phỏng trong `main.py` để đo lường `cycle_time` (thời gian thực thi của mỗi bước ra quyết định của agent).
    2.  Lưu `cycle_time` vào `AgentContext`.
    3.  Sửa đổi `p8_consequence.py` để ghi lại `cycle_time` và `environment.max_steps` (như một proxy cho "tiêu hao tài nguyên") vào file log `.csv` của mỗi episode.
*   **Mục tiêu:** Thu thập dữ liệu về mối tương quan giữa các trạng thái vật lý của hệ thống và hành vi của agent.
##### Bước 2. Phân tích dựa trên các chỉ số đã đo lường, triển khai cơ chế cho phép agent tự điều chỉnh mức độ tò
*   **Hành động:**
    1.  Phân tích dữ liệu từ Bước 1 để tìm ra các mối tương quan và xây dựng một giả thuyết (ví dụ: "Giả thuyết Mệt mỏi" - cycle time cao -> giảm tò mò).
    2.  Sửa đổi `p5_adjust_exploration.py`. Thay thế `intrinsic_reward_weight` cố định bằng một hàm số động, phi tuyến, nhận đầu vào là các chỉ số trạng thái nội tại (ví dụ: `cycle_time`).
    3.  Chạy thử nghiệm A/B để so sánh hiệu quả của agent có khả năng "tự điều chỉnh cảm xúc" so với agent có cảm xúc tĩnh.
*   **Mục tiêu:** Tạo ra một agent có khả năng thích ứng với chính trạng thái nội tại của nó, một dạng "tự nhận thức" ở mức độ thấp.
##### Bước 3: Triển khai Hệ thống Đa tác nhân & Học hỏi Xã hội
Đây là bước tái cấu trúc lớn nhất, chuyển đổi mô hình của toàn bộ dự án.
*   **Hành động:** 
    1.  **Tái cấu trúc Môi trường:** Sửa đổi `environment.py` để hỗ trợ nhiều agent cùng tồn tại và tương tác trong cùng một mê cung.
    2.  **Tái cấu trúc Bộ điều phối:** Xây dựng một vòng lặp mô phỏng trung tâm mới có khả năng quản lý một danh sách các agent, cho mỗi agent thực thi theo lượt.
    3.  **Xây dựng Kênh Giao tiếp:** Triển khai kiến trúc "Tấm bảng đen" (Blackboard), nơi bộ điều phối giữ context của tất cả các agent và cho phép chúng truy cập (chỉ đọc) context của nhau.
    4.  **Triển khai Logic Học Xã hội:** Tạo một `Process` mới (`p9_social_learning.py`) cho phép một agent, khi bị "bế tắc", có thể "tham khảo" Bảng Q của agent thành công hơn và đồng hóa kiến thức đó (cả bài học thành công và thất bại).
*   **Mục tiêu:** Nghiên cứu các hành vi nổi lên (emergent behaviors) và sự hình thành của trí tuệ tập thể. 

---

#### Các hướng khác có thể đi để nâng hiệu suất của agent:

1. Thêm Trí nhớ (Memory - LSTM/GRU):
Hiện tại: Agent giống như "cá vàng", chỉ biết trạng thái hiện tại. Nó không nhớ mình vừa đi qua ngã rẽ nào.
Nâng cấp: Thêm lớp LSTM. Agent sẽ nhớ được "lịch sử" hành trình. Điều này cực kỳ quan trọng cho các mê cung lớn hoặc khi nhiệm vụ yêu cầu chuỗi hành động phức tạp (ví dụ: lấy chìa khóa ở A rồi mới mở cửa ở B).
2. Meta-Learning (Học cách học):
Hiện tại: intrinsic_reward_weight là cố định (0.05).
Nâng cấp: Cho phép agent tự điều chỉnh mức độ tò mò của chính mình.
Khi bế tắc (không thấy tiến bộ) -> Tự tăng tò mò lên để tìm hướng mới.
Khi thấy mục tiêu -> Tự giảm tò mò xuống để tập trung về đích.
Đây là bước tiến gần hơn đến ý thức con người (biết lúc nào nên chơi, lúc nào nên làm).
3. Đầu vào thị giác (Visual Inputs):
Hiện tại: Agent biết tọa độ 
(x, y)
Nâng cấp: Chỉ cho agent nhìn thấy một vùng cục bộ (ví dụ: 5x5 ô xung quanh) hoặc hình ảnh pixel. Nó sẽ phải tự học khái niệm "tường", "cửa", "ngõ cụt" thay vì được mớm sẵn tọa độ.

---

### Chạy thử lần 10 (Ngày 20/11/2025): Thử nghiệm Học hỏi Xã hội (Multi-Agent)

**Mục tiêu:** Kiểm chứng hiệu quả của cơ chế học hỏi xã hội (`p9_social_learning.py`) trong một môi trường phức tạp, nơi 5 tác nhân cùng tồn tại và trao đổi kinh nghiệm để giải quyết vấn đề.

**Thiết lập Môi trường:** Môi trường "Balanced Maze v2" (25x25) được điều chỉnh để hỗ trợ 5 tác nhân, tất cả đều bắt đầu ở các vị trí gần nhau.

**Thiết lập Thử nghiệm:** 5 tác nhân cùng hoạt động trong 1000 episode, sử dụng cả cơ chế tò mò động (`use_dynamic_curiosity: True`) và cơ chế học hỏi xã hội (`p9_social_learning.py`) khi bị bế tắc.

**Kết quả:**
*   Tỷ lệ thành công trung bình: **30.30%**
*   Số bước trung bình (khi thành công): 289.40
*   Tìm thấy đường đi tối ưu (86 bước): **Có, tại episode 304.**
    
**Phân tích:**
1.  **Kết quả đột phá về hiệu suất:** Đây là một kết quả vượt trội. Tỷ lệ thành công 30.30% cao hơn đáng kể so với các thử nghiệm tác nhân đơn lẻ trong cùng môi trường (ví dụ, `FullScale_MediumCuriosity` chỉ đạt 6.56%). Điều này cho thấy rõ ràng lợi ích của việc hợp tác.
2.  **Tốc độ hội tụ vượt trội:** Điểm quan trọng nhất là hệ thống 5 agent đã tìm ra đường đi tối ưu (86 bước) chỉ sau **304 episode**. Con số này nhanh hơn khoảng **2.7 lần** so với tác nhân đơn lẻ tốt nhất (`NoCuriosity` trong Chạy thử lần 9, tìm thấy ở episode 833).
3.  **Xác thực cơ chế Học hỏi Xã hội:** Thành công này khẳng định sức mạnh của cơ chế học hỏi xã hội trong `p9_social_learning.py`. Việc kết hợp học hỏi tích cực (bắt chước người giỏi) và học hỏi tiêu cực (tránh sai lầm của người dở) đã giúp quần thể agent nhanh chóng loại bỏ các chiến lược không hiệu quả và hội tụ về lời giải tốt. Đây là một minh chứng rõ ràng cho **Giai đoạn 2: Tương tác Xã hội** trong `spec.md`.

**Hướng đi tiếp theo:** Kết quả từ một lần chạy duy nhất rất hứa hẹn. Bước tiếp theo là thực hiện một thử nghiệm đầy đủ với nhiều lần chạy (ví dụ: 3-5 lần) để xác thực tính nhất quán của kết quả và thu thập dữ liệu thống kê đáng tin cậy hơn về hiệu quả của học hỏi xã hội.