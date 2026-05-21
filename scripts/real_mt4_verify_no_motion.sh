#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
CONFIG="${CONFIG:-hardware/mt4_real/config/mt4_real_calibration.template.yaml}"

status=0

run_step() {
  local name="$1"
  shift
  echo
  echo "== ${name} =="
  "$@"
  local rc=$?
  if [[ "$name" == "serial scan" && "$rc" == "2" ]]; then
    echo "serial scan: no candidate ports found; continuing no-motion verification"
    return 0
  fi
  if [[ "$rc" != "0" ]]; then
    echo "${name}: failed with exit code ${rc}"
    status="$rc"
  fi
}

run_step "compileall" "$PYTHON_BIN" -m compileall -q hardware/mt4_real
run_step "serial scan" "$PYTHON_BIN" hardware/mt4_real/scripts/mt4_real_00_scan_serial_ports.py
run_step "SDK probe" "$PYTHON_BIN" hardware/mt4_real/scripts/mt4_real_01_probe_sdk_no_motion.py
run_step "homing dry-run" "$PYTHON_BIN" hardware/mt4_real/scripts/mt4_real_02_homing_guarded.py --config "$CONFIG"
run_step "micro move dry-run" "$PYTHON_BIN" hardware/mt4_real/scripts/mt4_real_03_micro_move_dry_run.py --config "$CONFIG" --joint base_yaw --delta-deg 0.5
run_step "policy output dry-run" "$PYTHON_BIN" hardware/mt4_real/scripts/mt4_real_04_policy_output_dry_run.py --config "$CONFIG"

echo
echo "no-motion verification complete; status=${status}"
exit "$status"
