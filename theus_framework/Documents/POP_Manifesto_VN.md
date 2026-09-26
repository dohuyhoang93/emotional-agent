Dưới đây là **POP Manifesto – Process Oriented Programming Manifesto**

Tuyên ngôn này thể hiện đầy đủ:

* triết lý tư duy
* triết lý thiết kế
* triết lý kiến trúc
* nguyên tắc vận hành
* lời cam kết của người phát triển
  và **chức năng cốt lõi phân biệt POP với OOP, FP, Clean Architecture**.

---

# 🟦 **POP MANIFESTO — TUYÊN NGÔN CHÍNH THỨC CỦA PROCESS-ORIENTED PROGRAMMING**

> [🇺🇸 Read English Version](./POP_Manifesto.md)

## 🌐 **Lời mở đầu**

Process-Oriented Programming (POP) là một triết lý lập trình đặt **quy trình** (process) làm trung tâm thay cho đối tượng, hàm thuần hay module.

POP không nhằm cạnh tranh với OOP hay FP, mà nhằm cung cấp một con đường **tường minh, thực dụng và dễ bảo trì** cho mọi hệ thống – từ đơn giản đến phức tạp – bằng cách đưa **logic vận hành của hệ thống** về dạng **các bước tuần tự, dễ đọc, dễ kiểm soát, dễ giải thích và dễ chứng minh**.

POP là sự kết hợp giữa **cách tư duy của con người**, **một mô hình toán-tư duy giản dị**, và **kỷ luật thiết kế kỹ thuật**.

POP nói rằng:

> “Mọi hệ thống đều là dòng chảy của dữ liệu đi qua chuỗi các quy trình được định nghĩa rõ ràng. Hãy mô hình hóa hệ thống bằng chính dòng chảy đó.”

---

## 🟦 **1. Triết lý cốt lõi**

### **1.1. Lập trình là mô hình hóa dòng chảy**

Mọi phần mềm – từ robot, PLC, AI, backend – đều là **chuỗi hành động có chủ đích**.

Process là hình thức tự nhiên nhất để mô tả hành động.

POP coi hệ thống như một **dòng chảy**:

```
Dữ liệu vào → Biến đổi → Kiểm tra → Quyết định → Hành động → Dữ liệu ra
```

Tất cả đều được mô hình hóa thành **các bước rõ ràng có tên**, không ẩn logic trong lớp, không nhét hành vi vào dữ liệu, không nhúng điều kiện vào cấu trúc mơ hồ.

---

### **1.2. Sự tường minh là giá trị tối thượng**

> “Nếu không thể giải thích, thì không được phép triển khai.”

POP đặt **tính giải thích** lên hàng đầu:

* Mỗi process phải được mô tả bằng **một câu đơn có chủ ngữ – vị ngữ – mục tiêu**.
* Mỗi sự thay đổi trong context phải có lý do domain rõ ràng.
* Mỗi bước trong workflow phải có thể đọc được như mô tả công việc.

Không chấp nhận:

* logic bị chôn dưới lớp abstraction mơ hồ,
* mô hình dữ liệu bị đẩy vào kiểu "đa năng",
* hành vi bí mật nằm trong object hoặc callback ẩn.

Minh bạch là an toàn.
Minh bạch là dễ bảo trì.
Minh bạch là tính người trong phần mềm.

---

### **1.3. Tránh nhị nguyên cực đoan – embrace phi-nhị-nguyên**

POP không theo đuổi:

* “pure function hay nothing”
* “context bất biến hay hỏng hoàn toàn”
* “một bước – một dòng code”
* “workflow chỉ được linear”

POP khẳng định:

> “Thế giới không phải nhị nguyên, phần mềm cũng vậy.”

POP cho phép:

* mutation có kiểm soát
* branching trong process nếu minh bạch
* process lớn nếu là một khối ngữ nghĩa
* parallel step nếu dễ giải thích
* workflow động nếu có quy tắc an toàn

Điều quan trọng không phải kích thước hay purity.
Quan trọng là **ngữ nghĩa chuẩn xác và khả năng kiểm chứng**.

---

### **1.4. Dữ liệu không mang hành vi – Context không được “biết làm gì”**

Context là:

* dòng dữ liệu đi qua workflow
* trung tâm lưu trạng thái của domain
* “trạng thái của thế giới mô phỏng”

Nhưng context **không được chứa hành vi**, không được chứa logic, không được tự ý biến đổi.

Context là “dữ liệu câm”, nhưng không phải dữ liệu ngu.
Nó là **hiện trạng hệ thống**, không phải nơi giấu hành động.

---

## 🟦 **2. Triết lý thiết kế**

### **2.1. Process là đơn vị thiết kế nhỏ nhất**

Không class, không object, không method ẩn logic.
POP dùng **process** làm đơn vị cơ bản:

```
process(context) → context_moi
```

Process phải:

* làm **một việc có nghĩa**
* không phá domain
* có đầu vào/đầu ra rõ ràng (đọc/ghi context)
* kiểm tra được bằng unit test
* dễ mô tả bằng lời

---

### **2.2. Workflow là nơi kiến trúc được nhìn thấy**

Workflow thể hiện:

* luồng công việc
* rẽ nhánh
* song song
* gộp kết quả
* lặp
* thử-thất bại (retry, fallback, compensation)

Workflow là **bản đồ hệ thống**.
Ai cũng đọc được, không cần biết lập trình.

---

### **2.3. Phân rã process theo ngữ nghĩa, không theo số dòng**

Quy tắc:

* Một process chứa **một ý nghĩa**, có thể gồm nhiều bước nhỏ.
* Không ép process phải cực nhỏ.
* Không cho process quá lớn đến mức khó giải thích.

---

### **2.4. Tái sử dụng là phụ, tường minh là chính**

POP chấp nhận code lặp nếu:

* giúp tường minh
* giảm coupling
* giảm abstraction tầng tầng lớp lớp

POP phản đối “generic hóa quá đà”, vì generic thường che giấu ngữ nghĩa.

---

## 🟦 **3. Triết lý kiến trúc**

### **3.1. Mô hình Context 3 Trục**

Context không còn phẳng. Nó là không gian 3 chiều để tối ưu hóa an toàn và hiệu năng:

*   **Layer (Phạm vi):** Global (Cấu hình), Domain (Nghiệp vụ), Local (Tạm thời).
*   **Zone (Chính sách):** Data (Persistent), Signal (Transient), Meta (Debug), Heavy (Zero-Copy).
*   **Semantic (Vai trò):** Input (Read-only), Output (Read-Write).

-> *Mục tiêu: Kiểm soát toàn diện vòng đời dữ liệu.*

---

### **3.2. Process-safe Context Evolution**

Context phải tiến hóa có kiểm soát:

* mỗi thay đổi phải quan sát được
* không bao giờ ghi ngầm
* không bao giờ reuse field cho nghĩa khác
* các domain field phải có ý nghĩa cố định

---

### **3.3. Luồng điều khiển: Từ Tuyến tính đến Phản ứng**

POP tiến hóa vượt ra khỏi các đồ thị tĩnh để đón nhận **Máy trạng thái (FSM)** và **Luật phản ứng (Reactive Rules)** cho các hệ thống động phức tạp:

*   **Khai báo (Declarative):** Luồng được định nghĩa trong cấu hình, tránh việc mã nguồn bị quấn vào logic điều hướng.
*   **Phản ứng (Reactive):** Việc thực thi được kích hoạt bởi các Sự kiện rõ ràng.
*   **Khả truy (Traceable):** Dù là tuyến tính hay phản ứng, đường dẫn thực thi luôn phải có thể truy vết một cách xác định.

---

### **3.4. POP không chống OOP hay FP – nó chọn thực dụng**

POP học từ FP:

* tính thuần khiết có kiểm soát
* bất biến cục bộ
* tránh side-effect không mong muốn

POP học từ OOP:

* modularity
* grouping theo domain

POP học từ Clean Architecture:

* tách domain và adapter
* đơn hướng phụ thuộc

Nhưng POP không rập khuôn.
POP đặt process làm trung tâm thay vì class hoặc function thuần.

---

## 🟦 **4. Triết lý vận hành**

### **4.1. Phần mềm là một công việc – hãy mô tả bằng công việc**

Workflow POP được viết bằng ngôn ngữ tự nhiên:

```
- gọi: "camera.chup_anh"
- gọi: "anh.tim_vat"
- nếu: ctx.vat.tim_thay
    thì:
      - gọi: "robot.gap"
```

Không từ viết tắt.
Không ký hiệu lập trình.
Không syntax khó nhớ.

---

### **4.2. Mọi bước đều có thể kiểm toán (audit)**

POP đảm bảo rằng:

* trước mỗi process: snapshot context
* sau mỗi process: snapshot context
* delta phải tường minh

Giúp kiểm soát lỗi, kiểm soát hành vi, và phục vụ an toàn công nghiệp.

---

### **4.3. Process dễ test – workflow dễ kiểm tra**

* process có input → output rõ ràng
* workflow có thể chạy giả lập (simulation)
* toàn bộ hệ thống có thể “step-through”

---

## 🟦 **5. Cam kết của người theo POP**

Tôi cam kết:

1. Không giấu logic.
2. Không nhồi hành vi vào dữ liệu.
3. Không tạo abstraction rối rắm.
4. Không phá domain context vì sự tiện tay.
5. Không cực đoan purity hay cực đoan mutable.
6. Luôn giải thích được mọi bước của hệ thống.
7. Ưu tiên sự rõ ràng hơn sự hào nhoáng kỹ thuật.
8. Viết phần mềm để người thật hiểu được.
9. Kiểm soát thay đổi bằng lý trí, không theo thói quen.
10. Tôn trọng dòng chảy tự nhiên của dữ liệu và logic.

---

## 🟦 **6. Tuyên bố cuối cùng**

**POP là phương pháp đặt con người vào trung tâm của tư duy lập trình.**

* Con người suy nghĩ theo bước → POP mô hình hóa theo bước.
* Con người hiểu sự vật qua hành động → POP mô hình hóa hành động qua process.
* Con người cảm nhận dòng chảy → POP tổ chức hệ thống bằng dòng chảy context.

POP không phải một kỹ thuật.
POP là một **quan điểm về sự rõ ràng và trung thực trong phần mềm**.
