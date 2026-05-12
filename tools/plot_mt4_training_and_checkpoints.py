from pathlib import Path
import csv
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tensorboard.backend.event_processing import event_accumulator


LOG_ROOT = Path.home() / "work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct"
OUT_DIR = Path.home() / "work/robotarm/mt4_isaac_lab_task/logs/plots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 이번 추천 학습 기준: 64 env x 32 steps
# 다른 설정으로 학습했다면 이 값만 바꾸면 됨.
EXPECTED_STEPS_PER_ITER = 64 * 32


def latest_run_dir():
    ckpts = sorted(LOG_ROOT.rglob("model_*.pt"), key=lambda p: p.stat().st_mtime)
    if ckpts:
        return ckpts[-1].parent

    events = sorted(LOG_ROOT.rglob("events.out.tfevents.*"), key=lambda p: p.stat().st_mtime)
    if events:
        return events[-1].parent

    raise SystemExit(f"[ERROR] no checkpoints or tensorboard events under {LOG_ROOT}")


def load_events(run_dir):
    ea = event_accumulator.EventAccumulator(str(run_dir))
    ea.Reload()
    return ea


def scalar_tags(ea):
    return ea.Tags().get("scalars", [])


def find_tag(tags, candidates):
    for cand in candidates:
        for tag in tags:
            if cand.lower() in tag.lower():
                return tag
    return None


def get_series(ea, tag):
    if tag is None:
        return [], []
    events = ea.Scalars(tag)
    return [e.step for e in events], [e.value for e in events]


def plot_group(ea, tags, group_name, keyword_list):
    matched = []
    for tag in tags:
        low = tag.lower()
        if any(k.lower() in low for k in keyword_list):
            matched.append(tag)

    if not matched:
        print(f"[WARN] no tags matched for {group_name}")
        return

    plt.figure(figsize=(11, 5))

    for tag in matched:
        xs, ys = get_series(ea, tag)
        if xs:
            plt.plot(xs, ys, label=tag)

    plt.title(f"MT4 training curve: {group_name}")
    plt.xlabel("step")
    plt.ylabel(group_name)
    plt.grid(True)
    plt.legend()

    out = OUT_DIR / f"mt4_{group_name}_curve.png"
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    plt.close()
    print("[OK] wrote", out)


def parse_ckpt_iter(path):
    m = re.search(r"model_(\d+)\.pt$", path.name)
    if not m:
        return None
    return int(m.group(1))


def nearest_value(xs, ys, target_step):
    if not xs:
        return None, None
    idx = min(range(len(xs)), key=lambda i: abs(xs[i] - target_step))
    return xs[idx], ys[idx]


def checkpoint_summary(run_dir, ea, tags):
    ckpts = sorted(run_dir.glob("model_*.pt"), key=lambda p: parse_ckpt_iter(p) if parse_ckpt_iter(p) is not None else -1)
    if not ckpts:
        print("[WARN] no model_*.pt in latest run")
        return

    success_tag = find_tag(tags, ["mt4/success_rate", "success_rate", "success"])
    pregrasp_dist_tag = find_tag(tags, ["mt4/mean_pregrasp_distance", "mean_pregrasp_distance", "pregrasp_distance"])
    mean_dist_tag = find_tag(tags, ["mt4/mean_distance", "mean_distance"])
    alignment_tag = find_tag(tags, ["mt4/mean_alignment", "mean_alignment", "alignment"])
    min_dist_tag = find_tag(tags, ["mt4/min_distance", "min_distance"])
    reward_tag = find_tag(tags, ["Train/mean_reward", "mean_reward", "reward"])

    print("[INFO] selected tags:")
    print(" success   =", success_tag)
    print(" pregrasp  =", pregrasp_dist_tag)
    print(" mean_dist =", mean_dist_tag)
    print(" alignment =", alignment_tag)
    print(" min_dist  =", min_dist_tag)
    print(" reward    =", reward_tag)

    sx, sy = get_series(ea, success_tag)
    pdx, pdy = get_series(ea, pregrasp_dist_tag)
    mdx, mdy = get_series(ea, mean_dist_tag)
    ax, ay = get_series(ea, alignment_tag)
    mindx, mindy = get_series(ea, min_dist_tag)
    rx, ry = get_series(ea, reward_tag)

    # 자동 추정: scalar step이 iteration 번호인지 total step인지 판단
    max_ckpt_iter = max(parse_ckpt_iter(p) or 0 for p in ckpts)
    max_scalar_step = max(sx + pdx + mdx + ax + mindx + rx) if (sx + pdx + mdx + ax + mindx + rx) else 0

    if max_scalar_step > max(1000, max_ckpt_iter * 10):
        step_mode = "total_steps"
    else:
        step_mode = "iteration"

    rows = []

    for ckpt in ckpts:
        it = parse_ckpt_iter(ckpt)
        if it is None:
            continue

        if step_mode == "total_steps":
            target_step = it * EXPECTED_STEPS_PER_ITER
        else:
            target_step = it

        ss, sv = nearest_value(sx, sy, target_step)
        ps, pv = nearest_value(pdx, pdy, target_step)
        ms, mv = nearest_value(mdx, mdy, target_step)
        als, alv = nearest_value(ax, ay, target_step)
        mins, minv = nearest_value(mindx, mindy, target_step)
        rs, rv = nearest_value(rx, ry, target_step)

        rows.append({
            "checkpoint": ckpt.name,
            "iteration": it,
            "target_step": target_step,
            "nearest_success_step": ss,
            "success_rate": sv,
            "mean_pregrasp_distance": pv,
            "mean_distance": mv,
            "mean_alignment": alv,
            "min_distance": minv,
            "mean_reward": rv,
            "path": str(ckpt),
        })

    csv_path = OUT_DIR / "mt4_checkpoint_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("[OK] wrote", csv_path)

    # checkpoint success graph
    if any(r["success_rate"] is not None for r in rows):
        xs = [r["iteration"] for r in rows if r["success_rate"] is not None]
        ys = [r["success_rate"] for r in rows if r["success_rate"] is not None]

        plt.figure(figsize=(9, 5))
        plt.plot(xs, ys, marker="o")
        plt.title("MT4 checkpoint success rate")
        plt.xlabel("checkpoint iteration")
        plt.ylabel("success rate")
        plt.grid(True)
        out = OUT_DIR / "mt4_checkpoint_success_rate.png"
        plt.tight_layout()
        plt.savefig(out, dpi=160)
        plt.close()
        print("[OK] wrote", out)

    distance_key = "mean_pregrasp_distance" if any(r["mean_pregrasp_distance"] is not None for r in rows) else "mean_distance"

    if any(r[distance_key] is not None for r in rows):
        xs = [r["iteration"] for r in rows if r[distance_key] is not None]
        ys = [r[distance_key] for r in rows if r[distance_key] is not None]

        plt.figure(figsize=(9, 5))
        plt.plot(xs, ys, marker="o")
        plt.title(f"MT4 checkpoint {distance_key}")
        plt.xlabel("checkpoint iteration")
        plt.ylabel(distance_key)
        plt.grid(True)
        out = OUT_DIR / "mt4_checkpoint_mean_distance.png"
        plt.tight_layout()
        plt.savefig(out, dpi=160)
        plt.close()
        print("[OK] wrote", out)


def main():
    run_dir = latest_run_dir()
    print("[INFO] run_dir =", run_dir)

    ea = load_events(run_dir)
    tags = scalar_tags(ea)

    print("[INFO] scalar tags:")
    for tag in tags:
        print(" -", tag)

    plot_group(ea, tags, "reward", ["reward", "mean_reward"])
    plot_group(ea, tags, "success", ["success"])
    plot_group(ea, tags, "distance", ["distance"])
    plot_group(ea, tags, "episode_length", ["episode_length", "length"])

    checkpoint_summary(run_dir, ea, tags)


if __name__ == "__main__":
    main()
