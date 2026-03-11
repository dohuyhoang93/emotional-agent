# Theus Framework Issue Report: The "Silent Deadlock" in Payload Validation

**Date:** 2026-03-07
**Component:** `theus.contracts.process` (Theus Engine Resolver)
**Severity:** Critical (Logic/State Freeze)
**Author:** SNN System Integration Team
**Status:** Open / Feedback Submitted

---

## 1. Executive Summary

Trong thực nghiệm "Multi-Agent Complex Maze" kéo dài 400 episodes (200.000 bước thời gian), hệ thống ghi nhận hiện tượng **Cognitive Freeze**: Cấu trúc mạng SNN (1024 nơ-ron) không có bất kỳ dấu hiệu học tập nào. Trung bình Firing Rate xấp xỉ 0 và giá trị Threshold giữ nguyên ở mức khởi tạo ($0.0504$). 

Sau quá trình điều tra pháp y (Forensic Analysis) và đánh giá qua Hệ thống Tiêu chuẩn Trí tuệ (Intellectual Virtues Audit), nguyên nhân gốc rễ được xác định không nằm ở sai sót toán học của hệ thống SNN, mà ở cơ chế **Dependency Validation** quá khắt khe kết hợp với **Silent Failure** của Theus Engine khi xử lý thuộc tính Dictionary lồng nhau.

## 2. Technical Details & Root Cause

### The Decorator Constraint
Quy trình `process_homeostasis` được quy định chặt chẽ bởi Theus `@process` decorator như sau:
```python
@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.snn_context.domain_ctx.metrics',
        'domain_ctx.snn_context.domain_ctx.metrics.fire_rate', # <--- The Block
        # ...
    ],
    # ...
)
def process_homeostasis(ctx: SNNSystemContext):
```

### The Infinite Deadlock Loop
Sự cố xảy ra theo chuỗi logic sau:
1. Tại $T=0$, Factory `create_snn_context_theus` khởi tạo `snn_context.domain_ctx.metrics` là một từ điển rỗng `{}`.
2. Khi Pipeline thực thi bước đầu tiên, Theus Validator quét danh sách `inputs` và tìm kiếm khóa `fire_rate` bên trong Dict `metrics`.
3. Vì khóa này không tồn tại, Theus Engine kết luận: *"Không đủ điều kiện đầu vào"* và **Skip toàn bộ tiến trình** mà không báo lỗi (Silent Bypass).
4. Do tiến trình bị bỏ qua, dòng mã `metrics['fire_rate'] = current_global_rate` ở cuối thân hàm không bao giờ được chạy.
5. Ở $T=1$, kịch bản lặp lại. Tiến trình vĩnh viễn không được chạy vì nó cần một Output từ chính nó để thoả mãn điều kiện Input ban đầu. Hệ thống SNN rơi vào thế "Chết lâm sàng".

## 3. Virtue Audit & Framework Empathy

Theo nguyên lý Fault Tolerance của Pop-Oriented Programming (POP), thiết kế "Silent Bypass" của Theus Theus Resolver là có chủ đích: 
Thay vì Crash toàn bộ hệ thống mô phỏng Agent chỉ vì một tham số bị thiếu, Engine chọn cách "Lướt qua" để hệ thống tiếp tục sống sót. Đây là một sự thấu cảm (Intellectual Empathy) sâu sắc vào quyết định thiết kế của nhóm. Tuy nhiên, cái giá phải trả là Logic Bug ngầm định hủy hoại khả năng nhận thức của mô hình học.

Việc yêu cầu Theus Engine phá bỏ tính Stateless hay Immutable State Deltas là thiếu thực tế và đi ngược triết lý gốc (Intellectual Integrity). 

## 4. Proposed Mitigation for Theus Team

Thay vì thay đổi Core Engine, chúng tôi đề xuất 3 cấp độ giải pháp có thể thảo luận:

### Cấp độ 1: Ứng dụng (Trực tiếp khắc phục tại EmotionAgent)
**Hành động:** Xóa bỏ khóa trực tiếp `metrics.fire_rate` khỏi mảng `inputs` của file `snn_homeostasis_theus.py`. Bản thân tiến trình sẽ dùng `dict.get('fire_rate', 0.0)` hoặc tính toán lại từ Tensor.
*   **Ưu điểm:** Khắc phục ngay lập tức 100% rủi ro Deadlock ở cấp độ nghiệp vụ.
*   **Nhược điểm:** Mất đi một phần tính tường minh về phụ thuộc (Explicit Dependency) mà Theus vốn tôn sùng.

### Cấp độ 2: Kiến trúc Trạng thái (Theus Bootstrap Pattern)
**Hành động:** Thiết lập quy chuẩn (Convention) cho mọi Factory Functions: Phải cấp phát giá trị rỗng (Dummy values / Bootstrap Defaults) cho toàn bộ cây thư mục State.
```python
# Trong create_snn_context_theus:
domain_ctx.metrics = {'fire_rate': 0.0}
```
*   **Ưu điểm:** Khớp tuyệt đối với Theus Schema.
*   **Nhược điểm:** Sinh ra Boilerplate khi cây State phức tạp.

### Cấp độ 3: Kiến trúc Engine (Theus Core Update)
**Hành động:** Bổ sung Cờ Cảnh Báo (Warning Flag) cho `Resolver`. Nếu một `@process` bị *skip* do thiếu Input, gán cờ `EngineInfo.Warnings` hoặc in ra logger ở cấp độ DEBUG/WARNING thay vì im lặng tuyệt đối. Hoặc giới thiệu khái niệm `Optional Inputs` trong Decorator.
```python
@process(
    inputs=['domain_ctx.snn_context.domain_ctx.metrics'],
    optional_inputs=['domain_ctx.snn_context.domain_ctx.metrics.fire_rate'] 
)
```
*   **Ưu điểm:** Nâng cao khả năng Debug và DX (Developer Experience) cho toàn ecosystem Theus.

**Conclusion:** 
Sự cố "Cognitive Freeze" là một case study đắt giá trong việc cân bằng giữa Schema Validation chặt chẽ và khả năng sinh tồn của hệ thống Agent. Chúng tôi đưa báo cáo này lên nhằm mở rộng cuộc thảo luận về Theus Resolver Protocol cho phiên bản 2.0.
