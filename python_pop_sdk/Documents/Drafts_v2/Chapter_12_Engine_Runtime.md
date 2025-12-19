# Chương 12: Theus Microkernel - Trái tim máy (Engine Internals)

---

## 12.1. Tổng quan Kiến trúc Microkernel

Engine của Theus không còn là một "Process Runner" đơn thuần. Nó được thiết kế như một **Microkernel** (Hệ điều hành hạt nhân nhỏ) chuyên dụng cho tự động hóa.

Mục tiêu của Theus Microkernel là quản lý sự **hỗn loạn** của thế giới thực thông qua sự **kỷ luật** của máy tính.

### Kiến trúc 3 Lớp (The 3-Layer Architecture)

```mermaid
graph TD
    UserCode[User Processes] -->|Calls| Kernel API
    
    subgraph "Theus Microkernel"
        Governance[Layer 3: Governance (Cảnh sát)]
        Execution[Layer 2: Execution (Dây chuyền)]
        Transport[Layer 1: Transport (Kho vận)]
    end
    
    Governance -->|Enforces| Execution
    Execution -->|Mutates| Transport
```

1.  **Transport Layer (Vận chuyển):** Nơi chứa Context và dữ liệu "câm". Nhiệm vụ duy nhất là lưu trữ đúng chỗ.
2.  **Execution Layer (Thực thi):** Nơi chạy các Process. Đây là "cơ bắp" của hệ thống.
3.  **Governance Layer (Quản trị):** Nơi chứa các luật lệ (Guard, Lock, Auditor). Đây là "bộ não" kiểm soát an toàn.

---

## 12.2. Cơ chế Quản trị Dữ liệu: "The Iron Triangle"

Để đảm bảo an toàn tuyệt đối, Theus sử dụng bộ 3 cơ chế bảo vệ gọi là "Tam giác sắt":

### 1. The Airlock (Shadowing) - Cách ly
*   **Vấn đề:** Nếu cho Process sửa trực tiếp Context gốc (`Master Context`), khi Process lỗi giữa chừng, Context sẽ bị hỏng (Inconsistent State).
*   **Giải pháp:** Theus tạo một bản sao (**Shadow Context**) cho mỗi Process.
    *   Process chỉ được sửa bản sao.
    *   Nếu thành công: Kernel thực hiện **Atomic Commit** (Merge bản sao về bản gốc).
    *   Nếu thất bại: Kernel hủy bản sao. Bản gốc nguyên vẹn.

### 2. The Gatekeeper (Context Guard) - Kiểm soát
*   **Vấn đề:** Process cố tình đọc/ghi vào biến không được phép.
*   **Giải pháp:** Lớp `ContextGuard` bọc lấy Context.
    *   Nó chặn mọi truy cập không khai báo (Illegal Read/Write).
    *   Nó đóng băng (`Frozen`) các biến Input để đảm bảo Process không vô tình sửa tham số đầu vào.

### 3. The 3-Axis Matrix - Luật pháp
Core của việc kiểm soát nằm ở **Ma trận An toàn 3 Trục** (Xem Chương 4). Kernel không chỉ check tên biến, mà check giao điểm của:
*   **Zone:** (Data/Signal)
*   **Semantic:** (Input/Output)
*   **Layer:** (Global/Domain)

> **Ví dụ:** Nếu Process cố gắng khai báo `inputs=['sig_stop']` (Dùng Signal làm đầu vào), Kernel sẽ chặn ngay lập tức vì vi phạm nguyên tắc Determinism (Signal không ổn định để Replay).

---

## 12.3. Pipeline Thực thi Công nghiệp (The Industrial Pipeline)

Mỗi khi bạn gọi lệnh chạy, Theus không chỉ "gọi hàm". Nó kích hoạt một dây chuyền 7 bước nghiêm ngặt:

1.  **Registry Lookup:** Tìm Process và Contract trong sổ cái.
2.  **Static Validation:** Kiểm tra tĩnh xem Input đã đủ trong Context chưa.
3.  **Shadowing & Locking:** Tạo Transaction ID, khóa Context, tạo bản sao.
4.  **Guard Injection:** Bọc bản sao bằng `ContextGuard`.
5.  **Execution (Unsafe Zone):** Chạy code Python của người dùng bên trong môi trường được bảo vệ.
6.  **Dynamic Audit:**
    *   Kiểm tra Output xem có vi phạm Rule ràng buộc không (ví dụ: `age < 0`).
    *   Nếu vi phạm nghiêm trọng -> **Interlock** (Dừng hệ thống).
7.  **Atomic Commit:** Merge dữ liệu và mở khóa.

---

## 12.4. Các mức độ An toàn (Safety Tiers)

Theus chia dữ liệu thành 3 hạng mục để bảo vệ:

### Tier 1: Primitives (Tuyệt đối an toàn)
*   `int`, `str`, `tupe`, `bool`.
*   Python không cho phép sửa nội tại (Immutable). Theus bảo vệ 100%.

### Tier 2: Managed Structures (An toàn cao)
*   `List`, `Dict`.
*   Theus tự động chuyển đổi thành `TrackedList` và `FrozenList`.
*   Nếu bạn thử `ctx.settings.append(1)` trên một Input List, bạn sẽ nhận lỗi `ContractViolation`.

### Tier 3: Foreign Objects (Cần kỷ luật)
*   `numpy.array`, `torch.Tensor`, `CustomClass`.
*   Theus không thể can thiệp vào bộ nhớ C++ của Numpy.
*   **Cảnh báo:** Developer phải tự ý thức không được sửa nội tại (mutate inplace) các object này nếu chúng là Input.

---

## 12.5. Kết luận
Theus Microkernel không sinh ra để làm chậm code của bạn. Nó sinh ra để **bảo hiểm** cho code của bạn. Có Theus, bạn có thể tự tin deploy logic phức tạp mà không sợ hiệu ứng cánh bướm (Butterfly Effect) làm sập hệ thống.
