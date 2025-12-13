# Chương 7: Mô hình Workflow & Ngôn ngữ DSL

---

## 7.1. Workflow là một Đồ thị (Graph Theory applied)

Trong POP, Workflow không phải là danh sách việc cần làm (ToDo List), mà là một **Đồ thị Thực thi (Execution Graph)**.
Mỗi nút (Node) là một Process. Các cạnh (Edge) là dòng chảy dữ liệu.

Chương này đi sâu vào 4 mô hình đồ thị được hỗ trợ bởi POP Engine và cách định nghĩa chúng bằng ngôn ngữ DSL (Domain Specific Language).

---

## 7.2. Bốn Mô hình Workflow Tiêu chuẩn

### A. Linear (Tuyến tính)
*   **Mô hình:** `Nodes` được nối tiếp nhau thành chuỗi đơn `P1 → P2 → P3`.
*   **Chi tiết:** Đây là dạng cơ bản nhất, đảm bảo thứ tự thực thi tuyệt đối.
*   **Khi nào dùng:** Pipeline nhập liệu (ETL), quy trình tuần tự không rẽ nhánh.
*   **Rủi ro:** Không xử lý được các logic nghiệp vụ phức tạp đòi hỏi điều kiện.
*   **DSL Example:**
    ```yaml
    # Linear Sequence
    steps:
      - call: vision.load_image
      - call: vision.enhancement
      - call: storage.save_raw
    ```

### B. Branching (Rẽ nhánh có điều kiện)
*   **Mô hình:** Tại Node điều kiện, luồng thực thi tách làm đôi: `P1 → if (Context.State) { P2a } else { P2b }`.
*   **Chi tiết:** Cho phép "Logic Business" can thiệp vào dòng chảy.
*   **Pitfall (Cạm bẫy):**
    *   *Implicit Branching:* Cố nhét logic `if/else` vào bên trong Process thay vì khai báo ra ngoài Workflow => Làm ẩn luồng đi.
*   **DSL Example:**
    ```yaml
    steps:
      - branch:
          when: "ctx.quality_score > 0.9" # Business Rule Expression
          then:
            - call: production.fast_track
          else:
            - call: qa.manual_review
    ```

### C. DAG (Directed Acyclic Graph - Song song hóa)
*   **Mô hình:** Một Node cha tách thành nhiều Node con chạy song song, sau đó hợp nhất (Join) lại. `P1 → {P2, P3} → P4`.
*   **Chi tiết:** Tối ưu hóa hiệu năng cho các tác vụ IO-bound hoặc CPU-bound độc lập.
*   **Deep Pitfall: Sự hội tụ trạng thái (State Convergence)**
    *   Vấn đề: P2 sửa `ctx.A`, P3 sửa `ctx.A`. Khi Join lại vào P4, giá trị nào của `ctx.A` được giữ?
    *   Giải pháp: Bắt buộc sử dụng **Merge Strategy** (xem mục 7.3).
*   **DSL Example:**
    ```yaml
    steps:
      - parallel:
          branches:
            - [ call: camera.capture_left ]
            - [ call: camera.capture_right ]
          merge:
            strategy: custom
            function: vision.stereo_merge # Deterministic Merge
    ```

### D. Dynamic (Vòng lặp & Phản hồi)
*   **Mô hình:** Đồ thị có thể chưa xác định lúc khởi chạy, hoặc có chu trình (Cycles) `P1 → P2 → P1`.
*   **Chi tiết:** Dùng cho các hệ thống Agent, Robot Control Loop, hoặc Retry logic.
*   **Deep Pitfall: Bùng nổ trạng thái (State Explosion) & Non-termination.**
    *   Hệ thống có thể chạy mãi mãi nếu không có `Guard Condition` (điều kiện thoát).
    *   Lịch sử Audit Log có thể phình to vô hạn.
*   **DSL Example:**
    ```yaml
    steps:
      - loop:
          until: "ctx.retry_count > 5 OR ctx.status == 'OK'"
          body:
            - call: api.request_data
            - call: logic.validate
    ```

---

## 7.3. Chiến lược Hợp nhất dữ liệu (Merge Strategies)

Khi sử dụng DAG (Song song), việc gộp Context từ các nhánh con là bài toán khó nhất. POP định nghĩa 4 chiến lược chuẩn:

1.  **Chiến lược Overwrite (Last-Writer-Wins):**
    *   *Cơ chế:* Nhánh nào xong sau cùng sẽ ghi đè Context.
    *   *Đánh giá:* **Nguy hiểm**. Chỉ dùng khi các nhánh sửa các vùng nhớ hoàn toàn rời rạc (Process Isolation).

2.  **Chiến lược Aggregate (Gom nhóm):**
    *   *Cơ chế:* Kết quả của mỗi nhánh được append vào một List trong Domain Context.
    *   *Đánh giá:* **An toàn**. Phù hợp cho việc thu thập dữ liệu (Map-Reduce pattern).

3.  **Chiến lược Reduce (Tính toán):**
    *   *Cơ chế:* Áp dụng toán tử (Sum, Min, Max) lên các trường dữ liệu số.
    *   *Đánh giá:* Dùng cho thống kê.

4.  **Chiến lược Custom (Chuyên biệt hóa):**
    *   *Cơ chế:* Gọi một Process đặc biệt (`MergeProcess`) để xử lý xung đột bằng logic nghiệp vụ.
    *   *Đánh giá:* **Khuyên dùng** cho các object phức tạp.

---

## 7.4. Trách nhiệm của Engine (Engine Responsibilities)

Engine không chỉ là "người chạy code". Nó là hệ điều hành của Workflow với các trách nhiệm tối thượng:

1.  **Graph Validation (Kiểm tra đồ thị):** Trước khi chạy, Engine phải duyệt cây để phát hiện vòng lặp chết (Dead Cycles) hoặc các tham chiếu không tồn tại (Dangling References).
2.  **Scheduling (Điều phối):** Quản lý Thread pool cho các nhánh Parallel, đảm bảo thứ tự thực thi cho Linear.
3.  **Snapshot & Rollback (Bảo toàn):**
    *   Trước mỗi Step quan trọng, Engine chụp ảnh (Snapshot) Domain Context.
    *   Nếu Step lỗi, Engine có thể khôi phục lại trạng thái cũ (nếu cấu hình Transaction).
4.  **Audit Trace (Truy vết):** Ghi lại *Con đường thực tế* (Actual Path) mà dữ liệu đã đi qua. (Lưu ý: Với Branching, con đường thực tế khác với con đường lý thuyết).
