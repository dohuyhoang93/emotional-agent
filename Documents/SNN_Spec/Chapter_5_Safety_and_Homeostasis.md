# Chapter 5: Physiological Homeostasis & Dampening

**Scope**: Regulating the "Temperature" and "Energy" of the brain.

## 5.1 Emotional Safety Valve (Hysteria Dampener)
**Process**: `process_hysteria_dampener` in `snn_advanced_features_theus.py`

This prevents "Epileptic Seizures" (Runaway Positive Feedback Loops) where the network fires uncontrollably.
*   **Monitor**: `fire_rate` (Global metric).
*   **Trigger**: If `fire_rate > saturation_threshold` (e.g., > 20%).
*   **Dampening Action**:
    *   **Emergency Brake**: Immediately multiplies all neuron thresholds by `(1 + dampening_factor)`.
    *   **Effect**: The network becomes "Numb" instantly. Firing stops.
*   **Recovery**: The `saturation_level` slowly decays, allowing thresholds to return to normal once the "panic" has subsided.

## 5.2 Physiological Balance (PID Homeostasis)
**Process**: `process_meta_homeostasis_fixed`

The long-term regulator that maintains the optimal cognitive load.
*   **Goal**: Keep the firing rate near a Target (e.g., 5%).
*   **Mechanism**: PID Controller (Proportional-Integral-Derivative).
    *   **P (React)**: Adjusts threshold based on immediate error.
    *   **I (Bias)**: Corrects long-term drift (e.g., if the agent is chronically lazy, `I` builds up to force it to be active).
    *   **D (Predict)**: Prevents overshoot (e.g., stops lowering threshold *before* the agent goes crazy).
*   **Result**: Ensures the agent is neither "Comatose" (0 spikes) nor "Hyperactive" (All spikes) over long periods.

## 5.3 Cognitive Focus (Lateral Inhibition)
**Process**: `process_lateral_inhibition`

A mechanism to enforce **Sparse Coding** and reduce noise.
*   **Mechanism**: Winner-Take-All (WTA).
*   **Logic**:
    *   In any processing tick, only the **Top-K** strongest neurons are allowed to "speak".
    *   The "Losers" are actively inhibited (Potential -= Inhibition).
## 5.4 Structural Optimization (Neural Darwinism)
**Process**: `process_neural_darwinism` in `snn_advanced_features_theus.py`

Beyond adjusting weights (STDP), the brain actively reshapes its architecture.
*   **Unit of Selection**: The Synapse.
*   **Mechanism**:
    1.  **Fitness Tracking**: Synapses gain fitness for active participation in rewards, lose fitness for inactivity or errors.
    2.  **Selection (The Reaper)**: Periodically, the bottom `X%` of synapses are pruned (Death).
    3.  **Reproduction (Cloning)**: The top `Y%` of synapses are cloned and mutated slightly (Birth).
## 5.5 Maintenance (Numerical Resync)
**Process**: `process_periodic_resync` in `snn_resync_theus.py`

Digital systems suffer from **Floating Point Drift**.
*   **Problem**: After millions of additions (integrations), tiny errors (`1e-16`) accumulate, eventually causing neurons to "ignite" spontaneously.
*   **Mechanism**: Periodic Garbage Collection (Every 1000 steps).
    *   Scans all neurons.
    *   If `|potential| < 1e-6`, force it to `0.0`.
    *   Re-normalizes vector prototypes to ensure length `1.0`.
*   **Analogy**: "Sleep Cleaning" or "Defragging" the brain.
