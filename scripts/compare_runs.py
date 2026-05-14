"""
Compare Run 1 (pre-fix) vs Run 2 (post-fix) learning performance.
Usage: python scripts/compare_runs.py
"""
import json
import statistics

# --- Load Run 2 data (nested metrics schema) ---
run2 = []
with open("results/multi_agent_complex_maze/metrics.jsonl") as f:
    for line in f:
        ep = json.loads(line.strip())
        m = ep.get("metrics", {})
        run2.append(
            {
                "ep": ep["episode"],
                "reward": m.get("avg_reward", 0),
                "success": m.get("success_rate", 0) > 0,
                "epsilon": m.get("epsilon"),
                "q": m.get("avg_q_predicted"),
                "loss": m.get("neural_loss_avg"),
                "firing_rate": m.get("avg_firing_rate"),
                "synapses": m.get("debug_total_synapses"),
                "steps": m.get("steps_per_episode"),
            }
        )

# --- Load Run 1 baseline ---
with open("results/run1_before_fix_baseline.json") as f:
    run1_baseline = json.load(f)
run1_all = run1_baseline.get("per_episode", [])
max_ep = run2[-1]["ep"]
run1 = [ep for ep in run1_all if ep["ep"] <= max_ep]

W = "=" * 60
print(W)
print("LEARNING PERFORMANCE COMPARISON: RUN 1 vs RUN 2")
print(W)
print(f"  Run 1: pre-fix  (ep 0-{max_ep})  | {len(run1)} eps")
print(f"  Run 2: post-fix (ep 0-{max_ep})  | {len(run2)} eps")
print()

# --- Success Rate ---
r1_succ = sum(1 for ep in run1 if ep.get("success", False))
r2_succ = sum(1 for ep in run2 if ep["success"])
print("SUCCESSES")
pct1 = r1_succ / len(run1) * 100
pct2 = r2_succ / len(run2) * 100
print(f"  Run 1: {r1_succ} ({pct1:.1f}%)")
print(f"  Run 2: {r2_succ} ({pct2:.1f}%)")

# --- Reward ---
r1_rew = [ep["reward"] for ep in run1]
r2_rew = [ep["reward"] for ep in run2]
print()
print("REWARD (avg_reward per episode)")
print(
    f"  Run 1: mean={statistics.mean(r1_rew):.2f}  "
    f"min={min(r1_rew):.2f}  max={max(r1_rew):.2f}  "
    f"stdev={statistics.stdev(r1_rew):.2f}"
)
print(
    f"  Run 2: mean={statistics.mean(r2_rew):.2f}  "
    f"min={min(r2_rew):.2f}  max={max(r2_rew):.2f}  "
    f"stdev={statistics.stdev(r2_rew):.2f}"
)
delta_mean = statistics.mean(r2_rew) - statistics.mean(r1_rew)
sign = "+" if delta_mean >= 0 else ""
print(f"  Delta: {sign}{delta_mean:.2f} reward/ep")

# --- Q-Value ---
r1_q_vals = [ep.get("q_max", ep.get("q")) for ep in run1]
r1_q = [v for v in r1_q_vals if v is not None]
r2_q = [ep["q"] for ep in run2 if ep["q"] is not None]
print()
print("Q-VALUE (avg predicted)")
if r1_q:
    print(f"  Run 1: mean={statistics.mean(r1_q):.2f}  stdev={statistics.stdev(r1_q):.2f}")
else:
    print("  Run 1: N/A")
if r2_q:
    print(f"  Run 2: mean={statistics.mean(r2_q):.2f}  stdev={statistics.stdev(r2_q):.2f}")
else:
    print("  Run 2: N/A")

# --- Neural Loss ---
r1_loss = [ep.get("loss") for ep in run1 if ep.get("loss") is not None]
r2_loss = [ep["loss"] for ep in run2 if ep["loss"] is not None]
print()
print("NEURAL LOSS (GatedNet)")
if r1_loss:
    print(f"  Run 1: mean={statistics.mean(r1_loss):.4f}  max={max(r1_loss):.4f}")
else:
    print("  Run 1: N/A (not logged)")
if r2_loss:
    print(f"  Run 2: mean={statistics.mean(r2_loss):.4f}  max={max(r2_loss):.4f}")
else:
    print("  Run 2: N/A")

# --- Epsilon ---
r1_eps = [ep.get("epsilon") for ep in run1 if ep.get("epsilon") is not None]
r2_eps = [ep["epsilon"] for ep in run2 if ep["epsilon"] is not None]
print()
print("EPSILON (exploration rate)")
if r1_eps:
    print(f"  Run 1: {max(r1_eps):.3f} -> {min(r1_eps):.3f}")
if r2_eps:
    print(f"  Run 2: {max(r2_eps):.3f} -> {min(r2_eps):.3f}")

# --- SNN state ---
r2_fire = [ep["firing_rate"] for ep in run2 if ep["firing_rate"] is not None]
r2_syn = [ep["synapses"] for ep in run2 if ep["synapses"] is not None]
print()
print("SNN STATE (Run 2)")
if r2_fire:
    print(f"  Firing rate: {r2_fire[0]:.4f} -> {r2_fire[-1]:.4f}  (target=0.130)")
if r2_syn:
    print(f"  Synapses:    {r2_syn[0]:,} -> {r2_syn[-1]:,}  (delta={r2_syn[-1]-r2_syn[0]:+,})")

# --- Windowed reward trend ---
print()
print("REWARD TREND (25-ep windows)")
header = f"  {'Window':<12} {'Run1 avg':>10} {'Run2 avg':>10} {'Delta':>10}  {'Verdict'}"
print(header)
print("  " + "-" * 60)
for w in range(0, max_ep + 1, 25):
    chunk_r1 = [ep["reward"] for ep in run1 if w <= ep["ep"] < w + 25]
    chunk_r2 = [ep["reward"] for ep in run2 if w <= ep["ep"] < w + 25]
    if not chunk_r1 or not chunk_r2:
        continue
    avg1 = statistics.mean(chunk_r1)
    avg2 = statistics.mean(chunk_r2)
    delta = avg2 - avg1
    sign = "+" if delta >= 0 else ""
    verdict = "BETTER" if delta > 5 else ("WORSE" if delta < -5 else "~same")
    print(
        f"  ep {w:3d}-{w + 24:<3d}    {avg1:>10.2f} {avg2:>10.2f} {sign}{delta:>9.2f}  {verdict}"
    )

# --- Recent trajectory (last 25 eps of Run 2) ---
recent_r2 = run2[-25:]
recent_reward = [ep["reward"] for ep in recent_r2]
recent_loss = [ep["loss"] for ep in recent_r2 if ep["loss"] is not None]
recent_q = [ep["q"] for ep in recent_r2 if ep["q"] is not None]
print()
print(f"RECENT TRAJECTORY (last 25 eps of Run 2, ep {recent_r2[0]['ep']}-{recent_r2[-1]['ep']})")
print(f"  Reward: mean={statistics.mean(recent_reward):.2f}  trend: {recent_reward[0]:.2f} -> {recent_reward[-1]:.2f}")
if recent_loss:
    print(f"  Loss:   mean={statistics.mean(recent_loss):.4f}")
if recent_q:
    print(f"  Q:      mean={statistics.mean(recent_q):.2f}")

print()
print(W)
