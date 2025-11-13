# Tiêu chuẩn Kiến trúc Hướng Quy trình (Process-Oriented Programming - POP)

## 1. Triết lý cốt lõi

Kiến trúc này được xây dựng dựa trên nguyên tắc cơ bản: **Tách biệt hoàn toàn giữa Dữ liệu (Data) và Hành vi (Behavior/Logic)**.

Mục tiêu là tạo ra các hệ thống có các đặc tính sau:
- **Minh bạch (Transparent):** Luồng hoạt động của hệ thống rõ ràng, tường minh, không có logic ẩn.
- **Dễ kiểm thử (Testable):** Từng đơn vị logic có thể được kiểm thử độc lập một cách dễ dàng.
- **Linh hoạt & Dễ mở rộng (Flexible & Extensible):** Dễ dàng thêm, bớt, hoặc sắp xếp lại các chức năng mà không ảnh hưởng lớn đến toàn bộ hệ thống.

Chúng ta từ bỏ mô hình OOP truyền thống, nơi dữ liệu và hành vi được đóng gói trong các đối tượng, để chuyển sang một mô hình mà ở đó, logic là một chuỗi các phép biến đổi trên dữ liệu "câm".

## 2. Các thành phần kiến trúc

Một hệ thống POP chuẩn bao gồm 5 thành phần chính:

### 2.1. Dữ liệu Ngữ cảnh (Context Data)

- Là các cấu trúc dữ liệu "câm" (plain data structures), chỉ chứa thông tin, không chứa phương thức hay logic.
- **QUY TẮC:** Phải định nghĩa các cấu trúc dữ liệu riêng biệt, có mục đích rõ ràng cho từng loại nghiệp vụ. **TRÁNH** tạo ra một đối tượng `context` toàn cục chứa tất cả mọi thứ ("God Object").

```python
# TỐT: Dữ liệu được định nghĩa rõ ràng
class CoffeeOrderData:
    def __init__(self, coffee_type):
        self.coffee_type = coffee_type
        self.has_water = False
        self.is_brewed = False
        self.sugar_level = 0

# XẤU: Dữ liệu là một "cái túi" không rõ ràng
# ctx = {} 
```

### 2.2. Quy trình (Process)

- Là một hàm thuần túy (pure function) hoặc gần thuần túy, nhận **Dữ liệu Ngữ cảnh** làm đầu vào, thực hiện một và chỉ một tác vụ, và trả về **Dữ liệu Ngữ cảnh** đã được biến đổi.
- Signature chuẩn: `def process_name(context: T) -> T:`

```python
def add_sugar(order_data: CoffeeOrderData) -> CoffeeOrderData:
    print("Thêm đường...")
    order_data.sugar_level += 1
    return order_data
```

### 2.3. Sổ đăng ký Quy trình (Process Registry)

- Là một cấu trúc dữ liệu (thường là Dictionary/Map) ánh xạ tên quy trình (dạng chuỗi) tới đối tượng hàm (function object).
- Điều này cho phép "bộ máy" có thể gọi hàm một cách linh hoạt từ tên được định nghĩa trong file cấu hình.

```python
REGISTRY = {
    "add_sugar": add_sugar,
    "boil_water": boil_water,
}
```

### 2.4. Định nghĩa Luồng quy trình (Workflow Definition)

- Là một tệp cấu hình bên ngoài (ưu tiên JSON hoặc YAML) định nghĩa chuỗi các bước cần thực hiện.
- Cấu trúc này cho phép thay đổi logic nghiệp vụ mà không cần sửa đổi mã nguồn.
- Hỗ trợ các bước tuần tự (chuỗi) và các bước "song song" (mảng lồng nhau).

```json
{
  "name": "Pha Cà phê Sữa",
  "steps": [
    "boil_water",
    "brew_coffee",
    [
      "add_sugar",
      "add_milk"
    ],
    "taste_test",
    "enjoy"
  ]
}
```

### 2.5. Bộ máy thực thi (Workflow Engine)

- Là một hàm đơn giản, nhận vào **Định nghĩa Luồng quy trình** và **Dữ liệu Ngữ cảnh** ban đầu.
- Vòng lặp của Engine sẽ đọc từng bước trong định nghĩa, tra cứu hàm tương ứng trong **Sổ đăng ký**, và thực thi nó.

```python
def run_workflow(workflow_steps: list, context: T) -> T:
    for step in workflow_steps:
        if isinstance(step, str):
            process_func = REGISTRY[step]
            context = process_func(context)
        elif isinstance(step, list): # Xử lý song song (hoặc tuần tự trong song song)
            for sub_step in step:
                process_func = REGISTRY[sub_step]
                context = process_func(context)
    return context
```

## 3. Tư duy nâng cao: "Đối tượng" là một Module/Label

Để quản lý các hệ thống phức tạp, chúng ta không hoàn toàn vứt bỏ khái niệm "đối tượng". Thay vào đó, chúng ta tái định nghĩa nó:

> **Một "Đối tượng" chỉ là một "Label" (nhãn) hay một "Module" (mô-đun) đại diện cho một tổ hợp các Quy trình liên quan hoạt động trên một loại Dữ liệu Ngữ cảnh cụ thể.**

- **Tổ chức mã nguồn:** Nhóm các `Process` và `Context Data` liên quan vào cùng một file/module.
  - `coffee_order_module.py` sẽ chứa `CoffeeOrderData`, `add_sugar`, `add_milk`...
  - `user_connection_module.py` sẽ chứa `ConnectionData`, `connect`, `disconnect`...
- **Lợi ích:** Cách tiếp cận này mang lại sự đóng gói ở cấp độ module, giúp mã nguồn có tổ chức và dễ tìm kiếm, nhưng vẫn giữ được sự linh hoạt và minh bạch của kiến trúc POP.

## 4. Rủi ro và Giải pháp

1.  **Rủi ro:** Tài liệu về luồng quy trình (`.json`, `.md`) bị lỗi thời so với mã nguồn.
    - **Giải pháp:** **KỶ LUẬT.** Coi việc cập nhật tài liệu là một phần không thể thiếu của mọi thay đổi. Tự động hóa việc tạo đồ thị từ file JSON nếu có thể.
2.  **Rủi ro:** Cấu trúc `Context Data` trở nên quá phức tạp và cồng kềnh.
    - **Giải pháp:** Tuân thủ nghiêm ngặt quy tắc "Dữ liệu Ngữ cảnh riêng biệt cho từng nghiệp vụ". Chia nhỏ các nghiệp vụ phức tạp thành các luồng quy trình con, mỗi luồng có Context Data riêng.
