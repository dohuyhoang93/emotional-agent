# EmotionAgent: Hybrid Emotional AI meets POP Architecture

**EmotionAgent** is a pioneering research project combining two fields:
1.  **Emotional AI:** A simulation of artificial intelligence with machine emotions, using a Hybrid mechanism between Q-Learning (Rationality) and Neural Networks (Emotion).
2.  **Process-Oriented Programming (POP):** A process-oriented software architecture ensuring transparency, testability, and absolute data integrity through Transactional Memory.

> **Project Status:** Active Development (Phase 3: SNN Integration)

---

## 🏗️ 1. POP Architecture (Process-Oriented Programming)

This project serves as the **Reference Implementation** for the Theus Framework. The entire core logic of the architecture has been extracted into an independent library: **[Theus Framework](https://github.com/dohuyhoang93/theus)**.

### Key Highlights of POP in EmotionAgent:
*   **Transactional Memory (Delta Architecture):** Every state change of the Agent (learning, moving, feeling) is recorded as a `DeltaEntry`.
*   **Time Travel & Rollback:** If the Agent encounters an error during processing (Process crash), the entire state automatically rolls back to the previous safe point.
*   **Deep Isolation:** Data is protected by 3 layers. Processes cannot modify data secretly without declaring it in `contracts`.

## 🧠 2. Hybrid Agent Model

The agent uses an **"Intelligence-Emotion Reinforcement Loop"**:
1.  **Intelligence (Q-Learning):** Decides actions based on reward (`Reward`).
2.  **Emotion (Intrinsic Motivation):** 
    *   Self-generates intrinsic rewards (`Intrinsic Reward`) when encountering surprises (High `TD-Error`).
    *   Emotional state stimulates or inhibits curiosity (`Exploration Rate`).
3.  **Social Learning:** The Agent has the ability to observe and learn from other nearby Agents.

## 📂 3. Project Structure

```
EmotionAgent/
├── theus/              # [CORE] Theus Framework (Independent, Reusable)
│   ├── theus/              # Framework Source code
│   └── examples/           # Hello World Examples
│
├── src/
│   ├── processes/          # Agent Business Logic (POP Processes)
│   ├── orchestrator/       # Experiment Management System
│   ├── core/               # Core Components (Context, etc.)
│   ├── adapters/           # Environment Interface (EnvironmentAdapter)
│   └── models.py           # Neural Network Models (MLP)
│
├── specs/              # Workflow Definitions and Schemas (YAML)
│   ├── workflow.yaml       # Agent Workflow
│   ├── orchestrator.yaml   # Orchestrator Workflow
│   └── audit_recipe.yaml   # Audit Configuration
│
├── multi_agent_complex_maze.json # Experiment Environment Config
├── environment.py      # Simulated Environment (GridWorld)
├── main.py             # Simulation Worker
└── run_experiments.py  # Orchestrator for Large-scale Experimentse-scale Experiments
```

## 🚀 4. Installation & Usage

### Installation
Since the project uses an internal POP SDK, you need to install dependencies:

```bash
# Install AI libraries
pip install torch pandas matplotlib

# (Optional) Install POP SDK in Editable mode
pip install -e theus
```

### Run Demo (Visual Mode)
Run a single Agent to see it working with a graphical interface:

```bash
python main.py --settings-override '{"visual_mode": true}'
```

### Run Experiments (Headless)
Run batch scenarios to collect metrics (CSV):

```bash
python run_experiments.py --config multi_agent_complex_maze.json
```

## 🗺️ 5. Development Roadmap

*   **Phase 1 & 2 (Completed):**
    *   ✅ Build POP Engine & Context Guard (Strict Mode).
    *   ✅ Implement Delta Architecture (Transaction/Rollback).
    *   ✅ **Hybrid Context Zones:** Separate Data (Persistent), Signal (Transient), and Meta (Diagnostic).
    *   ✅ **Semantic Audit:** Control Input/Output/Side-Effect/Error via Dual Gates.
    *   ✅ Extract POP SDK into separate library (Theus).
    *   ✅ Audit & Fix Logic Bugs (Deep Mutation, Zombie Proxy, etc.).

*   **Phase 3 (Current):**
    *   🚧 **Direct Sensory Mapping:** Convert Input from numbers (Grid ID) to Spike Signals.
    *   🚧 **SNN Integration:** Replace old Emotion model with Spiking Neural Network to process spike signals in real-time.
    *   🚧 **Hebbian Learning:** Implement "Fire together, wire together" learning mechanism.

---
*Author: Do Huy Hoang*
