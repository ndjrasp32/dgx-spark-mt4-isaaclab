#!/usr/bin/env bash
set -euo pipefail

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
export DISPLAY=:1
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
DEMO_SECONDS="${DEMO_SECONDS:-120}"

echo "[INFO] MT4 best-checkpoint classroom demo"
echo "[INFO] Runs one robot arm in real time with random targets."
echo "[INFO] Each episode has the task time limit; close Isaac Sim to stop early."
echo "[INFO] DEMO_SECONDS=${DEMO_SECONDS}"

if [[ "${DEMO_SECONDS}" == "0" ]]; then
  "${PROJECT_DIR}/scripts/play_best.sh" --num_envs 1 --real-time "$@"
else
  timeout --foreground "${DEMO_SECONDS}s" \
    "${PROJECT_DIR}/scripts/play_best.sh" --num_envs 1 --real-time "$@"
fi
