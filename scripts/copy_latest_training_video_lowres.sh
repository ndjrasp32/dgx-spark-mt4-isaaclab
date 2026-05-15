#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
ISAAC_LOG_ROOT="${HOME}/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct"
OUTPUT_DIR="${PROJECT_DIR}/logs/videos"

mkdir -p "${OUTPUT_DIR}"

LATEST_VIDEO="$(find "${ISAAC_LOG_ROOT}" -path '*/videos/train/*.mp4' -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | awk 'NR==1 {print $2}')"

if [[ -z "${LATEST_VIDEO:-}" || ! -f "${LATEST_VIDEO}" ]]; then
  echo "[ERROR] No training video was found under:"
  echo "        ${ISAAC_LOG_ROOT}/*/videos/train/*.mp4"
  echo "        Run a training command with --video first."
  exit 1
fi

RUN_NAME="$(basename "$(dirname "$(dirname "$(dirname "${LATEST_VIDEO}")")")")"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_FILE="${OUTPUT_DIR}/${STAMP}_stage4_center_low_exploration_${RUN_NAME}.mp4"

if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -y -i "${LATEST_VIDEO}" -vf "scale=640:-2" -c:v libx264 -preset veryfast -crf 30 -an "${OUTPUT_FILE}" >/dev/null 2>&1
else
  cp "${LATEST_VIDEO}" "${OUTPUT_FILE}"
fi

echo "[OK] Copied low-resolution training video:"
echo "     source=${LATEST_VIDEO}"
echo "     output=${OUTPUT_FILE}"
