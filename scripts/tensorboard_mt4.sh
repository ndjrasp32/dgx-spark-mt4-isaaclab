#!/usr/bin/env bash
set -euo pipefail

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

PORT="${1:-6006}"
LOG_DIR="logs/rsl_rl/mt4_simplified_reach_direct"

echo "[INFO] Starting TensorBoard for MT4 reach logs"
echo "[INFO] log_dir=${PWD}/${LOG_DIR}"
echo "[INFO] url=http://0.0.0.0:${PORT}/"

./isaaclab.sh -p -m tensorboard.main \
  --logdir "${LOG_DIR}" \
  --host 0.0.0.0 \
  --port "${PORT}"
