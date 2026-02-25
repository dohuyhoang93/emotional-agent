# Theus Framework Benchmark Master Report
**Date:** 2026-02-23 (Updated)
**Version:** v3.0.22 (Zero Trust + Zero Copy + RFC-002 Namespace Isolation)
**Environment:** Windows | Python 3.14.2 (Free-Threading) | Rust Core v3.1.2

---

## 1. Executive Summary

| Key Metric | v3.0.22 (2026-02-02) | v3.0.22 (2026-02-23) | Delta |
|---|---|---|---|
| Proxy overhead | ~50x | **39.7x** | ✅ -20% |
| TheusEncoder speedup | 3.5x | **3.0x** | ≈ stable |
| Zero-Copy vs Pickle (3000x3000) | 1.09x faster | **1.20x faster** | ✅ improved |
| Sub-Interp Init Speedup | 12.7x | **21.07x** | ✅ +65% |
| 200MB Scalability Speedup | 3.0x | **2.09x** | ⚠️ regressed |

**Key Findings:**
1. **Proxy overhead giảm 20%:** Deep Guard overhead từ ~50x xuống **39.7x** — cải thiện do tối ưu `ContextGuard`.
2. **Sub-Interpreter khởi động nhanh hơn 65%:** Init time từ 12.7x lên **21.07x** so với ProcessPool Spawn — tín hiệu rõ Python 3.14 free-threading đang trưởng thành.
3. **Zero-Copy Matrix 1.20x nhanh hơn Pickle** (cải thiện từ 1.09x).
4. **Scalability 200MB test nhẹ chậm hơn:** Theus ZC 0.50s vs Pickle 1.05s = 2.09x (cũ 3.0x). Cần điều tra thêm — có thể do Rust memory allocator init overhead thay đổi.
5. **SignalHub recv() latency:** 54.87µs (blocking), recv_async() 176.37µs — overhead async còn cao (+221%), cần cải thiện.

---

## 2. Core Performance (Micro-Benchmarks)

### 2.1 Proxy Overhead (Read)

| Mechanism | ops/sec | Latency/op | vs Old |
|---|---|---|---|
| **Native Python** | 3,305,204 | 0.30 µs | baseline |
| **Theus Proxy** | 2,516,864 | 0.40 µs | — |
| **Overhead (ops)** | 0.76x | — | — |

| Mechanism | Latency/op | vs Old |
|---|---|---|
| **Native Python** (comprehensive) | 0.19 µs | =0.19 µs |
| **Theus Proxy** (comprehensive) | **7.35 µs** | ✅ was 9.59 µs |
| **Overhead** | **39.7x** | ✅ was ~50x |

### 2.2 Serialization (TheusEncoder)

| Method | Time (5k items) | Speedup | vs Old |
|---|---|---|---|
| Manual `dict()` cast | 7.73 ms | 1x | ≈7.12 ms |
| **TheusEncoder** | **2.57 ms** | **3.0x** | ✅ was 2.05ms/3.5x |

---

## 3. High-Performance Computing (Heavy Zone)

### 3.1 Zero-Copy Vector Ops (3000×3000 float64, 68.66 MB)

| Implementation | Time | vs Sequential | vs Old |
|---|---|---|---|
| Sequential (baseline) | 1.68 s | 1x | — |
| Multi-thread (GIL) | 1.69 s | 1.00x | — |
| **MP Pickle** | 3.20 s | 0.52x | was 3.12s |
| **Theus Core ZC** | **2.66 s** | **0.63x** | ✅ was 2.87s |
| Theus Engine API | 3.58 s | 0.47x | was 4.50s |

> **Note:** Theus Core ZC bao gồm 0.06s copy time. Overhead Engine API giảm từ 1.63s xuống còn 0.92s.

### 3.2 Scalability (200MB Stress Test, 5000×5000 float64)

| Mechanism | Time | RAM | vs Old |
|---|---|---|---|
| ProcessPool (Pickle) | 1.05 s | O(N) copy | was 1.71s |
| **Theus Zero-Copy** | **0.50 s** | O(1) constant | ✅ was 0.56s |
| **Speedup** | **2.09x** | Essential | ⚠️ was 3.0x |

---

## 4. Isolation Technology

| Metric | ProcessPool | Sub-Interpreters | Speedup | vs Old |
|---|---|---|---|---|
| **Initialization** | 1.20 s | **0.057 s** | **21.07x** 🚀 | ✅ was 12.7x |
| **Execution** | 0.71 s | 0.69 s | **1.03x** | ≈1.7x |

---

## 5. SignalHub Performance (NEW)

| Mode | Throughput | Latency |
|---|---|---|
| `recv()` blocking | 18,226 msg/s | 54.87 µs |
| `recv_async()` native | 5,670 msg/s | 176.37 µs |
| `asyncio.to_thread(recv())` | 4,236 msg/s | 236.07 µs |

> ⚠️ `recv_async()` có overhead cao hơn 221.5% so với blocking. Tuy nhiên vẫn 1.3x nhanh hơn `to_thread` fallback.

---

## 6. Deep Access Latency (NEW)

| Method | ops/sec | Latency |
|---|---|---|
| Legacy `['key']` | 331,121 | 3.02 µs |
| Supervisor `.attr` | 214,517 | 4.66 µs |

---

## 7. Deployment Recommendations (Updated)

1. **`ctx.heavy` cho mọi dữ liệu > 10KB** — Proxy overhead 39.7x không phù hợp cho array ops. Zero-Copy cho AI workloads.
2. **`TheusEncoder`** cho REST API — giảm 70% serialization time.
3. **Sub-Interpreter ngày càng vượt trội:** Init speedup đạt 21x. Cần theo dõi NumPy PEP 684 compatibility để tận dụng hoàn toàn.
4. **Cần điều tra `recv_async()` latency** (+221%) — bottleneck ở async bridge layer.
5. **Scalability 200MB giảm từ 3.0x xuống 2.09x** — cần profiling thêm, có thể do GC tuning hoặc Rust allocator.

---
*Report updated 2026-02-23. Previous baseline: 2026-02-02.*
