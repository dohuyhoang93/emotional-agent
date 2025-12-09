# EmotionAgent: Prototype Tác nhân AI Nhận thức-Cảm xúc với Hệ thống Thử nghiệm Tự động

Dự án này là một prototype hoạt động, hiện thực hóa các ý tưởng trong tài liệu **[spec.md](Documents/spec.md)**. Nó mô phỏng một tác nhân AI học cách hoạt động trong môi trường "Thế giới Lưới" (Grid World) bằng kiến trúc nhận thức-cảm xúc tùy chỉnh.

Điểm nổi bật của dự án không chỉ nằm ở mô hình agent, mà còn ở **hệ thống dàn dựng thử nghiệm tự động**, cho phép cấu hình, thực thi và phân tích các kịch bản thử nghiệm phức tạp một cách khoa học và có hệ thống.

Mục tiêu chính của dự án là chứng minh và phân tích **Vòng lặp Tăng cường Trí tuệ-Cảm xúc**, nơi việc học hỏi (trí tuệ) và các trạng thái nội tại (cảm xúc máy) tương tác và ảnh hưởng lẫn nhau để định hình hành vi của tác nhân.

## 1. Kiến trúc Cốt lõi (Strict POP)

Dự án tuân thủ nghiêm ngặt **Kiến trúc Hướng Quy trình (Process-Oriented Programming - POP)**.

### a. Kiến trúc Context 3 Lớp (3-Layer Context)
Thay vì một object khổng lồ, dữ liệu được phân tách rõ ràng:
1.  **GlobalContext (Immutable):** Cấu hình tĩnh, siêu tham số, hằng số (Configuration).
2.  **DomainContext (Mutable):** Trạng thái nghiệp vụ (State), biến động theo thời gian (Agent Memory, Q-Table, Experiment Results).
3.  **SystemContext (Wrapper):** Lớp vỏ liên kết, tiêm các Dependency (Adapter) vào Process.

### b. Vòng lặp Tăng cường Trí tuệ-Cảm xúc
Trái tim của tác nhân, nơi lý trí và cảm xúc giao thoa:
1.  **Trí tuệ (Q-Learning):** Tác nhân học giá trị hành động. Tín hiệu `td_error` (độ bất ngờ) được đo đạc.
2.  **Cảm xúc (MLP/SNN):** Mô hình cảm xúc sinh ra Vector Cảm xúc (`E_vector`) từ trạng thái cơ thể.
3.  **Tương tác:**
    *   **Ngạc nhiên → Thưởng nội sinh:** `td_error` tạo ra phần thưởng tò mò (`R_intrinsic`).
    *   **Cảm xúc → Hành vi:** `E_vector` điều chỉnh `exploration_rate` (Độ tò mò/Mạo hiểm).

### c. Hệ thống Dàn dựng (Process Orchestrator)
Hệ thống Orchestrator cũng tuân theo POP:
*   **Workflow:** Định nghĩa bằng YAML (`workflows/orchestration_workflow.yaml`).
*   **Engine:** `POPEngine` chung cho cả Agent và Orchestrator.
*   **Processes:** Các process quản lý vòng đời thử nghiệm nằm tại `src/orchestrator/processes/`.

## 2. Cấu trúc Mã nguồn

```
EmotionAgent/
├── main.py                     # Worker: Chạy một lần mô phỏng (Agent Loop)
├── run_experiments.py          # Orchestrator: Dàn dựng thử nghiệm (Meta-Loop)
├── environment.py              # Môi trường GridWorld Logic
├── experiments.json            # File cấu hình thử nghiệm chính
│
├── workflows/                  # Định nghĩa Luồng xử lý (YAML)
│   ├── main_loop.yaml          # Chu trình sống của Agent (P1 -> P9)
│   └── orchestration_workflow.yaml # Chu trình chạy thử nghiệm
│
├── src/
│   ├── core/                   # Kernel của POP Architecture
│   │   ├── engine.py           # POPEngine, @process decorator
│   │   └── context.py          # 3-Layer Context Definitions
│   │
│   ├── processes/              # Các Process nghiệp vụ của Agent
│   │   ├── p1_perception.py
│   │   ├── ...
│   │   └── p9_social_learning.py
│   │
│   ├── orchestrator/           # Module Orchestrator
│   │   ├── context.py          # Context riêng cho Orchestrator
│   │   └── processes/          # Các Process quản lý thử nghiệm
│   │
│   ├── models/                 # Neural Models (MLP, SNN Future)
│   └── adapters/               # Giao tiếp với thế giới bên ngoài (Env, IO)
│
└── tests/ (Scripts kiểm thử)
    ├── test_mechanics_strict.py    # Kiểm tra ràng buộc cứng Logic
    └── test_context_integrity.py   # Kiểm tra tính toàn vẹn dữ liệu
```

## 3. Hướng dẫn Chạy chương trình

### a. Cài đặt
```shell
pip install torch pandas matplotlib pyyaml
```

### b. Chạy Thử nghiệm (Orchestration)
Để chạy các kịch bản định nghĩa trong `experiments.json`:
```shell
python run_experiments.py
```
Kết quả (CSV, biểu đồ, báo cáo) sẽ nằm trong thư mục `results/`.

### c. Chạy Worker Đơn lẻ (Debug)
Để chạy nhanh một mô phỏng (có hiển thị visual):
```shell
python main.py --settings-override '{"visual_mode": true}'
```

---

## 4. Hệ thống Kiểm thử & Đảm bảo Chất lượng (QA)

Dự án áp dụng cơ chế "SafeGuard" nghiêm ngặt trước khi commit code mới:

1.  **Kiểm tra Logic Cứng (`test_mechanics_strict.py`):**
    *   Đảm bảo simulation dừng CHÍNH XÁC tại `max_steps`.
    *   Đảm bảo đồng bộ step giữa Engine và Environment.

2.  **Kiểm tra Toàn vẹn Dữ liệu (`test_context_integrity.py`):**
    *   Chạy luồng End-to-End.
    *   So khớp: Input Config == Context Log == Output CSV.
    *   Đảm bảo tính trung thực của báo cáo khoa học.

**Lệnh chạy kiểm thử:**
```shell
# Chạy từng cái
python test_mechanics_strict.py
python test_context_integrity.py
```

---

## 5. Trạng thái & Roadmap

*   **Đã hoàn thành:**
    *   POP Architecture Base (Engine, Context 3-Layer).
    *   Q-Learning + Intrinsic Motivation Loop.
    *   Social Learning (Assimilation).
    *   Automated Orchestration & Reporting.
*   **Đang nghiên cứu:**
    *   **Spiking Neural Network (SNN):** Thay thế MLP bằng mạng nơ-ron xung sự kiện (Event-driven) để mô phỏng "Cảm giác" thực hơn. (Xem `design_snn.md`).

---
*Cập nhật lần cuối: 12/2025*
