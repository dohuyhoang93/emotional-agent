# LLM Reasoning và Formal Logic

Bài này chỉ mang tính giải trí trong không gian lý thuyết lập trình

Tính năng suy luận trong các mô hình AI ngôn ngữ lớn hiện tại (LLM reasoning) không thực sự là suy luận logic mà là mô phỏng lại quá trình suy luận logic. Bản chất nó vẫn là một máy dự đoán từ tiếp theo. Nhưng nó nhạy hơn với các văn bản có cấu trúc và ngữ cảnh mang tính suy luận. Đồng thời do các kỹ thuật tinh chỉnh trong quá trình huấn luyện cũng như lời nhắc đầu vào (promting) từ người dùng và mô hình cây quyết định (thử - sai - thử lại) mà AI - LLM có thể cho ra các kết luận logic. Nhưng về bản chất nó không thực sự đạt được tính logic. Chỉ là có vẻ hợp lý thôi. Nhiều trường hợp nó chính xác, cũng nhiều trường hợp thì sai. Và cả hai trường hợp này, hệ thống hiện tại đều không cung cấp khả năng tự kiểm chứng một cách tin cậy.

Khả năng suy luận logic chặt chẽ vốn đã có trong toán học - khoa học máy tính - lập trình. Đó là Formal logic (theorem prover). Tập trung vào chứng minh các mệnh đề trong không gian toán học có trước. Cơ bản của lĩnh vực này dựa trên việc chuyển đổi và hạ thấp dần các đối tượng/quy trình mang tính trừu tượng cao → thấp hơn thông qua toán học → thấp hơn nữa dưới dạng chương trình máy tính:

**Formal logic** (∀-mọi, ∃-tồn tại, ⇒, chứng minh)

↓ ánh xạ thành

**Cấu trúc dữ liệu + thuật toán** (AST, graph, SAT solver, resolution, type checker)

↓ biên dịch thành

**Lệnh máy** (so sánh bit, push/pop stack, jump, load/store)

↓ thực thi bằng

**Cổng logic** (AND, OR, NOT, XOR) trên transistor trong CPU.

Vì thế, về bản chất toàn bộ quá trình **chỉ là một chương trình search + rewrite symbol**, chạy trên CPU nơi mọi thứ cuối cùng quy về **mạch Boolean 0/1**.

Rất nhiều hệ thống lớn cần chứng minh tính chính xác tuyệt đối sử dụng các chương trình Formal logic (theorem prover). Điển hình như Intel dùng để kiểm chứng sự đúng đắn logic của các mạch trong thiết kế kiến trúc CPU. NASA và các hãng máy bay sử dụng để chứng minh không có lỗi trong thiết kế và trong các hệ thống tránh va chạm máy bay. Đây là các tác vụ đòi hỏi tính logic tuyệt đối nhưng với khối lượng và sự phức tạp khổng lồ mà không một cá nhân nào có thể làm được.

Hiển nhiên đến đây, bạn sẽ nghĩ đến việc mix hai cái này lại với nhau để tạo ra một giải pháp logic hoàn thiện hơn. LLM mạnh trong xác suất mẫu tương đồng, mang tính liên tưởng cao, có thể nói là “mềm” hơn. Formal logic mạnh về tính chặt chẽ, chính xác, coi là “cứng” hơn. Một quy trình lý tưởng và hoàn toàn khả thi trong nghiên cứu đó là:

## Chu trình lai (LLM reasoning ↔ Theorem prover)

1. **LLM reasoning (liên tưởng, sinh ý tưởng)**
    - Nhận đầu vào trừu tượng cao (ngôn ngữ tự nhiên, kiến thức đa miền).
    - Sinh ra giả thuyết / khung suy luận.
    - Ví dụ: “Nếu hệ thống có cơ chế A thì sẽ luôn an toàn với lỗi B”.
2. **Chuyển đổi → trừu tượng toán học**
    - Biểu diễn giả thuyết thành dạng formal (logic vị từ, tập luật, mệnh đề).
    - Đây là bước “dịch” từ suy nghĩ ngôn ngữ → mô hình toán.
    - Ví dụ: ∀x. (A(x) → ¬B(x)).
3. **Theorem prover (formal verification)**
    - Kiểm chứng xem giả thuyết có thực sự đúng trong hệ thống formal không.
    - Nếu đúng → ghi nhận.
    - Nếu sai → tạo phản hồi, phản ví dụ.
4. **Quay lại LLM reasoning**
    - LLM phân tích phản ví dụ / kết quả.
    - Sinh ra giả thuyết mới hoặc điều chỉnh mô hình.
    - Tiếp tục suy luận sang miền trừu tượng khác.
5. **Lặp lại vòng**
    - Mỗi chu kỳ đưa trừu tượng “mềm” (ngôn ngữ) → “cứng” (formal logic) để kiểm chứng.
    - Cứ thế vòng lặp tiến dần lên các tầng suy luận phức tạp.

Tóm gọn có thể trong ba dòng:

<aside>

Trừu tượng cao
↓ (dịch sang formal)
Trừu tượng toán học (chứng minh được)
↓ (kết quả / phản ví dụ)
Quay lại trừu tượng cao hơn

</aside>

Tất nhiên, điều gì cũng có khó khăn của nó.

Đầu tiên: Để chuyển từ đầu ra của các AI - LLM (thậm chí là các Machine Learning sử dụng thị giác máy tính)  sang các diễn giải trừu tượng toán học rồi sang ngôn ngữ lập trình là rất khó khăn. Các LLM tạo cú pháp lập trình chưa chính xác tuyệt đối để có thể làm đầu vào cho tầng tiếp theo. Thậm chí bản chất việc dùng ngôn ngữ để diễn tả các trừu tượng cũng không đảm bảo được hoàn toàn tính chính xác. Một số “thứ” không thực sự thuộc về các đại lượng vật lý có thể định lượng. Ví dụ như: mùi, vị, cảm giác xúc giác, cảm xúc, tình cảm … Hơn nữa, hiện tại chúng ta chỉ biết một thứ duy nhất để chuyển từ tư duy của chúng ta → máy tính: ngôn ngữ lập trình. Vốn là một trừu tượng ký tự với bộ quy tắc phức tạp với bộ não của con người và đem đau khổ cho lập trình viên. 

Các vấn đề cần suy luận logic trong đời thực đều là các vấn đề có tính trừu tượng rất cao và có các quy trình / quan hệ phức tạp. Việc chuyển đổi mô tả các vấn đề này qua từ ngữ  → ngôn ngữ lập trình là một việc khó khăn và tiềm ẩn nhiều sai sót.

Hiện tại hoàn toàn khuyết thiếu lớp trung gian này để chuyển từ tuy duy (con người có nhiều cách tư duy: ngôn ngữ, hình ảnh, không gian, âm thanh …) → ngôn ngữ lập trình (hay một phương thức lập trình nào đó chưa có) đảm bảo chính xác và dễ dàng.  Vấn đề này sẽ nói thêm ở một bài viết khác. Một số ngôn ngữ như Rust có thể phần nào cải thiện việc cú pháp sai do tính chặt chẽ và thông báo gỡ lỗi rất tường minh. Sẽ làm cơ sở để cho LLM sinh mã chính xác hơn. Nhưng ngay cả như vậy, đó chỉ là tiền đề. Còn chặng đường rất xa để có thể tập trung và tiêu chuẩn hóa một ngôn ngữ, đủ tài liệu và ví dụ đến mức LLM có thể tạo mã chính xác 100% cho miền vấn đề Formal logic (theorem prover) duy nhất.

Thứ hai: Máy tính của chúng ta chưa đủ nhanh và rẻ. LLM chạy rất tốn tài nguyên tính toán. Và các chương trình Formal logic (theorem prover) cũng tốn gần như thế. Việc mix hai con quái vật tính toán này lại với nhau trong một chu trình làm việc với nhiều vòng tính toán là một tác vụ tiêu tốn tài nguyên ở mức khổng lồ. Vấn đề càng phức tạp và không gian tìm kiếm càng lớn thì sẽ kéo theo bùng nổ quá trình tính toán.

Nhưng rõ ràng đây là một hướng đi rất khả thi để đạt được tính logic ở mức cơ bản. Giải quyết được các khó khăn kia không phải là tương lai xa. Khi đó, chúng ta có thể thật sự tiến gần hơn tới AI thực thụ.