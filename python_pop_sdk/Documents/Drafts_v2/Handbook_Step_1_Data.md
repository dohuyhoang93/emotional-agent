# Bước 1: Từ Hỗn loạn đến Ngăn nắp (Taming the Data)

---

## 1.1. Chuyện nhà Dev: "Ai đã sửa biến `config` của tôi?"

Hãy tưởng tượng bạn quay lại dự án sau 2 tháng nghỉ phép. Bạn nhận được ticket: *"App crash khi user đổi theme sang Dark Mode."*

Bạn mở code ra và thấy:
```python
# settings.py
config = {"theme": "light", "volume": 80}

# audio_module.py (Ông A viết)
from settings import config
def mute():
    config["volume"] = 0  # Sửa trực tiếp!

# ui_module.py (Ông B viết)
from settings import config
def set_dark_mode():
    config = "dark_mode_enabled"  # LỖI: Ghi đè cả dictionary bằng string!
```

Vấn đề không phải là đồng nghiệp của bạn kém. Vấn đề là **Biến Toàn cục (Global Variable)**. Nó giống như việc để ví tiền giữa quảng trường và hy vọng không ai lấy mất. Code của bạn đang ở trạng thái **Hỗn loạn (Chaos)**.

---

## 1.2. Giải pháp POP: Xây nhà cho Dữ liệu

Trong POP, nguyên tắc đầu tiên là: **"Dữ liệu không được vô gia cư."**
Mọi dữ liệu phải thuộc về một ngôi nhà cụ thể gọi là **Context**.

Chúng ta chia "ngôi nhà" này thành 3 phòng riêng biệt:
1.  **System Context:** Root Container. Chứa tất cả mọi thứ.
2.  **Global Context (Phòng Khách):** Chứa cấu hình tĩnh (Config, Constants). Chỉ đọc, ít thay đổi.
3.  **Domain Context (Phòng Làm việc):** Chứa dữ liệu nghiệp vụ chính (User Profile, Order Cart). Đây là nơi sôi động nhất và cần bảo vệ nhất.

---

## 1.3. Thực hành: Khởi tạo & Chiến lược Cài đặt

Trước khi gõ lệnh, hãy bàn về "Nhà" của SDK. Có 3 cách để cài `pop-sdk`, tùy thuộc vào mức độ "khó tính" của dự án:

### **Cách 1: Virtual Environment (Khuyên dùng)**
Đừng bao giờ cài `pop-sdk` (hay bất cứ lib nào) vào Python toàn cục của máy. Bạn sẽ sớm gặp địa ngục xung đột phiên bản ("Dependency Hell").
Luôn tạo môi trường ảo cho mỗi dự án:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate

# Sau đó mới cài
pip install python-pop-sdk
```

### **Cách 2: Vendoring (Cài cục bộ)**
Nếu dự án của bạn có yêu cầu bảo mật cao (No Internet), hoặc bạn muốn sửa đổi Core của POP để phù hợp với nhu cầu riêng, hãy dùng cách này.
Thay vì cài qua pip, bạn coi `pop-sdk` như một phần code của dự án:
1.  Tải source code `pop-sdk` về.
2.  Copy thư mục `pop` vào trong thư mục dự án của bạn (ví dụ: `libs/pop`).
3.  Khi import, Python sẽ ưu tiên lấy code trong thư mục đó.

> **Lợi ích:** Bạn kiểm soát 100% dòng code. Không lo pypi bị down hay tác giả cập nhật bản mới làm hỏng code cũ.

### **Cách 3: Khởi tạo Dự án**
Sau khi đã chọn được cách cài đặt, hãy dùng CLI để dựng bộ khung:

```bash
pop init my_agent
cd my_agent
```

---

## 1.4. Giải phẫu Dự án (Project Anatomy)

Lệnh `init` sẽ tạo ra cấu trúc thư mục tiêu chuẩn. Hãy cùng xem nó có ý nghĩa gì:

```text
my_agent/
├── .venv/                # Môi trường ảo (nếu bạn làm theo Cách 1)
├── .env                  # Cấu hình môi trường (Strict Mode)
├── main.py               # Điểm khởi chạy (Entry Point)
├── workflows/            # Nơi chứa kịch bản chạy (YAML)
│   └── main_workflow.yaml
└── src/
    ├── context.py        # <--- TRÁI TIM CỦA HỆ THỐNG
    └── processes/        # Nơi chứa Logic (Sẽ học ở Bước 2)
        └── p_hello.py
```

*   **`main.py`**: Chịu trách nhiệm khởi tạo Engine và đăng ký Process.
*   **`src/context.py`**: Đây là nơi quan trọng nhất lúc này. Nó định nghĩa "Ngôi nhà" của dữ liệu.

### **Tùy chỉnh Context (Greenfield Project)**
Nếu bạn làm dự án mới (Greenfield), hãy mở `src/context.py` và định nghĩa dữ liệu của bạn ngay. Chúng ta dùng `Pydantic` (hoặc Dataclasses) để có Type Safety.

```python
# src/context.py
from dataclasses import dataclass, field
from typing import List
from pop import BaseDomainContext, BaseGlobalContext

# 1. Global: Cấu hình Tĩnh
@dataclass
class GlobalContext(BaseGlobalContext):
    app_name: str = "SmartAgent"
    timeout: int = 30
    api_key: str = "sk-..."

# 2. Domain: Dữ liệu Nghiệp vụ (Thay đổi liên tục)
@dataclass
class DomainContext(BaseDomainContext):
    user_name: str = ""
    messages: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0
```

Ngay lập tức, bạn có **Autocompletion** và **Type Checking** trên toàn dự án. Không còn cảnh gõ nhầm `user_ame` hay gán string vào `timeout` nữa.

---

## 1.5. Chiến lược Di cư (Refactoring Legacy Code)

Nếu bạn đang có một dự án cũ ("Brownfield") với đầy rẫy biến toàn cục, đừng đập đi xây lại. Hãy áp dụng chiến lược **"Di dân từ từ"**:

1.  **Bước 1: Tạo Context song song.** Chạy `pop init` vào một thư mục con hoặc tự tạo file `context.py`.
2.  **Bước 2: Di chuyển Config.** Chuyển các biến trong `config.py` cũ vào `GlobalContext`.
    *   *Mẹo:* Trong code cũ, thay vì import `config`, hãy import `system.global_ctx`.
3.  **Bước 3: Gom nhóm State.** Tìm các biến toàn cục rời rạc (`current_user`, `is_loading`) và đưa vào `DomainContext`.

---

## 1.6. Tổng kết Bước 1

Chúng ta chưa viết logic xử lý nào, nhưng chúng ta đã thắng lớn:
*   **Tổ chức:** Dữ liệu đã có nơi chốn rõ ràng.
*   **An toàn:** Type Hint bảo vệ bạn khỏi nhưng lỗi ngớ ngẩn.
*   **Chuẩn hóa:** Cấu trúc dự án rõ ràng, người mới vào nhìn là hiểu ngay `context.py` chứa gì.

**Thử thách:** Hãy chạy `pop init`, sau đó sửa `DomainContext` để thêm một list `todo_items`. Thử viết code trong `main.py` để truy cập nó và xem IDE hỗ trợ bạn sướng thế nào!
