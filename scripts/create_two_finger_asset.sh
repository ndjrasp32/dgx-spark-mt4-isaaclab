#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
ISAACLAB_DIR="${HOME}/work/isaac/src/IsaacLab"

cd "${PROJECT_DIR}"
unset CMEEL_PREFIX
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

"${ISAACLAB_DIR}/isaaclab.sh" -p "${PROJECT_DIR}/tools/create_mt4_simplified_v4_two_finger_gripper.py"
