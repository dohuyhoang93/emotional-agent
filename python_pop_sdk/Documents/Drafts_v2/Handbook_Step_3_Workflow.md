# Bước 3: Thiết lập Dòng chảy (Theus Flow)

---

## 3.1. Nhạc Trưởng vô hình

Trong hệ thống Theus, bạn không cần viết class `MainApplication` hay hàm `run()` khổng lồ.
Thay vào đó, bạn đóng vai Nhạc trưởng (Conductor), sắp xếp các Process vào một danh sách phát (Playlist).

Chúng ta gọi playlist đó là **Workflow**.

---

## 3.2. Viết Workflow đầu tiên

Tạo file `specs/workflow.yaml`. Đây là "bản vẽ kỹ thuật" cho dây chuyền sản xuất của bạn.

```yaml
version: "2.0"
name: "Smart Camera Pipeline"

modes:
  # Chế độ mặc định
  production:
    steps:
      # Step 1: Lấy ảnh
      - "domain.vision.capture_frame"
      
      # Step 2: Xử lý
      - "domain.vision.check_quality"
      - "domain.vision.detect_objects"
      
      # Step 3: Quyết định (Orchestrator Logic)
      - "domain.behavior.decide_action"
      
      # Step 4: Hành động
      - "domain.actuators.execute_command"

settings:
  stop_on_error: true
```

---

## 3.3. Chạy Workflow (`theus run`)

Bạn không cần viết code Python để chạy file YAML này. Engine có sẵn CLI.

```bash
# Chạy chế độ production
theus run specs/workflow.yaml --mode production
```

**Điều gì xảy ra bên dưới?**
1.  **Bootstrapping:** Engine quét thư mục `src/`, tìm tất cả các hàm có decorator `@process` và đăng ký vào Registry.
2.  **Validation:** Engine kiểm tra xem các bước trong YAML có tồn tại trong Registry không.
3.  **Execution:** Engine tạo Context rỗng, và lần lượt gọi từng Process.
4.  **Transaction:** Mỗi bước là một transaction. Nếu `detect_objects` lỗi, Context quay về trạng thái sau khi xong `check_quality`.

---

## 3.4. Tư duy "Dòng chảy Tuyến tính" (Linear Flow Mindset)

Bạn sẽ thắc mắc: *"Tại sao không có if/else trong YAML?"*
Ví dụ bạn muốn: *Nếu ảnh mờ thì dừng lại, không detect nữa.*

Trong Theus, chúng tôi chủ trương **Logic nằm ở Code, không phải ở Config.**

**Cách làm đúng:**
Trong process `check_image_quality`, nếu ảnh mờ, hãy dùng `ctx.skip_workflow()` hoặc trả về một Error Code để Orchestrator xử lý.

```python
@process(...)
def check_image_quality(ctx):
    if is_blur(ctx.frame):
        # Dừng toàn bộ workflow hiện tại một cách an toàn
        return ctx.stop("IMAGE_BLURRED")
    return ctx.done()
```

---

## 3.5. Tổng kết

*   Workflow YAML là nơi **kê khai thứ tự**, không phải nơi lập trình.
*   Dùng `theus run` để thực thi.
*   Xử lý rẽ nhánh/dừng luồng bên trong Process Logic (dùng `ctx.stop` hoặc `ctx.fail`).
