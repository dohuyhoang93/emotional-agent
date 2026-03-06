"""
Profiling Script — Agent Step Pipeline
=======================================
Đo thời gian thực tế từng process trong pipeline.

Chạy: py profiling_pipeline.py
Output: Bảng thống kê + tổng thời gian mỗi process

Author: Do Huy Hoang
Date: 2026-03-05
"""
import sys
import time
import numpy as np
import json
import functools

sys.path.append('.')

_timings = {}


def _timed(name, func):
    """Wrapper đo thời gian."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        dt = time.perf_counter() - t0
        _timings.setdefault(name, []).append(dt)
        return result
    return wrapper


def create_instrumented_pipeline():
    """
    Tạo pipeline function đã instrument.
    NOTE: Import trực tiếp functions và wrap mỗi cái,
    thay vì monkey-patch module (vì pipeline dùng local references).
    """
    from src.processes.p1_perception import perception
    from src.processes.snn_rl_bridge import compute_intrinsic_reward_snn, restore_snn_attention, modulate_snn_attention
    from src.processes.experimental.snn_safety_theus import monitor_safety_triggers
    from src.processes.snn_composite_theus import process_snn_cycle
    from src.processes.snn_homeostasis_theus import process_homeostasis, process_meta_homeostasis_fixed
    from src.processes.snn_commitment_theus import process_commitment
    from src.processes.snn_advanced_features_theus import process_neural_darwinism, process_assimilate_ancestor
    from src.processes.rl_processes import select_action_gated, update_q_learning
    from src.processes.snn_social_quarantine_theus import process_inject_viral_with_quarantine, process_quarantine_validation
    from src.processes.snn_resync_theus import process_periodic_resync
    from src.processes.rl_snn_integration import execute_action_with_env, combine_rewards
    from src.processes.snn_recorder_process import process_record_snn_step

    # Wrap mỗi function
    w_perception = _timed("1_perception", perception)
    w_safety = _timed("2_monitor_safety", monitor_safety_triggers)
    w_restore_att = _timed("3_restore_attention", restore_snn_attention)
    w_modulate_att = _timed("4_modulate_attention", modulate_snn_attention)
    w_snn_cycle = _timed("5_snn_cycle", process_snn_cycle)
    w_homeostasis = _timed("6_homeostasis", process_homeostasis)
    w_commitment = _timed("7_commitment", process_commitment)
    w_darwinism = _timed("8_darwinism", process_neural_darwinism)
    w_ancestor = _timed("9_ancestor", process_assimilate_ancestor)
    w_intrinsic = _timed("10_intrinsic_reward", compute_intrinsic_reward_snn)
    w_action = _timed("11_select_action", select_action_gated)
    w_viral = _timed("12_viral_inject", process_inject_viral_with_quarantine)
    w_quarantine = _timed("13_quarantine_valid", process_quarantine_validation)
    w_meta_homeo = _timed("14_meta_homeostasis", process_meta_homeostasis_fixed)
    w_resync = _timed("15_periodic_resync", process_periodic_resync)
    w_execute = _timed("16_execute_action", execute_action_with_env)
    w_combine = _timed("17_combine_rewards", combine_rewards)
    w_qlearn = _timed("18_update_q_learning", update_q_learning)
    w_record = _timed("19_record_step", process_record_snn_step)

    def instrumented_pipeline(ctx):
        w_perception(ctx)
        w_safety(ctx)
        w_restore_att(ctx)
        w_modulate_att(ctx)
        w_snn_cycle(ctx)
        w_homeostasis(ctx)
        w_commitment(ctx)
        w_darwinism(ctx)
        w_ancestor(ctx)
        w_intrinsic(ctx)
        w_action(ctx)
        w_viral(ctx)
        w_quarantine(ctx)
        w_meta_homeo(ctx)
        w_resync(ctx)
        w_execute(ctx)
        w_combine(ctx)
        w_qlearn(ctx)
        w_record(ctx)

    return instrumented_pipeline


def print_results(num_episodes, num_agents, max_steps):
    """In bảng thống kê."""
    print("\n" + "=" * 85)
    print(f"  PROFILING RESULTS ({num_episodes} ep × {num_agents} agents × {max_steps} steps)")
    print("=" * 85)

    total_all = 0
    rows = []
    for name, durations in sorted(_timings.items(), key=lambda x: -sum(x[1])):
        total = sum(durations)
        avg = total / len(durations) * 1000
        total_all += total
        rows.append((name, len(durations), avg, total))

    print(f"\n{'Process':<40} {'Calls':>8} {'Avg(ms)':>10} {'Total(s)':>10} {'%':>7}")
    print("-" * 85)
    for name, calls, avg_ms, total_s in rows:
        pct = total_s / total_all * 100 if total_all > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"{name:<40} {calls:>8} {avg_ms:>10.3f} {total_s:>10.3f} {pct:>6.1f}% {bar}")

    print("-" * 85)
    print(f"{'TOTAL':<40} {'':>8} {'':>10} {total_all:>10.3f}")

    # Tính avg per agent-step
    if rows:
        max_calls = max(r[1] for r in rows)
        if max_calls > 0:
            avg_per_step = total_all / max_calls * 1000
            print(f"\nAvg per agent-step (all processes): {avg_per_step:.1f} ms")
            print(f"Total pipeline time: {total_all:.2f}s")


def main():
    from src.coordination.multi_agent_coordinator import MultiAgentCoordinator
    from src.core.context import GlobalContext
    from src.core.snn_context_theus import SNNGlobalContext
    from src.adapters.environment_adapter import EnvironmentAdapter
    from environment import GridWorld

    # Load config
    with open('experiments.json', 'r') as f:
        config = json.load(f)
    exp = config['experiments'][0]
    params = exp['parameters']

    # Profiling settings: 2 episodes × 50 steps (đủ để đo)
    NUM_EPISODES = 2
    MAX_STEPS = 50
    NUM_AGENTS = params['num_agents']
    snn_cfg = params['snn_config']

    print(f"Profiling: {NUM_EPISODES} ep × {NUM_AGENTS} agents × {MAX_STEPS} steps")
    print(f"SNN: {snn_cfg['num_neurons']} neurons, connectivity={snn_cfg['connectivity']}")

    # Setup
    global_ctx = GlobalContext(
        initial_needs=[0.5, 0.5],
        initial_emotions=[0.0] * 16,
        total_episodes=NUM_EPISODES,
        max_steps=MAX_STEPS,
        seed=42,
        switch_locations={
            s['id']: tuple(s['pos'])
            for s in params['environment_config'].get('logical_switches', [])
        },
        initial_exploration_rate=params.get('initial_exploration', 1.0),
    )
    global_ctx.start_positions = params['environment_config'].get(
        'start_positions', [[0, 0]] * NUM_AGENTS
    )

    snn_global_ctx = SNNGlobalContext(
        num_neurons=snn_cfg['num_neurons'],
        vector_dim=snn_cfg.get('vector_dim', 16),
        connectivity=snn_cfg['connectivity'],
        seed=42
    )

    coordinator = MultiAgentCoordinator(
        num_agents=NUM_AGENTS,
        global_ctx=global_ctx,
        snn_global_ctx=snn_global_ctx
    )

    env = GridWorld({
        'initial_needs': [0.5, 0.5],
        'initial_emotions': [0.0] * 16,
        'switch_locations': global_ctx.switch_locations,
        'environment_config': params['environment_config']
    })
    adapter = EnvironmentAdapter(env)

    # NOTE: Patch pipeline trong RLAgent
    # RLAgent.step() gọi run_agent_step_pipeline.
    # Thay thế bằng instrumented version.
    instrumented = create_instrumented_pipeline()
    import src.processes.agent_step_pipeline as pipe_mod
    pipe_mod.run_agent_step_pipeline = instrumented

    # Run
    for ep in range(NUM_EPISODES):
        t0 = time.perf_counter()
        coordinator.run_episode(env, adapter)
        dt = time.perf_counter() - t0
        print(f"Episode {ep}: {dt:.2f}s")

    print_results(NUM_EPISODES, NUM_AGENTS, MAX_STEPS)

    # Cleanup
    coordinator.cleanup()


if __name__ == '__main__':
    main()
