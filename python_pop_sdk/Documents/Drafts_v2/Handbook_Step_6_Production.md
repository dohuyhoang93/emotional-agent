# Bước 6: Sẵn sàng ra Trận (Production Readiness)

---

## 6.1. Chuyện nhà Dev: "Code chạy trên máy tôi!"

Bạn code xong, chạy thử thấy ngon. Đẩy lên server -> Crash.
Sếp hỏi: "Tại sao crash?". Bạn ú ớ: "Em không biết, không có log".
Tester bảo: "Tính năng này đã test chưa?". Bạn bảo: "Em chạy tay rồi".

Ở bước cuối cùng này, chúng ta sẽ biến dự án từ "đồ chơi" thành "vũ khí" thực thụ.

---

## 6.2. Kiểm thử (Testing): Dễ như ăn kẹo

Trong OOP, test rất khổ vì phải Mock đủ thứ object lằng nhằng.
Trong POP, test cực sướng vì:
1.  **Data là Dumb (Dataclass):** Chỉ cần `Context(val=1)`.
2.  **Process là Hàm thuần khiết:** Gọi hàm, check kết quả.
3.  **IO là Adapter:** Mock cái Adapter là xong.

### **Thực hành: Unit Test cho `validate_order`**
Tạo file `tests/test_validation.py`:

```python
import unittest
from src.context import SystemContext, GlobalContext, DomainContext, EnvContext
from src.processes.p_validation import validate_order

# 1. Mock Adapter
class MockWarehouse:
    stock_map = {"IPHONE": 0} # Tồn kho bằng 0

class TestValidation(unittest.TestCase):
    def test_out_of_stock(self):
        # 2. Setup Context Giả
        domain = DomainContext()
        domain.user.balance = 1000
        domain.order.items = [{"sku": "IPHONE", "quantity": 1}]
        
        # Inject Mock Adapter
        env = EnvContext()
        # Giả sử chúng ta đã sửa process để dùng WarehouseAdapter
        # env.warehouse = MockWarehouse() 
        # Hoặc nếu dùng data thuần:
        domain.warehouse.stock_map = {"IPHONE": 0}

        ctx = SystemContext(GlobalContext(), domain, env)

        # 3. Gọi Process trực tiếp (Không cần Engine)
        result = validate_order(ctx)

        # 4. Assert
        self.assertEqual(result, "FAILED")
        self.assertEqual(ctx.domain.order.status, "REJECTED")
        self.assertIn("Out of stock", ctx.domain.order.error)

if __name__ == '__main__':
    unittest.main()
```

Bạn thấy không? Không cần `MagicMock`, không cần `patch`. Chỉ là gán biến và so sánh.

---

## 6.3. Logging: Đèn pha trong đêm

Đừng dùng `print()`. Hãy dùng `logging` chuẩn của Python.
Và nhớ quy tắc: **Logging là một Side-effect**. Hãy khai báo nó.

```python
import logging

logger = logging.getLogger("APP")

@process(..., side_effects=['LOGGING'])
def calculate_discount(ctx):
    logger.info(f"Computing discount for User {ctx.domain.user.id}")
    # ...
```

Khi chạy Production, bạn chỉ cần config `logging.basicConfig(level=logging.ERROR)` để tắt bớt thông tin rác.

---

## 6.4. CLI: Biến Script thành App

Thay vì sửa code `main.py` mỗi lần muốn chạy flow khác nhau, hãy dùng `argparse` để nhận tham số từ bên ngoài.

```python
# main.py
import argparse
import sys
# ... imports ...

def main():
    parser = argparse.ArgumentParser(description="My POP Agent")
    parser.add_argument("command", choices=["run", "test"], help="Lệnh cần chạy")
    parser.add_argument("--flow", default="checkout", help="Tên workflow cần chạy")
    
    args = parser.parse_args()
    
    # Init Engine & Context...
    ctx = SystemContext(...)
    engine = POPEngine(ctx)
    # Register processes...

    if args.command == "run":
        yaml_file = f"workflows/{args.flow}.yaml"
        print(f"🚀 Starting Flow: {yaml_file}")
        engine.execute_workflow(yaml_file)
        
        # In kết quả cuối
        if ctx.domain.system_signal:
             print(f"🏁 Signal: {ctx.domain.system_signal}")

if __name__ == "__main__":
    main()
```

Giờ bạn có thể gõ:
*   `python main.py run --flow=vip_checkout`
*   `python main.py run --flow=refund`

---

## 6.5. Lời kết: Bạn đã là một POP Engineer

Chúc mừng! Bạn đã đi hết 6 bước tiến hóa:
1.  **Data:** Gom về một mối (`Context`).
2.  **Process:** Viết hàm thuần khiết, khai báo minh bạch (`@process`).
3.  **Workflow:** Vẽ luồng chạy bằng YAML.
4.  **Adapters:** Đẩy IO ra rìa, dùng `env_ctx`.
5.  **Complexity:** Chia nhỏ và trị (Signal Pattern).
6.  **Production:** Test, Log và đóng gói CLI.

POP không hứa làm bạn code nhanh hơn ngay ngày đầu.
Nhưng POP hứa rằng **6 tháng sau**, khi bạn nhìn lại code cũ, bạn sẽ mỉm cười vì vẫn hiểu nó làm gì, và dám sửa nó mà không sợ sập hệ thống.

**Hành trình của bạn mới chỉ bắt đầu. Hãy mang tư duy POP vào mọi dòng code bạn viết!**
