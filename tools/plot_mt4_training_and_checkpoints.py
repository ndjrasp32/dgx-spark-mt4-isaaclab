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
    pregrasp_success_tag = find_tag(tags, ["mt4/pregrasp_success_rate", "pregrasp_success_rate"])
    stage2_ready_tag = find_tag(tags, ["mt4/stage2_alignment_ready_rate", "stage2_alignment_ready_rate"])
    stage3_ready_tag = find_tag(tags, ["mt4/stage3_insertion_ready_rate", "stage3_insertion_ready_rate"])
    stage3_touch_ready_tag = find_tag(tags, ["mt4/stage3_touch_ready_rate", "stage3_touch_ready_rate"])
    pregrasp_dist_tag = find_tag(tags, ["mt4/mean_pregrasp_distance", "mean_pregrasp_distance", "pregrasp_distance"])
    touch_target_dist_tag = find_tag(tags, ["mt4/mean_touch_target_distance", "mean_touch_target_distance"])
    touch_error_tag = find_tag(tags, ["mt4/mean_touch_error", "mean_touch_error"])
    mean_dist_tag = find_tag(tags, ["mt4/mean_distance", "mean_distance"])
    insertion_lateral_tag = find_tag(tags, ["mt4/mean_insertion_lateral_error", "mean_insertion_lateral_error"])
    alignment_tag = find_tag(tags, ["mt4/mean_alignment", "mean_alignment", "alignment"])
    pregrasp_alignment_tag = find_tag(tags, ["mt4/mean_pregrasp_alignment", "mean_pregrasp_alignment"])
    insertion_alignment_tag = find_tag(tags, ["mt4/mean_insertion_alignment", "mean_insertion_alignment"])
    target_contact_tag = find_tag(tags, ["mt4/mean_target_contact_penalty", "mean_target_contact_penalty"])
    insertion_progress_tag = find_tag(tags, ["mt4/mean_insertion_progress", "mean_insertion_progress"])
    min_dist_tag = find_tag(tags, ["mt4/min_distance", "min_distance"])
    reward_tag = find_tag(tags, ["Train/mean_reward", "mean_reward", "reward"])

    print("[INFO] selected tags:")
    print(" success          =", success_tag)
    print(" pregrasp_success =", pregrasp_success_tag)
    print(" stage2_ready     =", stage2_ready_tag)
    print(" stage3_ready     =", stage3_ready_tag)
    print(" stage3_touch     =", stage3_touch_ready_tag)
    print(" pregrasp         =", pregrasp_dist_tag)
    print(" touch_target     =", touch_target_dist_tag)
    print(" touch_error      =", touch_error_tag)
    print(" mean_dist        =", mean_dist_tag)
    print(" lateral_error    =", insertion_lateral_tag)
    print(" alignment        =", alignment_tag)
    print(" pregrasp_align   =", pregrasp_alignment_tag)
    print(" insertion_align  =", insertion_alignment_tag)
    print(" contact_penalty  =", target_contact_tag)
    print(" insertion_prog   =", insertion_progress_tag)
    print(" min_dist         =", min_dist_tag)
    print(" reward           =", reward_tag)

    sx, sy = get_series(ea, success_tag)
    psx, psy = get_series(ea, pregrasp_success_tag)
    s2x, s2y = get_series(ea, stage2_ready_tag)
    s3x, s3y = get_series(ea, stage3_ready_tag)
    stx, sty = get_series(ea, stage3_touch_ready_tag)
    pdx, pdy = get_series(ea, pregrasp_dist_tag)
    tdx, tdy = get_series(ea, touch_target_dist_tag)
    tex, tey = get_series(ea, touch_error_tag)
    mdx, mdy = get_series(ea, mean_dist_tag)
    ilx, ily = get_series(ea, insertion_lateral_tag)
    ax, ay = get_series(ea, alignment_tag)
    pax, pay = get_series(ea, pregrasp_alignment_tag)
    iax, iay = get_series(ea, insertion_alignment_tag)
    tcx, tcy = get_series(ea, target_contact_tag)
    ipx, ipy = get_series(ea, insertion_progress_tag)
    mindx, mindy = get_series(ea, min_dist_tag)
    rx, ry = get_series(ea, reward_tag)

    # 자동 추정: scalar step이 iteration 번호인지 total step인지 판단
    max_ckpt_iter = max(parse_ckpt_iter(p) or 0 for p in ckpts)
    scalar_steps = sx + psx + s2x + s3x + stx + pdx + tdx + tex + mdx + ilx + ax + pax + iax + tcx + ipx + mindx + rx
    max_scalar_step = max(scalar_steps) if scalar_steps else 0

    if max_scalar_step > max(1000, max_ckpt_iter * 10):
        step_mode = "total_steps"
        steps_per_iter = max_scalar_step / max(max_ckpt_iter, 1)
    else:
        step_mode = "iteration"
        steps_per_iter = 1

    print("[INFO] checkpoint step mode =", step_mode)
    print("[INFO] estimated steps/iteration =", f"{steps_per_iter:.2f}")

    rows = []

    for ckpt in ckpts:
        it = parse_ckpt_iter(ckpt)
        if it is None:
            continue

        if step_mode == "total_steps":
            target_step = round(it * steps_per_iter)
        else:
            target_step = it

        ss, sv = nearest_value(sx, sy, target_step)
        pss, psv = nearest_value(psx, psy, target_step)
        s2s, s2v = nearest_value(s2x, s2y, target_step)
        s3s, s3v = nearest_value(s3x, s3y, target_step)
        sts, stv = nearest_value(stx, sty, target_step)
        ps, pv = nearest_value(pdx, pdy, target_step)
        tds, tdv = nearest_value(tdx, tdy, target_step)
        tes, tev = nearest_value(tex, tey, target_step)
        ms, mv = nearest_value(mdx, mdy, target_step)
        ils, ilv = nearest_value(ilx, ily, target_step)
        als, alv = nearest_value(ax, ay, target_step)
        pas, pav = nearest_value(pax, pay, target_step)
        ias, iav = nearest_value(iax, iay, target_step)
        tcs, tcv = nearest_value(tcx, tcy, target_step)
        ips, ipv = nearest_value(ipx, ipy, target_step)
        mins, minv = nearest_value(mindx, mindy, target_step)
        rs, rv = nearest_value(rx, ry, target_step)

        rows.append({
            "checkpoint": ckpt.name,
            "iteration": it,
            "target_step": target_step,
            "nearest_success_step": ss,
            "success_rate": sv,
            "pregrasp_success_rate": psv,
            "stage2_alignment_ready_rate": s2v,
            "stage3_insertion_ready_rate": s3v,
            "stage3_touch_ready_rate": stv,
            "mean_pregrasp_distance": pv,
            "mean_touch_target_distance": tdv,
            "mean_touch_error": tev,
            "mean_distance": mv,
            "mean_insertion_lateral_error": ilv,
            "mean_alignment": alv,
            "mean_pregrasp_alignment": pav,
            "mean_insertion_alignment": iav,
            "mean_target_contact_penalty": tcv,
            "mean_insertion_progress": ipv,
            "min_distance": minv,
            "mean_reward": rv,
            "path": str(ckpt),
        })

    csv_path = OUT_DIR / "mt4_checkpoint_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
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
    plot_group(ea, tags, "alignment", ["alignment"])
    plot_group(ea, tags, "touch_error", ["touch_error", "touch_target"])
    plot_group(ea, tags, "insertion_lateral_error", ["insertion_lateral_error"])
    plot_group(ea, tags, "stage", ["stage2", "stage3", "touch_ready", "insertion_progress", "pregrasp_success"])
    plot_group(ea, tags, "safety", ["object_overlap", "target_contact", "body_target_clearance"])
    plot_group(ea, tags, "episode_length", ["episode_length", "length"])

    checkpoint_summary(run_dir, ea, tags)


if __name__ == "__main__":
    main()
