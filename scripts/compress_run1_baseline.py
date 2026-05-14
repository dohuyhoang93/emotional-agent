"""
compress_run1_baseline.py
Nén kết quả Run 1 (trước khi fix penalty bug) thành baseline JSON nhỏ gọn.
Mục đích: có dữ liệu so sánh với Run 2 (sau fix).

Output: results/run1_before_fix_baseline.json
"""

import json
import statistics
from pathlib import Path

METRICS_PATH = Path("results/multi_agent_complex_maze/metrics.jsonl")
OUTPUT_PATH  = Path("results/run1_before_fix_baseline.json")
WINDOW       = 50  # episodes per summary window


def load_metrics(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            m = obj.get("metrics", {})
            rows.append({
                "ep":        obj["episode"],
                "ts":        obj.get("timestamp", ""),
                "reward":    m.get("avg_reward"),
                "success":   m.get("success_rate"),
                "q":         m.get("avg_q_predicted"),
                "loss":      m.get("neural_loss_avg"),
                "epsilon":   m.get("epsilon"),
                "firing":    m.get("avg_firing_rate"),
                "synapses":  m.get("debug_total_synapses"),
                "memory_mb": m.get("debug_process_memory_mb"),
            })
    return rows


def safe_stats(values: list) -> dict:
    vals = [v for v in values if v is not None]
    if not vals:
        return {"mean": None, "min": None, "max": None, "std": None}
    return {
        "mean": round(statistics.mean(vals), 4),
        "min":  round(min(vals), 4),
        "max":  round(max(vals), 4),
        "std":  round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0,
    }


def window_summaries(rows: list[dict], window: int) -> list[dict]:
    summaries = []
    for start in range(0, len(rows), window):
        chunk = rows[start: start + window]
        ep_start = chunk[0]["ep"]
        ep_end   = chunk[-1]["ep"]
        summaries.append({
            "ep_range":    f"{ep_start}-{ep_end}",
            "n_episodes":  len(chunk),
            "reward":      safe_stats([r["reward"]   for r in chunk]),
            "success_pct": safe_stats([r["success"]  for r in chunk]),
            "q_predicted": safe_stats([r["q"]        for r in chunk]),
            "loss":        safe_stats([r["loss"]      for r in chunk]),
            "epsilon":     safe_stats([r["epsilon"]   for r in chunk]),
            "firing_rate": safe_stats([r["firing"]    for r in chunk]),
            "synapses":    safe_stats([r["synapses"]  for r in chunk]),
        })
    return summaries


def detect_outliers(rows: list[dict]) -> list[dict]:
    """Episodes với |Q| > 50 hoặc reward > 0."""
    return [
        {"ep": r["ep"], "reward": r["reward"], "q": r["q"], "loss": r["loss"]}
        for r in rows
        if (r["q"] is not None and abs(r["q"]) > 50)
        or (r["reward"] is not None and r["reward"] > 0)
    ]


def main():
    print(f"[*] Đọc {METRICS_PATH} ...")
    rows = load_metrics(METRICS_PATH)
    print(f"    → {len(rows)} episodes")

    # --- Metadata ---
    total_eps   = len(rows)
    success_eps = sum(1 for r in rows if r["success"] and r["success"] > 0)
    final_eps   = rows[-1]["ep"]
    all_rewards = [r["reward"] for r in rows if r["reward"] is not None]
    all_success = [r["success"] for r in rows if r["success"] is not None]

    # --- Per-episode compact (key fields only) ---
    per_episode = [
        {
            "ep":      r["ep"],
            "reward":  round(r["reward"], 3)  if r["reward"]  is not None else None,
            "success": round(r["success"], 4) if r["success"] is not None else None,
            "q":       round(r["q"], 3)       if r["q"]       is not None else None,
            "loss":    round(r["loss"], 4)    if r["loss"]    is not None else None,
            "epsilon": round(r["epsilon"], 4) if r["epsilon"] is not None else None,
        }
        for r in rows
    ]

    # --- Windowed summaries ---
    windows = window_summaries(rows, WINDOW)

    # --- Outliers ---
    outliers = detect_outliers(rows)

    # --- Overall stats ---
    reward_by_phase = {}
    for phase_start in [0, 250, 500, 750, 1000, 1250, 1450]:
        phase_end = phase_start + 249
        chunk = [r["reward"] for r in rows
                 if phase_start <= r["ep"] <= phase_end and r["reward"] is not None]
        if chunk:
            reward_by_phase[f"ep_{phase_start}_{min(phase_end, final_eps)}"] = {
                "mean": round(statistics.mean(chunk), 3),
                "min":  round(min(chunk), 3),
                "max":  round(max(chunk), 3),
            }

    baseline = {
        "run_id":          "run1_before_penalty_fix",
        "run_date":        "2026-05-08",
        "fixed_in_commit": "env.py:247,296  step_penalty hardcode → self.step_penalty",
        "config": {
            "step_penalty_config":  -0.01,
            "step_penalty_actual":  -0.1,   # BUG: hardcoded
            "wall_penalty_config":  -0.1,
            "wall_penalty_actual":  -0.5,   # BUG: hardcoded
            "goal_reward":          10.0,
            "gate_open_reward":     1.0,
            "gate_close_penalty":  -1.2,
            "timeout_penalty":     -2.0,
            "max_steps":            500,
            "exploration_decay":    0.999,
            "num_agents":           1,
            "grid_size":           "25x25",
            "intrinsic_weight":     0.05,
        },
        "summary": {
            "total_episodes":          total_eps,
            "final_episode":           final_eps,
            "episodes_with_success":   success_eps,
            "overall_success_rate_pct": round(100 * sum(all_success) / len(all_success), 2),
            "reward_global":           safe_stats(all_rewards),
            "reward_first_100":        safe_stats([r["reward"] for r in rows[:100] if r["reward"] is not None]),
            "reward_last_100":         safe_stats([r["reward"] for r in rows[-100:] if r["reward"] is not None]),
            "reward_by_phase":         reward_by_phase,
            "q_value_global":          safe_stats([r["q"]    for r in rows if r["q"]    is not None]),
            "loss_global":             safe_stats([r["loss"] for r in rows if r["loss"] is not None]),
            "epsilon_range":           {
                "start": rows[0]["epsilon"],
                "end":   rows[-1]["epsilon"],
            },
            "synapse_range": {
                "min": min(r["synapses"] for r in rows if r["synapses"]),
                "max": max(r["synapses"] for r in rows if r["synapses"]),
            },
        },
        "outlier_episodes":   outliers,
        "windows_50ep":       windows,
        "per_episode":        per_episode,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False)

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"\n[✓] Baseline đã lưu: {OUTPUT_PATH}")
    print(f"    Kích thước: {size_kb:.1f} KB (so với 1,012 MB gốc)")
    print(f"\n=== TÓM TẮT RUN 1 (trước fix) ===")
    print(f"  Total episodes : {total_eps}")
    print(f"  Success rate   : {baseline['summary']['overall_success_rate_pct']}%")
    print(f"  Reward đầu 100 : mean={baseline['summary']['reward_first_100']['mean']}")
    print(f"  Reward cuối 100: mean={baseline['summary']['reward_last_100']['mean']}")
    print(f"  Q global       : mean={baseline['summary']['q_value_global']['mean']}")
    print(f"  Epsilon        : {baseline['summary']['epsilon_range']['start']:.4f} → {baseline['summary']['epsilon_range']['end']:.4f}")
    print(f"  Outlier eps    : {len(outliers)} (Q>50 hoặc reward>0)")


if __name__ == "__main__":
    main()
