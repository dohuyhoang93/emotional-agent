> [!NOTE]
> Tài liệu này là **Architecture Heritage** (Di sản kiến trúc). 
> Nó phản ánh quá trình thiết kế và ra quyết định. Để sử dụng API thực tế, hãy xem [API Reference](../01_Specs/THEUS_API_REFERENCE.md).

---

# 🧠 PHÂN TÍCH & CHIẾN LƯỢC: ZERO-COPY PARALLELISM (REVISED)

**Bối cảnh:** Theus V3 chưa đạt được "True Parallelism" do hạn chế của Python GIL và sự thiếu tương thích giữa Sub-Interpreters với các object phức tạp.

**Cập nhật (19/01/2026):** Dựa trên tài liệu `concurrent.interpreters` và đánh giá rủi ro (Virtue Audit), chúng ta điều chỉnh chiến lược từ "Khẳng định" sang "Tiếp cận Thận trọng".

---

## 1. 🔍 HIỆN TRẠNG & GIỚI HẠN KỸ THUẬT (THE HARD TRUTH)

### A. Sub-Interpreters không phải là "Phép màu"
*   **Thực tế:** Sub-Interpreters (PEP 734) có bộ nhớ heap riêng biệt.
*   **Giới hạn cốt tử:** Chỉ có **`memoryview`** (Flat Buffers: bytes, integers, floats) mới chia sẻ được Zero-Copy.
*   **Hệ quả:** Mọi cấu trúc dữ liệu phức tạp (Nested Dict, Tree, Custom Objects) **BẮT BUỘC** phải Pickle (Copy) hoặc Serialize, gây nghẽn cổ chai hiệu năng.

### B. Các giải pháp đã loại bỏ
*   **Pure PyObject Sharing:** Bất khả thi về vật lý (Segfault).
*   **Apache Arrow Plasma:** Đã khai tử (Deprecated).

---

---

## 2. 🛡️ CHIẾN LƯỢC ĐỀ XUẤT: HYBRID MODEL (PROPOSAL)

**Định nghĩa Cốt lõi:** Hãy coi Shared Memory chính là **"Cấu trúc Bất biến Song song" (Parallel Immutable Structure)**.
*   Nó tuân thủ quy tắc "Write-Once, Read-Many" giống hệt Immutable Object.
*   Khác biệt duy nhất: Nó nằm ngoài Heap của Python (Off-Heap) để né GIL.

Chúng ta đề xuất mô hình lai, tận dụng điểm mạnh của từng công nghệ nhưng chấp nhận sự phức tạp trong triển khai.

### Kiến trúc: "Compute Locally, Share Globally via Buffer"
1.  **Transport Layer (Shared Memory):**
    *   Sử dụng **Rust Core** để quản lý một vùng nhớ `mmap` lớn (The Arena).
    *   Expose vùng nhớ này dưới dạng `memoryview` hoặc `Arrow Buffer`.
2.  **Logic Layer (Sub-Interpreters):**
    *   Worker nhận `Buffer Descriptor` (địa chỉ, kích thước) thay vì data full.
    *   Worker tạo `memoryview` từ descriptor này để đọc dữ liệu thô (Tensors, Images).
3.  **State Management:**
    *   Tách biệt rõ ràng:
        *   **Light State (Config, Flags):** Dùng Pickle (chấp nhận được vì nhỏ).
        *   **Heavy State (Tensors, AI Models):** Dùng Shared Memory Buffer.

### Kế hoạch dự phòng (Fallback Plan)
Nếu việc implement Rust `mmap` quá phức tạp hoặc không ổn định:
*   **Plan B:** Sử dụng **Redis** hoặc **Ray Object Store**. Tốc độ chậm hơn Shared Memory (do Network/Socket overhead) nhưng độ ổn định và ease-of-use cao hơn gấp nhiều lần.

---

## 3. 🛡️ VAI TRÒ CỦA RUST (CRITICAL ANALYSIS)

### A. Memory Governor (Thống đốc)
Rust chịu trách nhiệm xin OS cấp phát `mmap` và dọn dẹp (RAII). Nó đảm bảo không có Memory Leak khi Python Worker crash (Zero-Downtime Recovery).

### B. Schema Arbiter (Trọng tài)
Vì `memoryview` là byte thô, Rust phải ép kiểu (Type Check) chặt chẽ lúc ghi để tránh việc Python đọc rác (Garbage Data) và gây crash.

---

## 4. 🗺️ LỘ TRÌNH THỰC THI (ROADMAP)

### Phase 0: Verification (Proof of Concept) - **CRITICAL**
*   **Mục tiêu:** Chứng minh `concurrent.interpreters` có thể đọc ghi `mmap` created by Rust một cách an toàn.
*   **Task:** Viết script test nhỏ (Rust tạo mmap -> Python Sub-Interpreter đọc via memoryview).
*   **Decision Gate:** Nếu PoC thất bại -> Chuyển ngay sang Plan B (Redis/Ray).

### Phase 1: The "Honest" Release
*   Update Docs: Thừa nhận V3.0 là Thread-based.
*   Warning: Cảnh báo user về CPU-bound tasks.

### Phase 2: Infrastructure (Chỉ khi Phase 0 OK)
*   Xây dựng `TheusShm` module trong Rust.
*   Bắt đầu migrate `ctx.heavy` sang dùng Buffer Protocol.


---

## 5. 🔮 API PREVIEW (DEVELOPER EXPERIENCE)

Sau khi "độ" xong, Developer sẽ sử dụng Theus V3 như sau:

### A. Producer (Ghi dữ liệu Shared)
Người dùng chỉ cần thao tác với `ctx.heavy` như dict thông thường. Rust Core sẽ tự động chuyển đổi object sang Shared Memory.

```python
# Main Process
import numpy as np

def load_models(ctx):
    # Tạo dữ liệu lớn (ví dụ ảnh 4K hoặc Model weights)
    # Rust sẽ tự động 'malloc' vùng nhớ mmap và copy data vào đó.
    ctx.heavy['camera_feed'] = np.random.rand(3840, 2160, 3).astype(np.float32)
    
    # Hỗ trợ cả Arrow Table
    ctx.heavy['market_data'] = arrow_table
```

### B. Consumer (Sub-Interpreter Worker)
Bên trong Worker, dữ liệu được "tái sinh" dưới dạng View (Zero-Copy).

```python
@process(parallel=True)  # Flag bật Sub-Interpreter
def analyze_frame(ctx):
    # 1. Access:
    # Ở đây 'frame' KHÔNG PHẢI là bản copy.
    # Nó là một numpy array trỏ thẳng vào vùng nhớ mmap chung.
    frame = ctx.heavy['camera_feed'] 
    
    # 2. Verify Zero-Copy:
    # frame.flags['OWNDATA'] sẽ là False
    # Địa chỉ bộ nhớ giống hệt Process cha.
    
    # 3. Compute:
    # Tính toán thoải mái với tốc độ C (numpy) mà không tốn RAM copy.
    result = np.mean(frame) 
    
    return {"brightness": result}
```

### C. Cơ chế ngầm (Under the hood)
Khác biệt nằm ở chỗ `ctx.heavy['key']` trong Sub-Interpreter thực chất làm 2 việc:
1.  Nhận `(memory_address, shape, dtype)` từ Rust.
2.  Gọi `np.asarray(memoryview)` để tạo wrapper cho user.
-> User cảm thấy "tự nhiên" như code Python thường, nhưng hiệu năng là System Programming.


---

## 6. ✍️ WRITE STRATEGY: IMMUTABILITY & CoW

Vấn đề "Ghi song song" (Parallel Write) được giải quyết bằng nguyên tắc cốt lõi của Theus: **Không bao giờ sửa tại chỗ (Never Mutate in Place).**

### A. Nguyên tắc: Copy-on-Write (CoW)
*   **ReadOnly by Default:** RAM Shared Memory luôn **Read-Only** đối với tất cả Reader.
*   **Write Flow:** Khi Worker cần sửa dữ liệu (ví dụ: Resize ảnh):
    1.  Worker xin Rust cấp phát một vùng nhớ Shared **MỚI** (New Arena).
    2.  Worker ghi kết quả vào vùng mới này.
    3.  Worker trả về `Descriptor` của vùng mới về cho Main Process.
    4.  Main Process cập nhật pointer trong `State` trỏ sang vùng mới (Atomic Pointer Swap).

### B. Xử lý Xung đột (Conflict Resolution: Global CAS)
*   **Logic:** Theus sử dụng **Global State Versioning**.
    *   Mỗi khi State thay đổi (dù chỉ 1 bit), `version` tăng lên +1.
    *   Lệnh `compare_and_swap(expected_version=N, new_data=...)` sẽ kiểm tra:
        *   Nếu `current_version == N`: **COMMIT**. (Cập nhật pointer, tăng version lên N+1).
        *   Nếu `current_version != N`: **REJECT**. (Ném lỗi `CAS Version Mismatch`).
*   **Hệ quả:**
    *   **An toàn:** Không bao giờ có chuyện 2 người cùng ghi đè lên nhau (Lost Update).
    *   **Retry:** Worker bị từ chối sẽ phải đọc lại State mới nhất và tính toán lại (hoặc merge lại) rồi thử Commit lại.
*   **Lợi ích:** Đảm bảo tính nhất quán tuyệt đối (Consistent) mà không cần Lock phức tạp trên từng byte bộ nhớ. Zero-Copy Write = Alloc new -> Write -> Swap Pointer.

---

## 7. ⚖️ PHÂN TÍCH RỦI RO & GIẢI PHÁP NÂNG CAO (CRITICAL ANALYSIS)

*Dựa trên kết quả thẩm định Phase 2 & 3 của Skill Critical Analysis.*

### A. Rủi ro của Global CAS "Ngây thơ"
1.  **Starvation (Đói tài nguyên):** Worker xử lý chậm (ví dụ 500ms) có thể **KHÔNG BAO GIỜ** commit được nếu các worker nhanh liên tục đẩy version lên (`v100` -> `v150` -> `v200`).
2.  **Thundering Herd (Hiệu ứng đám đông):** Khi tranh chấp cao, hàng trăm worker cùng retry đồng loạt -> Gây nghẽn cổ chai CPU vô ích.

### B. Giải pháp bổ sung
Để bảo toàn hiệu năng song song (Parallelism Performance), hệ thống cần bổ sung các cơ chế giảm xóc:

1.  **Key-Level CAS (Fine-grained Locking):**
    *   Thay vì kiểm tra version toàn cục, chỉ kiểm tra `HashMap<Key, Version>`.
    *   **Hiệu quả:** Xung đột giảm 90%. Worker sửa `camera` không bị chặn bởi worker sửa `audio`.

2.  **Exponential Backoff (Lò xo giảm tải):**
    *   Khi Commit Fail, Worker không retry ngay mà ngủ `sleep(base * 2^retries)`.
    *   **Hiệu quả:** Tự động điều tiết tải khi hệ thống kẹt, tránh sập nguồn.

3.  **Priority Escalation (Vé ưu tiên):**
    *   Nếu Worker fail quá 5 lần, nó được cấp quyền ưu tiên. Hệ thống tạm dừng các request khác trong 1ms để "cứu" worker chậm.
    *   **Hiệu quả:** Chống Starvation triệt để, đảm bảo tính công bằng (Fairness).

4.  **Fallback to Actor Model (Van an toàn cuối cùng):**
    *   Trong trường hợp tồi tệ nhất (1000 workers cùng ghi 1 key), hệ thống chuyển sang chế độ **Serialized Queue**.
    *   **Hiệu quả:** Chậm nhưng chắc, ngăn chặn crash.


---

## 8. 💥 PHÂN TÍCH TÁC ĐỘNG (IMPACT ANALYSIS)

Triển khai giải pháp Hybrid Zero-Copy sẽ tác động sâu rộng đến kiến trúc hiện tại (theo `THEUS_FEATURES.md`):

### 1. Immutable Structure & State Management
*   **Hiện tại:** Dựa vào `im::HashMap` và `Arc<PyObject>`.
*   **Tác động:**
    *   **Tích cực:** Nguyên tắc Copy-on-Write của Shared Memory hoàn toàn tương thích với triết lý Immutability. State vẫn là bất biến, chỉ thay đổi pointer trỏ đến vùng nhớ mới.
    *   **Thay đổi (Dual Mode):**
        *   `ctx.data`: Vẫn giữ `HashMap<String, Arc<PyObject>>` cho Light State (Config, Flags). Lý do: Convert `int/bool` sang SharedMem quá tốn kém (Overhead).
        *   `ctx.heavy`: Chuyển sang `HashMap<String, Arc<ShmRef>>` cho Heavy State (Tensor, Image).

### 2. Heavy Zone (`ctx.heavy`)
*   **Hiện tại:** Lưu `Dict[str, PyObject]`.
*   **Tác động:** Đây là nơi thay đổi lớn nhất.
    *   `ctx.heavy` sẽ chuyển thành `Dict[str, BufferDescriptor]`.
    *   Các hàm `get/set` sẽ phải tự động wrap/unwrap `memoryview`.
    *   Hiệu năng đọc/ghi sẽ tăng đột biến (do zero-copy), nhưng code phức tạp hơn.

### 3. Signal I/O Contract
*   **Hiện tại:** `SignalHub` dùng string-based signals (Pub/Sub).
*   **Tác động:** **Không bị ảnh hưởng nhiều**.
    *   Signal chỉ dùng để báo hiệu ("Có ảnh mới ở địa chỉ X"), bản thân ảnh nằm ở `heavy`.
    *   Mô hình "Control Plane (Signal) tách rời Data Plane (Shared Mem)" được củng cố.

### 4. Input/Output Contracts (`@process`)
*   **Hiện tại:** Contract kiểm tra kiểu dữ liệu Python (ví dụ `int`, `str`).
*   **Tác động:** Cần mở rộng hệ thống Type Shield.
    *   Thêm `SemanticType.SHM_READ` và `SemanticType.SHM_WRITE`.
    *   Contract phải validate được Schema của Arrow Buffer (ví dụ: đảm bảo tensor đúng chiều 3840x2160).

### 5. Audit Trail
*   **Hiện tại:** Log lại việc truy cập biến.
*   **Tác động:** Log sẽ chi tiết hơn.
    *   Thay vì log "Read Object A", hệ thống sẽ log "Read Memory Region 0x123 (Size: 50MB)".
    *   Giúp phát hiện Memory Leak hoặc truy cập vùng nhớ trái phép (Segfault risk).

---

## 9. 🚧 PHẠM VI ẢNH HƯỞNG & CƠ CHẾ KÍCH HOẠT (CLARIFICATION)

### A. "Strict Marshalling Boundary" (Tác động toàn diện)
Bạn nhận định rất đúng: **Tất cả đối tượng đều bị ảnh hưởng.**
Vì Sub-Interpreters không chia sẻ Heap, nên mọi dữ liệu đi vào/ra khỏi Worker đều phải qua **"Cửa khẩu" (Marshalling Boundary)**.

*   **Logic phân loại tự động (Auto-Dispatch):**
    *   **Light Objects (Config, Int, List nhỏ):** Theus dùng `pickle` (Copy). Chấp nhận chi phí thấp cho tiện lợi.
    *   **Heavy Objects (Tensor, Image > 1MB):** Theus dùng `SharedMemory` (Zero-Copy).
    *   **Mix Objects (Dict chứa cả Int và Tensor):** Hệ thống sẽ phải "mổ xẻ" (traverse) Dict, tách phần Heavy ra để Zero-Copy, phần còn lại Pickle, rồi qua bên kia ghép lại. -> **Đây là chi phí Runtime (Overhead) không thể tránh khỏi.**

### B. Cơ chế Kích hoạt (Activation Policy)
Để đảm bảo an toàn, ban đầu Theus V3 sẽ chọn **Explicit Opt-in (Dev chủ động bật)**. Engine không tự đoán.

**Lý do:** Không phải code nào cũng chạy được trên Sub-Interpreter (ví dụ: thư viện C cũ chưa hỗ trợ Multi-Phase Init).

**API Contract:**

```python
# Cách 1: Bật thủ công (Explicit) -> Khuyên dùng
@process(
    inputs=["camera"], 
    parallel=True,      # <--- Kích hoạt Sub-Interpreter
    workers=4           # <--- Số lượng Worker
)
def process_frame(ctx):
    pass

# Cách 2: Tắt (Mặc định) -> Chạy trên Main Thread (Asyncio/Thread)
@process(inputs=["config"])
def load_config(ctx):
    pass
```

*   **Runtime Logic:**
    *   Nếu `parallel=True`: Engine serialize input -> Send to Channel -> Worker deserialize -> Run.
    *   Nếu `parallel=False` (Default): Engine chạy trực tiếp (Direct Call) -> Zero Overhead.

---

## 10. 🔄 VÒNG ĐỜI DỮ LIỆU (DATA LIFECYCLE) - CLARIFIED

Câu trả lời cho việc "Input/Output đi về đâu?" là: **Redirect to Shared Memory.**

### A. Input Lifecycle (Main -> Worker)
Khi `@process(parallel=True)` được gọi:
1.  **Interceptor:** Engine chặn các tham số Input.
2.  **Assessment:** Kiểm tra kích thước và kiểu dữ liệu.
    *   Nếu là **Heavy Object** (Numpy, Bytes > 100KB):
        *   Engine **tự động** copy nó vào Shared Memory (nếu chưa có).
        *   Engine thay thế object gốc bằng một `BufferDescriptor` (Con trỏ).
    *   Nếu là **Light Object**: Giữ nguyên để Pickle.
3.  **Handoff:** Sub-Interpreter nhận `BufferDescriptor` và tái tạo thành `memoryview` (Zero-Copy) để Worker dùng.

### B. Output Lifecycle (Worker -> Main)
Khi Worker `return big_array`:
1.  **Allocation:** Worker (thông qua Wrapper của Theus) sẽ xin cấp phát vùng nhớ ngay trên Shared Memory để chứa `big_array`. **Nó không tạo trên Heap Python của Worker.**
2.  **Return:** Worker trả về `BufferDescriptor` của vùng nhớ đó.
3.  **Merge:** Main Process nhận Descriptor và cập nhật vào `ctx.heavy`.

-> **Kết luận:** Đúng, Dữ liệu Heavy sống hoàn toàn trên "Sân chơi chung" (Shared Memory), hoàn toàn né tránh cấu trúc mặc định của Python (Isolated Heap).

---

## 11. 🎯 KHUYẾN NGHỊ KỊCH BẢN SỬ DỤNG (USE CASE RECOMMENDATIONS)

Không phải bài toán nào cũng nên dùng `Parallel Immutable Structure`. Dưới đây là bảng phân loại "Nên & Không Nên":

### A. The "Sweet Spot" (Nên dùng ✅)
Kịch bản tận dụng tối đa sức mạnh của Zero-Copy & Sub-Interpreters:
1.  **AI Inference Pipeline:** Load Model lớn (1GB) vào Shared Memory. 4 Workers cùng đọc model đó để xử lý 4 luồng video khác nhau. -> **Tiết kiệm 3GB RAM.**
2.  **Image/Video Processing:** Resize, Filter, Encode hàng nghìn ảnh. Dữ liệu pixel nằm trên Shared Mem.
3.  **Complex Simulation:** Mô phỏng tài chính, game theory với state lớn chia sẻ chung.

### B. The Anti-Pattern (Không nên dùng ❌)
Kịch bản sẽ lỗ vốn vì Overhead (Marshalling + Context Switch) lớn hơn lợi ích:
1.  **Massive I/O Concurrency (Ví dụ: SMB Crawler):**
    *   **Lý do:** Tác vụ này "chờ mạng" là chính (I/O Bound). `asyncio` trên Main Thread làm tốt hơn, nhẹ hơn gấp 100 lần (không tốn RAM cho 100 Interpreters).
    *   **Khuyên dùng:** `asyncio.gather` + `aiofiles`.
2.  **High Frequency - Tiny Data:** Gửi 1 triệu message nhỏ liên tục.
    *   **Lý do:** Chi phí Pickle/Unpickle và quản lý Shared Mem lớn hơn chi phí xử lý.
    *   **Khuyên dùng:** Threading hoặc Actor Model nhẹ (Ray).

-> **Kết luận:** Hãy chọn công cụ đúng cho công việc. Theus V3 mạnh nhất ở **Heavy Compute + Heavy Data**.

---

## 12. 🔗 TÍCH HỢP VỚI HEAVY ZONE (HEAVY ZONE 2.0 INTEGRATION)

Để trả lời câu hỏi: "Kết hợp như thế nào?", câu trả lời là **Sự Nâng Cấp Độc Quyền (Exclusive Upgrade)**.

### A. Nguyên tắc "Cổng Duy Nhất" (The Only Gateway)
Theus V3 thiết lập một luật cứng (Hard Constraint):
*   **Zero-Copy Parallelism CHỈ hoạt động trên `ctx.heavy`.**
*   Mọi dữ liệu nằm trong `ctx.data`, `ctx.local`, hay biến cục bộ **đều mặc định dùng Pickle** (Deep Copy) khi qua Sub-Interpreter.

### B. Sự Tiến hóa (Evolution)
| Đặc điểm | Heavy Zone 1.0 (Hiện tại) | Heavy Zone 2.0 (Hybrid Zero-Copy) |
| :--- | :--- | :--- |
| **Bản chất** | Convention (Quy ước). Dev tự hứa không sửa đổi. | **Infrastructure (Hạ tầng).** Rust ép buộc không thể sửa đổi (ReadOnly View). |
| **Vị trí** | Heap Python (Managed by GC). | **Off-Heap (`mmap` managed by Rust).** |
| **Truy cập** | Reference Counting (Pass by Ref). | **Buffer Protocol (Pass by Address/Descriptor).** |
| **Sự cố** | Có thể bị sửa lén (Mutation). | **An toàn tuyệt đối (Crash nếu cố sửa ReadOnly Buffer).** |

### C. Hướng dẫn Dev (Migration Guide)
Nếu bạn muốn hưởng lợi từ tốc độ song song:
1.  **Identify:** Tìm các biến lớn trong code (ảnh, model, dataframe).
2.  **Move:** Chuyển chúng từ `ctx.data` sang `ctx.heavy`.
3.  **Run:** Bật cờ `parallel=True` cho process xử lý.
-> Hệ thống tự động kích hoạt Zero-Copy cho các key đó.
