# Architectural Comparison: Theus vs Pydantic vs Polars
## Phase 24 Strategy Definition

Để đạt được trạng thái "Industrial Grade", Theus học hỏi từ hai người khổng lồ trong hệ sinh thái Python-Rust: **Pydantic V2** (Validation/Schema) và **Polars** (Data Processing).

### 1. Pydantic V2: "Schema-First Preservation"
*   **Triết lý:** Dữ liệu phải luôn Đúng (Correctness).
*   **Kiến trúc:**
    *   `pydantic-core` (Rust) định nghĩa cấu trúc dữ liệu chặt chẽ.
    *   Validation chạy hoàn toàn dưới Rust.
    *   **Cơ chế:** Khi dữ liệu đi vào, nó được parse và validate ngay lập tức. Pydantic tạo ra một Python Object mới (Model) đã được "làm sạch".
*   **Điểm mạnh:** Type Safety tuyệt đối.
*   **Điểm yếu:** Chi phí Serialization/Deserialization (Serde) cao nếu dữ liệu thay đổi liên tục. Không thích hợp cho "Hot Loop" thay đổi trạng thái.

### 2. Polars: "Lazy Engine & Zero-Copy"
*   **Triết lý:** Dữ liệu phải xử lý Nhanh (Performance).
*   **Kiến trúc:**
    *   Python chỉ là một lớp vỏ (DSL) để xây dựng "Query Plan".
    *   Dữ liệu thực (Arrow Arrays) nằm hoàn toàn trong RAM của Rust.
    *   **Cơ chế:** "Lazy Evaluation". Không có gì chạy cho đến khi gọi `.collect()`. Trả về kết quả là một View hoặc Copy mới.
*   **Điểm mạnh:** Tốc độ xử lý dữ liệu lớn (Big Data) cực nhanh nhờ SIMD/Parallelism.
*   **Điểm yếu:** Khó debug (vì Lazy). Không phù hợp cho logic điều khiển luồng (Control Flow) phức tạp từng bước.

### 3. Theus Optimization (Phase 24): "The Hybrid Guardian"
Theus không chỉ là Validator (Pydantic) cũng không chỉ là Data Engine (Polars). Theus là **Process Orchestrator**. Chúng ta cần cả hai: **An toàn cho Logic** và **Tốc độ cho Tính toán**.

#### Chiến lược: **Tiered Optimization Model**

| Đặc điểm | Tier 1: Control Plane (Logic) | Tier 2: Data Plane (Heavy) |
| :--- | :--- | :--- |
| **Cảm hứng** | **Học từ Pydantic** | **Học từ Polars** |
| **Đối tượng** | Settings, Flags, States, Counters (Scalar/Small List) | Tensors, DataFrames, Large Arrays |
| **Cơ chế Rust** | **Typed Wrappers (`TheusGuard`)** | **Direct Pass-through (`Zero-Copy`)** |
| **Hành vi** | Proxy mọi truy cập (`getattr/setattr`). Kiểm tra quyền (Permissions). Ghi Audit Log. | Bỏ qua Proxy. Truyền thẳng địa chỉ bộ nhớ cho Numpy/Torch. |
| **Safety** | **Cao nhất (Strict)**. Transactional Rollback. | **Trung bình (Access Only)**. Chỉ kiểm soát ai được lấy, không kiểm soát họ làm gì. |
| **Overhead** | Micro-seconds (Chấp nhận được cho Logic) | **Nano-seconds (Zero Overhead)** |

### Phân tích Sâu: Tại sao Theus khác biệt?

1.  **ContextGuard không phải là Validator (Pydantic):**
    *   Pydantic validate dữ liệu **khi nhập vào**.
    *   Theus ContextGuard validate quyền truy cập **khi runtime**.
    *   *Sự khác biệt:* Pydantic dùng 1 lần (static). Theus dùng liên tục (dynamic hook). Do đó, Theus cần tối ưu hóa `__getattr__` ở mức Rust (PyO3) để giảm overhad xuống gần 0 như cách Polars xử lý expression.

2.  **ContextGuard không phải là Lazy Engine (Polars):**
    *   Polars chờ lệnh `.collect()` mới chạy.
    *   Theus phải chạy ngay lập tức (`Eager Execution`) vì Agent cần phản hồi realtime.
    *   *Sự khác biệt:* Theus không thể Lazy. Do đó, **Heavy Zone** là bắt buộc để tránh copy dữ liệu trong Eager Mode.

### Lộ trình Cải tổ (Refactor Roadmap)

1.  **Bước 1 (Đã xong): Python Magic Methods Patch.**
    *   Giúp code chạy được, thân thiện với developer ("Pythonic").
    *   *Nhược điểm:* Vẫn còn overhead gọi hàm Python.

2.  **Bước 2 (Sắp tới): Port ContextGuard sang Rust (`theus_core`).**
    *   Sử dụng `#[pyclass]` của PyO3 để define `ContextGuard`.
    *   Implement `__getattr__` bằng Rust để check permission map (HashMap lookup cực nhanh).
    *   Loại bỏ hoàn toàn code Python trong `guards.py`.

3.  **Bước 3: Specialized Wrappers.**
    *   Tự động detect kiểu dữ liệu:
        *   Nếu là Tensor -> Trả về `TheusTensorWrapper` (cho phép `+ - * /` tốc độ C++).
        *   Nếu là List -> Trả về `TheusListWrapper`.

### Kết luận
Cách tiếp cận của Theus là sự kết hợp thực dụng: **Giữ chặt Logic (như Pydantic) nhưng Buông lỏng Dữ liệu lớn (như Polars)**. Đây là con đường duy nhất để một Framework Python có thể chạy các thuật toán AI/SNN phức tạp mà không bị nghẽn cổ chai bởi chính cơ chế bảo vệ của nó.
