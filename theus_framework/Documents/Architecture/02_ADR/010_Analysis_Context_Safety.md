# Phân tích Chuyên sâu: An toàn Ngữ cảnh & Toàn vẹn Dữ liệu (Context Safety & Integrity)
**Ngày:** 2026-01-15
**Phiên bản:** Theus v2.2.6 -> v3.0 Candidates
**Triết lý:** Phi Nhị Nguyên (Non-Dualism) - Không nhìn nhận vấn đề là sự đối đầu giữa "An toàn" và "Hiệu năng", mà là sự chuyển dịch của "Độ chính xác" (Correctness) trong các không gian thời gian khác nhau.

---

## 🛑 Đề xuất 1: Zero-Copy Immutable Models

### 1. Phân tích Tư duy Phản biện (8 Thành tố)
*   **Mục đích (Purpose):** Giải quyết "Thuế Shadowing". Loại bỏ việc copy phòng vệ (Defensive Copy) tốn kém khi đọc dữ liệu, thay thế bằng sự bất biến từ thiết kế.
*   **Câu hỏi (Question):** Làm thế nào để đảm bảo tính *nguyên vẹn (integrity)* của dữ liệu lịch sử mà không cần sao chép nó liên tục?
*   **Thông tin (Information):** 
    *   Cơ chế hiện tại (v2.2.6): Lazy Shadow-on-Access. Chạm vào đâu, copy chỗ đó. An toàn nhưng Tốn kém.
    *   Hệ quả: Các mô hình AI lớn (Deep Learning Weights) gần như không thể dùng trong Context vì chi phí copy.
*   **Khái niệm (Concepts):** *Bất biến (Immutability)* không phải là "không thể thay đổi", mà là "thay đổi bằng cách tái sinh" (Rebirth). Trạng thái cũ không bị sửa, nó chỉ bị thay thế bởi trạng thái mới.
*   **Giả định (Assumptions):**
    *   Chi phí khởi tạo Object Python mới (Pydantic Model) nhỏ hơn chi phí Deep Copy + Guard Wrapping của Theus.
    *   Developer sẵn sàng từ bỏ cú pháp `obj.x = 1` (Imperative) để dùng `obj = obj.copy(x=1)` (Functional).
*   **Suy luận (Inference):** Nếu dữ liệu là bất biến, việc đọc (Read) an toàn tuyệt đối mà không cần Guard (Zero-Overhead). Guard chỉ cần kiểm soát việc *gán lại* (Re-binding) ở cấp gốc.
*   **Góc nhìn (Point of View):** Từ góc độ của Engine, đây là sự giải phóng. Engine không còn phải làm "bảo mẫu" đi theo canh giữ từng thuộc tính con.
*   **Hệ quả (Implications):** Chuyển dịch gánh nặng từ **Runtime** (Engine) sang **Developer** (Code style) và **Garbage Collector** (Python).

### 2. Phân tích Các Trường hợp (Case Analysis)
*   **Trường hợp Mẫu (Sample Case):**
    *   *Kịch bản:* User muốn cập nhật điểm số. `ctx.domain.user.score += 10`.
    *   *Hiện tại:* Theus copy `user`, copy `score`.
    *   *Đề xuất:* `ctx.domain.user = ctx.domain.user.copy(update={'score': ctx.domain.user.score + 10})`.
    *   *Đánh giá:* Dài dòng hơn, nhưng nhanh hơn.
*   **Trường hợp Liên quan (Related Case):**
    *   *Kịch bản:* Thêm phần tử vào danh sách Transaction Log.
    *   *Đề xuất:* `ctx.logs = (*ctx.logs, new_log)`. Tuple thay vì List.
*   **Trường hợp Biên (Edge Case):**
    *   *Kịch bản:* Một Tensor 1GB.
    *   *Hiện tại:* Chạm vào là crash bộ nhớ (OOM).
    *   *Đề xuất:* Pydantic/Torch hỗ trợ Shared Memory reference. Nếu Tensor là Immutable, ta có thể truyền tham chiếu pointer. Chi phí gần như = 0.
*   **Trường hợp Mâu thuẫn (Contradictory Case):**
    *   *Kịch bản:* Một bộ đếm (Counter) cần cập nhật 1 triệu lần/giây.
    *   *Vấn đề:* Việc tạo mới 1 triệu object (kể cả copy cạn) sẽ giết chết Garbage Collector của Python.
    *   *Giải pháp Phi Nhị Nguyên:* Trong trường hợp này, ta chấp nhận "Mutable Cell" nhưng cô lập nó trong một vùng "Hot Memory" đặc biệt, không Audit lịch sử từng bước (hoặc Audit dạng Batch). Sự Bất biến không phải là giáo điều, nó là công cụ.

---

## 🛑 Đề xuất 2: Hierarchical Write Scopes (Phạm vi Ghi Phân cấp)

### 1. Phân tích Tư duy Phản biện
*   **Mục đích:** Cân bằng giữa An toàn (Granularity) và Tiện dụng (Convenience).
*   **Câu hỏi:** Làm sao để Developer không lười biếng dùng Wildcard (`*`) mà vẫn không cảm thấy bị hành xác khi khai báo quyền?
*   **Khái niệm:** *Cây Quyền hạn (Permission Tree)*. Quyền hạn không phẳng, nó có hình dáng của cấu trúc dữ liệu.
*   **Góc nhìn:** Quyền hạn không phải là "Rào cản", mà là "Bản đồ Ý định" (Intent Map). Khi dev khai báo `writes=['domain.users.*']`, họ đang vẽ ra biên giới tác động của process.

### 2. Phân tích Các Trường hợp
*   **Trường hợp Mẫu:**
    *   Process `UpdateUserProfile` cần sửa tên, tuổi, địa chỉ.
    *   *Output:* `['domain.users.profile.*']`. An toàn, không chạm vào `domain.users.auth`.
*   **Trường hợp Liên quan:**
    *   Process `SystemReset`.
    *   *Output:* `['domain.*']` (Chấp nhận Wildcard ở cấp cao nhất cho Admin process).
*   **Trường hợp Biên:**
    *   Key động. `domain.data_{session_id}`.
    *   *Giải pháp:* Scopes phải hỗ trợ Regex hoặc Pattern Matching động. `domain.data_*`.
*   **Trường hợp Mâu thuẫn:**
    *   Process cần ghi vào 2 nhánh cực xa nhau: `domain.a` và `domain.z`.
    *   *Vấn đề:* Nếu gom nhóm, scope sẽ phình to. Nếu liệt kê, lại dài dòng.
    *   *Giải pháp:* Chấp nhận liệt kê rời rạc. Bản chất hành vi của process là phân tán, thì khai báo phải phản ánh sự phân tán đó.

---

## 🛑 Đề xuất 3: Transactional Outbox (Hộp thư đi Giao dịch)

### 1. Phân tích Tư duy Phản biện
*   **Mục đích:** Nhất quán Tối hậu (Eventually Consistency) giữa RAM (Transient) và Disk/Network (Persistent).
*   **Câu hỏi:** Sự thật nằm ở đâu? Trong RAM hay trong DB?
*   **Triết lý Phi Nhị Nguyên:** Sự thật là một *dòng chảy*. RAM là "Ý định" (Intent), DB là "Kết quả" (Effect). Outbox là cây cầu nối liền dòng chảy đó, đảm bảo không có "Ý định" nào bị mất (Loss) và không có "Kết quả" nào là ma (Phantom).
*   **Giả định:** Chúng ta chấp nhận độ trễ (Latency) để đổi lấy sự Tin cậy (Reliability).

### 2. Phân tích Các Trường hợp
*   **Trường hợp Mẫu:**
    *   Process trừ tiền tài khoản -> Ghi log Audit -> Gửi thông báo Push.
    *   Process ghi lệnh vào `ctx.outbox`. Commit RAM thành công. Worker đọc Outbox, thực hiện DB Write và API Call.
*   **Trường hợp Biên:**
    *   Mất điện ngay khi Commit RAM xong nhưng chưa Commit DB.
    *   *Vấn đề:* RAM bay màu. Outbox (trong RAM) cũng bay màu.
    *   *Giải pháp:* Outbox thực sự phải là một cơ chế *Double Write* (Ghi vào file tạm/WAL log trên đĩa trước) hoặc chấp nhận mất nếu RAM chết. Với Theus thuần Python, ta chấp nhận mất Outbox RAM (nghĩa là giao dịch coi như chưa từng xảy ra - Atomicity được bảo toàn: Không tiền mất, không log ghi).
    *   *Nguy hiểm thực sự:* Ghi DB xong -> Code Python crash trước khi Commit RAM. (Đây là cái Outbox ngăn chặn: Không bao giờ ghi DB trước).
*   **Trường hợp Mâu thuẫn:**
    *   Hệ thống Real-time Trading. Cần phản hồi Microsecond.
    *   *Vấn đề:* Outbox quá chậm.
    *   *Giải pháp:* Bypass. Tự ghi thẳng (Risk Accepted). Sự an toàn là một lựa chọn cấu hình, không phải luật sắt.

---

## 🛑 Đề xuất 4: Hybrid Schema (Cấu trúc Lai)

### 1. Phân tích Tư duy Phản biện
*   **Mục đích:** Xử lý sự hỗn loạn của Runtime (Dynamic Topology) mà không phá vỡ trật tự của Core (Strict Schema).
*   **Khái niệm:** *Âm Dương (Yin-Yang).*
    *   `domain` (Dương): Cứng rắn, trật tự, Typed, Pydantic, History, Audit.
    *   `scratchpad` (Âm): Mềm dẻo, hỗn loạn, Dict, No-Schema, Transient.
*   **Góc nhìn:** Một hệ thống sống cần cả Trật tự để tồn tại và Hỗn loạn để sáng tạo (AI Experiment, Runtime Plugins).

### 2. Phân tích Các Trường hợp
*   **Trường hợp Mẫu:**
    *   Hệ thống ngân hàng lõi + Module AI phân tích hành vi.
    *   `domain`: Chứa số dư (Bất khả xâm phạm).
    *   `scratchpad`: Chứa các tensor, heatmap tạm thời của AI.
*   **Trường hợp Biên:**
    *   Dev lỡ tay lưu object quan trọng vào `scratchpad`.
    *   *Hậu quả:* Mất audit trail.
    *   *Giải pháp:* UX/Linter cảnh báo. Nhưng về mặt kiến trúc, ta cho phép sự tự do này.
*   **Trường hợp Mâu thuẫn:**
    *   Cần promote dữ liệu từ Scratchpad sang Domain.
    *   *Vấn đề:* Scratchpad không có schema, có thể chứa rác không serialize được.
    *   *Giải pháp:* Có một Process "Gatekeeper" (Người gác cổng) làm nhiệm vụ Validate và Copy sạch từ Scratchpad sang Domain. Đây là điểm chuyển hóa Âm -> Dương.
