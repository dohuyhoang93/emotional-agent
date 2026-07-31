# RFC-007: KIẾN TRÚC XỬ LÝ TÍN HIỆU LẤY CẢM HỨNG THẦN KINH PHÂN MẢNH TỐI ƯU DỮ LIỆU
## (Sharded Data-Oriented Architecture for Neuro-Inspired Signal Processing)

**Mã RFC:** RFC-007  
**Dự án:** EmotionAgent (E.A)  
**Tác giả:** Technical Architecture Team  
**Trạng thái:** Chuẩn Thiết kế Kỹ thuật (Technical Architecture Specification)  
**Mô tả:** Hệ thống xử lý dữ liệu lấy cảm hứng từ thần kinh (Neuro-inspired Signal Processing System) được thiết kế theo nguyên lý Data-Oriented Design (DOD) và Phân mảnh Bộ nhớ (Memory Sharding) trên ngôn ngữ Go.

---

## 1. TỔNG QUAN HỆ THỐNG & ĐỊNH HƯỚNG TỐI ƯU HẠ TẦNG

### 1.1. Bối cảnh & Phân tích Hiệu năng Phần cứng
Trong các phiên bản phác thảo ban đầu (ADR-005, ADR-006), mô hình hệ thống được mô tả dựa trên các khái niệm trừu tượng của thần kinh học và đồ thị hướng đối tượng (Array-of-Structures — AoS). 

Kết quả phân tích đo đạc hiệu năng trên phần cứng thực tế (Bare-metal Execution Benchmark) chỉ ra các điểm nghẽn hạ tầng:
* **Tỷ lệ Cache Miss cao (Pointer Chasing):** Cấu trúc đồ thị lưu trữ dưới dạng danh sách con trỏ phân tán làm gia tăng tỷ lệ L1/L2 CPU Cache Miss. Khi quy mô nút tăng, việc truy xuất bộ nhớ không liên tục trở thành cổ chai hiệu năng chính.
* **Chi phí tính toán theo chu kỳ:** Việc duyệt ma trận thưa qua bảng băm hoặc con trỏ tốn nhiều CPU cycles cho thao tác giải tham chiếu (dereference) thay vì tập trung vào các phép toán xử lý tín hiệu.

### 1.2. Định hướng Thiết kế: Data-Oriented Design (DOD)
Hệ thống EmotionAgent là một **hệ thống xử lý dữ liệu phần mềm lấy cảm hứng từ thần kinh** (Neuro-inspired Data Processing System). Để tối ưu hóa cho phần cứng máy tính Von Neumann, hệ thống chuyển sang áp dụng nguyên lý Data-Oriented Design (DOD):

1. **Phân mảnh Bộ nhớ (Memory Sharding):** Dữ liệu được phân chia thành các vùng nhớ tĩnh (**Memory Arenas**) tương ứng với các luồng xử lý độc lập (CPU Cores).
2. **Sắp xếp Bố cục Bộ nhớ Liên tục (Contiguous Memory Layout):** Chuyển đổi từ mảng cấu trúc (AoS) sang cấu trúc mảng (Struct-of-Arrays — SoA) nhằm tối ưu hóa việc nạp dữ liệu vào thanh ghi **SIMD / AVX-512**.
3. **Phân định Ranh giới Khái niệm:** Tách biệt rõ ràng giữa *mô hình toán học/tín hiệu lấy cảm hứng từ thần kinh* (Spike, Phase, Synaptic Weight) và *cấu trúc dữ liệu khoa học máy tính* (Contiguous Array, Bitmask, SPSC Ring Buffer, SIMD Vector).

---

## 2. Mô HÌNH TOÁN HỌC & CẤU TRÚC DỮ LIỆU SNN $C^8$

### 2.1. Phân tầng Mô hình Tín hiệu (4-Layer Signal Pipeline)
Hệ thống duy trì đường ống xử lý tín hiệu 4 tầng:
- **Tầng 1 — Input Gateway (IG) [500Hz]:** Chuyển đổi tín hiệu đầu vào $x_{raw}$ thành vector 16 chiều $P_{in}$ thông qua phép chiếu cố định $W_{proj}$.
- **Tầng 2 — Vector Encoder Node (VEN) [500Hz]:** Biểu diễn tín hiệu không giám sát dựa trên quy tắc cập nhật cục bộ Oja (`ΔW_ij = η · y_i · (x_j - y_i · W_ij)`).
- **Tầng 3 — Threshold Classifier Node (TCN) [20Hz]:** Phân loại tín hiệu và tính toán giá trị quyết định theo công thức $Score = I_{signal} \times CosineSim(P_{signal}, P_{target})$.
- **Tầng 4 — Graph Lifecycle Manager [20Hz]:** Quản lý thời gian tồn tại (TTL), trạng thái cố định (Fossilization), và loại bỏ nút không hoạt động (Pruning).

### 2.2. Mã hóa Số Phức $C^8$ và Phép Liên hợp Pha
Để xử lý bài toán thứ tự thời gian của tín hiệu (Temporal Sequence Binding) mà không làm tăng trạng thái bên ngoài:
- Mỗi giá trị được biểu diễn dưới dạng số phức $z = r \cdot e^{i\theta}$, trong đó biên độ $r$ biểu thị cường độ tín hiệu và góc pha $\theta$ biểu thị thời điểm kích hoạt.
- **Phép Liên hợp Pha (Phase Conjugation):** Tín hiệu $X = r \cdot e^{i\theta}$ khi đi qua liên hợp $W = e^{-i\theta}$ sẽ triệt tiêu phần pha: $X \cdot W = r \cdot e^{i0} = r$. Các tín hiệu lệch pha sẽ tạo ra giao thoa triệt tiêu (Destructive Interference).

### 2.3. Cấu trúc Dữ liệu `AbstractionNode` (SoA Layout)
Mỗi nút xử lý được cấu hình với $K=8$ slot liên kết cố định, vừa khít với thanh ghi 512-bit (AVX-512):

```go
// AbstractionNode — Cấu trúc nút xử lý C^8 (SoA Alignment)
// Kích thước bộ nhớ cố định: 160 bytes
type AbstractionNode struct {
    // --- Định danh & Trạng thái (8 bytes) ---
    ID          uint32  // Mã định danh nút
    State       uint8   // Trạng thái: 0=Unallocated, 1=Fluid, 2=Solid
    ActiveSlots uint8   // Số lượng slot đang kết nối (0-8)
    _pad        uint16  // Căn bằng bộ nhớ 4-byte

    // --- Chỉ số Liên kết Tô-pô (32 bytes) ---
    // Slot [0]: Ngữ cảnh dự báo (Top-down Context)
    // Slot [1..7]: Đầu vào từ các nút cấp dưới (Bottom-up Input)
    ChildIDs [8]uint32

    // --- Mảng Trọng số Số Phức (SoA Layout — SIMD Alignment) ---
    WeightReal [8]float32  // 32 bytes — Mảng phần thực cos(-τ_k)
    WeightImag [8]float32  // 32 bytes — Mảng phần ảo sin(-τ_k)
    WeightAmp  [8]float32  // 32 bytes — Biên độ trọng số độc lập (0.0 - 1.0)

    // --- Chỉ số Động lực học (12 bytes) ---
    StabilityIndex float32  // Tỷ lệ thay đổi trọng số tiệm cận ổn định
    ActivationRate float32  // Tần suất kích hoạt gần đây
    ActivityEMA    float32  // Trung bình động hàm mũ của mức kích hoạt
}
```

---

## 3. THIẾT KẾ BỘ NHỚ PHÂN MẢNH (SHARDED MEMORY ARENAS)

### 3.1. Phân mảnh Bộ nhớ theo Luồng (Memory Arenas)
Hệ thống phân chia toàn bộ bộ nhớ thành $N$ **Memory Arenas** tương ứng với $N$ luồng xử lý (CPU Cores):
1. Mỗi Arena sở hữu một mảng liên tục `NodesArray []AbstractionNode` được cấp phát cố định.
2. Mỗi Arena được vận hành bởi một Goroutine duy nhất, đảm bảo tính toàn vẹn bộ nhớ nội bộ mà không cần sử dụng khóa đồng bộ (Mutex Lock).

### 3.2. Cấp phát Kiến tạo (Constructive Allocation / Zero-Initialization)
Nhằm tránh hiện tượng quá tải hàng đợi giao tiếp khi khởi tạo hệ thống:
1. Tại thời điểm $T=0$, 99% các phần tử trong `NodesArray` được đánh dấu `State = Unallocated`. Mạng không khởi tạo ma trận trọng số ngẫu nhiên.
2. Các nút cảm biến (Sensory Nodes) được định vị cố định tại các Arena đầu vào.
3. Khi xuất hiện dữ liệu đầu vào, hệ thống thực hiện cấp phát nút mới bằng cách chuyển trạng thái bit `Unallocated -> Fluid` ngay tại Arena cục bộ. Quá trình phát triển cấu trúc diễn ra từ dưới lên (Bottom-up).

---

## 4. QUẢN LÝ BỘ NHỚ HẠ TẦNG VÀ PHÂN TÍCH GIỚI HẠN VẬT LÝ

### 4.1. Cấp phát Bộ nhớ Tĩnh (Pre-allocated Object Pool)
Để loại bỏ độ trễ do thao tác tái cấp phát bộ nhớ (Reallocation / Garbage Collection) trong thời gian thực:
- Mảng bộ nhớ `[MAX_NODES]AbstractionNode` được khởi tạo hoàn toàn tại thời điểm khởi động hệ thống ($T=-1$).
- Thao tác khởi tạo hoặc xóa nút trong chu kỳ thực thi ($T > 0$) chỉ thực hiện thay đổi giá trị của trường `State` ($O(1)$), không kích hoạt các thao tác cấp phát bộ nhớ động trên Heap.

### 4.2. Hàng đợi Giao tiếp SPSC (Single-Producer Single-Consumer)
Đối với giao tiếp giữa các Arena (Inter-Core Communication):
- Hệ thống áp dụng ma trận hàng đợi **SPSC (Single-Producer Single-Consumer)** `SPSC_Buffer[SrcCore][DstCore]`.
- Thao tác ghi dữ liệu chỉ do Core nguồn thực hiện, thao tác đọc chỉ do Core đích thực hiện.
- Các cấu trúc hàng đợi được chèn **64-byte Cache Line Padding** để ngăn ngừa hiện tượng False Sharing trên CPU Cache L3.

```go
// SPSCBuffer — Hàng đợi vòng liên luồng tối ưu Cache Line
type SPSCBuffer struct {
    head        uint64
    _pad1       [56]byte // Padding chống False Sharing cho Head (64 bytes)
    tail        uint64
    _pad2       [56]byte // Padding chống False Sharing cho Tail (64 bytes)
    ring        [1024]SpikePacket
}
```

### 4.3. Phân tích Giới hạn Kỹ thuật của Cơ chế "Locality Migration" (Dọn nhà Bộ nhớ)

> [!CAUTION]
> **Phân tích Giới hạn Toán học & Tiêu tốn Hiệu năng:**
> 1. **Giới hạn Ánh xạ Đồ thị $N$-chiều lên Mảng 1D:** Đồ thị kết nối của mạng nơ-ron có tính chất liên kết chéo phức tạp (Complex Graph Topology). Một nút $B$ có thể kết nối đồng thời với các nút $A, C, D$. Thao tác di chuyển $B$ về vị trí kề cận $A$ trên thanh RAM (mảng 1D) có thể cải thiện L1 Cache Hit cho luồng $A \to B$, nhưng đồng thời làm tăng khoảng cách vật lý và Cache Miss cho các luồng $C \to B$ và $D \to B$. Việc chống phân mảnh ở cụm này có thể gây phân mảnh ở cụm khác.
> 2. **Chi phí Tiêu tốn Hiệu năng của Thao tác Di chuyển:** Việc copy dữ liệu struct và cập nhật lại mảng chỉ số liên kết giữa các luồng trong thời gian thực tốn CPU cycles và băng thông RAM. Nếu thực hiện liên tục sẽ gây ra hiện tượng **Migration Thrashing** (dời vị trí liên tục), làm giảm hiệu năng chung của hệ thống.

**Cơ chế Kiểm soát và Điều kiện Ràng buộc cho Locality Migration:**
Toàn bộ thao tác di chuyển bộ nhớ (Locality Migration) phải tuân thủ các quy tắc kiểm soát chặt chẽ:

1. **Chế độ Vận hành Bất đồng bộ theo Chu kỳ (Async Epoch-based Execution):** Tiến trình Migration KHÔNG được phép chạy trong vòng lặp thời gian thực ($10\text{ms}/frame$). Tiến trình này chạy bất đồng bộ theo chu kỳ Epoch (ví dụ: $5-10\text{ giây}/lần$) với hạn mức CPU được khống chế (tối đa $< 2\%$ tổng tài nguyên CPU).
2. **Ngưỡng Liên kết Áp đảo (Dominant Edge Constraint):** Thao tác di chuyển chỉ được kích hoạt khi liên kết giữa Nút $A$ và Nút $B$ chiếm tỷ trọng vượt trội so với tổng các liên kết khác của $B$:
   $$\frac{W_{A \to B}}{\sum_{k} W_{\text{other}_k \to B}} > \text{Threshold} \quad (\text{mặc định } 0.7)$$
3. **Thời gian Chờ Di chuyển (Migration Cooldown):** Mỗi nút sau khi di chuyển phải gắn một bộ đếm Cooldown ($T_{\text{cooldown}} = 100\text{ Epochs}$) để ngăn chặn hiện tượng di chuyển lặp đi lặp lại.
4. **Duy trì Giao tiếp SPSC cho Liên kết Chéo:** Đối với các liên kết không đạt ngưỡng áp đảo, hệ thống chấp nhận duy trì giao tiếp bất đồng bộ qua ma trận SPSC Buffer thay vì cưỡng ép di chuyển vị trí bộ nhớ.

### 4.4. Phân tầng Hội tụ (Hierarchical Hub Arenas)
Để xử lý các liên kết đa miền mà không làm bùng nổ độ phức tạp tính toán:
- Hệ thống thiết lập các **Hub Arenas** ở tầng trên để tiếp nhận tín hiệu từ các Sensory Arenas.
- Hub Arenas áp dụng hạn mức dung lượng (`Max_Capacity = 1024`) và bộ lọc cường độ tín hiệu (**Top-K Salience Filter**). Chỉ các tín hiệu vượt ngưỡng mới được truyền lên tầng hội tụ, khống chế độ phức tạp tính toán ở hằng số cho trước.

---

## 5. CẤU TRÚC ĐỒ THỊ THƯA HYBRID VÀ VÒNG LẶP TÍNH TOÁN SIMD

### 5.1. Cấu trúc Đồ thị Thưa Hybrid (Chunked Adjacency List)
Để đảm bảo tốc độ truy xuất mà không gặp hạn chế của mảng CSR/CSC tĩnh khi cấu trúc mạng thay đổi:
- Mỗi nút chứa $K=8$ slot liên kết tĩnh.
- Khi số lượng liên kết vượt quá $K=8$, hệ thống áp dụng cấu trúc đệ quy (Cascade Allocation): Đúc nút phụ $P_1$ (8 con), $P_2$ (các con còn lại) và liên kết qua nút quản lý $P_{master}$.
- Cấu trúc này đảm bảo mảng dữ liệu luôn giữ tính đọc tuyến tính khi tính toán SIMD.

### 5.2. Vòng lặp Tính toán SIMD (AVX-512 Dense Buffer Loop)
Nhằm tránh việc rẽ nhánh câu lệnh (`IF/ELSE`) làm giảm hiệu năng CPU Pipeline khi tính toán dữ liệu thưa:
1. Đầu mỗi chu kỳ `Tick()`, hệ thống quét nhanh và trích xuất danh sách các ID nút đang kích hoạt vào mảng nén `ActiveIndices []uint32`.
2. Vòng lặp tính toán AVX-512 chỉ thực thi trực tiếp trên mảng `ActiveIndices`. Toàn bộ dữ liệu trong mảng nén được nạp liên tục vào thanh ghi SIMD, loại bỏ thao tác kiểm tra điều kiện trong vòng lặp chính.

---

## 6. QUY TẮC CẬP NHẬT TRỌNG SỐ VÀ CÁC CƠ CHẾ BẢO VỆ

### 6.1. Phương trình Cập nhật Trọng số R-MPP
Trọng số $W_k$ được cập nhật dựa trên tín hiệu điều biến $M$:

$$\Delta W_k = \eta \cdot M \cdot Trace_k \cdot (X_k \cdot Y^*)$$

- $\eta$: Tốc độ học ($0.001$).
- $M$: Tín hiệu điều biến phần thưởng ($M > 0$: Thưởng, $M < 0$: Phạt).
- $Trace_k$: Dấu vết trách nhiệm của liên kết $k$.
- $X_k \cdot Y^*$: Phép chiếu Hermite đo góc lệch pha giữa đầu vào và đầu ra.

### 6.2. Cập nhật Trạng thái qua EMA Activity Trace
Để tránh việc Thời gian Trơ (Refractory Period) làm mất tín hiệu phần thưởng trì hoãn, hệ thống duy trì chỉ số trung bình động hàm mũ (`ActivityEMA`):

$$\text{ActivityEMA} = (0.9 \cdot \text{ActivityEMA}) + (0.1 \cdot \text{Spike}_{current})$$

- Thao tác khóa trơ (Refractory) chỉ tác động lên tín hiệu `Spike_{current}` để chặn vòng lặp phản hồi.
- Hàm cập nhật trọng số R-MPP tính toán phần thưởng dựa trên chỉ số `ActivityEMA`, đảm bảo việc cập nhật diễn ra liên tục.

### 6.3. Cơ chế Bảo vệ Trạng thái Hệ thống
1. **Inhibitory Tag:** Gán thẻ tăng ngưỡng tạm thời ($\Theta_j += \beta \cdot e^{-\mu t}$) cho các nút cạnh tranh khi đúc nút mới, ngăn chặn vòng lặp kích hoạt chéo.
2. **Orphan Signal:** Reset thời gian tồn tại về $TTL_{base}$ cho các nút con khi nút cha bị xóa, kích hoạt quá trình tự đánh giá lại.
3. **Activation Statistics:** Chuyển trạng thái nút sang `Solid` khi tần suất kích hoạt vượt ngưỡng $\text{ActivationRate} > R_{fossilize}$, đảm bảo duy trì cấu trúc đã hội tụ.

---

## 7. MA TRẬN PHÂN TÍCH VẤN ĐỀ VÀ GIẢI PHÁP KỸ THUẬT

| STT | Vấn đề Kỹ thuật | Nguyên nhân Hạ tầng | Hạn chế / Đánh đổi | Giải pháp Kỹ thuật trong RFC-007 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Tỷ lệ Cache Miss cao** | Cấu trúc đồ thị con trỏ phân tán (AoS) | Tốn bộ nhớ cho padding | **Data-Oriented Design (DOD)** + Layout SoA nạp SIMD AVX-512 |
| 2 | **Quá tải Hàng đợi Khởi tạo** | Khởi tạo trọng số ngẫu nhiên ban đầu | Cần thời gian đúc nút từ dưới lên | **Constructive Allocation**: Khởi tạo rỗng, cấp phát nút khi có dữ liệu |
| 3 | **Độ trễ do Tái cấp phát RAM** | Thao tác `realloc`/GC khi mảng phình to | Tốn bộ nhớ RAM cố định ban đầu | **Pre-allocated Object Pool**: Cấp phát tĩnh $100\%$ mảng tại $T=-1$, lật bit `State` |
| 4 | **Tranh chấp Cache L3 (False Sharing)** | Nhiều luồng cùng ghi vào một hàng đợi MPSC | Tăng số lượng hàng đợi bộ nhớ | **SPSC Matrix + 64-byte Padding**: Hàng đợi 1-Producer 1-Consumer độc quyền |
| 5 | **Phân mảnh do Giới hạn Ánh xạ 1D** | Nút kết nối đa chiều ($A, C, D \to B$) | Dọn cụm này gây phân mảnh cụm khác | **Hạn chế Locality Migration**: Chỉ dọn khi liên kết áp đảo ($>70\%$), chạy async epoch |
| 6 | **Ràng buộc Thứ tự Tín hiệu** | Số thực $R^n$ không mã hóa được pha | Tăng khối lượng tính toán số phức | **Mã hóa Số Phức $C^8$ + Phase Conjugation**: Triệt tiêu pha khi khớp thứ tự |
| 7 | **Xung đột Refractory & Reward** | Thời gian trơ khóa nút khiến mất Reward | Cần thêm biến lưu trạng thái EMA | **EMA Activity Trace**: Cập nhật trọng số dựa trên `ActivityEMA` $O(1)$ |

---

## 8. LỘ TRÌNH THỰC THI MÃ NGUỒN GO

1. **Khởi tạo Cấu trúc Bộ nhớ Tĩnh (`pkg/core/`):**
   - Đổi mới struct `AbstractionNode` (160 bytes) theo định dạng SoA tại `pkg/core/node.go`.
   - Triển khai mảng `MemoryArena` tĩnh trong `pkg/core/arena.go`.
   - Thiết lập ma trận `SPSCBuffer` với 64-byte padding trong `pkg/core/mailbox.go`.

2. **Xây dựng Vòng lặp Tính toán SIMD (`pkg/engine/`):**
   - Triển khai module trích xuất `ActiveIndices []uint32`.
   - Tối ưu hóa các phép toán R-MPP và phép nhân liên hợp pha bằng tập lệnh AVX-512 (`pkg/engine/simd_ops.go`).
   - Xây dựng vòng lặp execution `Tick()` không rẽ nhánh cho từng Arena Goroutine.

3. **Xây dựng Tiến trình Quản lý Bất đồng bộ (`pkg/services/`):**
   - Triển khai `LocalityMigrationWorker` chạy theo chu kỳ Epoch bất đồng bộ với điều kiện kiểm soát liên kết áp đảo ($>70\%$) và cooldown timer.
   - Triển khai module phân tầng Hub Arenas với bộ lọc Top-K Salience.
   - Xây dựng bộ kiểm thử Benchmark đo tỷ lệ Cache Miss và thời gian thực thi khung truyền.

---

*Tài liệu RFC-007 định nghĩa tiêu chuẩn kiến trúc kỹ thuật cho hệ thống EmotionAgent.*
