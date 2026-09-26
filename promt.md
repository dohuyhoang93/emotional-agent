Trong các tài liệu ADR và RFC mới nhất. Các kỹ sư đang thảo luận 2 vấn đề mang tính nền tảng cần phải giải quyết để đưa dự án lên 1 nấc thang tiếp theo.
1. Vấn đề giới hạn của ngôn ngữ lập trình và các tổ chức dữ liệu.
Mặc dù phiên bản hiện tại đã sử dụng @dataclass để đưa cách thiết kế theo nguyên lý ECS và Data Driven vào chương trình. Nhưng bản chất các @dataclass vẫn là python object. Chúng là mảng các con trỏ, nhưng lại trỏ đến các đối tượng thực tế là các địa chỉ bộ nhớ rải rác trên RAM. Để khắc phục, họ tạm thời gom nhặt và truyền tất cả các data đang rải rác này, trải phẳng ra và đưa vào trong đối tượng Numpy, để tăng tốc xử lý hàng loạt. Sau đó lại đưa trở lại python object @dataclass. Kể cả là viết lại bằng Go hay Rust, luôn có trade off. Do bản chất đối tượng thực tế muốn mô phỏng là SNN - neuron. Vốn là 1 thực thể độc lập, vừa có khả năng xử lý và lưu trữ thông tin, vừa truyền thông tin qua các kết nối. Dể mô phỏng lại quá trình này ở lớp trừu tượng phía trên, dù cố gắng thiết kế, tổ chức data như thế nào đi nữa cũng không thoát khỏi bản chất nền tảng bên dưới: Các ô nhớ địa chỉ RAM, hoặc phân tán rải rác, hoặc sắp xếp liền kề. Chúng không thể vừa sắp xếp liền kề để tối ưu xử lý, vừa linh hoạt để thay đổi lược đồ đồ thị. Đây là sự mâu thuẫn giữa triết lý mô phỏng đối tượng: đồ thị động liên tục, và kiến trúc Von-Neuman: đồ thị tĩnh.

2. Vấn đề kiến trúc vật lý.
Để tiến lên một bước tiếp theo: kiểm tra khả năng hình thành nhận thức từ "vòng lặp lạ" và "tư duy tương tự" như ý tưởng của nhà khoa học nhận thức Douglas Hofstadter. Hệ thống này phải có khả năng: Dữ liệu, hay thông tin sau quá trình xử lý, có khả năng quay ngược trở lại thay đổi cấu trúc vật lý nền tảng (CPU-RAM Von-Neuman) đang duy trì quá trình xử lý đó, mà không cần một metalogic hay metaprogram nào chi phối. Đó là một dạng trỗi dậy của cấu trúc, từ một hệ thống phức tạp. Giống như Lý thuyết về độ phức tạp mà viện SantaFe đang nghiên cứu.

Để làm rõ hai vấn đề này hơn nữa. Hãy đưa các SOTA hiện tại lên bàn cân để phân tích một cách trung lập, dựa trên các yếu tố đánh giá. Nhằm xem chúng đã và đang tiếp cận giải pháp cho hai vấn đề này như thế nào?

---
Ý tưởng để có vòng lặp lạ:
Các neuron được chia thành các lớp (layer) một cách trừu tượng.
Lớp đầu sẽ tiếp nhận các kích thích ban đầu cơ bản nhất giống như hệ thống thần kinh xúc giác, thị giác, thính giác (5 giác quan). Tổ hợp các neuron có cùng vector prototype và được kích thích này sẽ trải qua quá trình đúc ra 1 neuron đại diện duy nhất ở tầng trừu tượng tiếp theo. Các neuron trừu tượng này lại cho phép đúc tiếp các tổ hợp này thành các neuron đại diện tiếp theo nữa. Quá trình này là không có giới hạn.

---
What is consciousness? I don't know.

What is cognitive? I don't know.

Emotional Agent is project launched from the sentence of my wife :
"Emotions drive a more intellegent mind, and conversely, intellegence enables the mind experience more complex emotions."
A small project, throught repeated rounds testing and rewriting, raised questions that haunted me. Initialy, the question was: how to simulates emotions? And how to use that to influence the learning process of program. I use several derivated parameter to model emotions. These are curiosity (predict error) and discovery rate (exponential decay) to influence the decrease or increase in the rate of actions different from the predicted outcome. It worked. There were some result. But, I think those were just very simple reinforcement training methods. "Emulating emotions" is the lie to myself. Machine emotions are different from human emotions. But, parameters aren't emotions. These things have nothing in common, in any respect.