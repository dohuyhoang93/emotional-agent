# Chương 9: Hợp đồng Tin cậy (Theus Integrity Contracts)

---

## 9.1. Tại sao code cần "Hợp đồng"?

Hãy tưởng tượng bạn bước vào một nhà hàng sang trọng. Bạn xem thực đơn (Input), gọi món, và đầu bếp chế biến ra món ăn (Output). Nếu nhà hàng không có thực đơn, bạn sẽ phải vào tận bếp để hỏi xem có nguyên liệu gì. Đó là sự hỗn loạn.

Trong lập trình Theus, **Contract** là bản cam kết công khai của Process: *"Tôi cần gì, Tôi làm gì, và Tôi trả lại gì."*

Theus nâng tầm Contract lên thành **Luật (Law)**. Không giống như Type Hint trong Python (chỉ là gợi ý), Contract trong Theus được Engine **cưỡng chế (enforced)** tại Runtime.

---

## 9.2. Ba Trụ cột của Hợp đồng (The 3 Pillars of Contract)

Một Contract hợp lệ phải được xác định dựa trên **Ma trận An toàn 3 Trục** (xem Chương 4 và 12).

### **Pillar 1: Input Contract (Quyền Đọc)**
**Nguyên tắc:** *Pre-flight Check & Immutability.*
1.  **Khai báo toàn diện:** Process cấm truy cập bất kỳ biến nào không khai báo trong `inputs`.
2.  **Bất biến:** Dữ liệu Input bị Engine đóng băng (Frozen). Process chỉ được ĐỌC, không được SỬA.
    *   *Vi phạm:* `ctx.domain.user_id = 1` -> `ContractViolationError` (Illegal Write on Input).
3.  **Hạn chế Zone:** Cấm dùng `Signal` làm Input (vì Signal không ổn định).

### **Pillar 2: Output Contract (Quyền Ghi)**
**Nguyên tắc:** *Exclusive Mutation.*
1.  **Ghi đúng đích:** Process chỉ được ghi vào các field khai báo trong `outputs`.
2.  **Đảm bảo Type:** Theus check type của dữ liệu ghi ra so với Schema.
    *   *Vi phạm:* Ghi `str` vào field `int` -> `TypeError` (Audit Logged).

### **Pillar 3: Side-Effect Contract (Quyền Tác động)**
**Nguyên tắc:** *Managed I/O.*
1.  **Danh sách trắng (Whitelist):** Mọi tác động ra bên ngoài (API call, DB Write) phải được liệt kê.
2.  **Không logic ẩn:** Không được lén gọi `requests.get()` mà không khai báo.

---

## 9.3. Hệ thống Kiểm soát Lỗi (Error Contract)

Theus loại bỏ tư duy `try/catch` truyền thống. Lỗi là một phần của luồng dữ liệu.

### **Rule 1: Lỗi là Dữ liệu (Error as Data)**
Lỗi nghiệp vụ (Business Error) không phải là Exception. Nó là một trạng thái hợp lệ.
*   Ví dụ: "Không tìm thấy mặt" là một kết quả, không phải là crash.
*   Process phải trả về mã lỗi: `return ctx.fail("FACE_NOT_FOUND")`.

### **Rule 2: Minh bạch khả năng lỗi**
Process phải khai báo: `errors: ["TIMEOUT", "INVALID_DATA"]`.
Điều này giúp Workflow Engine biết cách điều hướng (Rẽ nhánh khi gặp lỗi này).

---

## 9.4. Tòa án Tối cao: Audit Recipe (`audit_recipe.yaml`)

Ngoài Contract của từng Process, Theus giới thiệu một cơ chế kiểm soát toàn cục gọi là **Audit Recipe**. Đây là nơi định nghĩa các luật lệ "siêu cấp" mà mọi Process phải tuân theo.

Ví dụ `specs/audit_recipe.yaml`:

```yaml
audit:
  input_gate:
    # Luật: Không bao giờ được phép process nếu nhiệt độ lò > 1000
    - check: "ctx.domain.sensor.temp > 1000"
      action: INTERLOCK # Dừng khẩn cấp toàn bộ hệ thống
      message: "Lò quá nhiệt, nguy hiểm!"
      
    # Luật: Cảnh báo nếu pin yếu
    - check: "ctx.domain.robot.battery < 20"
      action: WARN # Ghi log warning
      
  output_gate:
    # Luật: Không được ghi đè user_id thành null
    - check: "ctx.domain.user_id is None"
      action: BLOCK # Từ chối commit transaction này
      message: "Logic lỗi cố gắng xóa user_id"
```

**Các mức độ hành động (Action Levels):**
1.  **LOG/WARN:** Ghi nhận sự việc, Process vẫn chạy tiếp.
2.  **BLOCK:** Hủy bỏ kết quả của Transaction (Rollback). Hệ thống vẫn chạy tiếp.
3.  **INTERLOCK:** Dừng khẩn cấp toàn bộ hệ thống (Kill Switch). Dùng cho vi phạm an toàn nghiêm trọng.

---

## 9.5. Ví dụ Contract Toàn diện

Dưới đây là một ví dụ mẫu mực về một Process Contract trong Theus:

```python
@process(
    # [1] Input: Chỉ đọc, Bất biến
    inputs=[
        "domain.vision.target_coords", 
        "global.config.safety_limits" # Cross-layer read allowed
    ],
    
    # [2] Output: Quyền ghi độc quyền
    outputs=[
        "domain.robot.current_position",
        "domain.robot.status"
    ],
    
    # [3] Side-Effects: I/O ra thiết bị thật
    side_effects=["plc_controller"],
    
    # [4] Errors: Các khả năng thất bại
    errors=["OUT_OF_REACH", "GRIPPER_JAMMED"]
)
def pick_item(ctx):
    """
    Điều khiển cánh tay robot gắp vật thể.
    """
    # Logic implementation...
    pass
```

> **Lời kết:** Contract không làm chậm Dev. Contract giúp Dev ngủ ngon vì biết rằng: **"Những gì mình không cho phép thì không thể xảy ra."**
