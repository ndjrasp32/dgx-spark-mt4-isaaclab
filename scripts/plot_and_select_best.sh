#!/usr/bin/env bash
set -euo pipefail

cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
if [[ -z "${TERM:-}" || "${TERM}" == "dumb" ]]; then
  export TERM=xterm-256color
fi

TOOLS_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task/tools"
PROJECT_DIR="${HOME}/work/robotarm/mt4_isaac_lab_task"
PLOTS_DIR="${PROJECT_DIR}/logs/plots"
BEST_FILE="${PLOTS_DIR}/best_checkpoint.txt"

slugify() {
  tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9._-]+/_/g; s/^_+//; s/_+$//'
}

timestamp_from_run_name() {
  local run_name="$1"
  if [[ "${run_name}" =~ ^([0-9]{4})-([0-9]{2})-([0-9]{2})_([0-9]{2})-([0-9]{2})-([0-9]{2})$ ]]; then
    printf "%s%s%s_%s%s%s" \
      "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}" \
      "${BASH_REMATCH[4]}" "${BASH_REMATCH[5]}" "${BASH_REMATCH[6]}"
  else
    date +%Y%m%d_%H%M%S
  fi
}

echo "[INFO] Plotting MT4 training curves and checkpoint summaries..."
./isaaclab.sh -p "${TOOLS_DIR}/plot_mt4_training_and_checkpoints.py"

echo "[INFO] Selecting best MT4 checkpoint..."
./isaaclab.sh -p "${TOOLS_DIR}/select_best_mt4_checkpoint.py"

if [[ ! -s "${BEST_FILE}" ]]; then
  echo "[ERROR] best_checkpoint.txt was not created or is empty."
  echo "        Expected path: ${BEST_FILE}"
  echo "        Please check that training logs exist under logs/rsl_rl/mt4_simplified_reach_direct."
  exit 1
fi

echo "[OK] Best checkpoint:"
cat "${BEST_FILE}"

if [[ "${MT4_SKIP_PLOT_SNAPSHOT:-0}" == "1" ]]; then
  echo "[INFO] Skipping timestamped plot snapshot because MT4_SKIP_PLOT_SNAPSHOT=1."
  exit 0
fi

CHECKPOINT="$(tr -d '\r\n' < "${BEST_FILE}")"
RUN_DIR="$(dirname "${CHECKPOINT}")"
RUN_NAME="$(basename "${RUN_DIR}")"
RUN_STAMP="$(timestamp_from_run_name "${RUN_NAME}")"
LABEL="$(printf "%s" "${MT4_PLOT_LABEL:-plots}" | slugify)"
if [[ -z "${LABEL}" ]]; then
  LABEL="plots"
fi

SNAPSHOT_DIR="${PLOTS_DIR}/${RUN_STAMP}_${LABEL}"
mkdir -p "${SNAPSHOT_DIR}"

find "${PLOTS_DIR}" -maxdepth 1 -type f \( -name 'mt4_*.png' -o -name 'mt4_*.csv' -o -name 'best_checkpoint.txt' \) \
  -exec cp {} "${SNAPSHOT_DIR}/" \;

MANIFEST="${SNAPSHOT_DIR}/${RUN_STAMP}_${LABEL}_manifest.md"
{
  echo "# MT4 Plot Snapshot"
  echo
  echo "- timestamp: ${RUN_STAMP}"
  echo "- label: ${LABEL}"
  echo "- source_run: ${RUN_DIR}"
  echo "- best_checkpoint: ${CHECKPOINT}"
  echo
  echo "This directory is an immutable snapshot copied from logs/plots latest files."
} > "${MANIFEST}"

echo "[OK] Snapshot directory:"
echo "     ${SNAPSHOT_DIR}"
