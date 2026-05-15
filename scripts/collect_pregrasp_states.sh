#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
BEST_FILE="${PROJECT_DIR}/logs/plots/best_checkpoint.txt"
OUTPUT_FILE="${MT4_PREGRASP_STATE_OUTPUT:-${PROJECT_DIR}/data/pregrasp_states/latest.pt}"

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

TASK_NAME="Isaac-MT4-Simplified-Reach-Direct-v0"

if [[ -n "${MT4_POLICY_A_CHECKPOINT:-}" ]]; then
  CHECKPOINT_PATH="${MT4_POLICY_A_CHECKPOINT}"
else
  if [[ ! -s "${BEST_FILE}" ]]; then
    echo "[ERROR] No checkpoint was provided and best_checkpoint.txt is missing or empty:"
    echo "        ${BEST_FILE}"
    echo "        Run ${PROJECT_DIR}/scripts/plot_and_select_best.sh first, or set MT4_POLICY_A_CHECKPOINT."
    exit 1
  fi
  CHECKPOINT_PATH="$(tr -d '\r\n' < "${BEST_FILE}")"
fi

if [[ ! -f "${CHECKPOINT_PATH}" ]]; then
  echo "[ERROR] Policy checkpoint does not exist:"
  echo "        ${CHECKPOINT_PATH}"
  echo "        Set MT4_POLICY_A_CHECKPOINT to a valid model_*.pt file."
  exit 1
fi

echo "[INFO] Collecting pregrasp replay states for ${TASK_NAME}"
echo "[INFO] checkpoint=${CHECKPOINT_PATH}"
echo "[INFO] output=${OUTPUT_FILE}"

./isaaclab.sh -p "${PROJECT_DIR}/tools/collect_mt4_pregrasp_states.py" \
  --task "${TASK_NAME}" \
  --num_envs "${MT4_COLLECT_NUM_ENVS:-128}" \
  --max_steps "${MT4_COLLECT_MAX_STEPS:-20000}" \
  --min_states "${MT4_COLLECT_MIN_STATES:-512}" \
  --cooldown_steps "${MT4_COLLECT_COOLDOWN_STEPS:-20}" \
  --output "${OUTPUT_FILE}" \
  --checkpoint "${CHECKPOINT_PATH}" \
  --headless \
  "$@"
