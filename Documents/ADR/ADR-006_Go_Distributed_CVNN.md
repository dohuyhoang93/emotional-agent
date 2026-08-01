# ADR-006: Kiến trúc Đồ thị Xử lý Tín hiệu Hệ Phức (Complex-Valued SNN Graph Architecture)

**Ngày:** 15/07/2026
**Trạng thái:** Thiết kế Phác thảo — Đang Phân tích Phê bình — CHƯA Phê duyệt Triển khai
**Lịch sử Phân tích:** ICA ×4, Intellectual Virtue Auditor ×2, Systems Thinking ×1, 6-Hats ×1
**So sánh với:** ADR-005 (Kiến trúc R16 — Tô-pô Đồng thuận)

> [!CAUTION]
> Đây là tài liệu THIẾT KẾ ĐANG MỞ, không phải thiết kế đã chốt. Mục đích là ghi chép trung
> thực toàn bộ không gian thiết kế — bao gồm cả những nguy cơ chưa được giải quyết — để làm
> tiền đề cho các vòng phân tích tiếp theo. Không triển khai cho đến khi Mục 9 được giải quyết.

---

## 1. Động cơ & Bài toán Cốt lõi

ADR-005 (R16) đã giải quyết được bài toán Sụp đổ Không gian Đệ quy (Recursive Spatial Collapse)
bằng cách dịch chuyển ngữ nghĩa sang Tô-pô Đồ thị. Tuy nhiên, kiến trúc số thực vẫn mang một
giới hạn nền tảng không thể khắc phục:

**Bài toán Ràng buộc Cấu trúc (Structural Binding Problem):**
Không gian số thực R^n chỉ mã hóa được Khoảng cách Không gian (Spatial Distance) giữa các khái
niệm. Nó không thể mã hóa trực tiếp Quan hệ Thứ tự Thời gian (Temporal Order) giữa các thành tố
mà không cần thêm các biến trạng thái bên ngoài.

**Ví dụ minh họa — "Chó cắn Người" vs "Người cắn Chó":**
Cả hai câu dùng chung đúng 3 Nút: {Chó, Người, Cắn}. Bộ công cụ Tô-pô Đồ thị của ADR-005 không
thể phân biệt được hai pattern này vì chúng có Child_IDs giống hệt nhau. ADR-005 về lý thuyết có
thể xử lý thứ tự kích hoạt bằng thông tin thời điểm TTL, nhưng cơ chế chính thức và thanh lịch
vẫn còn thiếu.

**Giả thuyết ADR-006:** Không gian Số Phức C^n có thể cung cấp một cơ chế đại số thống nhất, nơi
Góc Pha (θ) mã hóa trực tiếp Thứ tự Thời gian mà không cần biến phụ nào.

---

## 2. Nền tảng Toán học (Mathematical Foundation)

### 2.1. Số Phức như một Cặp Thông tin Thống nhất

Một số phức `z = r × e^(i×θ)` đóng gói hai loại thông tin hoàn toàn độc lập:

| Thành phần | Ký hiệu       | Ý nghĩa Vật lý          | Vai trò trong Hệ thống         |
| :---       | :---          | :---                    | :---                           |
| Biên độ    | r = \|z\|     | Cường độ tín hiệu       | Mức độ quan trọng / Trọng số   |
| Góc Pha    | θ = arg(z)    | Thời điểm kích hoạt     | Mã hóa Thứ tự / Đồng bộ       |

**Phép nhân phức = Đại số Xoay vòng (Rotation Algebra):**

```
z1 × z2 = (r1 × r2) × e^(i × (θ1 + θ2))
```

Một phép toán duy nhất cộng đồng thời cả biên độ (nhân) lẫn thời gian (cộng pha). Đây là điều
mà số thực R^n KHÔNG BAO GIỜ làm được chỉ với 1 phép toán.

### 2.2. Phép Liên hợp Pha (Phase Conjugation) — Trái Tim của Kiến trúc

Cho tín hiệu `X = r × e^(i×θ)`, liên hợp phức của nó là: `X* = r × e^(-i×θ)`

**Tính chất then chốt (Cộng hưởng Hoàn hảo):**

```
X × X* = r² × e^(i×(θ - θ)) = r² × e^(i×0) = r²
```

Khi nhân tín hiệu với liên hợp của chính nó, toàn bộ thông tin Pha bị triệt tiêu, chỉ còn lại
Biên độ thuần túy (r²). Đây chính xác là cơ chế của **Gương Liên hợp Pha (Phase-Conjugate Mirror)**
trong Quang học Phi tuyến: Gương ghi lại "âm bản" (Liên hợp phức). Khi nhận lại cùng chùm tia đó,
toàn bộ nhiễu loạn bị triệt tiêu → Cộng hưởng cực đại.

### 2.3. Bậc Tự Do Thực Tế của C^4 (Effective Degrees of Freedom)

Một vector W trong C^4 có 8 thành phần số thực (4 biên độ + 4 pha). Sau khi loại bỏ bất biến hệ thống:

1. **Chuẩn hóa Biên độ (L2 Norm = 1):** Mất 1 bậc tự do biên độ → còn **3 trục Biên độ Tương đối**
2. **Bất biến Pha Toàn cục (Global Phase Invariance):** Mất 1 bậc tự do pha → còn **3 trục Pha Tương đối**

```
Bậc Tự Do Thực Tế của C^4 = 6
```

**Lượng hóa Dung lượng Biểu diễn** (3-bit biên độ = 8 mức, 4-bit pha = 16 bước):

```
Capacity = 8³ × 16³ = 512 × 4.096 ≈ 2.097.152 mẫu hình / Nút đơn lẻ
```

> [!NOTE]
> Con số 2 triệu là dung lượng lý thuyết tối đa của **MỘT Nút đơn lẻ** trong điều kiện lý tưởng.
> Trong hệ thống thực tế với nhiễu, xung đột và sai số pha, dung lượng thực dụng thấp hơn đáng kể.
> Xem Mục 5 — Phân tích Rủi ro.

### 2.4. Tại sao C^4 giải quyết được "Chó cắn Người"?

Trong không gian phức, Thời điểm kích hoạt (timing) được mã hóa thành Góc Pha. Quy ước:

```
Chủ thể kích hoạt ở pha 0°
Động từ kích hoạt ở pha 120°
Tân ngữ kích hoạt ở pha 240°
```

Nút Trừu tượng `P_DCP` được đúc để nhận dạng "Chó cắn Người" cài đặt Trọng số Synapse bằng
Liên hợp Pha của mẫu hình đó:

```
W_Cho   = e^(-i × 0°)
W_Can   = e^(-i × 120°)
W_Nguoi = e^(-i × 240°)
```

Khi "Người cắn Chó" xuất hiện (Người ở 0°, Cắn ở 120°, Chó ở 240°):

```
Sóng Người (0°)   qua W_Nguoi (-240°) → kết quả: -240°
Sóng Cắn  (120°)  qua W_Can   (-120°) → kết quả:    0°
Sóng Chó  (240°)  qua W_Cho     (0°)  → kết quả:  240°

Tổng = e^(-i×240°) + e^(i×0°) + e^(i×240°) = 0   (Triệt tiêu hoàn toàn)
```

`P_DCP` **im lặng tuyệt đối**. Hệ thống KHÔNG nhầm lẫn.

---

## 3. Hai Đề xuất Kiến trúc Chính và Ma trận So sánh

Qua nhiều vòng phân tích, hai hướng thiết kế chính đã được đề xuất và kiểm tra:

### Đề xuất A: Tô-pô Động N-nhánh (Dynamic Topology)

Mỗi Nút Trừu tượng sở hữu một mảng `Child_IDs` có độ dài tùy ý N. Mỗi kết nối (Edge) sở hữu
một Trọng số Phức `W_edge ∈ C^4` riêng biệt. Các Synapse hoàn toàn độc lập nhau.

- **Cơ sở toán học:** Mỗi Synapse là một bộ lọc pha độc lập. Không bị ràng buộc L2 Norm chung.
- **Luật học:** R-MPP cập nhật từng W_edge riêng lẻ → không có nhiễu chéo (Cross-talk).

### Đề xuất B: Cây Toàn ảnh Bậc 4 (Quaternary Holographic Tree)

Mỗi Nút Trừu tượng chứa đúng 4 kết nối con, tương ứng 1-1 với 4 thành phần của vector `W ∈ C^4`.
Mỗi Nút con `C_k` đóng góp một Vô hướng Phức (Complex Scalar) vào đúng 1 slot. Cấu trúc bộ nhớ
cố định hoàn toàn.

- **Cơ sở toán học:** `W_Y = [r_k × e^(-i×τ_k)]` — Liên hợp pha của trạng thái kích hoạt.
- **Khi pattern đúng:** `Score = Σ r_k²` — Cộng hưởng cực đại.

### Ma trận Đối chiếu Tàn nhẫn

| Tiêu chí               | Đề xuất A (N-nhánh Động)                       | Đề xuất B (Bậc 4 Cố định)                     | Trọng số  |
| :---                   | :---                                           | :---                                          | :---      |
| **Bộ nhớ & GC**        | ❌ Slice động, phân mảnh RAM, GC liên tục      | ✅ Struct cố định, Zero GC                     | Cao       |
| **SIMD / AVX-512**     | ❌ Vòng lặp ngẫu nhiên, vô hiệu hóa SIMD      | ✅ 8 floats = 1 lệnh YMM, O(1)               | Cao       |
| **Độ trễ Latency**     | ✅ Cây nông, 1 Tick từ đáy lên đỉnh            | ❌ Cây sâu 5 Tầng = 5 Ticks, sụp đổ pha      | Rất Cao   |
| **Luật Học R-MPP**     | ✅ Synapse độc lập, Zero nhiễu chéo            | ❌ L2 Norm gây nhiễu chéo khi phạt 1 kênh    | Cao       |
| **Biểu diễn Ngữ nghĩa**| ✅ Hữu cơ, N khái niệm con bất kỳ             | ❌ Ép đủ 4 con, nguy cơ ảo giác Padding       | Trung bình|

> [!IMPORTANT]
> **Kết luận Ma trận:** Không có Đề xuất nào thắng tuyệt đối. Đề xuất A đúng về Toán học SNN
> nhưng thảm họa về Kỹ thuật Phần mềm. Đề xuất B siêu tốc về Phần cứng nhưng sai về Động lực
> học Học máy và Latency.

---

## 4. Đề xuất C: Kiến trúc Lai ghép K-Slot (Hybrid K-Slot Architecture)

Điểm giao thoa của A và B: Dùng **Cấu trúc bộ nhớ Cố định** (mạnh của B) nhưng giải phóng
khỏi ràng buộc Bậc 4 cứng nhắc và L2 Norm toàn cục (mạnh của A).

### 4.1. Hằng số K và Lý do Chọn K = 8

Chọn K = 8 vì: 8 số phức = 16 số float = vừa khít 1 lệnh AVX-512 `_mm512_mul_ps`.
CPU hiện đại tính toán trọn 1 Nút trong 1 Clock Cycle. Không có vòng lặp, không có
Branch Prediction penalty.

Với K = 8, độ sâu cây đệ quy chỉ là **3 Tầng** để bao quát 8³ = 512 cảm biến, thay vì
5 Tầng của Cây Bậc 4 (4⁵ = 1024). Giảm đáng kể bài toán Asymmetric Latency.

### 4.2. Cấu trúc Dữ liệu (Struct Design)

```go
// AbstractionNode — Nút Trừu tượng C^8 Lai ghép
// Tổng kích thước: ~160 bytes (vừa trong 3 Cache Line = 192 bytes)
type AbstractionNode struct {
    // --- Định danh & Trạng thái (8 bytes) ---
    ID          uint32  // Định danh Nút duy nhất
    State       uint8   // 0=Fluid (đang học), 1=Solid (đã hội tụ)
    ActiveSlots uint8   // Số slot đang dùng thực tế (0-8)
    _pad        uint16  // Căn bằng 4-byte alignment

    // --- Kết nối Tô-pô (32 bytes) ---
    // Mảng TĨNH — Không dùng Slice, Zero GC, Cache-friendly
    // Slot [0]: DÀNH RIÊNG cho Context Top-down (Predictive Coding)
    // Slot [1..7]: dành cho Child Nodes (Bottom-up input)
    ChildIDs [8]uint32

    // --- Bộ Bù Pha Độc lập (SoA Layout — Tối ưu AVX-512) ---
    // Mỗi slot [k]: W_k = WeightAmp[k] × e^(i × Phase[k])
    // KHÔNG có L2 Norm toàn cục — tránh nhiễu chéo khi cập nhật riêng lẻ
    WeightReal [8]float32  // 32 bytes — Phần Thực của W_k
    WeightImag [8]float32  // 32 bytes — Phần Ảo của W_k
    WeightAmp  [8]float32  // 32 bytes — Biên độ độc lập (0.0–1.0, Clipping)

    // --- Chỉ số Học (8 bytes) ---
    StabilityIndex float32  // Tốc độ thay đổi W (tiệm cận 0 = Solid)
    ActivationRate float32  // Tần suất bắn xung gần đây
}
```

### 4.3. Các Đặc tính Kỹ thuật Cốt lõi

**A. Chuẩn hóa Độc lập (Decoupled Normalization):**

Không dùng L2 Norm toàn cục cho cả vector. Mỗi `WeightAmp[k]` bị giới hạn riêng:
`0.0 ≤ WeightAmp[k] ≤ 1.0` (Clipping độc lập từng slot).
Khi Phạt `C_3` (làm `WeightAmp[3]` giảm), các slot 0,1,2,4,5,6,7 KHÔNG bị ảnh hưởng.

**B. Ngưỡng Kích hoạt Động (Adaptive Threshold):**

```
V_th = α × Σ_k( WeightAmp[k] × 1[ChildIDs[k] ≠ 0] )
```

Nút có 2 slot dùng có ngưỡng thấp hơn tỷ lệ thuận — không bao giờ bị câm tịt vì ít con hơn Nút khác.

**C. Slot [0] làm Kênh Ngữ cảnh Top-down (Context Injection):**

Slot [0] dành riêng cho tín hiệu từ Tầng cao hơn truyền xuống (Top-down Modulation). Điều này
hiện thực hóa luồng thông tin hai chiều (Bottom-up Activation + Top-down Context), tạo nền tảng
cho Predictive Coding.

> [!WARNING]
> Hệ quả tiêu cực của C: Vòng phản hồi Top-down → Bottom-up có thể tạo Feedback Howl nếu không
> có cơ chế kiểm soát Refractory. Xem Rủi ro R3.

---

## 5. Phân tích Rủi ro Hệ thống (Risk Analysis)

Mọi hệ logic đều có bất toàn (Định lý Gödel). Mọi quyết định cấu trúc đều phải đối mặt với
trường hợp liên quan, trường hợp biên, và trường hợp xung đột. Dưới đây là toàn bộ danh sách
rủi ro đã được phát hiện qua nhiều vòng audit.

### 5.1. CRITICAL — Chưa Giải quyết (BẮT BUỘC trước khi Triển khai)

> [!CAUTION]
> **R1: Đường về của Phần thưởng (Reward Back-Propagation)**
>
> **Vấn đề:** Struct K-Slot chỉ lưu `ChildIDs` (Đồ thị một chiều Cha→Con). Khi Môi trường ném
> Phần thưởng M vào Nút Quyết định (Tầng cao nhất), làm cách nào M đi ngược về các Nút Synapse
> ở Tầng 1 để cập nhật `WeightAmp[k]` của chúng?
>
> **Hệ quả nếu bỏ qua:** R-MPP chỉ cập nhật được Nút Trừu tượng cao nhất. Toàn bộ các Tầng
> dưới KHÔNG học được gì từ Phần thưởng của Môi trường → Hệ thống trở thành "mô hình cứng
> không học được".
>
> **Các lựa chọn khả dĩ (chưa chọn):**
> - *Lựa chọn 1 — Đối xứng Struct:* Mỗi Nút lưu thêm `ParentIDs [P]uint32`. Tạo đồ thị hai
>   chiều thực sự. Chi phí: +32 bytes/Nút. Ưu điểm: Đơn giản, rõ ràng, không tập trung.
> - *Lựa chọn 2 — Bảng Ngược Trung tâm:* Duy trì `map[NodeID][]ParentID` ngoài Struct. Chi phí:
>   Heap memory, điểm tập trung duy nhất (vi phạm tính Phân tán), latency cao khi tra cứu.
> - *Lựa chọn 3 — Phát sóng Phần thưởng Có Phạm vi:* Khi Nút P nhận M, nó phát
>   `M' = M × WeightAmp[k]` đến `ChildIDs[k]`. Nút con tự nhận và tự cập nhật. Chi phí:
>   Tín hiệu M phải đi qua Queue, thêm 1 Tick latency mỗi Tầng.

> [!CAUTION]
> **R2: Thuật toán Cấp phát Đồ thị (Graph Casting — O(V²) Problem)**
>
> **Vấn đề:** Để "Đúc" một Nút Cha mới, Graph Manager phải phát hiện nhóm các Nút đang đồng
> bộ pha với nhau. Trong mạng 1 triệu Nút, tính Ma trận Tương quan Pha (V × V) là O(V²) —
> hoàn toàn bất khả thi trong thời gian thực (100ms/frame).
>
> **Hệ quả nếu bỏ qua:** Hệ thống không bao giờ tự động học được cấu trúc khái niệm mới.
> Đồ thị bị đóng cứng ở trạng thái khởi tạo.
>
> **Các lựa chọn khả dĩ (chưa chọn):**
> - *Lựa chọn 1 — LSH:* Locality-Sensitive Hashing cho Không gian Pha. Tìm kiếm đồng bộ pha
>   trong O(N log N). Phần hại: Tỷ lệ âm tính giả (False Negative).
> - *Lựa chọn 2 — Casting Theo Chu kỳ:* Chỉ chạy thuật toán Casting mỗi T=1000 Ticks. Phần
>   hại: Độ trễ học (Learning Latency) cao.
> - *Lựa chọn 3 — Cục bộ hóa Tô-pô:* Một Nút chỉ xem xét Casting với các Nút trong phạm vi
>   vật lý gần nó (cùng Goroutine/Process). O(K²) cực nhỏ. Phần hại: Hạn chế độ phong phú
>   khái niệm.

> [!WARNING]
> **R3: Feedback Howl — Vòng lặp Phản hồi Không Hội tụ**
>
> **Vấn đề:** Nếu Nút P (Tầng 3) kích hoạt và gửi Context xuống C (Tầng 2) qua Slot [0], C
> kích hoạt và lại truyền tín hiệu lên P, P lại kích hoạt... Vòng lặp tự khuếch đại vô hạn.
>
> **Hệ quả:** Toàn mạng bị "Động kinh" (Seizure) — tất cả Nút bắn xung liên tục, mất khả
> năng phân biệt tín hiệu thực sự.
>
> **Giải pháp tạm:** Thời gian Trơ (Refractory Period T). Sau khi bắn xung, Nút bị khóa T
> Ticks — không nhận bất kỳ tín hiệu nào kể cả Context. Tuy nhiên T = bao nhiêu? Cần công thức:
>
>     T_refractory = ceil(Depth(P) × Tick_Propagation_Delay)
>
> Công thức này chưa được kiểm chứng bằng thực nghiệm. T quá ngắn: vẫn xảy ra Howl.
> T quá dài: Hệ thống "đứng hình" (Temporal Blindness) — bỏ lỡ tín hiệu thực.

### 5.2. WARNING — Có Giải pháp Tạm

> [!WARNING]
> **R4: "Bóng ma Null Slot" (Ghost Synapse — Spurious Learning)**
>
> **Vấn đề:** Slot có `ChildIDs[k] = 0` (Null, không kết nối), nhưng `WeightAmp[k] ≠ 0`. Nếu hàm
> R-MPP vô tình cập nhật Slot Null (do tín hiệu nhiễu từ môi trường), `WeightAmp[k]` tăng lên.
> Slot Null trở thành một Synapse "ma" hút nhiễu, tạo Giao thoa Xây dựng giả tạo.
>
> **Giải pháp:** Null-Masking. TRƯỚC khi chạy R-MPP:
>
> ```go
> for k := range node.ChildIDs {
>     if node.ChildIDs[k] == 0 { continue }  // BỎ QUA Slot Null
>     // ... tính Delta_W_k ...
> }
> ```

### 5.3. NOTE — Đã Có Giải pháp Tạm

> [!NOTE]
> **R5: Tràn Slot (Slot Overflow)**
> Khái niệm có 12 thành tố, Struct chỉ có 8 slot.
> **Giải pháp tạm — Cascade Allocation:** Đúc P_1 (8 con đầu) + P_2 (4 con còn lại + 4 Null)
> + P_master (gom P_1 và P_2). Đánh đổi: Tăng độ sâu đồ thị 1 Tầng.

> [!NOTE]
> **R6: Lũy tiến Sai số Pha (Phase Drift Cascading)**
> Sai số pha nhỏ tại Tầng 1 nhân dồn qua nhiều Tầng, phá hủy cơ chế Giao thoa.
> **Giải pháp tạm — Phase-Resync Gate:** Khi Nút bắn xung, phát Spike chuẩn hóa (pha được làm
> tròn về giá trị chuẩn gần nhất), không truyền pha thô có sai số.

> [!NOTE]
> **R7: Trùng lặp Ngữ nghĩa (Semantic Aliasing / Hash Collision)**
> Với chỉ 6 Bậc Tự Do thực tế, hai đồ thị con khác nhau có thể tạo ra cùng vector C^4.
> **Giải pháp tạm — Sparse Distributed Representation (SDR):** Một khái niệm cấp cao được đại
> diện bởi K = 10 Nút song song. Xác suất để nhiễu đánh lừa cả 10 Nút cùng lúc ≈ 0.

> [!NOTE]
> **R8: Mất ổn định Luật Học (Learning Stability — thiếu L2 Norm)**
> Không có L2 Norm toàn cục, `WeightAmp[k]` có thể tăng về Max=1.0 cho mọi slot (mất tính
> cạnh tranh, Nút trở thành "thùng rác" nhận diện mọi thứ).
> **Giải pháp tạm — Homeostatic Decay:** Mỗi Tick: `WeightAmp[k] *= (1 - decay_rate)`.
> Synapse buộc phải liên tục được củng cố bởi R-MPP nếu không muốn tự phai dần.

---

## 6. Cơ chế Học Tăng cường qua Pha (Reward-Modulated Phase Plasticity — R-MPP)

### 6.1. Phương trình Cốt lõi

Khi Nút P nhận tín hiệu X_k từ Nút con k và sinh ra Output Y:

```
ΔW_k = η × M × Trace_k × (X_k × Y*)
```

| Ký hiệu   | Giải thích                                                                      |
| :---      | :---                                                                            |
| η         | Tốc độ học — cực nhỏ (ví dụ 0.001) để tránh Chaotic Oscillation               |
| M         | Tín hiệu Điều biến từ Môi trường (M > 0 = Reward, M < 0 = Punishment)         |
| Trace_k   | Dấu vết Trách nhiệm (Eligibility Trace) — cao nếu Synapse k đóng góp nhiều     |
| Y*        | Liên hợp phức của Output Y (đảo pha ngược lại)                                 |
| X_k × Y*  | Phép chiếu Hermitian — đo Góc lệch Pha giữa đầu vào và đầu ra                |

### 6.2. Vật lý của M < 0 (Phép Trừng Phạt — Ức chế Tự nhiên)

Nhân ΔW_k với M < 0 đảo dấu toàn bộ phương trình. Về hình học số phức, điều này tương đương với
việc xoay góc pha của W_k thêm một góc nhỏ `(η × π)` mỗi lần bị phạt. Qua nhiều lần bị phạt,
góc pha dần đạt 180°. Khi đó, cùng tín hiệu X_k sẽ tạo ra Giao thoa Triệt tiêu (Destructive
Interference) tại P thay vì cộng hưởng.

> [!IMPORTANT]
> Đây là cơ chế Ức chế (Inhibition) **TỰ NHIÊN** từ đại số số phức — KHÔNG cần viết logic
> if/else ức chế bên ngoài. Việc xoay pha xảy ra **TỪNG BƯỚC NHỎ** theo cấp số η (không tức
> thì) — đây là tính năng quan trọng để tránh Oscillation do Reward/Punishment xen kẽ.

### 6.3. Trường hợp Xung đột: Dao động Pha (Chaotic Oscillation)

**Kịch bản:** Môi trường không bao giờ trắng đen rõ ràng. Cùng một hành động vừa được Reward
(trong ngữ cảnh A) vừa bị Punishment (trong ngữ cảnh B).

**Rủi ro:** Trọng số Synapse xoay qua xoay lại không hội tụ. Nút không bao giờ đạt Solid.

**Giám sát bắt buộc:** `StabilityIndex` và `ActivationRate` phải được ghi log liên tục. Khi
`StabilityIndex` dao động lớn trong thời gian dài: (a) Khái niệm phụ thuộc Ngữ cảnh → cần
Bifurcation, hoặc (b) η quá lớn → cần giảm.

### 6.4. Các Vòng lặp Động lực học Hệ thống (System Dynamics Loops)

**Vòng lặp Tăng cường R1 — Hóa thạch Mẫu hình (Consolidation Loop):**
```
Nút con đồng pha → Nút cha bắn xung → Nhận Reward (M > 0)
→ WeightAmp[k] tăng → Lần sau kích hoạt dễ hơn
→ StabilityIndex giảm dần → Nút chuyển Fluid → Solid
```

**Vòng lặp Cân bằng B1 — Quên và Cắt tỉa (Pruning/Forgetting Loop):**
```
Môi trường thay đổi → Tín hiệu sai pha → Nút cha không bắn xung
→ WeightAmp[k] phai dần do Homeostatic Decay
→ Khi WeightAmp[k] < 0.05: slot[k] reset về Null_ID (Cắt Synapse)
→ Khi quá nhiều slot bị cắt: Nút quay về Fluid, nguy cơ bị Pruning
```

**Vòng lặp Cân bằng B2 — Hạn chế Ám ảnh (Refractory Loop):**
```
Nút bắn xung quá thường xuyên → Thời gian Trơ kích hoạt
→ Nút bị khóa T Ticks → ActivationRate giảm → Hệ thống ổn định
```

---

## 7. Cơ chế Đúc Nút (Phase-Conjugate Casting)

### 7.1. Thuật toán Đúc

**Đầu vào:** Tập `S = {C_1, ..., C_K}` Nút đang đồng bộ pha (phát hiện bởi Graph Manager).
**Đầu ra:** Nút Cha P mới với Bộ Bù Pha được cài đặt tự động.

**Bước 1 — Ghi nhận Tô-pô:**
```
P.ChildIDs[0] = 0           // Slot 0 dành cho Context Top-down
P.ChildIDs[k] = C_k.ID     // k = 1..K
P.ActiveSlots = K
```

**Bước 2 — Khởi tạo Bộ Bù Pha:**
Đo trạng thái kích hoạt hiện tại của mỗi C_k: `z_k = r_k × e^(i×τ_k)`
Thiết lập Trọng số Synapse bằng Liên hợp Pha: `W_k = z_k* / |z_k| = e^(-i × τ_k)`
```
WeightReal[k] = cos(-τ_k)
WeightImag[k] = sin(-τ_k)
WeightAmp[k]  = 1.0
```

**Bước 3 — Kết quả Cộng hưởng khi Pattern đúng:**
```
Score(P) = Σ_k Real(X_k × W_k)
         = Σ_k r_k × cos(τ_k - τ_k)
         = Σ_k r_k    (Cộng hưởng cực đại)
```

### 7.2. Xử lý Tràn Slot: Cây Đúc Đệ quy (Cascade Casting)

Khi có hơn K = 8 Nút đồng bộ pha (ví dụ 12 Nút):

```
Vòng 1: Đúc P_1 từ {C_1..C_8}
         Đúc P_2 từ {C_9..C_12 + Null×4}
Vòng 2: Đúc P_master từ {P_1, P_2 + Null×6}
```

Độ sâu đồ thị tăng 1 Tầng. Latency truyền tín hiệu tăng 1 Tick. Phải cập nhật Adaptive
Threshold của P_master theo số slot active thực tế (2/8 = 25%).

---

## 8. So sánh Tổng thể với ADR-005 (R16)

| Khía cạnh               | ADR-005 (R16, Tô-pô Đồng thuận)                | ADR-006 (C8, Phase-Locked K-Slot)              |
| :---                    | :---                                           | :---                                           |
| **Bộ nhớ / Nút**        | ~100 bytes (Vector + Metadata)                 | ~160 bytes (K-Slot Struct đầy đủ)              |
| **Ngữ nghĩa Nút**       | Tô-pô (Child_IDs + Graph Consensus)            | Tô-pô (K-Slot) + Pha (Phase Compensators)      |
| **Phân biệt Thứ tự**    | ❌ Không — "Chó cắn Người" = "Người cắn Chó"  | ✅ Có — Phân biệt bằng Giao thoa Pha           |
| **Luật Học**            | Complex Oja's + Hebbian (Tầng 1)               | R-MPP (Mọi Tầng, có Eligibility Trace)         |
| **Ức chế**              | Inhibitory Tags (thủ công, cần code thêm)      | Destructive Interference (tự nhiên, miễn phí)  |
| **SIMD Tối ưu**         | ✅ 16 float = 1 lệnh AVX-512                   | ✅ 16 float = 1 lệnh AVX-512                  |
| **Phân giải Thời gian** | Không có cơ chế chính thức                     | 16 bước pha (~6ms/bước @ chu kỳ 100ms)        |
| **Hội tụ Luật Học**     | ✅ Ổn định — Oja's Rule có proof-of-convergence | ❌ Chưa — R-MPP chưa có proof-of-convergence   |
| **Rủi ro Chưa giải**    | 0 rủi ro Critical                              | 3 rủi ro Critical (R1, R2, R3)                |
| **Phức tạp Triển khai** | Trung bình                                     | Cao — phụ thuộc giải pháp R1, R2, R3          |

---

## 9. Điều kiện Tiên quyết Bắt buộc Trước khi Triển khai

Trước khi bất kỳ dòng code Go nào được viết cho ADR-006, CÁC BÀI TOÁN SAU BẮT BUỘC phải
được giải quyết ở cấp độ thiết kế chi tiết, với lựa chọn rõ ràng và phân tích đánh đổi:

| #  | Bài toán             | Trạng thái   | Mô tả Yêu cầu                                          |
|:---|:---------------------|:-------------|:-------------------------------------------------------|
| 1  | Đường về Phần thưởng | **[?] CHƯA** | Chọn 1 trong 3 phương án. Phân tích chi phí bộ nhớ.   |
| 2  | Casting Algorithm    | **[?] CHƯA** | Chọn LSH, Community Detection, hay Cục bộ hóa. Đo O(). |
| 3  | Feedback Howl        | **[?] CHƯA** | Xác định công thức T_refractory và kiểm chứng.         |
| 4  | Ghost Synapse        | **[✓] ĐÃ CÓ** | Null-Masking — giải pháp rõ ràng, sẵn sàng code.      |
| 5  | Slot Overflow        | **[✓] ĐÃ CÓ** | Cascade Allocation — giải pháp rõ ràng.               |
| 6  | Phase Drift          | **[✓] ĐÃ CÓ** | Phase-Resync Gate — giải pháp rõ ràng.                |
| 7  | Semantic Aliasing    | **[✓] ĐÃ CÓ** | SDR (K Nút song song) — giải pháp rõ ràng.           |
| 8  | Learning Stability   | **[✓] ĐÃ CÓ** | Homeostatic Decay — giải pháp rõ ràng.               |

---

## 10. Kết luận và Trạng thái Quyết định

**ADR-006 là kiến trúc có nền tảng toán học vượt trội so với ADR-005** trong bài toán Ràng buộc
Cấu trúc (Binding Problem) và Phân biệt Thứ tự Thời gian (Temporal Ordering). Cơ chế Giao thoa
Pha giải quyết tự nhiên nhiều vấn đề mà ADR-005 phải giải quyết bằng code thủ công.

**Tuy nhiên, ADR-006 ở trạng thái Thiết kế Phác thảo Rủi ro Cao.** 3 bài toán cốt lõi (R1,
R2, R3) chưa được giải quyết sẽ khiến hệ thống KHÔNG HỌC ĐƯỢC hoặc KHÔNG ỔN ĐỊNH nếu triển
khai với thiết kế hiện tại.

> [!CAUTION]
> **KHÔNG ĐƯỢC** triển khai ADR-006 song song hay thay thế ADR-005 cho đến khi R1, R2, R3 được
> giải quyết hoàn toàn ở cấp độ thiết kế chi tiết.

**Gợi ý Chiến lược (Không ràng buộc — cần quyết định bởi Architecture Lead):**

Xây dựng ADR-006 như một Module Thực nghiệm (Experimental Module) chạy song song với ADR-005:
1. Triển khai ADR-005 làm Core trước (ADR-005 đã sẵn sàng, rủi ro thấp).
2. Xây dựng ADR-006 như một Tầng Thực nghiệm riêng biệt, có interface rõ ràng.
3. Đo lường hiệu suất thực tế (Latency, Memory, Learning Convergence) bằng dữ liệu thực.
4. Quyết định thay thế hoàn toàn dựa trên evidence — không dựa trên lý thuyết.

---

*(Tài liệu được tổng hợp sau: ICA ×4, Intellectual Virtue Auditor ×2, Systems Thinking ×1,
6-Hats ×1 — Ngày 15/07/2026)*
