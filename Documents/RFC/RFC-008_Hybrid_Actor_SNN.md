# RFC-008: KIẾN TRÚC HYBRID ACTOR VÀ XỬ LÝ TÍN HIỆU PHỨC TRONG MẠNG SNN
## (Hybrid Actor Architecture and Complex Signal Processing for Real-Time SNN)

**Mã RFC:** RFC-008  
**Dự án:** EmotionAgent (E.A)  
**Tác giả:** Technical Architecture Team  
**Trạng thái:** Dự thảo Tiêu chuẩn Kỹ thuật (Technical Architecture Specification Draft)  
**Mục tiêu:** Định hình mô hình kiến trúc lai giữa Actor Model (OOP) và Data-Oriented Design (DOD), kết hợp các kỹ thuật xử lý bare-metal và đại số số phức $C^8$ tối ưu cho hệ thống xử lý tín hiệu theo thời gian thực.

---

## 1. TỔNG QUAN & TƯ DUY KIẾN TRÚC LAI (HYBRID ACTOR MODEL)

### 1.1. So sánh Định hướng: RFC-007 (DOD Thuần) vs RFC-008 (Hybrid Actor)
- **RFC-007 (DOD Thuần):** Coi toàn bộ mạng SNN là một Cơ sở dữ liệu In-Memory phân mảnh. Dữ liệu được quét tuyến tính theo mảng tĩnh cố định. Tối ưu tuyệt đối cho tính toán SIMD nhưng hạn chế trong việc linh hoạt hóa các quy trình định tuyến thông điệp phức tạp.
- **RFC-008 (Hybrid Actor):** Kết hợp tính linh hoạt của mô hình Actor (giao tiếp định tuyến hướng thông điệp) với hiệu năng tối ưu bộ nhớ của DOD. 

### 1.2. Phân định Ranh giới Kỹ thuật & Hạ tầng Go
- **Không dùng mô hình 1-Goroutine-per-Neuron ngây thơ:** Việc gán 1 Goroutine cho 1 Nút gây ra rào cản chi phí lập lịch (Context Switch Overhead $\approx 100-200\text{ns} \gg 2-5\text{ns}$ cho phép toán số học).
- **Mô hình Micro-Worker Actor Pool:** Nhóm các Nút SNN theo cụm/tầng và giao cho các Worker Goroutines (gắn cố định trên các CPU Cores) xử lý.
- **Tách biệt rõ ràng:** Mô hình toán học thần kinh (Spike, Phase, Synaptic Weight) được đóng gói trong các cấu trúc dữ liệu SoA phẳng, trong khi Go Runtime được dùng để điều phối luồng công việc cấp cao.

---

## 2. BỘ MẪU THIẾT KẾ KIẾN TRÚC (DESIGN PATTERNS)

### 2.1. Pattern 1: Micro-Worker Actor Pool Pattern
Nút SNN không phải là một Goroutine riêng lẻ mà là một phần tử dữ liệu nằm trong mảng quản lý của một **Actor Worker Pool**:
- Mỗi Worker Pool đại diện cho một phân vùng xử lý (Cluster/Arena).
- Giao tiếp giữa các Worker Pools thực hiện qua cơ chế định tuyến bất đồng bộ, giữ cho số lượng Goroutine luôn bằng với số lượng Threads phần cứng ($N_{\text{goroutine}} = P_{\text{logical\_cores}}$).

### 2.2. Pattern 2: Core-Local Sharded Bitmask Pattern
Giải quyết tận gốc vấn đề tranh chấp khóa ghi (Lock Contention) trên bus bộ nhớ:
- Thay vì dùng mảng Bitmask dùng chung toàn cục, mỗi CPU Core sở hữu một vùng Bitmask riêng (`CoreBitmask[CoreID][WordIdx]`).
- Core $i$ chỉ ghi vào bitmask $i$ của mình. Thao tác ghi bit nhị phân diễn ra ở tốc độ cục bộ ($< 0.5\text{ns}$), hoàn toàn không cần lệnh `LOCK` bus bộ nhớ.

### 2.3. Pattern 3: Zero-Syscall Active Read Pass Pattern
Loại bỏ hoàn toàn cơ chế chờ thụ động của Kernel (Futex Syscall / `sys_futex`):
- Không dùng cơ chế đánh thức ngắt nhân OS (Kernel IPI Lock Storm).
- Các Worker Threads chủ động quét vùng nhớ Bitmask SHM ở Userspace bằng tập lệnh bit-scan (`tzcnt`) hoặc SIMD (`_mm512_test_epi64_mask`), trích xuất vị trí các bit `1` trong 1 clock cycle.

### 2.4. Pattern 4: Cascade Node Allocation Pattern
Quản lý các nút có kết nối vượt quá hằng số $K=8$:
- Đúc nút phụ $P_1$ (8 con), $P_2$ (các con còn lại) và liên kết qua nút quản lý $P_{\text{master}}$.
- Đảm bảo mảng dữ liệu luôn duy trì cấu trúc phẳng liên tục cho thao tác nạp thanh ghi SIMD.

---

## 3. KỸ THUẬT XỬ LÝ BARE-METAL (PROCESSING TECHNIQUES)

### 3.1. Kỹ thuật Ghi Cục bộ (Core-Local Bitmask Writing)
Thao tác ghi xung nhị phân diễn ra hoàn toàn không tranh chấp:

```go
// Thao tác ghi bit nhị phân cục bộ trên CoreID (Zero Lock / Zero Bus contention)
func (a *MemoryArena) FireSpike(nodeIdx uint32) {
    wordIdx := nodeIdx / 64
    bitIdx := nodeIdx % 64
    // Ghi trực tiếp vào mảng bitmask riêng của Core, không dùng atomic.Or
    a.localBitmask[wordIdx] |= (1 << bitIdx)
}
```

### 3.2. Kỹ thuật Định lượng Pha Sub-tick (Sub-Tick Phase Quantization)
Bảo toàn độ phân giải thời gian dưới $1\text{ms}$ trong một chu kỳ tính toán $10\text{ms}$:
- Chu kỳ $10\text{ms}$ được chia thành 16 nấc pha (Phase Bins), mỗi nấc tương ứng $\approx 0.625\text{ms}$.
- Thời điểm xuất hiện xung $t_{\text{spike}}$ được quy đổi thành góc pha $\theta \in [0, 2\pi)$:

$$\theta = \left( \frac{t_{\text{spike}} \pmod{10\text{ms}}}{10\text{ms}} \right) \times 2\pi$$

### 3.3. Kỹ thuật Quét Bitmask Vector hóa (SIMD / `tzcnt` Scan)
Trích xuất danh sách các nút bắn xung ở Userspace mà không cần loop `IF/ELSE`:

```go
// Trích xuất vị trí các bit 1 siêu tốc bằng lệnh tzcnt (Trailing Zero Count)
func ScanBitmask(word uint64, baseIdx uint32, activeIndices *[]uint32) {
    for word != 0 {
        tz := bits.TrailingZeros64(word) // Biên dịch thành 1 lệnh CPU tzcnt
        *activeIndices = append(*activeIndices, baseIdx + uint32(tz))
        word &= word - 1 // Xóa bit 1 thấp nhất
    }
}
```

### 3.4. Kỹ thuật Cấp phát Bộ nhớ Tĩnh $T=-1$ (Object Pooling)
Toàn bộ cấu trúc bộ nhớ được khởi tạo nguyên khối tại $T=-1$. Thao tác sinh/diệt nút ở runtime ($T > 0$) chỉ là phép lật bit trạng thái `State` ($O(1)$), bảo đảm zero Garbage Collection (GC) overhead.

---

## 4. NỀN TẢNG TOÁN HỌC HỢP LÝ (MATHEMATICAL FOUNDATION)

### 4.1. Mã hóa Số Phức $C^8$ trên Không gian Hilbert
Mỗi trạng thái tín hiệu được đại diện bởi số phức $z = r \cdot e^{i\theta}$:
- Biên độ $r = |z|$: Biểu thị cường độ tín hiệu.
- Góc pha $\theta = \text{arg}(z)$: Biểu thị thời điểm kích hoạt tương đối.

### 4.2. Đại số Liên hợp Pha (Phase Conjugation Algebra)
Phép nhân tín hiệu $X_k$ với liên hợp trọng số $W_k^*$:

$$X_k \cdot W_k^* = (r_k e^{i \tau_k}) \cdot e^{-i \tau_k} = r_k e^{i 0^\circ} = r_k$$

* **Cộng hưởng Tăng cường (Constructive Resonance):** Khi các tín hiệu đến đúng thứ tự thời gian kỳ vọng ($\tau_1, \tau_2$), bộ bù pha $W_k^*$ quay toàn bộ các pha về góc $0^\circ$, tạo ra tổng cường độ dương $(r_1 + r_2)$.
* **Giao thoa Triệt tiêu (Destructive Interference):** Khi tín hiệu đến sai thứ tự hoặc bị nhiễu, góc pha sau khi nhân bị lệch sang góc âm (ví dụ $180^\circ \to -r_k$), tự động triệt tiêu nhiễu mà không cần logic điều kiện `IF/ELSE`.

### 4.3. Cập nhật Trọng số R-MPP và Dư âm EMA
Cập nhật trọng số dựa trên tín hiệu phần thưởng $M$:

$$\Delta W_k = \eta \cdot M \cdot Trace_k \cdot (X_k \cdot Y^*)$$

Để giải quyết mâu thuẫn giữa Thời gian Trơ (Refractory Period) và Phần thưởng chì hoãn:

$$\text{ActivityEMA} = (0.9 \cdot \text{ActivityEMA}) + (0.1 \cdot \text{Spike}_{current})$$

- Refractory Period chỉ khóa `Spike_{current}` để chặn bão Howl.
- Hàm R-MPP nhân phần thưởng $M$ với `ActivityEMA` $O(1)$, đảm bảo cập nhật trọng số liên tục ngay cả khi nút đang trong trạng thái trơ.

---

## 5. TỔNG HỢP SO SÁNH QUY MÔ KIẾN TRÚC RFC-007 VS RFC-008

| Hạng mục Phân tích | RFC-007 (Data-Oriented Design) | RFC-008 (Hybrid Actor Model) |
| :--- | :--- | :--- |
| **Triết lý chủ đạo** | In-Memory Database / Quét mảng phẳng | Actor Worker Pools / Routing hướng thông điệp |
| **Đơn vị Thực thi** | CPU Core Arena (Mảng tĩnh $O(N)$) | Worker Pool Goroutines ($N_{\text{goroutine}} = P_{\text{cores}}$) |
| **Giao tiếp Liên Core** | SPSC Matrix Ring Buffer | Core-Local Bitmask SHM + SIMD Read Pass |
| **Xử lý Thời gian** | Frame-based $10\text{ms}$ | Sub-Tick Phase Quantization (16 nấc pha $\approx 0.625\text{ms}$) |
| **Xử lý Nhiễu Tín hiệu** | Bộ lọc ngưỡng tĩnh | Đại số Phức $C^8$ Destructive Interference |
| **Độ linh hoạt Đồ thị** | Cố định theo dải mảng tĩnh | Linh hoạt qua mô hình định tuyến Actor |

---

*Tài liệu RFC-008 tổng hợp bộ mẫu thiết kế, kỹ thuật xử lý bare-metal và nền tảng toán học cho kiến trúc Hybrid Actor SNN.*
