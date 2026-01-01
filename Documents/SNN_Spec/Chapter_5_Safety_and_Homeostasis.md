# Chapter 5: Physiological Homeostasis & Dampening

**Scope**: Regulating the "Temperature" and "Energy" of the brain.

> [!IMPORTANT]
> **Implementation Status**: All safety mechanisms are **FULLY IMPLEMENTED** as of 2025-12-30.

---

## 5.1 Emotional Safety Valve (Hysteria Dampener)

**Process**: `process_hysteria_dampener`  
**File**: `src/processes/snn_advanced_features_theus.py::process_hysteria_dampener` (Lines 39-82)  
**Status**: ✅ **IMPLEMENTED**

This prevents "Epileptic Seizures" (Runaway Positive Feedback Loops) where the network fires uncontrollably.

### Mechanism

*   **Monitor**: `fire_rate` (Global metric).
*   **Trigger**: If `fire_rate > saturation_threshold` (e.g., > 30%).
*   **Dampening Action**:
    *   **Emergency Brake**: Immediately increases all neuron thresholds by `dampening_factor`.
    *   **Effect**: The network becomes "Numb" instantly. Firing stops.
*   **Recovery**: The thresholds slowly decay back to baseline via meta-homeostasis.

**Implementation**:
```python
def process_hysteria_dampener(ctx: SystemContext):
    """Emergency brake for runaway firing."""
    snn_ctx = ctx.domain_ctx.snn_context
    metrics = snn_ctx.domain_ctx.metrics
    
    # Get current fire rate
    current_fire_rate = metrics.get('fire_rate', 0.0)
    
    # Panic threshold
    panic_threshold = 0.3  # 30% activity
    dampening_factor = 0.05  # 5% threshold increase
    
    if current_fire_rate > panic_threshold:
        # Emergency: Raise all thresholds
        for neuron in snn_ctx.domain_ctx.neurons:
            neuron.threshold += dampening_factor
        
        metrics['hysteria_dampener_triggered'] = True
        metrics['dampener_count'] = metrics.get('dampener_count', 0) + 1
```

**Hyperparameters**:
- `panic_threshold`: 0.3 (30% firing rate)
- `dampening_factor`: 0.05 (5% threshold boost)

---

## 5.2 Physiological Balance (PID Homeostasis)

**Process**: `process_meta_homeostasis_fixed`  
**File**: `src/processes/snn_homeostasis_theus.py::process_meta_homeostasis_fixed` (Lines 138-220)  
**Status**: ✅ **IMPLEMENTED**

The long-term regulator that maintains the optimal cognitive load.

### Mechanism: PID Controller

*   **Goal**: Keep the firing rate near a Target (e.g., 5%).
*   **Mechanism**: PID Controller (Proportional-Integral-Derivative).
    *   **P (React)**: Adjusts threshold based on immediate error.
    *   **I (Bias)**: Corrects long-term drift (e.g., if the agent is chronically lazy, `I` builds up to force it to be active).
    *   **D (Predict)**: Prevents overshoot (e.g., stops lowering threshold *before* the agent goes crazy).
*   **Result**: Ensures the agent is neither "Comatose" (0 spikes) nor "Hyperactive" (All spikes) over long periods.

**Implementation**:
```python
def process_meta_homeostasis_fixed(ctx: SNNSystemContext):
    """PID controller for long-term firing rate homeostasis."""
    domain = ctx.domain_ctx
    global_ctx = ctx.global_ctx
    
    # Target firing rate
    target_rate = global_ctx.target_firing_rate  # 0.05 (5%)
    
    # Current firing rate
    current_rate = domain.metrics.get('fire_rate', 0.0)
    
    # Error
    error = target_rate - current_rate
    
    # PID terms
    kp = global_ctx.homeostasis_kp  # 0.001 (Proportional gain)
    ki = global_ctx.homeostasis_ki  # 0.0001 (Integral gain)
    kd = global_ctx.homeostasis_kd  # 0.0005 (Derivative gain)
    
    # Integral accumulation
    if not hasattr(domain, 'error_integral'):
        domain.error_integral = 0.0
    domain.error_integral += error
    
    # Derivative (change in error)
    if not hasattr(domain, 'prev_error'):
        domain.prev_error = 0.0
    error_derivative = error - domain.prev_error
    domain.prev_error = error
    
    # PID output
    adjustment = (
        kp * error +
        ki * domain.error_integral +
        kd * error_derivative
    )
    
    # Apply to all neurons
    for neuron in domain.neurons:
        neuron.threshold -= adjustment  # Lower threshold if firing too low
        
        # Clamp to safe range
        neuron.threshold = max(0.1, min(neuron.threshold, 2.0))
    
    # Metrics
    domain.metrics['homeostasis_adjustment'] = adjustment
    domain.metrics['error_integral'] = domain.error_integral
```

**Hyperparameters**:
- `target_firing_rate`: 0.05 (5%)
- `kp`: 0.001 (proportional gain)
- `ki`: 0.0001 (integral gain)
- `kd`: 0.0005 (derivative gain)
- `threshold_min`: 0.1
- `threshold_max`: 2.0

**PID Formula**:
```
adjustment = Kp * error + Ki * ∫error dt + Kd * d(error)/dt

where:
  error = target_rate - current_rate
  ∫error dt = cumulative error (integral)
  d(error)/dt = rate of change (derivative)
```

---

## 5.3 Cognitive Focus (Lateral Inhibition)

**Process**: `process_lateral_inhibition`  
**File**: `src/processes/snn_advanced_features_theus.py::process_lateral_inhibition` (Lines 102-125)  
**Status**: ✅ **IMPLEMENTED** (Vectorized)

A mechanism to enforce **Sparse Coding** and reduce noise.

### Mechanism: Winner-Take-All (WTA)

*   **Logic**:
    *   In any processing tick, only the **Top-K** strongest neurons are allowed to "speak".
    *   The "Losers" are actively inhibited (Potential -= Inhibition).

**Implementation** (Vectorized):
```python
def _lateral_inhibition_vectorized(ctx: SystemContext):
    """Winner-Take-All lateral inhibition."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    from src.core.snn_context_theus import ensure_tensors_initialized
    ensure_tensors_initialized(snn_ctx)
    
    t = snn_ctx.domain_ctx.tensors
    potentials = t['potentials']  # (N,)
    
    # Get WTA parameters
    wta_k = snn_ctx.global_ctx.wta_k  # Top-K (e.g., 10)
    inhibition_strength = snn_ctx.global_ctx.inhibition_strength  # 0.1
    
    # Find top-K neurons
    top_k_indices = np.argsort(potentials)[-wta_k:]
    
    # Create inhibition mask (all neurons except top-K)
    inhibition_mask = np.ones(len(potentials), dtype=bool)
    inhibition_mask[top_k_indices] = False
    
    # Apply inhibition to losers
    potentials[inhibition_mask] -= inhibition_strength
    
    # Clamp to non-negative
    potentials[inhibition_mask] = np.maximum(0.0, potentials[inhibition_mask])
    
    # Metrics
    snn_ctx.domain_ctx.metrics['inhibited_neurons'] = np.sum(inhibition_mask)
```

**Hyperparameters**:
- `wta_k`: 10 (top-K winners)
- `inhibition_strength`: 0.1 (penalty for losers)


> [!IMPORTANT]
> **Design Note: Feed-Forward Priority**
> The Lateral Inhibition mechanism operates on the **Spike Queue** (delayed activity). 
> However, **Sensory Input** is often injected directly into Potentials (Feed-Forward bypass).
> 
> **Consequence**: Fresh sensory inputs can "bypass" the inhibition check in the same timestep they arrive. 
> This is a deliberate design choice to prioritize **Bottom-Up Perception** over **Internal Stability**. 
> - Input Strength (e.g., 1.5) usually exceeds Inhibition Strength (e.g., 0.2).
> - This ensures the SNN remains responsive to the environment even under heavy suppression.

---

## 5.4 Structural Optimization (Neural Darwinism)

**Process**: `process_neural_darwinism`  
**File**: `src/processes/snn_advanced_features_theus.py::process_neural_darwinism` (Lines 127-210)  
**Status**: ✅ **IMPLEMENTED**

> [!NOTE]
> This section is covered in detail in **Chapter 2: Learning Mechanisms (Section 2.4)** and **Chapter 6: Population and Evolution**.

Beyond adjusting weights (STDP), the brain actively reshapes its architecture.

*   **Unit of Selection**: The Synapse.
*   **Mechanism**:
    1.  **Fitness Tracking**: Synapses gain fitness for active participation in rewards, lose fitness for inactivity or errors.
    2.  **Selection (The Reaper)**: Periodically, the bottom `X%` of synapses are pruned (Death).
    3.  **Reproduction (Cloning)**: The top `Y%` of synapses are cloned and mutated slightly (Birth).

**Brief Implementation**:
```python
def process_neural_darwinism(ctx: SystemContext):
    """Evolutionary pruning and recycling."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    # Prune weak synapses
    for synapse in list(snn_ctx.domain_ctx.synapses):
        if synapse.commit_state == COMMIT_STATE_REVOKED:
            snn_ctx.domain_ctx.synapses.remove(synapse)
        elif synapse.weight < prune_threshold:
            snn_ctx.domain_ctx.synapses.remove(synapse)
    
    # Recycle dead neurons
    for neuron in snn_ctx.domain_ctx.neurons:
        if neuron.fire_count == 0 and has_no_solid_connections(neuron):
            # Reset
            neuron.prototype_vector = random_unit_vector(16)
            neuron.fire_count = 0
```

---

## 5.5 Maintenance (Numerical Resync)

**Process**: `process_periodic_resync`  
**File**: `src/processes/snn_resync_theus.py::process_periodic_resync` (Lines 14-78)  
**Status**: ✅ **IMPLEMENTED**

Digital systems suffer from **Floating Point Drift**.

*   **Problem**: After millions of additions (integrations), tiny errors (`1e-16`) accumulate, eventually causing neurons to "ignite" spontaneously.
*   **Mechanism**: Periodic Garbage Collection (Every 1000 steps).
    *   Scans all neurons.
    *   If `|potential| < 1e-6`, force it to `0.0`.
    *   Re-normalizes vector prototypes to ensure length `1.0`.
*   **Analogy**: "Sleep Cleaning" or "Defragging" the brain.

**Implementation**:
```python
def process_periodic_resync(ctx: SNNSystemContext):
    """Periodic Resync - Fix numerical drift."""
    domain = ctx.domain_ctx
    global_ctx = ctx.global_ctx
    
    # Run every 1000 steps
    if domain.current_time % 1000 != 0:
        return
    
    resync_count = 0
    
    for neuron in domain.neurons:
        # Reset tiny potentials to 0
        if abs(neuron.potential) < 1e-6:
            neuron.potential = 0.0
            resync_count += 1
        
        # Reset tiny potential_vector elements
        neuron.potential_vector[np.abs(neuron.potential_vector) < 1e-6] = 0.0
        
        # Normalize prototype_vector
        norm = np.linalg.norm(neuron.prototype_vector)
        if norm > 0:
            neuron.prototype_vector /= norm
        else:
            # Reset if zero vector
            neuron.prototype_vector = np.random.randn(neuron.vector_dim)
            neuron.prototype_vector /= np.linalg.norm(neuron.prototype_vector)
            resync_count += 1
        
        # Clamp threshold
        neuron.threshold = np.clip(
            neuron.threshold,
            global_ctx.threshold_min,
            global_ctx.threshold_max
        )
    
    # Update metrics
    domain.metrics['resync_count'] += 1
    domain.metrics['resync_neurons'] = resync_count
```

**Hyperparameters**:
- `resync_interval`: 1000 steps
- `potential_threshold`: 1e-6 (cleanup threshold)
- `vector_threshold`: 1e-6 (cleanup threshold)

> [!NOTE]
> **Usage**: This process should be added to workflows that run for extended periods (>10,000 steps) to prevent numerical drift. It's particularly important for dream cycles and long-running experiments.

---

## 5.6 Implementation Status Summary

| Mechanism | Status | File | Notes |
|-----------|--------|------|-------|
| **Hysteria Dampener** | ✅ Implemented | `snn_advanced_features_theus.py` | Emergency brake |
| **PID Homeostasis** | ✅ Implemented | `snn_homeostasis_theus.py` | Long-term regulation |
| **Lateral Inhibition** | ✅ Implemented | `snn_advanced_features_theus.py` | WTA sparse coding |
| **Neural Darwinism** | ✅ Implemented | `snn_advanced_features_theus.py` | Structural evolution |
| **Periodic Resync** | ✅ Implemented | `snn_resync_theus.py` | Numerical cleanup |

---

## 5.7 Safety Hierarchy

The system has **3 layers of protection**:

```
Layer 1: Lateral Inhibition (Every Step)
├─ Prevents noise amplification
└─ Enforces sparse coding

Layer 2: Hysteria Dampener (Reactive)
├─ Triggers when fire_rate > 30%
└─ Emergency threshold boost

Layer 3: PID Homeostasis (Continuous)
├─ Maintains target fire_rate (5%)
└─ Gradual threshold adjustment
```

**Interaction**:
1. **Normal**: PID keeps firing at 5%
2. **Spike**: Hysteria dampener kicks in at 30%
3. **Recovery**: PID gradually lowers thresholds back to baseline

---

## 5.8 Hyperparameters Summary

| Parameter | Value | Description |
|-----------|-------|-------------|
| `panic_threshold` | 0.3 | Hysteria trigger (30%) |
| `dampening_factor` | 0.05 | Emergency threshold boost |
| `target_firing_rate` | 0.05 | PID target (5%) |
| `homeostasis_kp` | 0.001 | Proportional gain |
| `homeostasis_ki` | 0.0001 | Integral gain |
| `homeostasis_kd` | 0.0005 | Derivative gain |
| `wta_k` | 10 | Top-K winners |
| `inhibition_strength` | 0.1 | Lateral inhibition penalty |

---

## 5.9 Harmonic Homeostasis (Elastic Anchoring)

**Process**: `process_homeostasis`  
**File**: `src/processes/snn_homeostasis_theus.py::process_homeostasis` (Lines 14-143)  
**Status**: ✅ **IMPLEMENTED** (2026-01-01)

**Philosophy**: Non-dualistic threshold regulation that balances **Global Stability** (collective network health) with **Local Autonomy** (individual neuron specialization).

### Problem Statement

Traditional homeostasis mechanisms face a dilemma:
- **Global-only**: All neurons receive identical updates → No diversity, uniform thresholds
- **Local-only**: Neurons self-regulate independently → Network instability, potential collapse

**Harmonic Homeostasis** rejects this binary choice, implementing **both** with dynamic balance modulated by neuron maturity (Solidity).

### Mechanism: Elastic Anchoring

The system implements a "birth-life-maturity" cycle:

1. **Birth (±5% Variance)**
   - Neurons initialize with `threshold = base × uniform(0.95, 1.05)`
   - Breaks initial symmetry
   
2. **Youth (S≈0): Guided Exploration**
   - 80% Global influence (stability)
   - 20% Local influence (baseline personality)
   - High adaptive noise (exploration)
   
3. **Maturity (S≈1): Autonomous Specialization**
   - 0% Global influence
   - 100% Local influence
   - Minimal noise (stability)

### Mathematical Model

#### Threshold Update Formula

$$\Delta T_i = w_{global} \cdot \Delta_{global} + w_{local} \cdot \Delta_{local,i} + \epsilon_i$$

**Weight Calculation:**
```
w_local = S_i + (1 - S_i) × β_base
w_global = 1 - w_local

where:
  S_i: Solidity ratio (neuron maturity) ∈ [0, 1]
  β_base: Baseline local influence = 0.2
```

**Error Terms:**
```
E_global = mean(FR_traces) - FR_target  (Scalar)
E_local,i = FR_trace,i - FR_target      (Vector)

Δ_global = E_global × rate_global
Δ_local,i = E_local,i × rate_local
```

**Adaptive Noise:**
```
ε_i ~ N(0, σ_noise × (1 - S_i))

Young neurons (S=0): Full noise → Exploration
Mature neurons (S=1): No noise → Stability
```

### Implementation (Vectorized)

```python
def process_homeostasis(ctx: SNNSystemContext):
    """Harmonic Homeostasis with Elastic Anchoring."""
    
    # 1. Update firing traces (Exponential Moving Average)
    spikes = (last_fire_times == current_time).astype(np.float32)
    firing_traces[:] = decay * firing_traces + (1 - decay) * spikes
    
    # 2. Calculate errors
    error_global = np.mean(firing_traces) - target_fire_rate  # Scalar
    error_local = firing_traces - target_fire_rate  # Vector (N,)
    
    # 3. Compute weights (with baseline plasticity)
    w_local = solidity + (1.0 - solidity) * base_local_influence  # (N,)
    w_global = 1.0 - w_local
    
    # 4. Blend adjustments
    adjustment_global = error_global * rate_global
    adjustment_local = error_local * rate_local
    delta = w_global * adjustment_global + w_local * adjustment_local
    
    # 5. Add adaptive noise (decreases with maturity)
    noise_scale = 0.0001 * (1.0 - solidity)
    delta += np.random.normal(0, noise_scale, size=delta.shape)
    
    # 6. Apply update
    thresholds += delta
    np.clip(thresholds, threshold_min, threshold_max, out=thresholds)
```

### Hyperparameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `homeostasis_rate` | 0.0001 | Global adjustment rate |
| `local_homeostasis_rate` | 0.0005 | Local adjustment rate (faster) |
| `trace_decay` (τ) | 0.999 | Slow decay for stable local average |
| `base_local_influence` (β) | 0.2 | Minimum local weight for fluid neurons |
| `noise_scale` (σ) | 0.0001 | Base noise magnitude |
| `birth_variance` | ±5% | Initial threshold randomization |

### Performance Characteristics

- **Complexity:** O(N) per timestep
- **SIMD Optimization:** AVX-512 support (16× parallelism for float32)
- **Memory:** +8 bytes/neuron for `firing_traces` tensor
- **Overhead:** <1ms for 100,000 neurons

### Design Rationale

**Why not pure Local?**
- Young neurons lack history → Would drift randomly
- Network-wide collapse possible without global anchor

**Why not pure Global?**
- Prevents specialization → All neurons identical
- Wastes neural capacity → No functional diversity

**Why Harmonic (Both)?**
- **Emergence:** Diversity arises naturally from simple rules + noise
- **Stability:** Global anchor prevents catastrophic failure
- **Efficiency:** Mature neurons optimize for their niche
- **Biological Plausibility:** Mirrors developmental neuroscience

### Validation Metrics

Monitor these to verify correct operation:
- `avg_threshold`: Should stabilize around initial value (0.6)
- `std_threshold`: Should **increase** over time (diversity emerging)
- `fire_rate`: Should converge to `target_fire_rate` (0.02)

### Integration Notes

**Solidity Source:**
- If Phase 10.5 (Derived Commitment) is active: Uses `solidity_ratios` tensor
- Otherwise: Defaults to `zeros_like(thresholds)` (all fluid)

**Emergency Rescue:**
- If global firing rate < 1e-6: Reset all thresholds to minimum + inject noise
- Prevents "network death" scenarios

---

> [!NOTE]
> **Related Chapters**:
> - Chapter 2: Learning Mechanisms (Neural Darwinism details)
> - Chapter 3: Dream Architecture (Hysteria dampener in dreams)
> - Chapter 6: Population and Evolution (Darwinism details)
