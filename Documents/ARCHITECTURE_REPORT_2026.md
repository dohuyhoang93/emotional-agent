# DeepSearch EmotionAgent: Architectural Specification 2026

**Date:** 2026-01-13
**Version:** Phase 16 (Hybrid Reward & Meta-Cognition)
**Author:** Do Huy Hoang & Antigravity (Assistant)

---

## 1. Triết lý Thiết kế: POP & Theus Framework
Dự án được xây dựng trên nền tảng **Process-Oriented Programming (POP)**, sử dụng framework **Theus**. Khác với OOP truyền thống (nơi dữ liệu và hành vi bị đóng gói cùng nhau), POP tách biệt hoàn toàn chúng.

### 1.1 Nguyên lý Cốt lõi
1.  **Context (Dữ liệu):** Là các cấu trúc "câm" (Dictionaries/Dataclasses), chứa toàn bộ trạng thái của Agent và Môi trường.
2.  **Process (Hành vi):** Là các hàm thuần túy (Pure Functions) biến đổi Context.
3.  **Workflow (Luồng):** File YAML định nghĩa thứ tự gọi các Process.

### 1.2 Theus Orchestration Diagram

```mermaid
graph TD
    subgraph "Theus Framework"
        W[Workflow Engine] -->|Reads| YAML[workflow.yaml]
        W -->|Loads| R[Process Registry]
        W -->|Injects| C[System Context]
        
        R -->|Returns| P1[Process: Perception]
        R -->|Returns| P2[Process: SNN Cycle]
        R -->|Returns| P3[Process: RL Decision]
        
        subgraph "Execution Loop"
            P1 -->|Modifies| C
            P2 -->|Modifies| C
            P3 -->|Modifies| C
        end
    end
    
    style C fill:#f9f,stroke:#333
    style YAML fill:#ff9,stroke:#333
```

---

## 2. Kiến trúc Nhận thức Tổng thể (Cognitive Architecture)
EmotionAgent sử dụng mô hình **Dual-Process Theory** (Lý thuyết xử lý kép), kết hợp giữa mạng xung thần kinh (SNN) và học tăng cường (RL).

*   **Hệ thống 1 (SNN):** Nhanh, trực giác, xử lý Novelty (Sự mới lạ) và Cảm xúc.
*   **Hệ thống 2 (RL):** Chậm, logic, tối ưu hóa phần thưởng (Q-Learning).
*   **Cầu nối (Bridge):** Gated Attention Network & Hybrid Reward.

### 2.1 Agent Flow Diagram

```mermaid
graph LR
    Env[Environment 25x25] -->|Sensor Vector 16-dim| Perception
    
    subgraph "Agent Brain"
        Perception -->|Input| SNN[Spiking Neural Network]
        Perception -->|State Key| RL[Q-Learning Core]
        
        subgraph "SNN (System 1)"
            SNN -->|Compare Prototypes| Novelty[Novelty Metric]
            SNN -->|Fire Pattern| EmoVec[Emotion Vector]
        end
        
        subgraph "RL (System 2)"
            RL -->|Predict Q| Action
            Action -->|TD Error| Surprise[Surprise Metric]
        end
        
        Novelty -->|Inhibits| Confidence
        Surprise -->|Inhibits| Confidence
        
        Confidence -->|Modulates| RL
        EmoVec -->|Gates| Action
    end
    
    Action -->|Step| Env
    Env -->|Extrinsic Reward| RewardCalc
    Novelty -->|Intrinsic Reward| RewardCalc
    Surprise -->|Intrinsic Reward| RewardCalc
    
    RewardCalc[Hybrid Reward System] -->|Total Reward| RL
```

---

## 3. Các Cơ chế Chuyên sâu (Deep Mechanisms)

### 3.1 Neural Darwinism (Tiến hóa Thần kinh)
Hệ thống không train theo kiểu Backprop (cập nhật trọng số toàn mạng). Nó train theo kiểu **Chọn lọc Tự nhiên** từng Synapse.

*   **Fluid Synapse:** Liên kết mới, dễ thay đổi (dễ học, dễ quên).
*   **Solid Synapse:** Liên kết đã được kiểm chứng (TD-Error thấp liên tiếp). Khó thay đổi, bảo vệ ký ức.
*   **Pruning:** Synapse vô dụng (TD-Error cao) bị cắt bỏ.

```mermaid
stateDiagram-v2
    [*] --> FLUID: New Synapse
    
    FLUID --> SOLID: Consecutive Correct Prediction
    FLUID --> REVOKED: High TD-Error (Penalty)
    
    SOLID --> FLUID: High Surprise (Major Prediction Error)
    REVOKED --> [*]: Pruned (Deleted)
    
    note right of SOLID
        Protected Memories
        (Long Term)
    end note
```

### 3.2 Hybrid Reward & Meta-Cognition (Phase 16)
Cơ chế giải quyết vấn đề "Sparse Reward".

*   **Công thức:** $R_{total} = R_{extrinsic} + (w_1 \times Novelty) + (w_2 \times |TD\_Error|)$
*   **Confidence (Tự tin):** $EMA((1 - Novelty) \times e^{-|TD|})$.

```mermaid
sequenceDiagram
    participant SNN as SNN (System 1)
    participant Action as Action Logic
    participant Env as Environment
    participant Bridge as Reward Bridge
    participant RL as RL Learner
    
    SNN->>Bridge: Novelty (0.8) "Lạ quá!"
    Action->>Env: Interact
    Env->>Bridge: Extrinsic Reward (0) "Chưa tới đích"
    
    rect rgb(200, 255, 200)
    Note over Bridge: CALCULATE HYBRID
    Bridge->>Bridge: Total = 0 + (0.1*0.8) = 0.08
    end
    
    Bridge->>RL: Reward (0.08)
    RL->>RL: Update Q-Table
    RL->>Bridge: TD-Error (High) "Ngạc nhiên!"
    
    rect rgb(255, 200, 200)
    Note over Bridge: UPDATE CONFIDENCE
    Bridge->>Bridge: Conf = Low (Lạ + Sai)
    end
```

### 3.3 Dreaming (Giấc Mơ & Cân bằng Nội môi)
Khi không có Input (Sleep Mode), SNN tự kích hoạt ngẫu nhiên để củng cố ký ức.

*   **Coherence Check:** Đếm tỷ lệ neuron bắn xung ($Rate$).
*   **Reward:**
    *   $Rate \in [5\%, 30\%]$: Thưởng (+0.1) $\rightarrow$ Củng cố đường truyền ổn định.
    *   $Rate > 40\%$: Phạt (-0.5) $\rightarrow$ Ức chế đường truyền gây động kinh.
    *   $Rate < 5\%$: Phạt (-0.2) $\rightarrow$ Kích thích đường truyền chết.

---

## 4. Động lực học Tập thể (Collective/Evolutionary)
Hệ thống hỗ trợ Multi-Agent training thông qua cơ chế **Ancestral Memory Assimilation** (Đồng hóa Ký ức Tổ tiên).

```mermaid
graph TD
    pop[Population]
    
    subgraph "Evolution Cycle"
        Best[Best Agent] -->|Save Weights| GlobalStore[Ancestral Store]
        
        GlobalStore -->|Inject Synapses| NewAgent[New Generation Agent]
        
        subgraph "Quarantine Process"
            NewAgent -->|Load Synapse| Check{Is Safe?}
            Check -- Yes --> Accept[Assimilate]
            Check -- No (High Error) --> Reject[Quarantine/Discard]
        end
    end
    
    NewAgent --> pop
```

### 4.1 Viral Learning (Học tập lây lan)
Tương tự như Virus, một Agent tìm ra đường đi đúng (Goal) sẽ "lây lan" kiến thức đó (Synapse trọng số cao) sang các Agent khác thông qua cơ chế `process_inject_viral`.
*   **Quarantine:** Để tránh lây lan "kiến thức độc hại" (phần thưởng ảo), mỗi kiến thức nạp vào phải trải qua quy trình kiểm tra (Quarantine Validation) trong môi trường Sandbox ảo trước khi được chấp nhận vào não bộ chính.
