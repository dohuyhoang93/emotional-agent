# Chapter 3: Semantic Dream & Protection Architecture

**Scope**: How the agent simulates reality, learns from it, and protects itself from "mental crashes".

## 3.1 The Dream Cycle (Biological Simulation)
Dreams in Theus SNN serve as a **Memory Consolidation** mechanism, functioning independently of external sensory input.

### A. Stimulation (`process_inject_dream_stimulus`)
*   **Mechanism**: The agent enters a "Sleep State" where external sensors are disconnected.
*   **Input**: The system injects **Stochastic Noise** (White Noise) into the input neurons to simulate REM sleep.
*   **Deep Sleep (PGO Waves)**: Occasional strong bursts of stimulus (probability ~1%) are injected to forcibly trigger random associative chains, retrieving dormant memories.

### B. Consolidation (`process_stdp_3factor`)
*   **Logic**: Standard STDP (Spike-Timing Dependent Plasticity) continues to operate.
*   **Effect**:
    *   **Reinforcement**: Existing strong synapse chains (valid memories) fire synchronously due to the noise, reinforcing their weights (LTP).
    *   **Pruning**: Weak or spurious connections fail to synchronize and eventually decay or are pruned by Darwinism processes.
    *   **Outcome**: Transformation of "Fluid" short-term memories into "Solid" long-term structures.

### C. Visualization (`process_decode_dream`)
*   **Problem**: Monitoring internal state without external context.
*   **Solution**: The system decodes the `Spike_Queue` into a spatial coordinate `(x, y)` using the `process_decode_dream` inverse model.
*   **Result**: Allows observers to see "what the agent is dreaming about" (e.g., replaying a path to the goal).

## 3.2 Defense Mechanisms (The Immune System)
To prevent "Epileptic Seizures" (Runaway Feedback Loops) common in Recurrent SNNs.

### Layer 1: Self-Regulation (Fast Homeostasis)
*   **Process**: `process_dream_learning`
*   **Logic**: Proportional Control (Heuristic).
    *   If `Fire_Rate > Nightmare_Threshold`: **Aggressively Increase Thresholds**.
    *   Effect: Makes neurons "numb" immediately.

### Layer 2: Emergency Brake (Sanity Check)
*   **Process**: `process_dream_sanity_check`
*   **Logic**: If Layer 1 failed and the system is still in `Nightmare` state from the previous tick:
    *   **Action**: `Spike_Queue.clear()`
    *   **Effect**: Total blackout. Stops the seizure instantly.

## 3.3 The "Groggy" Effect (Wake-up Persistence)
An emergent phenomenon of State Persistence.

### The Phenomenon
1.  **Nightmare**: Agent raises thresholds significantly (`+0.05`) to suppress fear/overload.
2.  **Wake Up**: The system switches workflow (`agent_main.yaml`) **without resetting** neuron states.
3.  **Result**: The agent enters reality with "High Defense" (High Thresholds). It is unresponsive and sluggish.

### The Recovery
*   **Mechanism**: `process_meta_homeostasis_fixed` (PID Controller).
*   **Rate**: Very slow (`0.0001` per step).
*   **Duration**: It takes hundreds of ticks for the agent to "sober up" and return to peak performance.

## 3.4 Applications
1.  **Safety Training**: Learning to avoid "Lava" in dreams prevents burning in reality.
2.  **Prospective Memory**: Tagging synapses during dreams (`trace_slow`) primes them for rapid "One-Shot Learning" when the event actually occurs in reality (Dejà vu).
