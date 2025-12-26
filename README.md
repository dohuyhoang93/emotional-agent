# EmotionAgent: A Process-Oriented Neuro-Symbolic Cognitive Architecture

> **Abstract:** This repository houses the reference implementation of **EmotionAgent**, an autonomous cognitive architecture that integrates Spiking Neural Networks (SNN) with Reinforcement Learning (RL) within a Process-Oriented Programming (POP) framework. Unlike traditional Deep RL models that suffer from catastrophic forgetting and lack interpretability, EmotionAgent employs **True Neural Darwinism** (Structural Plasticity) and a **Strict Audit Trail** to ensure continuous, safe, and transparent learning.

---

## 🔬 1. The Research Problem

Contemporary AI faces three critical challenges:
1.  **Catastrophic Forgetting:** Neural networks tend to overwrite old knowledge when learning new tasks.
2.  **Black Box Opacity:** It is difficult to trace *why* an agent made a specific decision.
3.  **Static Topology:** Most models have a fixed number of neurons/layers, unable to adapt to varying problem complexities.

**EmotionAgent** addresses these by proposing a **Hybrid Biological-Computational Model** where the network structure itself evolves (neurogenesis/pruning), and every micro-decision is transactionally audited.

---

## 🏗️ 2. System Architecture (Theus V2)

The project is built on the **Theus Framework**, a dedicated SDK for Process-Oriented Programming.

### 2.1 The "Living" Brain (SNN-RL Hybrid)
Instead of a monolithic network, the agent's brain is a dynamic ecosystem:

| Component | Function | Biological Analogue |
| :--- | :--- | :--- |
| **SNN Core** | Temporal Pattern Recognition & Clustering | Neocortex (Spiking Dynamics) |
| **RL Engine** | Goal-Directed Decision Making (Q-Learning) | Basal Ganglia (Reward System) |
| **Gated Network** | Dynamic weighting of Rational vs. Intuitive | Thalamus (Signal Gating) |
| **Intrinsic Module**| Curiosity & Fatigue regulation | Neurotransmitters (Dopamine/Serotonin)|

### 2.2 True Neural Darwinism (Structural Plasticity)
We implement a dual-level evolutionary mechanism that operates in real-time:
*   **Synaptic Selection (Pruning):** Connections with low efficacy are physically removed from the graph. **SOLID** connections (long-term potentiation) are shielded from pruning.
*   **Neurogenesis (Reincarnation):** "Dead" neurons (inactive > 2k steps) are detected, their potentials reset, and they are re-wired to new latent spaces. This allows the agent to recycle computational resources to learn new concepts without growing the model size.

### 2.3 Semantic Dreaming (Memory Consolidation)
During idle periods, the agent enters a "Dream State" where high-surprise memories are replayed. Crucially, these memories are not exact replicas but are **semantically warped** towards cluster centroids, reinforcing generalizable concepts rather than overfitting to specific instances.

---

## 📊 3. State-of-the-Art Comparison

| Feature | DeepMind (IMPALA/A3C) | Intel (Loihi/Lava) | **EmotionAgent (Ours)** |
| :--- | :--- | :--- | :--- |
| **Core Paradigm** | Deep RL (LSTM/Transformer) | Neuromorphic SNN | **Hybrid Neuro-Symbolic** |
| **Learning Rule** | Backpropagation (Global) | Local STDP | **3-Factor STDP + Q-Learning** |
| **Plasticity** | Weights Only (Static Graph) | Weights Only | **Structural (Nodes/Edges Evolve)** |
| **Safety** | Reward Hacking Risk | Hardware Constraints | **Strict Audit (Theus Engine)** |
| **Interpretability**| Low (Black Box) | Medium (Spike Trains) | **High (Transactional Logs)** |

> **Key Advantage:** EmotionAgent achieves "Lifetime Learning" through its Commitment Layer (`SOLID` state), significantly outperforming standard RL in non-stationary environments where rules change dynamically.

---

## 📂 4. Repository Structure

The project follows a standardized Process-Oriented Architecture:

```bash
EmotionAgent/
├── theus/                  # [CORE] Theus Framework (The Engine)
├── src/
│   ├── agents/             # Agent Cognitive Modules
│   ├── processes/          # Business Logic (Pure Functions, e.g., STDP, Pruning)
│   ├── coordination/       # Multi-Agent Swarm Intelligence
│   └── orchestrator/       # Experiment Manager
├── workflows/              # [YAML] Declarative Execution Flows
├── specs/                  # [YAML] Logic Constraints & Audit Recipes
└── documents/              # Technical Specifications
```

---

## 🚀 5. Replication & Usage

### Prerequisites
*   Python 3.10+
*   Theus Framework (Included as submodule)

### Installation
```bash
# 1. Install Dependencies
pip install torch pandas matplotlib networkx numpy

# 2. Install Theus Hook
pip install -e theus
```

### Running Experiments
The complete simulation pipeline (Initialization -> Simulation -> Structual Evolution -> Reporting) is automated.

```bash
# Run the Standard Benchmark (Complex Maze V2)
python run_experiments.py
```

### Analysis
Post-experiment forensics can be performed to generate synaptic connectivity graphs and learning curves:

```bash
python run_post_process.py
```

---

## 📜 6. Citation & License

This project is open-source under the MIT License.
*Principal Investigator: Do Huy Hoang*
