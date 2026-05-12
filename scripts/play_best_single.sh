#!/usr/bin/env bash
set -euo pipefail

"${HOME}/work/robotarm/mt4_isaac_lab_task/scripts/play_best.sh" --num_envs 1 --real-time "$@"
