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
  scripts/play_best_single.sh \
  scripts/kill_isaac_processes.sh \
  scripts/record_experiment_result.sh \
  scripts/tensorboard_mt4.sh \
  scripts/train_visual_16_300.sh \
  scripts/verify_before_push.sh

echo "[INFO] Checking Python syntax..."
"${ISAACLAB_DIR}/isaaclab.sh" -p -m py_compile "${PROJECT_DIR}/tools/record_mt4_experiment.py"
"${ISAACLAB_DIR}/isaaclab.sh" -p -m py_compile "${PROJECT_DIR}/tools/plot_mt4_training_and_checkpoints.py"
"${ISAACLAB_DIR}/isaaclab.sh" -p -m py_compile "${PROJECT_DIR}/tools/select_best_mt4_checkpoint.py"
"${ISAACLAB_DIR}/isaaclab.sh" -p -m py_compile "${PROJECT_DIR}/source/mt4_reach_direct/mt4_reach_env.py"

echo "[INFO] Running plot/select smoke test..."
scripts/plot_and_select_best.sh

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

echo "[OK] Verification complete. Review git diff, commit, then push origin main."
