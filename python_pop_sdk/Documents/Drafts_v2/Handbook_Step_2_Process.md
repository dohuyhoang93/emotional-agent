# Bước 2: Nghệ thuật của Hành động Thuần khiết (The Art of Pure Action)

---

## 2.1. Chuyện nhà Dev: "Hàm này làm gì? Làm tất cả!"

Bạn đang debug một lỗi sai lệch tồn kho. Bạn tìm thấy một hàm `process_order()` dài 500 dòng.
Nó làm gì?
1.  Tính tổng tiền, check hạng thành viên (Logic).
2.  Query DB để lấy tồn kho (Implicit IO).
3.  Gửi email xác nhận (Side-effect).
4.  Dùng `datetime.now()` để tạo `created_at` (Non-deterministic).
5.  Modifiy thẳng vào biến global `TOTAL_REVENUE` (Global Mutation).

Đây là **"Spaghetti Function"**. Mọi thứ dính chùm vào nhau, không thể gỡ ra để test riêng lẻ.

---

## 2.2. Giải pháp POP: Process & Bản Hợp đồng (The Contract)

Trong POP, hàm không còn tự do muốn làm gì thì làm. Nó bị ràng buộc bởi một **Contract** (Hợp đồng).

Hãy xem lại SDK. Decorator `@process` cho phép bạn khai báo 4 điều:
1.  **`inputs`**: Tôi cần đọc gì?
2.  **`outputs`**: Tôi sẽ ghi gì?
3.  **`side_effects`**: Tôi có tác động ra bên ngoài không (Log, DB, API)?
4.  **`errors`**: Những lỗi nào tôi có thể trả về?

---

## 2.3. Thực hành: Xử lý Đơn hàng Thực tế

Hãy viết process `validate_order` với đầy đủ các thành phần của hợp đồng.

```python
from pop import process
from src.context import SystemContext

@process(
    name="validate_order",
    inputs=[
        'domain.user',      
        'domain.order',     
        'domain.warehouse'  
    ],
    outputs=[
        'domain.order.status',  
        'domain.order.error'    
    ],
    # Khai báo Side Effect và Error (Optional nhưng rất nên dùng)
    side_effects=['LOGGING'], 
    errors=['FAILED', 'REJECTED'] 
)
def validate_order(ctx: SystemContext):
    user = ctx.domain.user
    order = ctx.domain.order
    warehouse = ctx.domain.warehouse
    
    # Side-effect đã khai báo: Logging
    print(f"--- Validating Order for User: {user.name} ---")

    # Check 1: User bị khóa?
    if not user.is_active:
        ctx.domain.order.status = "REJECTED"
        ctx.domain.order.error = "User is banned"
        return "REJECTED" 

    # Check 2: Đủ tiền không?
    if user.balance < order.total_amount:
        ctx.domain.order.status = "REJECTED"
        ctx.domain.order.error = f"Insufficient funds: {user.balance} < {order.total_amount}"
        return "FAILED"

    # Check 3: Còn hàng không?
    for item in order.items:
        available = warehouse.stock_map.get(item.sku, 0)
        if available < item.quantity:
            ctx.domain.order.status = "REJECTED"
            ctx.domain.order.error = f"Out of stock: {item.sku}"
            return "FAILED"

    # Nếu qua hết
    ctx.domain.order.status = "VALIDATED"
    ctx.domain.order.error = ""
    return "OK"
```

---

## 2.4. Sự thật về SDK: Cái gì bị chặn, cái gì là Kỷ luật?

Bạn có thể thắc mắc: *"Nếu tôi lén gọi DB trong hàm này thì SDK có chặn không?"*

Câu trả lời là: **Không (với bản Python hiện tại).**
Python là ngôn ngữ động, SDK không thể can thiệp vào việc bạn import thư viện DB hay gọi `datetime.now()`.

### **1. Cái SDK chặn (Enforced by Code)**
*   **Truy cập Dữ liệu (State Access):** `ContextGuard` sẽ chặn đứng nếu bạn đọc/ghi vào biến Context chưa khai báo trong `inputs/outputs`. Đây là cơ chế "Soft Customs Gate" bảo vệ bộ nhớ.

### **2. Cái do bạn tự giác (Enforced by Discipline)**
*   **Side Effects (IO/DB):** Bạn phải tự giác đẩy logic IO ra ngoài rìa (Adapter) hoặc tách thành Process riêng. Khai báo `side_effects` giúp đồng nghiệp biết hàm này không "thuần khiết".
*   **Determinism (Time/Random):** Bạn phải tự giác không dùng `datetime.now()` để đảm bảo Process có thể test được (Testability).

> **Lời khuyên:** Đừng coi Contract là gông cùm. Hãy coi nó là tấm biển chỉ dẫn giúp code của bạn không đi lạc vào rừng rậm "Spaghetti".

---

## 2.5. Tổng kết Bước 2

*   Viết Process = Viết Hợp đồng (Contract).
*   **Inputs/Outputs:** Bắt buộc và bị kiểm soát chặt bởi SDK.
*   **Side Effects/Errors:** Khai báo để minh bạch hóa hệ thống.

**Thử thách:** Hãy thử xóa dòng `outputs=['domain.order.status']` và chạy lại code. Bạn sẽ thấy SDK ném lỗi `PermissionDenied` ngay lập tức khi hàm cố gán giá trị. Cảm giác an toàn tuyệt vời!

---

## 2.5. Tổng kết Bước 2

Bạn vừa viết được một khối logic:
1.  **An toàn:** Không ai sửa được state nếu không khai báo output.
2.  **Dễ test:** Chỉ cần tạo Context giả với `user.balance = 0`, gọi hàm, và assert `order.status == "REJECTED"`. Không cần mock DB!
3.  **Rõ ràng:** Nhìn vào `inputs=['warehouse']` là biết hàm này phụ thuộc kho hàng.

**Thử thách:** Hãy thêm logic "Giảm giá 10% nếu User VIP" vào đoạn code trên. Nhớ thêm `domain.order.total_amount` vào danh sách `outputs` trước khi sửa nó nhé! Nếu không Engine sẽ báo lỗi `PermissionDenied`.
