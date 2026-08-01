# ADR-005: Kiến trúc Lõi Tính toán Đa tác nhân Phân tán — Phiên bản Hoàn chỉnh

**Ngày:** 14/07/2026  
**Trạng thái:** Đề xuất Hoàn chỉnh — Chờ Phê duyệt Triển khai  
**Lịch sử:** Đã trải qua 6 vòng Phân tích phản biện (Virtue Auditor × 4, ICA × 3, 6-Hats × 2, Systems Thinking × 2, Critical Analysis × 2)

---

## 1. Tầm nhìn Kỹ thuật & Triết học Cốt lõi

Hệ thống là một **Mạng Xử lý Tín hiệu Đồ thị Phân tán (Distributed Graph Signal Processing Network)**, chạy hoàn toàn trên CPU phổ thông.

**Ba cam kết không thể phá vỡ:**
1. **Không có Reinforcement Learning:** Phần thưởng từ môi trường chỉ đóng vai trò **Tín hiệu Điều biến (Modulator)**, không phải Tín hiệu Dạy học (Teacher Signal).
2. **Tính cục bộ (Locality):** Mọi phép tính, mọi cập nhật, đều thực hiện cục bộ tại từng Nút/Cạnh. Không có Gradient toàn cục, không có Backpropagation.
3. **Phần cứng Thực tế (Hardware Sympathy):** Thiết kế dọn đường cho AVX-512. Dữ liệu SoA (Struct of Arrays), vector 16 chiều, tính toán hàng loạt (Batch).

---

## 2. Kiến trúc Pipeline 4 Tầng

```
┌─────────────────────────────────────────────────────────────┐
│  TẦNG 1: Input Gateway (IG)          [Không học - 500Hz]    │
│  Nhiệm vụ: Tín hiệu thô → (Pattern_Vector 16D, Intensity)   │
└────────────────────────┬────────────────────────────────────┘
                         │ Spike Packets
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  TẦNG 2: Vector Encoder Node (VEN)   [Không Giám sát 500Hz] │
│  Nhiệm vụ: Học Biểu diễn (Oja's Rule) + Đúc Nút trừu tượng │
│  ← Nhận: Inhibitory Tags (cục bộ, xuyên Cluster)            │
│  ← Nhận: Orphan Signal (từ Nút cha bị xóa)                  │
│  ← Nhận: Modulator Signal (từ TCN, không thường xuyên)      │
└────────────────────────┬────────────────────────────────────┘
                         │ Ring Buffer (500Hz → 20Hz)
                         │ LimbicOutput { Pattern[16], Intensity }
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  TẦNG 3: Threshold Classifier Node (TCN)  [Điều biến 20Hz]  │
│  Nhiệm vụ: Phân loại → Ra Quyết định Hành động              │
│  → Phát: Modulator Signal khi nhận Reward từ môi trường     │
└────────────────────────┬────────────────────────────────────┘
                         │ Action Signal
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  TẦNG 4: Graph Lifecycle Manager          [Hàng Tick 20Hz]  │
│  Nhiệm vụ: TTL Decay, Hóa thạch, Pruning, Orphan Broadcast │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Lõi Toán học từng Tầng

### 3.1. TẦNG 1 — Input Gateway (IG)

**Chuyển đổi Observation → Signal Packet:**

Ma trận chiếu ngẫu nhiên cố định `W_proj` (kích thước 16 × d) chiếu tín hiệu thô xuống không gian 16 chiều:

```
P_in  = normalize( W_proj × x_raw )     -- Pattern Vector (16D)
I_in  = L2_norm( x_raw )                -- Intensity Scalar (1D)
```

**Biện minh:** `W_proj` được khởi tạo ngẫu nhiên và đóng băng vĩnh viễn (Không học). Theo Định lý Johnson-Lindenstrauss, phép chiếu ngẫu nhiên bảo tồn khoảng cách tương đối giữa các vector với xác suất cao. Cách này vector hóa mọi loại đầu vào (text, ảnh, âm thanh) về cùng một không gian mà không cần pipeline tiền xử lý riêng.

**Hệ quả bậc 2:** Vì `W_proj` cố định và giống nhau trên mọi máy, không gian 16D là **đồng nhất** — Nút được chia sẻ qua P2P có thể chèn trực tiếp mà không cần bước Alignment.

---

### 3.2. TẦNG 2 — Vector Encoder Node (VEN): Học Không Giám sát

#### 3.2.1. Luật Học Oja's Rule (Thay thế 3-STDP)

**Lý do từ bỏ 3-STDP:**
3-STDP tối ưu hóa Quyết định Hành động thông qua Phần thưởng trì hoãn. Trong bài toán Trừu tượng hóa Đệ quy, tín hiệu Phần thưởng đến quá muộn (nhiều giây sau khi Nút biểu diễn đã được đúc). Đây là lỗi **Nhầm lẫn Thể loại (Category Error)**: dùng công cụ tối ưu Hành động để làm nhiệm vụ xây dựng Biểu diễn.

**Luật thay thế — Oja's Rule:**

```
ΔW_ij = η · y_i · ( x_j  -  y_i · W_ij )

Trong đó:
  x_j  : Tín hiệu đầu vào tại Synapse j
  y_i  : Tín hiệu ra của Nơ-ron i  =  Σ_j ( W_ij · x_j )
  η    : Tốc độ học cục bộ
```

**Tại sao Oja's Rule, không phải Hebbian thuần túy?**
Hebbian thuần túy `ΔW = η · y · x` làm trọng số tăng vô hạn (Weight Explosion). Số hạng trừ `(-y_i · W_ij)` trong Oja's Rule là **cơ chế ổn định hóa nội sinh** — tự động giữ `||W_i|| = 1` (Unit Vector) **mà không cần gọi phép tính Square Root**.

**Hệ quả bậc 2:**
- Vì vector trọng số luôn là Unit Vector, Cosine Similarity và Dot Product trở nên **đồng nhất** tại VEN → Giải quyết toàn bộ tranh luận Cosine vs Dot Product.
- Tiết kiệm ~64.000 phép căn bậc hai mỗi giây mỗi Cluster (128 nơ-ron × 500Hz).

#### 3.2.2. Ngưỡng Kích hoạt Spike

```
Spike_i = 1   nếu  y_i > Θ_i
Spike_i = 0   ngược lại
```

`Θ_i` được điều chỉnh bằng **Adaptive Threshold** (Intrinsic Homeostasis): Nếu Nơ-ron `i` Spike quá thường xuyên, `Θ_i` tăng dần — ngăn một Nơ-ron độc chiếm toàn bộ mạng.

#### 3.2.3. Cơ chế Đúc Nút — Dynamic Graph Compression

**Điều kiện kích hoạt:**

```
NẾU  min( W_ij )  >  W_solid     với mọi cạnh (i,j) trong G_sub
THÌ  Lifecycle.Allocate( Nút_C_mới )
```

**Vector của Nút mới (Centroid):**

```
P_C = normalize( (1 / |G_sub|) · Σ P_i )    với mọi i trong G_sub
```

**Hệ quả bậc 2:** Centroid của nhiều Unit Vectors không nhất thiết là Unit Vector. Nút C phải được chuẩn hóa **một lần duy nhất** khi cấp phát — chi phí chấp nhận được (1 lần mỗi sự kiện Đúc, không phải mỗi Tick).

---

### 3.3. TẦNG 3 — Threshold Classifier Node (TCN): Học Điều biến

#### 3.3.1. Toán học Ra Quyết định

**Tại sao `Cosine × Intensity`, không phải thuần Dot Product?**

Dot Product phụ thuộc cả Góc lẫn Độ dài. Nếu TCN dùng Dot Product thuần, hệ thống rơi vào "Cuộc chạy đua vũ trang độ lớn" (Magnitude Arms Race): Nơ-ron không cần xoay đúng hướng, chỉ cần bơm độ dài vector lên vô hạn là thắng — phá hủy hoàn toàn khả năng Tự Phân Cụm của VEN.

Giải pháp: Tách rời hai chiều thông tin:

```
Score  =  I_signal  ×  CosineSim( P_signal, P_target )

         ╔═══════════╗    ╔══════════════════════════════════╗
         ║  Cường độ ║    ║  Độ khớp hướng (bất biến Độ dài) ║
         ╚═══════════╝    ╚══════════════════════════════════╝

Action = Execute   nếu  Score > Θ_decision
Action = Inhibit   ngược lại
```

**Hệ quả bậc 2:** CosineSim trả về `[-1, 1]`. Khi nhân với `I_signal > 0`, Score có thể âm — một tín hiệu mạnh đi **sai hướng** sẽ chủ động ức chế hành động (Negative Score), mạnh hơn là không có tín hiệu (Score = 0). Hệ thống tự nhiên học được cả "điều nên tránh".

#### 3.3.2. Vòng lặp Điều biến (Modulator Loop)

Khi nhận Reward `R` từ môi trường:

```
M  =  tanh(R)  ×  exp( -λ · t_delay )

TTL_node  +=  M × γ       -- M lan truyền về VEN, tăng TTL Nút Tạm thời
```

**Hệ quả bậc 2:** Khi `t_delay` lớn (Sparse Reward), `M ≈ 0` → Cơ chế Hóa thạch bị vô hiệu hóa → "Vòng lặp Alzheimer" (Học mà không nhớ). Đây là lý do bắt buộc phải có **Hóa thạch bằng Tần suất** làm cơ chế dự phòng (xem Mục 5.3).

---

### 3.4. TẦNG 4 — Graph Lifecycle Manager

Mỗi Chu kỳ 20Hz, thực hiện tuần tự:

```
1. DECAY      : TTL_node -= Δt                   (mọi Nút Tạm thời)
2. FOSSILIZE  : NẾU TTL_node > TTL_fossilize     → Hóa thạch (vĩnh cửu)
3. FOSSILIZE  : NẾU ActivationRate > R_fossilize → Tự Hóa thạch (Mục 5.3)
4. PRUNING    : NẾU TTL_node <= 0               → Xóa, phát Orphan Signal
```

---

## 4. Đánh đổi Kiến trúc: Cường độ 1D vs 16D

**Góc nhìn ủng hộ 16D (Đa kênh - Multiplexing):**
- Sức mạnh biểu đạt cao hơn, đồ thị nhỏ gọn hơn, P2P ít tốn băng thông hơn.
- Tương tự Multi-head Attention trong Transformer.

**Góc nhìn ủng hộ 1D (Structuralist):**
- Oja's Rule cập nhật **một trọng số vô hướng 1D** cho mỗi Synapse. Nếu Intensity là 16D nhưng Synapse là 1D, mọi thông tin đa kênh bị trộn lẫn khi qua Synapse → **Nhiễu chéo (Cross-talk)** không kiểm soát được → Toàn bộ sự ổn định của Oja's Rule sụp đổ.

> [!TIP]
> **Quyết định Khởi điểm (MVP):** Chọn **1D Intensity Scalar** vì tương thích với toán học Oja's Rule. Sự phức tạp biểu đạt nổi lên từ Cấu trúc Đồ thị (Graph Topology), không phải từ Payload tín hiệu.
>
> **Kế hoạch dự phòng:** Nếu benchmark cho thấy đồ thị phình to gây sập băng thông P2P, sẽ có dữ liệu thực nghiệm để nâng cấp lên kiến trúc Đa khoang (Multi-compartment) với trọng số Tensor — từ đó kích hoạt lại 16D.

---

## 5. Ba Cơ chế Phòng vệ Bắt buộc

### 5.1. Inhibitory Tag (Thẻ Ức chế Ngang)

**Vấn đề:** Các Nơ-ron cùng "Lớp Trừu tượng" hình thành Vòng lặp Phản hồi Dương lẫn nhau (A kích hoạt B, B kích hoạt A) mà Local Backpressure không đủ mạnh để chặn các vòng lặp tần số thấp.

**Giải pháp — Không dùng WTA toàn cục** (WTA toàn cục đòi hỏi đồng bộ hóa xuyên Goroutine):

```
Khi Nút C được đúc:
  Với mọi Nút j trong cùng Lớp Trừu tượng, j ≠ C:
    Θ_j  +=  β × exp( -μ · t )

  Trong đó t là thời gian kể từ khi Tag được gắn.
  Tag tự giảm dần (Decaying Counter) — không cần Goroutine đồng bộ để xóa.
```

**Hệ quả bậc 2:** Tạo ra **Bầu cử Tự nhiên (Natural Election)** — Nút được kích hoạt bởi tín hiệu thực chất nhất sẽ thắng theo thời gian, không phải Nút may mắn được đúc trước.

---

### 5.2. Orphan Signal (Tín hiệu Mồ côi)

**Vấn đề:** Khi Nút cha bị Pruning, các Nút con trở thành **Cây Zombie** — tiêu tốn Node Pool mà không còn ngữ nghĩa.

**Giải pháp:**

```
Khi Lifecycle xóa Nút P (cha):
  Với mọi Nút C_i trong Children(P):
    TTL_Ci  ←  TTL_base       -- Reset về TTL cơ bản
```

Nút con bị reset buộc phải tự chứng minh giá trị của mình một lần nữa.

**Hệ quả bậc 2:** Tạo ra **Hiệu ứng Sóng (Cascade)** — khi môi trường thay đổi (Concept Drift), toàn bộ cây khái niệm cũ dần tự xóa bỏ, nhường chỗ cho khái niệm mới. Đây chính là cơ chế **Học Liên tục (Continual Learning)** không cần can thiệp thủ công.

---

### 5.3. Activation Statistics (Hóa thạch bằng Tần suất)

**Vấn đề:** Trong môi trường Phần thưởng Thưa thớt (Sparse Reward), `M ≈ 0`, cơ chế Hóa thạch chính bị vô hiệu hóa → Hệ thống không tích lũy được Trí nhớ Dài hạn ("Vòng lặp Alzheimer").

**Giải pháp:**

```
ActivationRate_node  =  SpikeCount( T_window )  /  T_window

NẾU  ActivationRate  >  R_fossilize:
  → Tự Hóa thạch, độc lập hoàn toàn với Modulator
```

**Hệ quả bậc 2:** Tạo ra **Thiên kiến Tần suất (Frequency Bias)** — Pattern lặp đi lặp lại được ghi nhớ vĩnh cửu dù chưa được môi trường xác nhận.

**Giải pháp bậc 3 (Review định kỳ):**

```
Định kỳ mỗi T_review:
  Với mọi Nút Hóa thạch bằng Tần suất:
    NẾU  ActivationRate  <  R_prune:
      → Phá Hóa thạch, TTL_node  ←  TTL_base
```

---

## 6. Phân tích Đệ quy & Tự Quy chiếu

### 6.1. Đệ quy Cấu trúc (Cấp 1) — Xảy ra, Có thể kiểm soát

`Pixel → Cạnh → Hình → Vật thể → Khái niệm`

Quá trình này xảy ra tự nhiên qua nhiều vòng Graph Compression. Điều chỉnh cần thiết:

```
TTL_depth  =  TTL_base  ×  α^depth        (α > 1)
```

Nơ-ron cấp trừu tượng cao hơn (`depth` lớn) sẽ sống lâu hơn để chờ được kiểm định.

### 6.2. Đệ quy Khái niệm (Cấp 2) — Xảy ra, Nguy hiểm, Đã có Phòng vệ

Vòng lặp phản hồi khái niệm (A kích hoạt B, B kích hoạt A) được chặn bởi **Inhibitory Tag** (Mục 5.1). Không thể chặn 100%, nhưng đủ để ngăn vòng lặp trở nên vô hạn.

### 6.3. Tự Quy chiếu (Cấp 3 — Strange Loop) — Không xảy ra trong MVP

Để xảy ra, hệ thống cần **Bộ nhớ Tự mô hình (Self-modeling Memory)** — một thành phần lưu trữ và xử lý trạng thái hiện tại của toàn bộ mạng lưới như một Đối tượng dữ liệu. Kiến trúc phân tán Cluster-SoA không hỗ trợ điều này theo định nghĩa.

> [!NOTE]
> Sự vắng mặt của Strange Loop ở MVP là **Thiết kế Cố ý**, không phải thiếu sót. Nó đảm bảo hệ thống luôn dừng được và cho ra kết quả xác định. Strange Loop sẽ là đề tài cho một ADR riêng biệt ở giai đoạn xa hơn.

---

## 7. Kiến trúc Mạng P2P (Topology Transfer)

Mọi kiến thức được vật chất hóa thành **Nút Hóa thạch** trong đồ thị. Việc chia sẻ P2P chỉ cần gửi danh sách Nút Hóa thạch (mỗi Nút là `[16]float32 + metadata`). Máy nhận dùng Cosine Similarity để chèn Nút mới vào đúng vị trí trong đồ thị nội bộ.

Vì tất cả máy dùng cùng `W_proj` cố định, không gian 16D là **đồng nhất** — không cần bước Embedding Alignment.

---

## 8. Bảng Tóm Tắt

| Tầng | Thuật toán | Loại Học | Nhịp |
|---|---|---|---|
| **IG** | Random Projection (Frozen) | Không học | 500Hz |
| **VEN** | Oja's Rule + Graph Compression | Không Giám sát | 500Hz |
| **TCN** | Cosine × Intensity + Threshold | Điều biến từ Reward | 20Hz |
| **Lifecycle** | TTL Decay + Fossilize (×2) + Pruning | Hỗn hợp | 20Hz |

| Cơ chế Phòng vệ | Giải quyết | Hệ quả bậc 2 |
|---|---|---|
| **Inhibitory Tag** | Vòng lặp khái niệm (A↔B) | Bầu cử Tự nhiên giữa các Nút cạnh tranh |
| **Orphan Signal** | Cây Zombie | Học Liên tục tự động (Continual Learning) |
| **Activation Statistics** | Vòng lặp Alzheimer | Thiên kiến Tần suất → Cần Review định kỳ |
