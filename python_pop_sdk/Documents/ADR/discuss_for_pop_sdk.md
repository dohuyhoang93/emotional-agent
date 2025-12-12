
# 1. Audit context
## Các câu hỏi gợi mở
###  1. Hiện tại cơ chế audit context đang kiểm soát những gì của context ngoài context contract và delta?
## Thảo luận:
### RANGE SPEC Cho Context
Lấy cảm hứng từ các nhà máy công nghiệp.
Một máy công nghiệp được quản lý trạng thái của nó và của sản phẩm của nó trên hệ thống với 3 hệ thống spec con:
FDC: spec dành riêng cho sản phẩm. Loại range spec. Có thiết lập độ nghiêm trọng cho từng parametter. Vượt n lần của policy -> interlock. Chưa vượt n thì warning.
RMS: spec cho các parametter trên máy, thường là loại range spec. Tùy biến được cấp độ nghiêm trọng cho từng parametter. Vi phạm vượt quá n lần thì interlock.
ECM: spec cố định, là một giá trị xác định và cấp cao nhất. Vi phạm 1 lần: interlock
Riêng alarm chia 2 loại: serious - nghiêm trọng, dừng máy lập tức và light - warning, loại chưa xác định được đối xử như serious.

Đối với POP
1 process bản thân nó có các đôi tượng context riêng và các context mà nó tương tác (giống như sản phẩm)

Global: context toàn hệ thống
Domain context: context này giống như các "sản phẩm" mà process đang thao tác sản xuất
Local context: context riêng của nội bộ process, giống như các parameter của máy tự động công nghiệp.
Error: cũng là context nhưng thuộc loại đặc biệt, thuộc về riêng process, gần như có thể xếp vào local context
Và thêm 1 cái mà process có mà các máy công nghiệp không có: side effect : các context tương tác với bên ngoài env.adapter

Hệ thống audit context ngoài việc kiểm soát context contract và delta như hiện tại. Nghĩa là kiểm soát: process có đang truy cập context hợp lệ không - contract? và delta - context có đúng đắn hay không - nhưng chỉ là dạng thành công hay tất bại chung chung của domain context.
Audit system phải nâng cấp lên nữa thành một hệ thống toàn diện hơn:

1. Các loại range spec của context
GLobal: toàn bộ hệ thống workflow; không có range mà là một giá trị xác định, chỉ có khớp hoặc không khớp
Domain context: có cả loại giá trị xác định và loại giá trị là một miền range spec
Local context: tương tự domain nhưng chỉ áp dụng cho nội bộ của 1 process.
Error: tương tự local, nhưng chia ra là lỗi nghiêm trọng, cảnh báo, và chưa được xác định
Side effect: chưa cân nhắc kỹ, cần thảo luận thêm từ bạn. Có thể có kiểu spec như local

Việc phân kia như thế này sẽ có tác động như thế nào nếu được áp dụng vào audit policy? lợi và hại là gì?

2. Type of context spec
Giống như môi trường sản xuất. Context cũng sẽ thay đổi tùy theo đặc thù nghiệp vụ và tiến hóa theo thời gian.
Vì vậy spec của nó cũng phải được thay đổi phù hợp và linh hoạt, nhanh chóng.
Ví dụ: Kịch bản chuyển đổi loại hình nghiệp vụ (bao gồm cả chuyển đổi workflow)
Case 1 (tương đương quy trình sản xuất model 1): -> Case 2 (tương đương quy trình sản xuất model 2)
Thì tuy số lượng và chủng loại context trong cả workflow không thay đổi, bản thân process không biết và không quan tâm gì đến điều này.
Tuy nhiên giá trị khởi tạo đầu vào (giống như nguyên liệu) của context đã thay đổi, kèm theo đó là phải có bộ spec tương ứng kèm theo đi cùng. 
Audit policy sử dụng bọ spec này để hoạt động và kiểm soát context cho từng process.
Điều này đòi hỏi pop-sdk phải có cơ chế khai báo - đăng ký - thay đổi - vận hành một loạt các bản spec này. Các spec này cũng gần như cấu hình yaml work flow vậy: minh bạch, dễ hiểu, linh hoạt.

Điều này sẽ có tác động như thế nào khi đưa vào pop-sdk? đặc biệt là trong tầm nhìn pop-sdk universal Rust safety isolation custom gate architecture?

# 2. Các kịch bản workflow phức tạp
## Các câu hỏi gợi mở
### POP SDK engine hiện tại đang hỗ trợ các kịch bản workflow như thế nào?
Trong thực tế, việc thay đổi workflow ngay trong quá trình vận hành cũng như trong giai đoạn phát triển là rất phổ biến. POP sdk phải sẵn sàng và đặt tầm nhìn vào vấn đề này.
### Thảo luận:
1. Các khía cạnh nào cần đánh giá để xây dựng engine hỗ trợ các kịch bản workflow phức tạp?
2. Đâu là các vấn đề cần đối mặt với từng loại workflow?
3. Liệu có phải trong tất cả các loại workflow, tại 1 thời điểm, chỉ duy nhất 1 process được phép thay đổi 1 đối tượng trong 1 domain context (concurrency locking) ?
4. Nếu kịch bản là song song hoàn toàn trên 1 đối tượng domain context (shared memory context), liệu chiến lược tạo bản sao rồi sau đó có cơ chế audit và merge lại có phải là chiến lược hợp lý không ? hay còn cách tiếp cận khác tối ưu ?

# 3. Tầm nhìn chiến lược cho hệ thống phân tán.
## Các câu hỏi gợi mở.
### POP SDK MVP hiện tại
1. POP SDK hiện tại là MVP, khả năng triển khai cho 1 hệ phân tán như thế nào?
2. Context tập trung của nó sẽ là điểm nghẽn và điểm nguy hiểm nhất ra sao?
3. Nếu đặt nó: pop-sdk engine là 1 node server, và cũng triển khai chính nó với vai trò là 1 master quản lý thì sao? ai sẽ quản lý ai, quản lý ra sao trong môi trường bất ổn của internet?

### POP SDK và tầm nhìn micro service
1. Trong các mô hình phân tán như vậy, đâu là cá khía cạnh mà POP cần xem xét?
2. Đâu là các giải pháp và cách tiếp cận khả thi và tối ưu, giữ vững triết lý phi nhị nguyên?
3. Các khái niệm VAP , SAGA trong lý thuyết của micro service là gì?

# 4. Side effect và Error
## Thảo luận:
### Quản lý side effect
1. Side effect của context contract đang được quản lý như thế nào?
2. Các khía cạnh nào cần xem xét để xây dựng cơ chế quản lý side effect cho pop-sdk engine ? Đảm bảo tường minh và thuận tiện?
3. Đâu là phổ các giải pháp và cách tiếp cận khả thi và tối ưu, giữ vững triết lý phi nhị nguyên? 

### Quản lý error
1. Error của context contract đang được quản lý như thế nào? Có phải pop-sdk đang bắt và ném các lỗi chưa khai báo contract không? Nếu có thì lợi và hại là gì?
2. Các khía cạnh nào cần xem xét để xây dựng cơ chế quản lý error cho pop-sdk engine ? Đảm bảo tường minh và thuận tiện?
3. Đâu là phổ các giải pháp và cách tiếp cận khả thi và tối ưu, giữ vững triết lý phi nhị nguyên?

