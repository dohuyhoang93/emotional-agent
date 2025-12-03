# Spiking Neural Network

## 1. Mục đích của tài liệu này là gì?

Đề xuất một kiến trúc mạng nơ-ron theo mô hình spiking để thay thế cho MLP đang được sử dụng để học và tính toán vector cảm xúc của agent trong thử nghiệm này.

Tại sao?
MLP sử dụng các phép nhân matrix để tính toán và học các đại lượng vector được gán cho 1 cái tên là vector cảm xúc. Tuy nhiên nếu mở rộng mô hình này với việc đưa nhiều vector cảm xúc vào, và các vector này có thể là phụ thuộc tuyến tính sẽ dẫn tới:

- Khó khăn trong xác định độ tương đồng giữa các vector. Do khoảng cách giữa các vector trong không gian nhiều chiều là rất lớn.
- Bùng nổ tính toán và khó hội tụ do không tìm được điểm lõm của bề mặt loss. 

Hơn nữa, việc sử dụng vector để biểu diễn cảm xúc có thể không phù hợp với các đặc điểm của cảm xúc như sự thay đổi theo thời gian, sự phức tạp của các cảm xúc và sự tương tác giữa các cảm xúc. Bản chất việc gán "cảm xúc" cho 1 vector cũng không tuân thủ triết lý "phi nhân" của dự án này.

## 2. Các câu hỏi cần trả lời:

### 2.1. Đâu là phương pháp tối ưu hơn để có một cơ chế tự nhiên hơn cho việc học được mối liên hệ nhân quả giữa các sự kiện thay vì dùng MLP?

        Tối ưu hơn ở đây có nghĩa là:
            - Tiết kiệm chi phí tính toán.
            - Dễ mở rộng quy mô và độ phức tạp.
            - Giảm sự phụ thuộc vào sự tinh chỉnh của các tham số do con người đưa vào.
            - Kết quả chính xác tương đương hoặc tốt hơn so với MLP.

### 2.1.1. Tiết kiệm chi phí tính toán:
Cơ chế mới phải loại bỏ việc tính toán các phép tính nhân ma trận có kích thước lớn hoặc các tensor lớn. Thay vào đó chỉ có chi phí tính toán của các phép tính đơn giản hoặc biến đổi dữ liệu đơn giản.
 
### 2.1.2. Dễ mở rộng quy mô và độ phức tạp:
Cơ chế mới phải dễ dàng mở rộng quy mô và độ phức tạp. Tốt nhất là có thể dễ dàng mở rộng chỉ bằng khai báo cấu hình. Độ phức tạp của nó không tăng theo số lượng dữ liệu cũng như kích thước của mô hình. Mà độ phức tạp chỉ đến từ kiến trúc trừu tượng của mô hình trong thiết kế.
 
### 2.1.3. Giảm sự phụ thuộc vào sự tinh chỉnh của các tham số do con người đưa vào:
Cơ chế mới phải có khả năng tự điều chỉnh để đạt được mục tiêu mà không cần sự tinh chỉnh của các tham số phức tạp do con người đưa vào.
Để đạt được điểm này, cơ chế mới phải có quy trình rất đơn giản tại các thành phần cơ bản. Nhưng khi kết hợp nhiều thành phần sẽ tạo ra nhiều tổ hợp và kết quả. Hiệu ứng nhân quả và lan truyền là rất mạnh, tạo ra các hiệu ứng phức tạp.

### 2.1.4. Kết quả chính xác tương đương hoặc tốt hơn so với MLP:
Điều này trở thành mục tiêu để xác định cơ chế này có khả thi hay không.

### 2.2 Cấu trúc đó là gì?

Đó là spiking neural network.
Nhưng là phiên bản đơn giản do tôi tự thiết kế.

#### 2.2.1. Cấu tạo
Cấu tạo của cấu trúc này sẽ được cấu tạo từ 1 thành phần đơn vị cơ bản nhất là neuron.

Neuron này sẽ có các thành phần chính là:
- Input: nhận vào các tín hiệu từ các neuron khác hoặc từ môi trường.
- Ngưỡng kích hoạt: giống như một màng có thể thay đổi độ nhạy của nó. Khi tín hiệu vào vượt quá ngưỡng này, neuron sẽ kích hoạt và tạo ra tín hiệu spike.
- Connection: kết nối với các neuron khác để tạo ra mạng lưới.

Các neuron này sẽ được nhóm lại với nhau theo từng nhóm để tạo thành quy trình hoạt động.

Ví dụ: 
- Nhóm neuron giao cảm chịu trách nhiệm tiếp nhận tín hiệu từ môi trường. Chuyển đổi thành tín hiệu để lan truyền.
- Nhóm neuron trí nhớ: liên kết tín hiệu đặc thù với các neuron khác để hình thành 1 con đường tắt, tự điều chỉnh độ nhạy của ngưỡng kích hoạt. Có thể thông qua cơ chế boots chủ động: tự khuếch đại tín hiệu để kích hoạt ngưỡng kích hoạt của neuron khác.
- Nhóm neuron trạng thái : các trạng thái nội tại của mô hình. (sau này có thể gọi bằng cái tên trừu tượng như "cảm xúc").
- Nhóm neuron vận động: điều khiển hành vi tương tác với môi trường.
- Nhóm neuron logic: tạm thời chưa biết (có thể chứa các logic hình thức bậc 1).

Ở đây cần làm rõ:

1. Tín hiệu kích thích: là 1 tín hiệu có độ phân giải. Giả sử là 1 vector 16 chiều với 16 phần tử. Tạm coi như tín hiệu có độ phân giải 16 phần tử. Mỗi phần tử có giá trị khác nhau từ 1 đến 8 đại diện cho cường độ hay mức độ.
16 độ phân giải này sẽ là tổ hợp tạo nên đặc tính đặc trưng của thông tin mà nó mang.

Một tín hiệu có cường độ mạnh thì có hiệu ứng lan truyền mạnh hơn.

Một tín hiệu yếu nhưng có thời gian dài lặp đi lặp lại cũng khiến neuron thay đổi ngưỡng kích hoạt của nó. Tạo ra hiệu ứng lan truyền mạnh mẽ.

2. Ngưỡng kích hoạt:
Giống như 1 màng nhưng có số lượng đầu dò độ nhạy nhất định. Ví dụ tín hiệu có 16 độ phân giải nhưng màng chỉ có 4 đầu dò. Nó sẽ phản ứng trước với 4 độ phân giải có cường độ cao nhất. Khi hết 4 đầu dò, nó sẽ không phản ứng với các độ phân giải thấp hơn. Nghĩa là không cho đi qua.

#### 2.2.2. Nguyên lý hoạt động

Khi tín hiệu kích thích vào, neuron sẽ kích hoạt và tạo ra tín hiệu spike. Lan truyền này sẽ đến tất cả các neuron. Có thể theo 1 thứ tự nhất định hoặc không. Tôi chưa hoàn thiện lý thuyết phần này.

environment --> Giao cảm -> Trí nhớ -> [Trạng thái <-> Logic] -> Vận động --> tương tác với environment -->  Giao cảm

tín hiệu cuối cùng đạt đủ cường độ đi đến neuron vận động sẽ điều khiển hành vi của mô hình.

### 2.3 Các vấn đề phức hợp:
1. Kiểm soát ức chế (Inhibition Control): Một hệ thống thông minh không chỉ cần biết hưng phấn (kích hoạt neuron) mà còn cần biết ức chế. SNN cần có cơ chế để "làm nguội" các xung thần kinh nếu chúng quá hỗn loạn (tương tự việc giữ exploration rate ở 0.3).

2. Cân bằng: Cần tìm điểm cân bằng giữa việc "học nhanh" (Social Learning) và "thận trọng" (Baseline). Có thể trong SNN, các tín hiệu từ đồng đội chỉ nên đóng vai trò "gợi ý" (kích thích nhẹ điện thế màng) chứ không nên "chi phối" (gây phóng điện ngay lập tức).