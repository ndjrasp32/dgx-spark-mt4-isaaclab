#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
BEST_FILE="${PROJECT_DIR}/logs/plots/best_checkpoint.txt"
STATE_FILE="${MT4_REACH_STAGE4_STATE_FILE:-${PROJECT_DIR}/data/stage4_center_states/latest.pt}"

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

TASK_NAME="Isaac-MT4-Simplified-Reach-Direct-v0"

if [[ ! -s "${BEST_FILE}" ]]; then
  echo "[ERROR] Stage-4 center training needs a starting checkpoint."
  echo "        best_checkpoint.txt was not found or is empty:"
  echo "        ${BEST_FILE}"
  echo "        Run ${PROJECT_DIR}/scripts/plot_and_select_best.sh first."
  exit 1
fi

if [[ ! -f "${STATE_FILE}" ]]; then
  echo "[ERROR] Stage-4 replay state file does not exist:"
  echo "        ${STATE_FILE}"
  echo "        Run ${PROJECT_DIR}/scripts/collect_stage4_center_states.sh first."
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

export MT4_REACH_TRAINING_MODE=stage4_center
export MT4_REACH_RESET_MODE=pregrasp_replay
export MT4_REACH_PREGRASP_STATE_FILE="${STATE_FILE}"
export MT4_REACH_REPLAY_PROB="${MT4_REACH_REPLAY_PROB:-0.90}"
export MT4_REACH_REPLAY_JOINT_NOISE="${MT4_REACH_REPLAY_JOINT_NOISE:-0.008}"
export MT4_REACH_REPLAY_TARGET_NOISE="${MT4_REACH_REPLAY_TARGET_NOISE:-0.002}"
export MT4_REACH_REPLAY_JOINT_VELOCITY_SCALE="${MT4_REACH_REPLAY_JOINT_VELOCITY_SCALE:-0.12}"
export MT4_REACH_FINAL_CENTER_RADIUS="${MT4_REACH_FINAL_CENTER_RADIUS:-0.035}"

echo "[INFO] Stage-4 center replay-reset curriculum training for ${TASK_NAME}"
echo "[INFO] mode=${MT4_REACH_TRAINING_MODE} reset=${MT4_REACH_RESET_MODE}"
echo "[INFO] replay_state_file=${MT4_REACH_PREGRASP_STATE_FILE}"
echo "[INFO] replay_prob=${MT4_REACH_REPLAY_PROB} joint_noise=${MT4_REACH_REPLAY_JOINT_NOISE} target_noise=${MT4_REACH_REPLAY_TARGET_NOISE}"
echo "[INFO] final_center_radius=${MT4_REACH_FINAL_CENTER_RADIUS}"
echo "[INFO] resume_run=${LOAD_RUN} checkpoint=${LOAD_CHECKPOINT}"
echo "[INFO] num_envs=128 max_iterations=300 headless=true"

./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
  --task "${TASK_NAME}" \
  --num_envs 128 \
  --max_iterations 300 \
  --headless \
  --resume \
  --load_run "${LOAD_RUN}" \
  --checkpoint "${LOAD_CHECKPOINT}" \
  "$@"
