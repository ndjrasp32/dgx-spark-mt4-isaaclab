#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
ISAACLAB_DIR="${HOME}/work/isaac/src/IsaacLab"
BEST_FILE="${PROJECT_DIR}/logs/plots/best_checkpoint.txt"

cd "${PROJECT_DIR}"
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

echo "[INFO] Verifying MT4 IsaacLab helper scripts..."

echo "[INFO] Checking shell syntax..."
bash -n scripts/train_128_1000.sh \
  scripts/plot_and_select_best.sh \
  scripts/play_best.sh \
  scripts/play_guided_blue_checkpoint.sh \
  scripts/play_best_single.sh \
  scripts/play_best_demo.sh \
  scripts/kill_isaac_processes.sh \
  scripts/record_experiment_result.sh \
  scripts/tensorboard_mt4.sh \
  scripts/collect_pregrasp_states.sh \
  scripts/collect_stage4_center_states.sh \
  scripts/train_visual_16_300.sh \
  scripts/train_stage_b_insertion_128_500.sh \
  scripts/train_stage_b_replay_reset_128_500.sh \
  scripts/train_stage4_center_replay_128_300.sh \
  scripts/train_stage4_center_push_replay_128_250.sh \
  scripts/train_stage4_push_strong_replay_128_300.sh \
  scripts/train_stage4_relaxed_success_128_300.sh \
  scripts/train_stage4_time_pressure_visual_16_120.sh \
  scripts/train_stage4_weighted_balance_128_300.sh \
  scripts/train_stage4_near_terminal_128_300.sh \
  scripts/train_stage4_latched_progressive_128_300.sh \
  scripts/train_stage4_guided_blue_128_300.sh \
  scripts/train_stage4_blue_center_128_300.sh \
  scripts/play_stage4_blue_center_best.sh \
  scripts/train_stage4_center_visual_low_exploration_16_120.sh \
  scripts/copy_latest_training_video_lowres.sh \
  scripts/verify_before_push.sh

echo "[INFO] Checking Python syntax..."
"${ISAACLAB_DIR}/isaaclab.sh" -p -m py_compile "${PROJECT_DIR}/tools/record_mt4_experiment.py"
"${ISAACLAB_DIR}/isaaclab.sh" -p -m py_compile "${PROJECT_DIR}/tools/plot_mt4_training_and_checkpoints.py"
"${ISAACLAB_DIR}/isaaclab.sh" -p -m py_compile "${PROJECT_DIR}/tools/select_best_mt4_checkpoint.py"
"${ISAACLAB_DIR}/isaaclab.sh" -p -m py_compile "${PROJECT_DIR}/tools/collect_mt4_pregrasp_states.py"
"${ISAACLAB_DIR}/isaaclab.sh" -p -m py_compile "${PROJECT_DIR}/source/mt4_reach_direct/mt4_reach_env.py"

echo "[INFO] Running plot/select smoke test..."
MT4_SKIP_PLOT_SNAPSHOT=1 scripts/plot_and_select_best.sh

if [[ ! -s "${BEST_FILE}" ]]; then
  echo "[ERROR] best_checkpoint.txt was not created or is empty."
  echo "        Expected path: ${BEST_FILE}"
  echo "        Train first, then run scripts/plot_and_select_best.sh."
  exit 1
fi

CHECKPOINT="$(tr -d '\r\n' < "${BEST_FILE}")"

if [[ -z "${CHECKPOINT}" ]]; then
  echo "[ERROR] best_checkpoint.txt is empty."
  echo "        Expected path: ${BEST_FILE}"
  exit 1
fi

if [[ ! -f "${CHECKPOINT}" ]]; then
  echo "[ERROR] The selected checkpoint does not exist:"
  echo "        ${CHECKPOINT}"
  echo "        Re-run scripts/plot_and_select_best.sh after training logs are available."
  exit 1
fi

echo "[OK] Selected checkpoint exists:"
echo "     ${CHECKPOINT}"

echo "[INFO] Git status:"
git status --short

echo "[INFO] Git diff summary:"
git diff --stat

BRANCH="$(git branch --show-current)"
if [[ -z "${BRANCH}" ]]; then
  BRANCH="<current-branch>"
fi

echo "[OK] Verification complete. Review git diff, commit, then push origin ${BRANCH}."
