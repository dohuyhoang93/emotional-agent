# Phân tích Dependency: NumPy trong Theus Framework

**Ngày thực hiện:** 2026-03-24  
**Phân hệ ảnh hưởng:** `theus/structures.py`, `theus/context.py`, Multi-processing/Sub-interpreter Engine.

---

## 1. Mục đích điều tra
Tài liệu này làm rõ lý lịch kiến trúc đằng sau quyết định kết dính Theus Framework (vốn định hình là lõi điều phối Rust/Python nhẹ nhàng) với NumPy (một thư viện toán học đồ sộ).

---

## 2. Vị trí Code phát hiện NumPy
Qua rà soát (`grep_search`), NumPy đang được import (đa số ở dạng *Lazy Import* bên trong hàm, hoặc bọc `try...except`) tại:
- **`theus/structures.py`**: `ManagedAllocator` và định nghĩa `ShmArray`.
- **`theus/context.py`**: `HeavyZoneWrapper`, và các class `rebuild_shm_array`.
- Hơn 10 kịch bản kiểm thử (`verify_heavy_zone.py`, `test_zero_copy_proof.py`...) và các benchmark.

---

## 3. Lý do ra đời (The "Why")
NumPy không được sử dụng để tính toán ma trận bên trong Theus. Thay vào đó, nó được sử dụng làm **Backend Bộ nhớ (Memory Backend)** cho tính năng **Heavy Zone (Zero-Copy Shared Memory)**.

*Bối cảnh:* Theus được thiết kế cho các tác vụ AI Agents (ví dụ: huấn luyện SNN, reinforcement learning). Các tiến trình (process) thường xuyên phải trao đổi các Tensor đồ sộ (ví dụ: state observation 1000 chiều, ma trận replay buffer). Nếu truyền các biến này qua `Outbox` hoặc `Global State` thông thường (dùng Pickle serialization), CPU sẽ bị thắt cổ chai hoàn toàn bởi quá trình *Serialize -> Copy -> Deserialize.*

*Giải pháp:* 
- Thêm một phân vùng bộ nhớ tên là `heavy` (`ctx.heavy`).
- Khi cấp phát bộ nhớ tại `ctx.heavy.alloc()`, Theus gọi `multiprocessing.shared_memory`.
- Để Process khác có thể đọc vùng RAM này mà không cần parse/copy, Theus dùng NumPy `ndarray(buffer=shm.buf)` lấy pointer gắn thẳng vào bộ nhớ. Do đó **Zero-Copy** ra đời.

---

## 4. Tác động của quyết định này (Architectural Impact)

### Ưu điểm (Lợi ích mang lại)
1. **Hiệu năng phi thường (Performance Leap):** Zero-Copy IPC loại bỏ hoàn toàn chi phí truyền tải qua mạng ảo hay Pipe (thông lượng qua RAM có thể đạt hàng chục GB/s), giúp Theus vô địch về tốc độ khi điều phối mô hình AI đa luồng.
2. **Liền mạch với Hệ sinh thái AI:** NumPy ndarray là chuẩn chung (lingua franca) của Data Science. Đưa NumPy vào Theus giúp output từ Heavy Zone có thể được feed thẳng vào PyTorch/TensorFlow không mất một nano giây convert nào.

### Nhược điểm (Trade-offs)
1. **Purity (Sự thuần khiết của Framework lõi):** TheusCore đánh mất khả năng gọi là "framework siêu nhẹ chỉ dùng Standard Library". 
2. **Hệ sinh thái:** Việc Theus bắt buộc phải xử lý phụ thuộc C-extension phức tạp từ bên thứ 3 khiến bảo trì gặp rủi ro dài hạn.

---

## 5. Hệ quả sâu rộng (Far-reaching Consequences)

Decisions mang NumPy vào lõi tạo ra các chuỗi phản ứng phụ (ripple effects) mạnh mẽ:

1. **Khả năng tương thích Sub-interpreter (PEP 684)**
   - Vấn đề lõi: Numpy (dưới bản 2.x) chia sẻ C-Global State, khiến nó thường xuyên crash khi bị inject vào các Sub-interpreter biệt lập.
   - Hệ quả hiện tại: Code của Theus (`parallel.py`) liên tục phải chứa các đoạn Try/Catch cực đoan để xử lý NumPy fallback nếu Sub-Interpreter không load được thư viện này. Đây là **tech-debt** rất lớn của dự án.

2. **Rủi ro rò rỉ bộ nhớ Zombie (Memory Leaks)**
   - Đối tượng `ShmArray` của numpy nắm giữ Handle (`shm`) của hệ điều hành. Nếu Python GC (Garbage Collector) dọn NumPy array không sạch, hoặc Process sập, Handle sẽ biến thành "Zombie Memory" chiếm dụng RAM hệ thống.
   - *Hệ quả:* Đội ngũ Theus phải viết hẳn một `MemoryRegistry` bằng Rust để làm Garbage Collector chéo (Cross-process) chuyên đi săn và giết các SHM handle do NumPy vô tình bỏ lại. Một sự phình to kiến trúc đáng kể.

3. **Cơ chế Pickling phức tạp**
   - NumPy mặc định khi `pickle.dumps()` sẽ hốt toàn bộ dữ liệu (data) đem nén lại. Điều này vô hình trung biến Zero-Copy thành Deep-Copy (gây siêu lag).
   - Hệ quả: Lập trình viên phải can thiệp đè lên phương thức thần thánh `__reduce__` của class `ShmArray` (trong `theus/context.py`) để hack: *buộc Pickle chỉ di chuyển cái Tên (SHM name) và Kích thước thay vì di chuyển cục Data.*

4. **Kích thước Deployment**
   - Khiến Theus container image bị đội lên hàng trăm MB (kích cỡ của NumPy và các thư viện số lớn C++ đi kèm). Triển khai Theus lên vi điều khiển (IoT) hoặc Edge Devices sẽ trở nên cực kỳ khó khăn.

---

## 6. Đề xuất Kiến trúc (Recommendations)

Cấu trúc hiện tại của Theus khá "khôn ngoan" khi đã cố gắng để các khối import NumPy nằm sau các `try...except ImportError`. Tuy nhiên, về lâu dài, để bảo vệ tính Purity của lõi:

1. **Tách Rời (Optional Dependency):** Chỉ nên khai báo NumPy dưới dạng Optional `pip install theus[heavy]`. Nếu user cài bản theus thường, chức năng Heavy Zone bị tắt hoặc chỉ dùng Bytearray thuần túy của Python.
2. **Abstraction (Python Buffer Protocol):** Trừu tượng hóa hoàn toàn bằng Python `memoryview` (hỗ trợ C-Buffer Protocol nguyên bản của Python) tại tầng dưới thay vì gọi hàm Numpy. Trả NumPy proxy cho User chỉ ở Tầng API Wrapper cao nhất, giúp tháo gỡ sự trói buộc C-Extension độc hại cho Sub-interpreters.
