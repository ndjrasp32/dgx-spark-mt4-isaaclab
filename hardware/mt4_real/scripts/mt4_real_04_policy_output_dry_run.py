#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from hardware.mt4_real.mt4_real_common import SAFE_JOINTS, load_yaml_config, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate policy-to-command dry-run output without touching hardware.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml_config(args.config)
    max_delta = float(config.get("max_delta_deg_per_command", 1.0))
    interval = float(config.get("command_interval_sec", 0.5))
    sample = {joint: 0.0 for joint in SAFE_JOINTS}
    sample["base_yaw"] = min(0.5, max_delta)

    print("policy output dry-run")
    print(f"max_delta_deg_per_command: {max_delta}")
    print(f"command_interval_sec: {interval}")
    print(f"sample_command_deg: {sample}")
    print("motion: not attempted")
    print("result: dry_run_only")

    write_jsonl(
        "policy_output",
        {
            "dry_run": True,
            "command_interval_sec": interval,
            "max_delta_deg_per_command": max_delta,
            "sample_command_deg": sample,
            "result": "dry_run_only",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
