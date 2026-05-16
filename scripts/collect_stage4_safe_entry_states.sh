#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
BEST_FILE="${PROJECT_DIR}/logs/plots/best_checkpoint.txt"
OUTPUT_FILE="${MT4_STAGE4_SAFE_ENTRY_OUTPUT:-${PROJECT_DIR}/data/stage4_safe_entry_states/latest.pt}"

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

TASK_NAME="Isaac-MT4-Simplified-Reach-Direct-v0"

if [[ -n "${MT4_STAGE4_SOURCE_CHECKPOINT:-}" ]]; then
  CHECKPOINT_PATH="${MT4_STAGE4_SOURCE_CHECKPOINT}"
else
  if [[ ! -s "${BEST_FILE}" ]]; then
    echo "[ERROR] No checkpoint was provided and best_checkpoint.txt is missing or empty:"
    echo "        ${BEST_FILE}"
    echo "        Run ${PROJECT_DIR}/scripts/plot_and_select_best.sh first, or set MT4_STAGE4_SOURCE_CHECKPOINT."
    exit 1
  fi
  CHECKPOINT_PATH="$(tr -d '\r\n' < "${BEST_FILE}")"
fi

if [[ ! -f "${CHECKPOINT_PATH}" ]]; then
  echo "[ERROR] Stage-4 source checkpoint does not exist:"
  echo "        ${CHECKPOINT_PATH}"
  exit 1
fi

echo "[INFO] Collecting safe Stage-4 entry replay states for ${TASK_NAME}"
echo "[INFO] checkpoint=${CHECKPOINT_PATH}"
echo "[INFO] output=${OUTPUT_FILE}"
echo "[INFO] filters: alignment>=${MT4_STAGE4_INSERTION_ALIGNMENT:-0.68}, progress=${MT4_STAGE4_MIN_INSERTION_PROGRESS:-0.10}-${MT4_STAGE4_MAX_INSERTION_PROGRESS:-0.70}, distance=${MT4_STAGE4_MIN_DISTANCE:-0.065}-${MT4_STAGE4_MAX_DISTANCE:-0.170}"

./isaaclab.sh -p "${PROJECT_DIR}/tools/collect_mt4_pregrasp_states.py" \
  --task "${TASK_NAME}" \
  --num_envs "${MT4_COLLECT_NUM_ENVS:-128}" \
  --max_steps "${MT4_COLLECT_MAX_STEPS:-30000}" \
  --min_states "${MT4_COLLECT_MIN_STATES:-512}" \
  --cooldown_steps "${MT4_COLLECT_COOLDOWN_STEPS:-16}" \
  --output "${OUTPUT_FILE}" \
  --checkpoint "${CHECKPOINT_PATH}" \
  --pregrasp_distance "${MT4_STAGE4_PREGRASP_DISTANCE:-0.200}" \
  --insertion_alignment "${MT4_STAGE4_INSERTION_ALIGNMENT:-0.68}" \
  --min_insertion_progress "${MT4_STAGE4_MIN_INSERTION_PROGRESS:-0.10}" \
  --max_insertion_progress "${MT4_STAGE4_MAX_INSERTION_PROGRESS:-0.70}" \
  --max_touch_error "${MT4_STAGE4_MAX_TOUCH_ERROR:-0.150}" \
  --min_distance "${MT4_STAGE4_MIN_DISTANCE:-0.065}" \
  --max_distance "${MT4_STAGE4_MAX_DISTANCE:-0.170}" \
  --target_contact_penalty "${MT4_STAGE4_TARGET_CONTACT_PENALTY:-0.0001}" \
  --allow_unheld \
  --headless \
  "$@"
