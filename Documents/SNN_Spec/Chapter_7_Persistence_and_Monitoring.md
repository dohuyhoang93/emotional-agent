# Chapter 7: Persistence & Monitoring

**Scope**: Ensuring Long-Term Memory and Observability. How the agent saves its soul and how we watch it dream.

## 7.1 Persistence (Digital Immortality)
**Process**: `p_save_checkpoint.py` (in Orchestrator)
**Utility**: `src/utils/snn_persistence.py`

To prevent "Catastrophic Forgetting" upon system shutdown, the agent implements a full-stack serialization mechanism.

### 7.1.1 The Checkpoint Structure
A checkpoint (`.json` or `.pkl`) captures the holistic state of the agent:
1.  **Hardware State (Architecture)**:
    *   Neuron Count, Scalar/Vector Dims, Connectivity Map.
    *   *Constraint*: To Resume, the new run MUST match these hardware specs exactly.
2.  **Physiological State (Plasticity)**:
    *   Synaptic Weights (Long-term memory).
    *   Neuron Thresholds (Homeostatic state).
    *   Commitment States (Fluid/Solid/Revoked).
3.  **Psychological State (Beliefs)**:
    *   RL Q-Table (Value function).
    *   Believed Switch States (World Model).
    *   Intrinsic Memory (Novelty history).

### 7.1.2 Resume Protocol
*   **Command**: `run_experiments.py --resume <checkpoint_path>`
*   **Flexibility**: While "Hardware" is rigid, "Software" (Hyperparameters) is flexible. You can resume a trained brain and subject it to new learning rates, changing fatigue rules, or different environments.

## 7.2 The Blackbox Recorder (Offline Monitoring)
**Utility**: `src/utils/snn_recorder.py`

Real-time visualization of 1000+ vector neurons is computationally prohibitive (Python GIL bottleneck). Theus uses a "Flight Recorder" approach.

### 7.2.1 Binary Recording Format
Data is buffered in RAM and flushed to compressed binary files (`.bin.gz`) to minimize IO latency.
*   **Frequency**: Every Simulation Step (10-100ms).
*   **Payload**:
    *   `Episode ID` (uint16)
    *   `Step ID` (uint16)
    *   `Neuron Potentials` (float16 array) - "EEG" of the SNN.
    *   `Spike Events` (Sparse Index List) - Who fired?

### 7.2.2 The "Replay" Workflow
1.  **Simulation Phase**: Agent runs at full speed (headless). Recorder silently saves `replay.bin.gz`.
2.  **Analysis Phase**:
    *   Use `visualizer.py` to load the binary file.
    *   Render the neural activity as a movie.
    *   Capabilities: Rewind, Slow Motion, Heatmap Overlay.

## 7.3 Conclusion
This architecture allows the SNN to scale to massive sizes without being slowed down by the observer, while ensuring that no successful mutation is ever lost to a power outage.
