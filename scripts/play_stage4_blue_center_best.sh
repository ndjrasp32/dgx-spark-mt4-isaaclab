#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
BEST_FILE="${PROJECT_DIR}/logs/plots/best_checkpoint.txt"
STATE_FILE="${MT4_REACH_STAGE4_STATE_FILE:-${PROJECT_DIR}/data/stage4_center_states/latest.pt}"

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
export DISPLAY=:1
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

TASK_NAME="Isaac-MT4-Simplified-Reach-Direct-v0"
DEMO_SECONDS="${DEMO_SECONDS:-120}"

if [[ ! -s "${BEST_FILE}" ]]; then
  echo "[ERROR] best_checkpoint.txt was not found or is empty."
  echo "        Expected path: ${BEST_FILE}"
  echo "        Run plot_and_select_best.sh after training first."
  exit 1
fi

if [[ ! -f "${STATE_FILE}" ]]; then
  echo "[ERROR] Stage-4 replay state file does not exist:"
  echo "        ${STATE_FILE}"
  echo "        Run ${PROJECT_DIR}/scripts/collect_stage4_center_states.sh first."
  exit 1
fi

CHECKPOINT="$(tr -d '\r\n' < "${BEST_FILE}")"
if [[ ! -f "${CHECKPOINT}" ]]; then
  echo "[ERROR] The checkpoint recorded in best_checkpoint.txt does not exist:"
  echo "        ${CHECKPOINT}"
  echo "        Re-run plot_and_select_best.sh to refresh the selected checkpoint."
  exit 1
fi

if command -v xdpyinfo >/dev/null 2>&1 && ! xdpyinfo -display "${DISPLAY}" >/dev/null 2>&1; then
  echo "[WARN] DISPLAY=${DISPLAY} is not accessible from this shell."
  echo "       If you are using VNC, run this in the VNC terminal first:"
  echo "       xhost +SI:localuser:${USER}"
fi

export MT4_REACH_TRAINING_MODE=stage4_center
export MT4_REACH_RESET_MODE=pregrasp_replay
export MT4_REACH_PREGRASP_STATE_FILE="${STATE_FILE}"
export MT4_REACH_REPLAY_PROB="${MT4_REACH_REPLAY_PROB:-0.96}"
export MT4_REACH_REPLAY_JOINT_NOISE="${MT4_REACH_REPLAY_JOINT_NOISE:-0.002}"
export MT4_REACH_REPLAY_TARGET_NOISE="${MT4_REACH_REPLAY_TARGET_NOISE:-0.0005}"
export MT4_REACH_REPLAY_JOINT_VELOCITY_SCALE="${MT4_REACH_REPLAY_JOINT_VELOCITY_SCALE:-0.04}"
export MT4_REACH_MOVING_PREGRASP="${MT4_REACH_MOVING_PREGRASP:-1}"
export MT4_REACH_MOVING_PREGRASP_GOAL="${MT4_REACH_MOVING_PREGRASP_GOAL:-center}"
export MT4_REACH_MOVING_PREGRASP_STEPS="${MT4_REACH_MOVING_PREGRASP_STEPS:-5}"
export MT4_REACH_MOVING_PREGRASP_FINAL_FRACTION="${MT4_REACH_MOVING_PREGRASP_FINAL_FRACTION:-1.0}"
export MT4_REACH_MOVING_PREGRASP_STEP_RADIUS="${MT4_REACH_MOVING_PREGRASP_STEP_RADIUS:-0.018}"
export MT4_REACH_MOVING_PREGRASP_HOLD_STEPS="${MT4_REACH_MOVING_PREGRASP_HOLD_STEPS:-8}"
export MT4_REACH_MOVING_PREGRASP_REWARD_WEIGHT="${MT4_REACH_MOVING_PREGRASP_REWARD_WEIGHT:-18.0}"
export MT4_REACH_DESIRED_TOUCH_DISTANCE="${MT4_REACH_DESIRED_TOUCH_DISTANCE:-0.0}"
export MT4_REACH_FINAL_INSERTION_WEIGHT="${MT4_REACH_FINAL_INSERTION_WEIGHT:-32.0}"
export MT4_REACH_FINAL_CENTER_RADIUS="${MT4_REACH_FINAL_CENTER_RADIUS:-0.050}"
export MT4_REACH_NEAR_TERMINAL_RADIUS="${MT4_REACH_NEAR_TERMINAL_RADIUS:-0.060}"
export MT4_REACH_NEAR_TERMINAL_WEIGHT="${MT4_REACH_NEAR_TERMINAL_WEIGHT:-5.0}"
export MT4_REACH_STAGE_LATCH_WEIGHT="${MT4_REACH_STAGE_LATCH_WEIGHT:-0.6}"
export MT4_REACH_PROGRESSIVE_STAGE_WEIGHT="${MT4_REACH_PROGRESSIVE_STAGE_WEIGHT:-0.35}"
export MT4_REACH_ACTION_SCALE="${MT4_REACH_ACTION_SCALE:-0.024}"
export MT4_REACH_ACTION_PENALTY="${MT4_REACH_ACTION_PENALTY:-0.020}"
export MT4_REACH_STAGE4_PUSH_WEIGHT="${MT4_REACH_STAGE4_PUSH_WEIGHT:-64.0}"
export MT4_REACH_STAGE4_PUSH_IMPROVEMENT_WEIGHT="${MT4_REACH_STAGE4_PUSH_IMPROVEMENT_WEIGHT:-100.0}"
export MT4_REACH_STAGE4_PUSH_DEPTH_WEIGHT="${MT4_REACH_STAGE4_PUSH_DEPTH_WEIGHT:-40.0}"
export MT4_REACH_STAGE4_SHORTEST_PATH_WEIGHT="${MT4_REACH_STAGE4_SHORTEST_PATH_WEIGHT:-48.0}"
export MT4_REACH_STAGE4_DISTANCE_SHELL_WEIGHT="${MT4_REACH_STAGE4_DISTANCE_SHELL_WEIGHT:-40.0}"
export MT4_REACH_STAGE4_TIME_PENALTY="${MT4_REACH_STAGE4_TIME_PENALTY:-0.080}"
export MT4_REACH_STAGE3_TIME_PRESERVE_WEIGHT="${MT4_REACH_STAGE3_TIME_PRESERVE_WEIGHT:-0.6}"
export MT4_REACH_TERMINAL_SUCCESS_QUALITY_WEIGHT="${MT4_REACH_TERMINAL_SUCCESS_QUALITY_WEIGHT:-20.0}"
export MT4_REACH_SUCCESS_BONUS="${MT4_REACH_SUCCESS_BONUS:-72.0}"
export MT4_REACH_CENTER_PUSH_IMPROVEMENT_SCALE="${MT4_REACH_CENTER_PUSH_IMPROVEMENT_SCALE:-0.008}"
export MT4_REACH_CENTER_DISTANCE_SHELL_SIZE="${MT4_REACH_CENTER_DISTANCE_SHELL_SIZE:-0.005}"
export MT4_REACH_STAGE4_PUSH_READY_PROGRESS="${MT4_REACH_STAGE4_PUSH_READY_PROGRESS:-0.70}"

echo "[INFO] Playing blue-center Stage-4 checkpoint for ${TASK_NAME}"
echo "[INFO] checkpoint=${CHECKPOINT}"
echo "[INFO] moving_pregrasp goal=${MT4_REACH_MOVING_PREGRASP_GOAL} steps=${MT4_REACH_MOVING_PREGRASP_STEPS} radius=${MT4_REACH_MOVING_PREGRASP_STEP_RADIUS} hold_steps=${MT4_REACH_MOVING_PREGRASP_HOLD_STEPS}"
echo "[INFO] DEMO_SECONDS=${DEMO_SECONDS}"

if [[ "${DEMO_SECONDS}" == "0" ]]; then
  ./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
    --task "${TASK_NAME}" \
    --checkpoint "${CHECKPOINT}" \
    --num_envs 1 \
    --real-time \
    "$@"
else
  timeout --foreground "${DEMO_SECONDS}s" \
    ./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
      --task "${TASK_NAME}" \
      --checkpoint "${CHECKPOINT}" \
      --num_envs 1 \
      --real-time \
      "$@"
fi
