from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path
import re


PROJECT_DIR = Path.home() / "work/robotarm/mt4_isaac_lab_task"
PLOTS_DIR = PROJECT_DIR / "logs/plots"
BEST_PATH = PLOTS_DIR / "best_checkpoint.txt"
SUMMARY_PATH = PLOTS_DIR / "mt4_checkpoint_summary.csv"
LOG_PATH = PROJECT_DIR / "experiments/mt4_reach_experiment_log.csv"

FIELDS = [
    "timestamp",
    "run_label",
    "seed",
    "num_envs",
    "max_iterations",
    "reward_profile",
    "action_penalty",
    "notes",
    "checkpoint",
    "checkpoint_iteration",
    "success_rate",
    "stage1_alignment_ready_rate",
    "pregrasp_entry_success_rate",
    "pregrasp_entry_ready_rate",
    "pregrasp_entry_reached_rate",
    "pregrasp_success_rate",
    "pregrasp_hold_ready_rate",
    "pregrasp_held_rate",
    "stage2_pregrasp_ready_rate",
    "stage2_alignment_ready_rate",
    "stage3_insertion_ready_rate",
    "stage3_touch_ready_rate",
    "stage4_center_ready_rate",
    "stage4_push_ready_rate",
    "mean_pregrasp_entry_distance",
    "mean_pregrasp_distance",
    "mean_gripper_center_pregrasp_distance",
    "mean_touch_error",
    "mean_distance",
    "mean_alignment",
    "mean_pregrasp_alignment",
    "mean_insertion_alignment",
    "mean_target_contact_penalty",
    "mean_pregrasp_center_progress",
    "mean_insertion_progress",
    "mean_center_push_progress",
    "mean_best_center_push_progress",
    "mean_center_push_improvement",
    "mean_best_target_center_distance",
    "mean_target_center_improvement",
    "mean_target_center_shell_improvement",
    "mean_center_shortest_path_score",
    "mean_pregrasp_line_error",
    "min_distance",
    "mean_reward",
    "checkpoint_path",
    "plot_snapshot_dir",
    "report_path",
    "metrics_csv_path",
    "reward_plot",
    "success_plot",
    "distance_plot",
    "episode_length_plot",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record the current MT4 reach best checkpoint into the experiment log.")
    parser.add_argument("--run-label", default="baseline", help="Short label for this experiment row.")
    parser.add_argument("--seed", default="42", help="Training seed used for the run.")
    parser.add_argument("--num-envs", default="128", help="Number of parallel environments.")
    parser.add_argument("--max-iterations", default="1000", help="Training iterations.")
    parser.add_argument("--reward-profile", default="baseline", help="Reward setting summary.")
    parser.add_argument("--action-penalty", default="0.01", help="Action penalty setting summary.")
    parser.add_argument("--notes", default="", help="Classroom observation notes.")
    return parser.parse_args()


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip().lower())
    slug = slug.strip("_")
    return slug or "experiment"


def run_timestamp_from_checkpoint(checkpoint_path: str, fallback: datetime) -> str:
    run_name = Path(checkpoint_path).parent.name
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})$", run_name)
    if match:
        year, month, day, hour, minute, second = match.groups()
        return f"{year}{month}{day}_{hour}{minute}{second}"
    return fallback.strftime("%Y%m%d_%H%M%S")


def find_plot_snapshot(checkpoint_path: str, timestamp_prefix: str) -> Path | None:
    checkpoint_parent = Path(checkpoint_path).parent
    candidates = sorted(
        [
            path
            for path in PLOTS_DIR.iterdir()
            if path.is_dir()
            and path.name.startswith(timestamp_prefix)
            and (path / "best_checkpoint.txt").is_file()
        ],
        key=lambda path: path.stat().st_mtime,
    )
    for path in reversed(candidates):
        best_text = (path / "best_checkpoint.txt").read_text(encoding="utf-8").strip()
        if best_text == checkpoint_path or Path(best_text).parent == checkpoint_parent:
            return path
    return candidates[-1] if candidates else None


def require_file(path: Path, message: str) -> None:
    if not path.exists():
        raise SystemExit(f"[ERROR] {message}\n        Expected path: {path}")
    if path.is_file() and path.stat().st_size == 0:
        raise SystemExit(f"[ERROR] file is empty: {path}")


def load_best_checkpoint() -> str:
    require_file(BEST_PATH, "best_checkpoint.txt was not found. Run scripts/plot_and_select_best.sh first.")
    checkpoint = BEST_PATH.read_text(encoding="utf-8").strip()
    if not checkpoint:
        raise SystemExit(f"[ERROR] best_checkpoint.txt is empty: {BEST_PATH}")
    if not Path(checkpoint).exists():
        raise SystemExit(
            "[ERROR] The checkpoint recorded in best_checkpoint.txt does not exist:\n"
            f"        {checkpoint}\n"
            "        Re-run scripts/plot_and_select_best.sh after training logs are available."
        )
    return checkpoint


def load_summary_row(checkpoint_path: str) -> dict[str, str]:
    require_file(SUMMARY_PATH, "checkpoint summary CSV was not found. Run scripts/plot_and_select_best.sh first.")
    with SUMMARY_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        if row.get("path") == checkpoint_path:
            return row

    checkpoint_name = Path(checkpoint_path).name
    for row in rows:
        if row.get("checkpoint") == checkpoint_name:
            return row

    raise SystemExit(
        "[ERROR] best checkpoint was not found in mt4_checkpoint_summary.csv:\n"
        f"        {checkpoint_path}\n"
        "        Re-run scripts/plot_and_select_best.sh to refresh the summary."
    )


def ensure_log_header() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0:
        with LOG_PATH.open("w", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n").writeheader()
        return

    with LOG_PATH.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
        existing_fields = list(rows[0].keys()) if rows else []

    if existing_fields == FIELDS:
        return

    with LOG_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def main() -> None:
    args = parse_args()
    checkpoint_path = load_best_checkpoint()
    summary = load_summary_row(checkpoint_path)
    ensure_log_header()
    now = datetime.now()
    timestamp = run_timestamp_from_checkpoint(checkpoint_path, now)
    run_slug = slugify(args.run_label)
    plot_snapshot_dir = find_plot_snapshot(checkpoint_path, timestamp)
    report_path = LOG_PATH.parent / f"{timestamp}_{run_slug}.md"
    metrics_csv_path = LOG_PATH.parent / f"{timestamp}_{run_slug}_metrics.csv"

    row = {
        "timestamp": now.isoformat(timespec="seconds"),
        "run_label": args.run_label,
        "seed": args.seed,
        "num_envs": args.num_envs,
        "max_iterations": args.max_iterations,
        "reward_profile": args.reward_profile,
        "action_penalty": args.action_penalty,
        "notes": args.notes,
        "checkpoint": summary.get("checkpoint", ""),
        "checkpoint_iteration": summary.get("iteration", ""),
        "success_rate": summary.get("success_rate", ""),
        "stage1_alignment_ready_rate": summary.get("stage1_alignment_ready_rate", ""),
        "pregrasp_entry_success_rate": summary.get("pregrasp_entry_success_rate", ""),
        "pregrasp_entry_ready_rate": summary.get("pregrasp_entry_ready_rate", ""),
        "pregrasp_entry_reached_rate": summary.get("pregrasp_entry_reached_rate", ""),
        "pregrasp_success_rate": summary.get("pregrasp_success_rate", ""),
        "pregrasp_hold_ready_rate": summary.get("pregrasp_hold_ready_rate", ""),
        "pregrasp_held_rate": summary.get("pregrasp_held_rate", ""),
        "stage2_pregrasp_ready_rate": summary.get("stage2_pregrasp_ready_rate", ""),
        "stage2_alignment_ready_rate": summary.get("stage2_alignment_ready_rate", ""),
        "stage3_insertion_ready_rate": summary.get("stage3_insertion_ready_rate", ""),
        "stage3_touch_ready_rate": summary.get("stage3_touch_ready_rate", ""),
        "stage4_center_ready_rate": summary.get("stage4_center_ready_rate", ""),
        "stage4_push_ready_rate": summary.get("stage4_push_ready_rate", ""),
        "mean_pregrasp_entry_distance": summary.get("mean_pregrasp_entry_distance", ""),
        "mean_pregrasp_distance": summary.get("mean_pregrasp_distance", ""),
        "mean_gripper_center_pregrasp_distance": summary.get("mean_gripper_center_pregrasp_distance", ""),
        "mean_touch_error": summary.get("mean_touch_error", ""),
        "mean_distance": summary.get("mean_distance", ""),
        "mean_alignment": summary.get("mean_alignment", ""),
        "mean_pregrasp_alignment": summary.get("mean_pregrasp_alignment", ""),
        "mean_insertion_alignment": summary.get("mean_insertion_alignment", ""),
        "mean_target_contact_penalty": summary.get("mean_target_contact_penalty", ""),
        "mean_pregrasp_center_progress": summary.get("mean_pregrasp_center_progress", ""),
        "mean_insertion_progress": summary.get("mean_insertion_progress", ""),
        "mean_center_push_progress": summary.get("mean_center_push_progress", ""),
        "mean_best_center_push_progress": summary.get("mean_best_center_push_progress", ""),
        "mean_center_push_improvement": summary.get("mean_center_push_improvement", ""),
        "mean_best_target_center_distance": summary.get("mean_best_target_center_distance", ""),
        "mean_target_center_improvement": summary.get("mean_target_center_improvement", ""),
        "mean_target_center_shell_improvement": summary.get("mean_target_center_shell_improvement", ""),
        "mean_center_shortest_path_score": summary.get("mean_center_shortest_path_score", ""),
        "mean_pregrasp_line_error": summary.get("mean_pregrasp_line_error", ""),
        "min_distance": summary.get("min_distance", ""),
        "mean_reward": summary.get("mean_reward", ""),
        "checkpoint_path": checkpoint_path,
        "plot_snapshot_dir": str(plot_snapshot_dir) if plot_snapshot_dir else "",
        "report_path": str(report_path),
        "metrics_csv_path": str(metrics_csv_path),
        "reward_plot": str((plot_snapshot_dir or PLOTS_DIR) / "mt4_reward_curve.png"),
        "success_plot": str((plot_snapshot_dir or PLOTS_DIR) / "mt4_success_curve.png"),
        "distance_plot": str((plot_snapshot_dir or PLOTS_DIR) / "mt4_distance_curve.png"),
        "episode_length_plot": str((plot_snapshot_dir or PLOTS_DIR) / "mt4_episode_length_curve.png"),
    }

    with LOG_PATH.open("a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n").writerow(row)

    with metrics_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)

    report_path.write_text(
        "\n".join(
            [
                f"# {timestamp} {args.run_label}",
                "",
                "## Summary",
                "",
                f"- timestamp: {row['timestamp']}",
                f"- checkpoint: `{row['checkpoint']}`",
                f"- checkpoint path: `{checkpoint_path}`",
                f"- plot snapshot: `{row['plot_snapshot_dir']}`" if row["plot_snapshot_dir"] else "- plot snapshot: latest only",
                f"- reward profile: `{row['reward_profile']}`",
                f"- notes: {row['notes'] or '(none)'}",
                "",
                "## Metrics",
                "",
                "| metric | value |",
                "|---|---:|",
                f"| success_rate | {row['success_rate']} |",
                f"| stage1_alignment_ready_rate | {row['stage1_alignment_ready_rate']} |",
                f"| pregrasp_entry_success_rate | {row['pregrasp_entry_success_rate']} |",
                f"| pregrasp_entry_ready_rate | {row['pregrasp_entry_ready_rate']} |",
                f"| pregrasp_entry_reached_rate | {row['pregrasp_entry_reached_rate']} |",
                f"| pregrasp_success_rate | {row['pregrasp_success_rate']} |",
                f"| pregrasp_hold_ready_rate | {row['pregrasp_hold_ready_rate']} |",
                f"| pregrasp_held_rate | {row['pregrasp_held_rate']} |",
                f"| stage2_pregrasp_ready_rate | {row['stage2_pregrasp_ready_rate']} |",
                f"| stage2_alignment_ready_rate | {row['stage2_alignment_ready_rate']} |",
                f"| stage3_insertion_ready_rate | {row['stage3_insertion_ready_rate']} |",
                f"| stage3_touch_ready_rate | {row['stage3_touch_ready_rate']} |",
                f"| stage4_center_ready_rate | {row['stage4_center_ready_rate']} |",
                f"| stage4_push_ready_rate | {row['stage4_push_ready_rate']} |",
                f"| mean_pregrasp_entry_distance | {row['mean_pregrasp_entry_distance']} |",
                f"| mean_pregrasp_distance | {row['mean_pregrasp_distance']} |",
                f"| mean_gripper_center_pregrasp_distance | {row['mean_gripper_center_pregrasp_distance']} |",
                f"| mean_touch_error | {row['mean_touch_error']} |",
                f"| mean_distance | {row['mean_distance']} |",
                f"| mean_insertion_alignment | {row['mean_insertion_alignment']} |",
                f"| mean_target_contact_penalty | {row['mean_target_contact_penalty']} |",
                f"| mean_pregrasp_center_progress | {row['mean_pregrasp_center_progress']} |",
                f"| mean_center_push_progress | {row['mean_center_push_progress']} |",
                f"| mean_best_center_push_progress | {row['mean_best_center_push_progress']} |",
                f"| mean_center_push_improvement | {row['mean_center_push_improvement']} |",
                f"| mean_best_target_center_distance | {row['mean_best_target_center_distance']} |",
                f"| mean_target_center_improvement | {row['mean_target_center_improvement']} |",
                f"| mean_target_center_shell_improvement | {row['mean_target_center_shell_improvement']} |",
                f"| mean_center_shortest_path_score | {row['mean_center_shortest_path_score']} |",
                f"| mean_pregrasp_line_error | {row['mean_pregrasp_line_error']} |",
                "",
                "## Interpretation",
                "",
                "- 선생님 관찰과 Codex 제안, 실제 그래프 해석은 이 아래에 이어서 적는다.",
                "- 다음 push 전에는 이 파일을 실험 기록의 고정 스냅샷으로 본다.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print("[OK] recorded experiment row:")
    print(" log_path      =", LOG_PATH)
    print(" report_path   =", report_path)
    print(" metrics_csv   =", metrics_csv_path)
    print(" plot_snapshot =", row["plot_snapshot_dir"])
    print(" run_label     =", row["run_label"])
    print(" checkpoint    =", row["checkpoint"])
    print(" success_rate  =", row["success_rate"])
    print(" stage1_ready  =", row["stage1_alignment_ready_rate"])
    print(" entry_succ    =", row["pregrasp_entry_success_rate"])
    print(" entry_ready   =", row["pregrasp_entry_ready_rate"])
    print(" entry_reached =", row["pregrasp_entry_reached_rate"])
    print(" pregrasp_succ =", row["pregrasp_success_rate"])
    print(" pregrasp_hold =", row["pregrasp_hold_ready_rate"])
    print(" pregrasp_held =", row["pregrasp_held_rate"])
    print(" stage2_pregrp =", row["stage2_pregrasp_ready_rate"])
    print(" stage2_ready  =", row["stage2_alignment_ready_rate"])
    print(" stage3_ready  =", row["stage3_insertion_ready_rate"])
    print(" stage3_touch  =", row["stage3_touch_ready_rate"])
    print(" stage4_center =", row["stage4_center_ready_rate"])
    print(" stage4_push   =", row["stage4_push_ready_rate"])
    print(" entry_dist    =", row["mean_pregrasp_entry_distance"])
    print(" pregrasp_dist =", row["mean_pregrasp_distance"])
    print(" touch_error   =", row["mean_touch_error"])
    print(" mean_distance =", row["mean_distance"])
    print(" push_progress =", row["mean_center_push_progress"])
    print(" best_push     =", row["mean_best_center_push_progress"])
    print(" push_improve  =", row["mean_center_push_improvement"])
    print(" shell_improve =", row["mean_target_center_shell_improvement"])
    print(" shortest_path =", row["mean_center_shortest_path_score"])
    print(" line_error    =", row["mean_pregrasp_line_error"])


if __name__ == "__main__":
    main()
