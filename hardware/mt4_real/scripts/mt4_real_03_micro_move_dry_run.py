#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from hardware.mt4_real.mt4_real_common import SAFE_JOINTS, load_yaml_config, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MT4 micro move placeholder. Real motion is intentionally not implemented.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--joint", default="base_yaw", choices=SAFE_JOINTS)
    parser.add_argument("--delta-deg", type=float, default=0.5)
    parser.add_argument("--execute", action="store_true", help="Rejected until real joint mapping is calibrated")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml_config(args.config)
    max_delta = float(config.get("max_delta_deg_per_command", 1.0))
    delta = float(args.delta_deg)

    if abs(delta) > max_delta:
        result = "blocked_delta_too_large"
        print(f"result: {result}")
        write_jsonl(
            "micro_move",
            {
                "dry_run": True,
                "joint": args.joint,
                "delta_deg": delta,
                "max_delta_deg_per_command": max_delta,
                "result": result,
            },
        )
        return 4

    if args.execute:
        result = "blocked_execute_not_implemented"
        print("micro move execute is intentionally disabled until joint mapping is calibrated")
        write_jsonl(
            "micro_move",
            {
                "dry_run": True,
                "joint": args.joint,
                "delta_deg": delta,
                "result": result,
            },
        )
        return 5

    print("MT4 micro move dry-run")
    print(f"joint: {args.joint}")
    print(f"delta_deg: {delta}")
    print("motion: not attempted")
    print("result: dry_run_only")
    write_jsonl(
        "micro_move",
        {
            "dry_run": True,
            "joint": args.joint,
            "delta_deg": delta,
            "result": "dry_run_only",
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
