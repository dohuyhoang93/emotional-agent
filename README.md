# EmotionAgent: Hybrid Emotional AI meets POP Architecture

**EmotionAgent** là dự án nghiên cứu tiên phong kết hợp hai lĩnh vực:
1.  **Emotional AI:** Mô phỏng trí tuệ nhân tạo có cảm xúc máy, sử dụng cơ chế lai (Hybrid) giữa Q-Learning (Lý trí) và Neural Networks (Cảm xúc).
2.  **Process-Oriented Programming (POP):** Một kiến trúc phần mềm hướng quy trình, đảm bảo tính trong suốt, khả năng kiểm thử và toàn vẹn dữ liệu tuyệt đối thông qua cơ chế Transactional Memory.

> **Project Status:** Active Development (Phase 3: SNN Integration)

---

## 🏗️ 1. Kiến trúc Hướng Quy trình (POP Architecture)

Dự án này là **Reference Implementation** (Bản mẫu) cho Theus Framework. Toàn bộ logic lõi của kiến trúc đã được tách ra thành thư viện độc lập: **[Theus Framework](theus/README.md)**.

### Điểm nổi bật của POP trong EmotionAgent:
*   **Transactional Memory (Delta Architecture):** Mọi thay đổi trạng thái của Agent (học hỏi, di chuyển, cảm xúc) đều được ghi lại dưới dạng `DeltaEntry`.
*   **Time Travel & Rollback:** Nếu Agent gặp lỗi trong quá trình suy nghĩ (Process crash), toàn bộ trạng thái sẽ tự động Rollback về thời điểm an toàn trước đó.
*   **Deep Isolation:** Dữ liệu được bảo vệ 3 lớp. Process không thể sửa đổi lén lút dữ liệu nếu không khai báo trong `contracts`.

## 🧠 2. Mô hình Agent Hybrid

Tác nhân sử dụng **"Vòng lặp Tăng cường Trí tuệ-Cảm xúc"**:
1.  **Trí tuệ (Q-Learning):** Quyết định hành động dựa trên phần thưởng (`Reward`).
2.  **Cảm xúc (Intrinsic Motivation):** 
    *   Tự tạo ra phần thưởng nội sinh (`Intrinsic Reward`) khi gặp điều bất ngờ (`TD-Error` cao).
    *   Trạng thái cảm xúc kích thích hoặc kìm hãm sự tò mò (`Exploration Rate`).
3.  **Học hỏi Xã hội (Social):** Agent có khả năng quan sát và học hỏi từ Agent khác ở gần.

## 📂 3. Cấu trúc Dự án

```
EmotionAgent/
├── theus/              # [CORE] Theus Framework (Độc lập, Reusable)
│   ├── theus/              # Source code SDK
│   └── examples/           # Ví dụ Hello World
│
├── src/
│   ├── processes/          # Logic nghiệp vụ Agent (POP Processes)
│   ├── orchestrator/       # Hệ thống quản lý thử nghiệm
│   ├── models/             # Neural Network Models (MLP, SNN)
│   └── adapters/           # Giao tiếp môi trường (GridWorld)
│
├── workflows/              # Định nghĩa luồng xử lý (YAML)
├── multi_agent_complex_maze.json # Cấu hình môi trường thử nghiệm
│
├── main.py                 # Worker chạy mô phỏng
└── run_experiments.py      # Orchestrator chạy thử nghiệm diện rộng
```

## 🚀 4. Hướng dẫn Cài đặt & Chạy

### Cài đặt
Do dự án sử dụng POP SDK nội bộ, bạn cần cài đặt các dependency:

```bash
# Cài đặt các thư viện AI
pip install torch pandas matplotlib

# (Tùy chọn) Install POP SDK ở chế độ Editable
pip install -e theus
```

### Chạy Demo (Visual Mode)
Chạy một Agent đơn lẻ để xem nó hoạt động trên giao diện đồ họa:

```bash
python main.py --settings-override '{"visual_mode": true}'
```

### Chạy Thử nghiệm (Headless)
Chạy hàng loạt kịch bản để thu thập số liệu (CSV):

```bash
python run_experiments.py --config multi_agent_complex_maze.json
```

## 🗺️ 5. Lộ trình Phát triển (Roadmap)

*   **Phase 1 & 2 (Đã xong):**
    *   ✅ Xây dựng POP Engine & Context Guard (Strict Mode).
    *   ✅ Implement Delta Architecture (Transaction/Rollback).
    *   ✅ **Hybrid Context Zones:** Phân tách Data (Persistent), Signal (Transient) và Meta (Diagnostic).
    *   ✅ **Semantic Audit:** Kiểm soát Input/Output/Side-Effect/Error thông qua Dual Gates.
    *   ✅ Tách POP SDK thành thư viện riêng (Theus).
    *   ✅ Audit & Fix Logic Bugs (Deep Mutation, Zombie Proxy, etc.).

*   **Phase 3 (Hiện tại):**
    *   🚧 **Direct Sensory Mapping:** Chuyển đổi Input từ số (Grid ID) sang Tín hiệu Xung (Spike).
    *   🚧 **SNN Integration:** Thay thế model Emotion cũ bằng Spiking Neural Network để xử lý tín hiệu xung theo thời gian thực.
    *   🚧 **Hebbian Learning:** Cài đặt cơ chế học "Fire together, wire together".

---
*Author: Do Huy Hoang*
