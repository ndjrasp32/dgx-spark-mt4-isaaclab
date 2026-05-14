#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
BEST_FILE="${PROJECT_DIR}/logs/plots/best_checkpoint.txt"

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

TASK_NAME="Isaac-MT4-Simplified-Reach-Direct-v0"

if [[ ! -s "${BEST_FILE}" ]]; then
  echo "[ERROR] Stage-B insertion training needs a starting checkpoint."
  echo "        best_checkpoint.txt was not found or is empty:"
  echo "        ${BEST_FILE}"
  echo "        Run a baseline first, then run:"
  echo "        ${PROJECT_DIR}/scripts/plot_and_select_best.sh"
  exit 1
fi

CHECKPOINT_PATH="$(tr -d '\r\n' < "${BEST_FILE}")"
if [[ ! -f "${CHECKPOINT_PATH}" ]]; then
  echo "[ERROR] The checkpoint recorded in best_checkpoint.txt does not exist:"
  echo "        ${CHECKPOINT_PATH}"
  echo "        Re-run ${PROJECT_DIR}/scripts/plot_and_select_best.sh after training logs are available."
  exit 1
fi

LOAD_RUN="$(basename "$(dirname "${CHECKPOINT_PATH}")")"
LOAD_CHECKPOINT="$(basename "${CHECKPOINT_PATH}")"

export MT4_REACH_TRAINING_MODE=stage_b_insertion

echo "[INFO] Stage-B insertion curriculum training for ${TASK_NAME}"
echo "[INFO] mode=${MT4_REACH_TRAINING_MODE}"
echo "[INFO] resume_run=${LOAD_RUN} checkpoint=${LOAD_CHECKPOINT}"
echo "[INFO] num_envs=128 max_iterations=500 headless=true"

./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
  --task "${TASK_NAME}" \
  --num_envs 128 \
  --max_iterations 500 \
  --headless \
  --resume \
  --load_run "${LOAD_RUN}" \
  --checkpoint "${LOAD_CHECKPOINT}" \
  "$@"
