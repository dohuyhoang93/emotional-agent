# Tổng quan Kiến trúc và Tương tác Hệ thống Agent Cảm xúc

## 1. Triết lý Tổng thể

Hệ thống này không chỉ là một tập hợp các agent học tăng cường (Reinforcement Learning) thông thường. Đây là một nỗ lực mô phỏng một **hệ sinh thái xã hội phức hợp**, nơi các cá nhân sở hữu cả trí thông minh cá nhân và trí thông minh xã hội. Mỗi agent không chỉ học từ môi trường mà còn từ "trạng thái tâm lý" nội tại của chính nó (như sự tự tin, mệt mỏi) và từ thành công hay thất bại của các agent khác.

Kiến trúc này được xây dựng dựa trên sự **phân chia vai trò** rõ ràng:

-   **Agent (Cá nhân):** Tự đưa ra quyết định, tự học hỏi, tự cảm nhận và tự yêu cầu sự giúp đỡ.
-   **Orchestrator (`main.py`):** Đóng vai trò là "Thế giới" hay "Người quản lý Bảng đen", tạo ra môi trường cho các tương tác xã hội nhưng không can thiệp vào quyết định của agent.

## 2. Trí tuệ của một Agent: Hệ thống Điều khiển Hai Tầng

Hành vi của mỗi agent được điều khiển bởi hai vòng lặp lồng vào nhau, mô phỏng hai tầng bậc suy nghĩ: **Cảm tính (tức thời)** và **Lý trí (chiến lược)**.

### Tầng 1: Vòng lặp Nội tại - Cảm tính & Phản ứng Tức thời

Đây là chu trình ra quyết định ở mỗi bước (step) của agent.

1.  **Tính toán Cảm xúc (`p3`):**
    -   Agent đưa trạng thái hiện tại vào một mạng nơ-ron (MLP) để tính toán ra một "vector cảm xúc".
    -   Thành phần quan trọng nhất là **"Sự tự tin" (Confidence)**, phản ánh mức độ agent "hiểu" giá trị của trạng thái hiện tại.

2.  **Điều chỉnh Hành vi (`p5`):**
    -   **Logic:** `Sự tự tin càng thấp -> Sự không chắc chắn (Uncertainty) càng cao -> Tỷ lệ khám phá (Exploration Rate) càng tăng vọt.`
    -   Đây là một **cơ chế phản ứng cảm tính**: Khi agent cảm thấy "sợ hãi" hay không chắc chắn, nó sẽ hành động bốc đồng và ngẫu nhiên hơn để tìm lối thoát. Ngược lại, khi tự tin, nó sẽ tập trung khai thác con đường mà nó cho là tốt nhất.

3.  **Hành động và Ghi nhận Hậu quả (`p6`, `p7`, `p8`):**
    -   Agent hành động và nhận "sự ngạc nhiên" (`td_error`) từ môi trường.
    -   **Cơ chế "Mệt mỏi" (Fatigue):** Đây là một phần của tầng lý trí hoạt động bên trong vòng lặp.
        -   Nếu agent xử lý nhanh (`cycle_time` thấp), nó được xem là "khỏe". Trọng số của **phần thưởng tò mò (intrinsic reward)** sẽ cao, khuyến khích nó khám phá những điều mới mẻ.
        -   Nếu agent xử lý chậm (`cycle_time` cao), nó bị xem là "mệt". Trọng số tò mò sẽ giảm xuống, khiến nó bớt hứng thú với việc khám phá và tập trung hơn vào các mục tiêu đã biết.
    -   `td_error` và `phần thưởng` được dùng để cập nhật Q-table và **huấn luyện lại mạng MLP cảm xúc**, giúp các dự đoán về "Sự tự tin" ngày càng chính xác hơn.

### Tầng 2: Vòng lặp Can thiệp - Lý trí & Học hỏi Xã hội

Đây là cơ chế chiến lược, chỉ được kích hoạt khi một agent rơi vào tình trạng **"bế tắc" (stagnation)** (hoạt động kém hiệu quả trong một thời gian dài).

1.  **Tự nhận thức Bế tắc (`p9`):**
    -   Agent tự kiểm tra lịch sử thành công của mình. Nếu quá thấp, nó sẽ kích hoạt cơ chế học hỏi xã hội.

2.  **Chủ động Tìm kiếm Sự giúp đỡ (`p9`):**
    -   Agent được trao quyền truy cập vào "Bảng đen" (`all_contexts`) từ `main.py`.
    -   Nó **tự mình** phân tích và xác định ai là agent "giỏi nhất" và ai là "tệ nhất" dựa trên lịch sử thành công của họ. Vai trò này **thay đổi liên tục** tùy theo phong độ của cả nhóm.

3.  **Đồng hóa Kiến thức (`p9`):**
    -   **Học từ người giỏi nhất:** Sao chép một phần Q-table của họ. Đây là một cú hích kiến thức cực lớn, giúp agent thoát khỏi điểm tối ưu cục bộ.
    -   **Tránh sai lầm của người tệ nhất:** Gán một giá trị trừng phạt rất lớn vào Q-table của mình cho những hành động đã dẫn đến thất bại của agent tệ nhất.

## 3. Sự Tương tác Phức hợp và Hành vi Nổi bật

Sự kết hợp của các cơ chế trên tạo ra một hệ thống có hành vi phức tạp và tinh vi hơn nhiều so với tổng các thành phần của nó.

-   **Phục hồi từ Bế tắc:** Học hỏi xã hội không chỉ cải thiện Q-table. Kiến thức mới giúp agent hoạt động hiệu quả hơn -> `cycle_time` giảm -> agent hết "mệt" -> agent sẵn sàng tò mò trở lại. Đây là một vòng lặp **phục hồi tâm lý** hoàn chỉnh.

-   **Cân bằng giữa Khai thác và Khám phá:** Agent có hai cách khám phá. Một là khám phá **ngẫu nhiên** khi "sợ hãi", hai là khám phá **có chủ đích** khi nó "khỏe" và tò mò. Sự cân bằng này được điều chỉnh tự động dựa trên cả trạng thái nội tại và hiệu quả hoạt động.

-   **Hệ thống Xã hội Linh hoạt:** Không có một "lãnh đạo" cố định. Bất kỳ agent nào cũng có thể trở thành "thầy" hoặc "tấm gương xấu", tạo ra một cấu trúc xã hội linh hoạt, nơi kiến thức được phổ biến một cách tự nhiên từ những cá nhân thành công.

## 4. Kết luận

Đây là một hệ thống mô phỏng hành vi thông minh ở nhiều cấp độ. Nó không chỉ giải quyết một bài toán trong mê cung, mà còn khám phá cách các yếu tố tâm lý (tự tin, mệt mỏi) và xã hội (học hỏi từ người khác) có thể tương tác với nhau để tạo ra một trí tuệ tập thể có khả năng thích ứng và tự phục hồi.
