"""
Profile Pipeline Performance
============================
Đo thời gian từng phase trong agent_step_pipeline để xác định bottleneck.
Chạy: .venv/Scripts/python.exe profile_pipeline.py
"""
import time
import numpy as np

# --- Setup minimal context ---
from src.core.context import SystemContext, GlobalContext, DomainContext
from src.core.snn_context_theus import SNNGlobalContext, create_snn_context_theus
from src.utils.shm_tensor_store import ShmTensorStore

def make_agent_ctx(agent_id=0):
    global_ctx = GlobalContext()
    domain_ctx = DomainContext(agent_id=agent_id)
    snn_global = SNNGlobalContext()
    snn_global.num_neurons = 1024
    snn_global.connectivity = 0.1
    snn_global.vector_dim = 16
    snn_global.seed = 42

    snn_ctx = create_snn_context_theus(
        num_neurons=snn_global.num_neurons,
        connectivity=snn_global.connectivity,
        vector_dim=snn_global.vector_dim,
        seed=snn_global.seed + agent_id,
        initial_threshold=0.05,
        tau_decay=0.9,
        threshold_min=0.01
    )
    snn_ctx.domain_ctx.heavy_tensors = ShmTensorStore(allocator=None, prefix=f"prof_{agent_id}")
    domain_ctx.snn_context = snn_ctx

    # Fake observation
    domain_ctx.current_observation = {
        'agent_pos': (0, 0),
        'step_count': 0,
        'sensor_vector': np.zeros(16, dtype=np.float32)
    }
    domain_ctx.previous_observation = None
    domain_ctx.last_action = 0
    domain_ctx.last_reward = {'extrinsic': -0.1, 'intrinsic': 0.0, 'total': -0.1}
    domain_ctx.td_error = 0.0
    domain_ctx.intrinsic_reward = 0.0
    domain_ctx.current_exploration_rate = 1.0
    domain_ctx.heavy_q_table = {}
    domain_ctx.heavy_snn_emotion_vector = None
    domain_ctx.heavy_previous_snn_emotion_vector = None
    domain_ctx.heavy_gated_network = None
    domain_ctx.heavy_gated_optimizer = None

    system_ctx = SystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)
    return system_ctx


def profile_phase(name, func, ctx, n=5):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            func(ctx)
        except Exception as e:
            print(f"  ⚠ {name} errored: {e}")
            break
        times.append(time.perf_counter() - t0)
    if times:
        print(f"  {name:45s}  avg={np.mean(times)*1000:8.2f}ms  max={np.max(times)*1000:8.2f}ms")
    return np.mean(times) if times else 0.0


print("=" * 70)
print("PROFILE: Agent Step Pipeline — 1024 neurons, connectivity=0.1")
print("=" * 70)

ctx = make_agent_ctx(0)

# Import processes
from src.processes.p1_perception import perception
from src.processes.snn_rl_bridge import compute_intrinsic_reward_snn, restore_snn_attention, modulate_snn_attention
from src.processes.snn_composite_theus import process_snn_cycle
from src.processes.snn_homeostasis_theus import process_homeostasis, process_meta_homeostasis_fixed
from src.processes.snn_commitment_theus import process_commitment
from src.processes.snn_advanced_features_theus import process_neural_darwinism, process_assimilate_ancestor
from src.processes.rl_processes import select_action_gated, update_q_learning
from src.processes.snn_social_quarantine_theus import process_inject_viral_with_quarantine, process_quarantine_validation
from src.processes.snn_resync_theus import process_periodic_resync
from src.processes.snn_recorder_process import process_record_snn_step
from src.core.snn_context_theus import sync_to_heavy_tensors, ensure_heavy_tensors_initialized
from src.processes.snn_core_theus import _integrate_impl, _fire_impl
from src.processes.snn_learning_theus import _clustering_impl
from src.processes.snn_learning_3factor_theus import _stdp_3factor_impl
from src.processes.snn_advanced_features_theus import _lateral_inhibition_vectorized

print("\n--- Từng process trong pipeline ---")
N_RUNS = 3  # Ít hơn để nhanh

# Warmup SNN tensors
ensure_heavy_tensors_initialized(ctx.domain_ctx.snn_context)
sync_to_heavy_tensors(ctx.domain_ctx.snn_context)

totals = {}
totals['perception']         = profile_phase("1. perception",              perception,                  ctx, N_RUNS)
totals['snn_cycle']          = profile_phase("4. process_snn_cycle (FULL)",process_snn_cycle,           ctx, N_RUNS)
totals['homeostasis']        = profile_phase("5. process_homeostasis",      process_homeostasis,         ctx, N_RUNS)
totals['commitment']         = profile_phase("6. process_commitment",       process_commitment,          ctx, N_RUNS)
totals['neural_darwinism']   = profile_phase("6b. process_neural_darwinism",process_neural_darwinism,   ctx, N_RUNS)
totals['select_action']      = profile_phase("7. select_action_gated",      select_action_gated,         ctx, N_RUNS)
totals['periodic_resync']    = profile_phase("8. process_periodic_resync",  process_periodic_resync,     ctx, N_RUNS)

print("\n--- Chi tiết bên trong SNN cycle (1 tick) ---")
totals['sync_to']    = profile_phase("  sync_to_heavy_tensors",   lambda c: sync_to_heavy_tensors(c.domain_ctx.snn_context),   ctx, N_RUNS)
totals['integrate']  = profile_phase("  _integrate_impl",          lambda c: _integrate_impl(c, sync=False),                    ctx, N_RUNS)
totals['fire']       = profile_phase("  _fire_impl",               lambda c: _fire_impl(c, sync=False),                         ctx, N_RUNS)
totals['clustering'] = profile_phase("  _clustering_impl",         _clustering_impl,                                            ctx, N_RUNS)
totals['stdp']       = profile_phase("  _stdp_3factor_impl",       _stdp_3factor_impl,                                          ctx, N_RUNS)
totals['lateral']    = profile_phase("  _lateral_inhibition",      _lateral_inhibition_vectorized,                              ctx, N_RUNS)

print("\n--- Ước tính thời gian 1 episode (500 steps × 5 agents) ---")
ticks = 10  # ticks_per_step
snn_tick_total = (totals['integrate'] + totals['fire'] + totals['clustering'] + totals['stdp'] + totals['lateral']) * ticks
snn_total = snn_tick_total + totals['sync_to'] * 2  # sync_to + sync_from
pipeline_per_step = (totals['perception'] + snn_total + totals['homeostasis'] +
                     totals['commitment'] + totals['select_action'])
episode_s = pipeline_per_step * 500 / 1000  # ms → s, 500 steps
print(f"  SNN per tick:          {(totals['integrate']+totals['fire']+totals['clustering']+totals['stdp']+totals['lateral'])*1000:.1f}ms")
print(f"  SNN per step (10tick): {snn_total*1000:.1f}ms")
print(f"  Pipeline per step:     {pipeline_per_step*1000:.1f}ms")
print(f"  Episode (500 steps):   {episode_s:.1f}s  ≈  {episode_s/60:.1f} min  (single agent)")
print(f"  Episode (5 agents parallel): {episode_s:.1f}s  ≈  {episode_s/60:.1f} min (nếu parallel perfect)")
print(f"\n  → Lý thuyết: {episode_s:.0f}s, thực tế: ~960s  (overhead factor: {960/episode_s:.1f}x)")
