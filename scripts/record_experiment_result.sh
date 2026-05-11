#!/usr/bin/env bash
set -euo pipefail

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

./isaaclab.sh -p "${HOME}/work/robotarm/mt4_isaac_lab_task/tools/record_mt4_experiment.py" "$@"
