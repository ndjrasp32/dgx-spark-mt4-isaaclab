#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
ISAACLAB_DIR="${HOME}/work/isaac/src/IsaacLab"

cd "${PROJECT_DIR}"
unset CMEEL_PREFIX
export DISPLAY="${DISPLAY:-:1}"
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

if [[ ! -f "${PROJECT_DIR}/assets/usd/mt4_simplified_v4_two_finger.usd" ]]; then
  "${PROJECT_DIR}/scripts/create_two_finger_asset.sh"
fi

if command -v xdpyinfo >/dev/null 2>&1 && ! xdpyinfo -display "${DISPLAY}" >/dev/null 2>&1; then
  echo "[WARN] DISPLAY=${DISPLAY} is not accessible from this shell."
  echo "       In the Spark/VNC terminal, run:"
  echo "       xhost +SI:localuser:${USER}"
fi

"${ISAACLAB_DIR}/isaaclab.sh" -p "${PROJECT_DIR}/tools/view_mt4_mars_twin.py" "$@"
