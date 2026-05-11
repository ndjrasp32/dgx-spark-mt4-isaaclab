from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path


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
    "mean_distance",
    "min_distance",
    "mean_reward",
    "checkpoint_path",
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
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def main() -> None:
    args = parse_args()
    checkpoint_path = load_best_checkpoint()
    summary = load_summary_row(checkpoint_path)
    ensure_log_header()

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
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
        "mean_distance": summary.get("mean_distance", ""),
        "min_distance": summary.get("min_distance", ""),
        "mean_reward": summary.get("mean_reward", ""),
        "checkpoint_path": checkpoint_path,
        "reward_plot": str(PLOTS_DIR / "mt4_reward_curve.png"),
        "success_plot": str(PLOTS_DIR / "mt4_success_curve.png"),
        "distance_plot": str(PLOTS_DIR / "mt4_distance_curve.png"),
        "episode_length_plot": str(PLOTS_DIR / "mt4_episode_length_curve.png"),
    }

    with LOG_PATH.open("a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(row)

    print("[OK] recorded experiment row:")
    print(" log_path      =", LOG_PATH)
    print(" run_label     =", row["run_label"])
    print(" checkpoint    =", row["checkpoint"])
    print(" success_rate  =", row["success_rate"])
    print(" mean_distance =", row["mean_distance"])


if __name__ == "__main__":
    main()
