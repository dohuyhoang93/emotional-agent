"""
SNN Dream Processes for Theus Framework
=======================================
Processes for managing inputs during Sleep/Dream state.

[INC-025 Fix] Removed all _target bypass patterns. All state mutations now
go through the ContextGuard proxy and are explicitly returned from each process.

Author: Theus Agent
Date: 2025-12-27
"""
import numpy as np
from theus.contracts import process
from src.core.context import SystemContext

@process(
    inputs=[
        'domain_ctx',
        'domain_ctx.snn_context',
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.snn_context.domain_ctx.current_time',
        'domain_ctx.snn_context.global_ctx.dream_noise_level',
    ],
    outputs=['domain_ctx.snn_context.domain_ctx.metrics'],
    side_effects=[]
)
def process_inject_dream_stimulus(ctx: SystemContext):
    """
    Stimulate neurons randomly to simulate 'REM' activity.

    [INC-025 Fix] Accesses snn_context via the standard ContextGuard API.
    Returns updated metrics explicitly so the Engine can track the delta.
    """
    try:
        result = _inject_impl(ctx)
        return result
    except Exception:
        import traceback
        import logging
        logging.getLogger("Theus").error(f"CRASH in process_inject_dream_stimulus: {traceback.format_exc()}")
        raise


def _inject_impl(ctx) -> dict:
    """
    Implementation for Dream Stimulus injection.

    [INC-025 Fix] Uses standard attribute access (ctx.domain_ctx.snn_context)
    instead of accessing ctx._target directly. If snn_context is None,
    raises AttributeError loudly instead of returning silently — consistent
    with the Strict Contract philosophy (INC-023).
    """
    # NOTE: Access via standard ContextGuard path. If snn_context is None here,
    # the Validator should have caught it before this point (INC-023).
    # We raise explicitly rather than returning silently (fail-loud principle).
    domain_ctx = ctx.domain_ctx
    if domain_ctx is None:
        raise AttributeError("process_inject_dream_stimulus: ctx.domain_ctx is None")

    snn_ctx = getattr(domain_ctx, 'snn_context', None)
    if snn_ctx is None:
        raise AttributeError(
            "process_inject_dream_stimulus: ctx.domain_ctx.snn_context is None. "
            "Ensure the snn_context is initialized before Dream phase begins."
        )

    snn_domain = snn_ctx.domain_ctx
    snn_global = snn_ctx.global_ctx

    noise_level = 0.1
    try:
        noise_level = float(getattr(snn_global, 'dream_noise_level', 0.1))
    except (TypeError, ValueError):
        import logging
        logging.getLogger("Theus").debug("dream_noise_level cast failed — using default 0.1")

    active_count = 0
    for neuron in snn_domain.neurons:
        # Random input current
        input_current = np.random.uniform(0, noise_level)

        # Possibility of 'burst' (PGO waves)
        if np.random.random() < 0.01:  # 1% chance of strong stimulus
            input_current += 0.5

        neuron.potential += input_current

        if input_current > 0.1:
            active_count += 1

    # NOTE: Return metrics explicitly so Engine registers the delta.
    # Previously this was written directly to _target and silently lost (INC-025).
    existing_metrics = dict(getattr(snn_domain, 'metrics', {}) or {})
    existing_metrics['dream_active_count'] = active_count
    return {'domain_ctx.snn_context.domain_ctx.metrics': existing_metrics}


@process(
    inputs=[
        'domain_ctx',
        'domain_ctx.snn_context',
        'domain_ctx.snn_context.domain_ctx.neurons',
        'domain_ctx.snn_context.domain_ctx.current_time',
        'domain_ctx.snn_context.domain_ctx.metrics',
        'domain_ctx.intrinsic_reward',
    ],
    outputs=[
        'domain_ctx.intrinsic_reward',
        'domain_ctx.snn_context.domain_ctx.metrics',
    ],
    side_effects=[]
)
def apply_dream_reward(ctx: SystemContext) -> dict:
    """
    Evaluate Dream Coherence and apply intrinsic reward/penalty.
    Used during SLEEP phase to reinforce stable patterns.

    Logic:
    - Goldilocks Zone (5% - 30% firing): Coherent (+0.1)
    - Silence (<5%): Boring (-0.2)
    - Epilepsy (>40%): Nightmare (-0.5)

    [INC-025 Fix] All mutations returned explicitly via dict.
    No _target bypass used.
    """
    # NOTE: Standard access via ContextGuard. If snn_context is None,
    # the Validator should have blocked execution (INC-023 + INC-025).
    snn_ctx = getattr(ctx.domain_ctx, 'snn_context', None)
    if snn_ctx is None:
        raise AttributeError(
            "apply_dream_reward: ctx.domain_ctx.snn_context is None. "
            "Cannot apply dream reward without SNN context."
        )

    snn_domain = snn_ctx.domain_ctx

    # Calculate Actual Firing Rate (Network Response)
    current_time = snn_domain.current_time
    active_neurons = 0
    for neuron in snn_domain.neurons:
        if neuron.last_fire_time == current_time:
            active_neurons += 1

    total_neurons = len(snn_domain.neurons)
    firing_rate = active_neurons / total_neurons if total_neurons > 0 else 0.0

    # Coherence Reward Logic
    if 0.05 <= firing_rate <= 0.3:
        reward = 0.1
        state = "COHERENT"
    elif firing_rate < 0.05:
        reward = -0.2
        state = "SILENCE"
    else:
        reward = -0.5
        state = "NIGHTMARE"

    # NOTE: Return ALL changed fields explicitly.
    # Previously, domain.metrics was written via _target and silently lost (INC-025).
    existing_metrics = dict(getattr(snn_domain, 'metrics', {}) or {})
    existing_metrics['dream_coherence_state'] = state
    existing_metrics['dream_firing_rate'] = firing_rate
    existing_metrics['dream_reward'] = reward

    return {
        'domain_ctx.intrinsic_reward': reward,
        'domain_ctx.snn_context.domain_ctx.metrics': existing_metrics,
    }
