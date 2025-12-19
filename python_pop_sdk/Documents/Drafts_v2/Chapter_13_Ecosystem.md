# Chương 13: Hệ sinh thái & Công cụ (Theus Ecosystem)

---

## 13.1. Theus CLI (`theus`)

Theus không chỉ là thư viện, nó là một **Framework Agentic** hoàn chỉnh.
Trung tâm của hệ sinh thái là lệnh `theus` - công cụ giúp bạn khởi tạo, vận hành và kiểm tra Agent.

### Các lệnh phổ biến:
*   `theus init [name]`: Khởi tạo dự án chuẩn.
*   `theus run [workflow]`: Chạy một workflow.
*   `theus visualize`: Vẽ đồ thị workflow ra file ảnh.
*   `theus audit`: Quét code để phát hiện vi phạm contract (Static Analysis).

---

## 13.2. Tiện ích mở rộng (Theus Extensions)

Theus được thiết kế để mở rộng (Extensible). Cộng đồng có thể đóng góp các "Process Pack".

### Standard Library (`theus.stdlib`)
Tích hợp sẵn:
*   `theus.stdlib.http`: Các process gọi API.
*   `theus.stdlib.files`: Đọc ghi file an toàn.
*   `theus.stdlib.time`: Timer, Delay, Schedule.

### Community Hub
Trong tương lai, bạn có thể cài thêm:
```bash
pip install theus-opencv
pip install theus-llm
```

---

## 13.3. Tầm nhìn: From Ops to No-Code

Lộ trình phát triển của Theus:
1.  **Giai đoạn 1 (Developer Experience):** Tập trung vào Python SDK, CLI và VSCode Extension.
2.  **Giai đoạn 2 (Visual Editor):** UI kéo thả Workflow cho Non-tech user.
3.  **Giai đoạn 3 (AI Architect):** "Theus, hãy tạo workflow nhận diện khách hàng VIP", và AI sẽ tự viết YAML + Python cho bạn.

Theus chính là nền tảng (Foundation) vững chắc để xây dựng những giấc mơ đó.
