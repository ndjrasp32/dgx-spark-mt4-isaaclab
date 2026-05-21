#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from hardware.mt4_real.mt4_real_common import (
    import_sdk_objects,
    load_yaml_config,
    validate_calibration_config,
    write_jsonl,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded MT4 homing. Dry-run unless both execute flags are present.")
    parser.add_argument("--config", required=True, help="Calibration YAML path")
    parser.add_argument("--execute", action="store_true", help="Allow real homing command")
    parser.add_argument(
        "--i-understand-this-moves-the-real-robot",
        action="store_true",
        help="Required with --execute because homing moves the real robot",
    )
    parser.add_argument("--homing-mode", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml_config(args.config)
    issues = validate_calibration_config(config)

    port = str(config.get("serial_port", ""))
    baudrate = int(config.get("baudrate", 115200))
    execute_confirmed = args.execute and args.i_understand_this_moves_the_real_robot
    dry_run = not execute_confirmed

    print("MT4 guarded homing")
    print(f"config: {args.config}")
    print(f"serial_port: {port}")
    print(f"baudrate: {baudrate}")
    print(f"homing_mode: {args.homing_mode}")
    print(f"dry_run: {str(dry_run).lower()}")
    print("warning: real homing can move the physical robot")

    if issues:
        for issue in issues:
            print(f"config issue: {issue}")
        write_jsonl(
            "homing",
            {
                "dry_run": True,
                "serial_port": port,
                "baudrate": baudrate,
                "homing_mode": args.homing_mode,
                "result": "blocked_config_invalid",
                "issues": issues,
            },
        )
        return 4

    if dry_run:
        print("result: dry_run_only")
        write_jsonl(
            "homing",
            {
                "dry_run": True,
                "serial_port": port,
                "baudrate": baudrate,
                "homing_mode": args.homing_mode,
                "result": "dry_run_only",
            },
        )
        return 0

    sdk = import_sdk_objects()
    if not sdk.get("mt4_uart_found"):
        print("result: blocked_sdk_missing")
        write_jsonl(
            "homing",
            {
                "dry_run": True,
                "serial_port": port,
                "baudrate": baudrate,
                "homing_mode": args.homing_mode,
                "result": "blocked_sdk_missing",
            },
        )
        return 5

    import serial  # type: ignore

    serial_handle = None
    try:
        serial_handle = serial.Serial(port, baudrate, timeout=1)
        mt4 = sdk["MT4_UART"]()
        mt4.init(serial_handle, -1)
        mt4.homing(args.homing_mode)
        print("result: homing_command_sent")
        write_jsonl(
            "homing",
            {
                "dry_run": False,
                "serial_port": port,
                "baudrate": baudrate,
                "homing_mode": args.homing_mode,
                "result": "homing_command_sent",
            },
        )
        return 0
    finally:
        if serial_handle is not None and serial_handle.is_open:
            serial_handle.close()
            print("serial: closed")


if __name__ == "__main__":
    raise SystemExit(main())
