#!/usr/bin/env bash
set -euo pipefail

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
export DISPLAY=:1
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

TASK_NAME="Isaac-MT4-Simplified-Reach-Direct-v0"
BEST_FILE="${HOME}/work/robotarm/mt4_isaac_lab_task/logs/plots/best_checkpoint.txt"

if [[ ! -f "${BEST_FILE}" ]]; then
  echo "[ERROR] best_checkpoint.txt was not found."
  echo "        Expected path: ${BEST_FILE}"
  echo "        Run this first:"
  echo "        ${HOME}/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh"
  exit 1
fi

CHECKPOINT="$(tr -d '\r\n' < "${BEST_FILE}")"

if [[ -z "${CHECKPOINT}" ]]; then
  echo "[ERROR] best_checkpoint.txt is empty."
  echo "        Expected path: ${BEST_FILE}"
  echo "        Run plot_and_select_best.sh again after training finishes."
  exit 1
fi

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
  echo "       Then run play_best.sh again from the same user/session."
fi

echo "[INFO] Playing ${TASK_NAME}"
echo "[INFO] checkpoint=${CHECKPOINT}"

./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/play.py \
  --task "${TASK_NAME}" \
  --checkpoint "${CHECKPOINT}" \
  "$@"
