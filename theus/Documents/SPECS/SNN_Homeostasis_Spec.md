# SNN Harmonic Homeostasis Specification

**Version:** 1.0  
**Date:** 2026-01-01  
**Author:** Theus Framework Team  
**Status:** Implemented

## Overview

Harmonic Homeostasis is a non-dualistic threshold regulation mechanism for Spiking Neural Networks (SNNs) that balances **Global Stability** (collective network health) with **Local Autonomy** (individual neuron specialization). This approach replaces the traditional binary choice between global-only or local-only homeostasis with a continuous, maturity-modulated blend.

## Theoretical Foundation

### Core Philosophy: Elastic Anchoring

The system implements a "birth-life-maturity" cycle where neurons:
1. **Birth:** Start with slight variance (±5%) to break initial symmetry
2. **Youth (S≈0):** Primarily follow global guidance while exploring via noise
3. **Maturity (S≈1):** Achieve autonomy, self-regulating based on local history

### Mathematical Model

#### Threshold Update Formula

$$\Delta T_i = w_{global} \cdot \Delta_{global} + w_{local} \cdot \Delta_{local,i} + \epsilon_i$$

Where:
- $w_{global} = 1 - w_{local}$
- $w_{local} = S_i + (1 - S_i) \cdot \beta_{base}$
- $S_i$: Solidity ratio (neuron maturity) ∈ [0, 1]
- $\beta_{base}$: Baseline local influence = 0.2
- $\epsilon_i$: Adaptive noise

#### Error Calculation

**Global Error (Scalar):**
$$E_{global} = \overline{FR}_{network} - FR_{target}$$

**Local Error (Vector):**
$$E_{local,i} = FR_{trace,i} - FR_{target}$$

Where $FR_{trace,i}$ is an exponential moving average:
$$FR_{trace,i}(t) = \tau \cdot FR_{trace,i}(t-1) + (1-\tau) \cdot spike_i(t)$$

#### Adaptive Noise

$$\epsilon_i \sim \mathcal{N}(0, \sigma_{noise} \cdot (1 - S_i))$$

Noise decreases with maturity, allowing young neurons to explore and mature neurons to stabilize.

## Implementation Details

### Hyperparameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `homeostasis_rate` | 0.0001 | Global adjustment rate |
| `local_homeostasis_rate` | 0.0005 | Local adjustment rate (faster) |
| `trace_decay` (τ) | 0.999 | Slow decay for stable local average |
| `base_local_influence` (β) | 0.2 | Minimum local weight for fluid neurons |
| `noise_scale` (σ) | 0.0001 | Base noise magnitude |
| `birth_variance` | ±5% | Initial threshold randomization |

### Vectorization Strategy

All operations are fully vectorized using NumPy for $O(N)$ complexity with minimal Python overhead:

```python
# 1. Update firing traces (Vector EMA)
spikes = (last_fire_times == current_time).astype(np.float32)
firing_traces[:] = decay * firing_traces + (1 - decay) * spikes

# 2. Calculate errors
error_global = np.mean(firing_traces) - target_fire_rate  # Scalar
error_local = firing_traces - target_fire_rate  # Vector

# 3. Compute weights
w_local = solidity + (1.0 - solidity) * base_local_influence
w_global = 1.0 - w_local

# 4. Blend adjustments
delta = w_global * (error_global * rate_global) + w_local * (error_local * rate_local)

# 5. Add adaptive noise
noise_scale = 0.0001 * (1.0 - solidity)
delta += np.random.normal(0, noise_scale, size=delta.shape)

# 6. Apply update
thresholds += delta
np.clip(thresholds, threshold_min, threshold_max, out=thresholds)
```

### Performance Characteristics

- **Complexity:** $O(N)$ per timestep
- **SIMD Optimization:** Utilizes AVX-512 on modern CPUs (16× parallelism for float32)
- **Scalability:** Tested up to 100,000 neurons with <1ms overhead per step

## Integration with Theus Framework

### Process Contract

```python
@process(
    inputs=[
        'domain_ctx.neurons',
        'domain_ctx.metrics.fire_rate',
        'global_ctx.target_fire_rate',
        'global_ctx.homeostasis_rate',
        'global_ctx.local_homeostasis_rate',
        'global_ctx.trace_decay',
        'global_ctx.threshold_min',
        'global_ctx.threshold_max',
        'domain_ctx.tensors'
    ],
    outputs=[
        'domain_ctx.neurons',
        'domain_ctx.tensors'
    ],
    side_effects=[]
)
def process_homeostasis(ctx: SNNSystemContext):
    # Implementation as shown above
```

### Data Structures

**New Tensors:**
- `firing_traces` (N,): Per-neuron firing rate history
- `solidity_ratios` (N,): Neuron maturity levels (if Phase 10.5 active)

**New Global Parameters:**
- `local_homeostasis_rate`: float
- `trace_decay`: float

## Behavioral Analysis

### Symmetry Breaking

The combination of birth variance and adaptive noise ensures threshold diversity:
1. **Initial:** Neurons start with thresholds in [0.57, 0.63] (assuming base=0.6)
2. **Early Training:** Noise dominates (S=0), creating exploration
3. **Convergence:** High-performing neurons solidify, low-performers remain fluid

### Stability Guarantees

- **Emergency Rescue:** If global firing rate < 1e-6, system resets all thresholds to minimum and injects noise
- **Clipping:** All thresholds bounded by [threshold_min, threshold_max]
- **Gradual Adaptation:** Small learning rates prevent oscillations

## Validation Metrics

Monitor these metrics to verify correct operation:
- `avg_threshold`: Should stabilize around initial value
- `std_threshold`: Should increase over time (diversity emerging)
- `fire_rate`: Should converge to `target_fire_rate`

## Future Extensions

1. **Solidity-Aware Learning:** Modulate STDP rates based on neuron maturity
2. **Meta-Homeostasis Integration:** PID controller for global parameters
3. **Multi-Timescale Traces:** Fast (20ms) and slow (5000ms) firing history

## References

- Turrigiano, G. (2008). "The Self-Tuning Neuron: Synaptic Scaling of Excitatory Synapses." *Cell*
- Kirkpatrick et al. (2017). "Overcoming catastrophic forgetting in neural networks." *PNAS* (EWC)
- Theus Framework Documentation: `/Documents/POP_specification.md`
