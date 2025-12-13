# Chương 8: Adapter (Cổng giao tiếp I/O)

---

## 8.1. Định vị Adapter trong POP

Khác với Clean Architecture xem Adapter là một "tầng" (Layer) bao bọc Core, POP định nghĩa Adapter đơn giản hơn nhiều:
> **Adapter là cổng giao tiếp "câm" (Dumb Pipe) giữa Process và thế giới bên ngoài (Hardware/Network).**

Trong POP:
*   Adapter **KHÔNG** phải là một layer logic.
*   Adapter **KHÔNG** tham gia vào dòng chảy Context.
*   Adapter chỉ là công cụ (Tool) được Process sử dụng.

---

## 8.2. Mô hình Environment (Env Object)

Thay vì dùng Dependency Injection (DI) phức tạp để tiêm Adapter vào Process, POP gom tất cả Adapter vào một object duy nhất gọi là `Env` (Environment).

**Cấu trúc cuộc gọi chuẩn:**
```python
def process_name(ctx: Context, env: Environment) -> Context:
    # Logic dùng Adapter thông qua Env
    raw_data = env.camera.capture() 
    ctx.data = raw_data
    return ctx
```

---

## 8.3. Bốn Quy tắc Vàng của Adapter (The 4 Adapter Rules)

### **Rule 1: Adapter không chứa Business Logic**
Adapter chỉ làm nhiệm vụ chuyển đổi dữ liệu thô (Raw Data) từ phần cứng thành định dạng mà Process hiểu được (và ngược lại).
*   *Cấm:* `adapter.save_user_if_valid(user)` (Có logic "if valid").
*   *Đúng:* `adapter.save_bytes(data)` (Chỉ thực thi lệnh I/O).

### **Rule 2: Adapter không trả về Context**
Adapter trả về dữ liệu nguyên thủy (Primitive Types) hoặc Object của thư viện bên thứ 3. Việc map dữ liệu đó vào Context là việc của Process.
*   *Lý do:* Để Adapter tái sử dụng được cho nhiều Context khác nhau.

### **Rule 3: Phân tách theo Tài nguyên (Resource Paritioning)**
Adapter phải được tổ chức theo loại tài nguyên vật lý, không phải theo tính năng phần mềm.
*   `adapters/camera.py` (Chứa mọi thứ liên quan đến Camera).
*   `adapters/database.py` (Chứa mọi thứ liên quan đến SQL).
*   *Không được:* `adapters/login_adapter.py` (Đây là tính năng, không phải tài nguyên).

### **Rule 4: Gọi Tường minh (Explicit Invocation)**
Process phải gọi Adapter một cách trực tiếp và tường minh thông qua biến `env`.
*   **Không dùng Magic:** Không có `Auto-wiring`, không có `Implicit Global Sockets`.
*   Code phải đọc được dòng chảy: `Context -> Process -> Env -> Adapter -> Hardware`.

---

## 8.4. Anti-OOP Manifesto (Không Interface, Không DI)

Spec Chapter 9 khẳng định dứt khoát:
> **POP từ chối sự phức tạp của Interface/Abstract Class cho Adapter.**

Trong 99% trường hợp thực tế, bạn không thay đổi Database hay Camera mỗi ngày. Việc tạo ra hàng tá `interface` (như `ICamera`, `IDatabase`) chỉ làm code phình to và khó đọc (Cognitive Overhead).

**Giải pháp POP:**
*   Viết Adapter class cụ thể (`RedisAdapter`, `RealsenseCamera`).
*   Gắn nó vào `Env`.
*   Nếu cần thay đổi (ví dụ: đổi từ Redis sang Memcached), hãy sửa code trong Adapter hoặc thay thế instance trong `Env` lúc khởi chạy (Configuration Phase). Đừng làm phức tạp hóa code runtime bằng Polymorphism không cần thiết.

---

## 8.5. Ví dụ Cấu trúc Adapter

**File: `adapters/camera_driver.py`**
```python
class CameraDriver:
    def connect(self, ip: str): ...
    def read_frame(self) -> bytes:
        # Code OpenCV / SDK
        return b'\x00...'
```

**File: `engine/env.py`**
```python
@dataclass
class Environment:
    camera: CameraDriver
    db: DatabaseDriver
    # ...
```

**File: `modules/vision/process.py`**
```python
def capture_image(ctx, env):
    # Process gọi Adapter. Adapter không biết gì về ctx.
    frame = env.camera.read_frame() 
    if not frame:
        ctx.error = "Camera Timeout"
    else:
        ctx.raw_image = frame
    return ctx
```
