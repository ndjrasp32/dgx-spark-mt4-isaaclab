#!/usr/bin/env bash
set -euo pipefail

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
export DISPLAY="${DISPLAY:-:1}"
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

TASK_NAME="Isaac-MT4-Simplified-Reach-Direct-v0"

if command -v xdpyinfo >/dev/null 2>&1 && ! xdpyinfo -display "${DISPLAY}" >/dev/null 2>&1; then
  echo "[WARN] DISPLAY=${DISPLAY} is not accessible from this shell."
  echo "       If you are using VNC, run this in the VNC terminal first:"
  echo "       xhost +SI:localuser:${USER}"
fi

echo "[INFO] Visual training demo for ${TASK_NAME}"
echo "[INFO] num_envs=16 max_iterations=300 display=${DISPLAY}"

./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
  --task "${TASK_NAME}" \
  --num_envs 16 \
  --max_iterations 300 \
  "$@"
