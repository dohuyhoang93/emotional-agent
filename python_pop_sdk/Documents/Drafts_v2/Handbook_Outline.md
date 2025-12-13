# Đề cương: Sổ tay Đồng hành POP (The POP Companion Handbook)

---

## 🟥 Triết lý Tiếp cận (The Approach)

Khác với phần "Lý thuyết Cốt lõi" (Core Specification) khô khan và nghiêm ngặt, cuốn Sổ tay này được thiết kế như một người bạn đồng hành (Mentor).
*   **Phong cách:** Tiến hóa (Evolutionary). Không áp đặt toàn bộ kiến trúc ngay từ đầu.
*   **Phương pháp:** Đặt vấn đề (Tại sao code hiện tại khó bảo trì?) -> Gợi mở giải pháp (Tư duy POP) -> Thực hành (Dùng `pop-sdk`).
*   **Mục tiêu:** Giúp Developer tự nhận ra giá trị của POP qua từng bài toán cụ thể.

---

## 🟦 Lộ trình Tiến hóa (The Evolutionary Arc)

### **Bước 1: Từ Hỗn loạn đến Ngăn nắp (Taming the Data)**
*   **Vấn đề:** "Biến toàn cục (Global Variable) ở khắp nơi. Tôi không biết ai đang sửa dữ liệu của tôi."
*   **Giải pháp Tư duy:** Gom tất cả vào Context. Phân chia rõ System/Domain/Local.
*   **Thực hành SDK:**
    *   Tạo `UserContext` với Pydantic.
    *   Sử dụng `pop-cli init` để tạo cấu trúc thư mục.

### **Bước 2: Nghệ thuật của Hành động Thuần khiết (The Art of Pure Action)**
*   **Vấn đề:** "Hàm này vừa tính toán, vừa ghi log, vừa gọi database. Test rất khó."
*   **Giải pháp Tư duy:** Tách biệt Side-effect. Process chỉ là hàm thuần túy biến đổi Input -> Output.
*   **Thực hành SDK:**
    *   Viết hàm `@process` đầu tiên.
    *   Khai báo Contract `inputs/outputs`.
    *   Chạy thử với `engine.run()`.

### **Bước 3: Dòng chảy được Điều phối (Orchestrated Flow)**
*   **Vấn đề:** "Code chính của tôi là một chuỗi if/else lồng nhau 10 cấp. Đọc không hiểu gì cả."
*   **Giải pháp Tư duy:** Linear Pipeline. Nhìn logic như một dây chuyền sản xuất.
*   **Thực hành SDK:**
    *   Sử dụng YAML để ghép nối các Process lại với nhau.
    *   Visualize dòng chảy bằng công cụ (nếu có) hoặc sơ đồ tư duy.

### **Bước 4: Tương tác với Thực tại (Interacting with Reality)**
*   **Vấn đề:** "Làm sao tôi mock được cái Camera này để test logic?"
*   **Giải pháp Tư duy:** Adapter & Environment. Xem IO là các plugin, không phải code cứng.
*   **Thực hành SDK:**
    *   Tạo `CameraAdapter` protocol.
    *   Inject vào `env`.
    *   Viết Unit Test thay thế adapter thật bằng adapter giả.

### **Bước 5: Chinh phục Đại Monolith (The Complex Monolith)**
*   **Vấn đề:** "Dự án lớn quá, một file YAML dài 1000 dòng."
*   **Giải pháp Tư duy:** Modularization. Chia nhỏ thành các Sub-flow. Branching và Dynamic Router.
*   **Thực hành SDK:**
    *   Tổ chức module theo Feature.
    *   Sử dụng `use_subflow` trong YAML.
    *   Xử lý rẽ nhánh thông minh.

### **Bước 6: Sẵn sàng ra Trận (Production Readiness)**
*   **Vấn đề:** "Lỗi xảy ra trên Production nhưng tôi không biết tại sao."
*   **Giải pháp Tư duy:** Observability & Error Handling.
*   **Thực hành SDK:**
    *   Đọc Audit Log của Engine.
    *   Xử lý lỗi (Fail-fast strategy).
    *   Cấu hình Performance Monitor.

---

## 🟩 Định dạng Trình bày

Mỗi chương sẽ tuân theo cấu trúc:
1.  **Chuyện nhà Dev:** Một tình huống đau đầu thực tế (e.g., "Bug lúc 3 giờ sáng").
2.  **Câu hỏi Gợi mở:** "Tại sao chúng ta lại để dữ liệu chạy lung tung như vậy?"
3.  **Góc nhìn POP:** Giới thiệu khái niệm giải quyết vấn đề.
4.  **Show me the Code:** Hướng dẫn từng bước với `pop-sdk`.
5.  **Challenge:** Bài tập nhỏ để Dev tự mở rộng.
