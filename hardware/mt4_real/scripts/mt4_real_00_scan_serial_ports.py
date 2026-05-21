#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from hardware.mt4_real.mt4_real_common import serial_candidates, write_jsonl


def main() -> int:
    candidates = serial_candidates()
    print("serial scan: no motion attempted")
    if candidates:
        print("candidate ports: " + ", ".join(port["device"] for port in candidates))
    else:
        print("candidate ports: none")
    for port in candidates:
        print(f"- {port['device']} | {port['description']} | {port['hwid']}")

    write_jsonl(
        "serial_scan",
        {
            "dry_run": True,
            "motion": "not_attempted",
            "candidate_ports": [port["device"] for port in candidates],
            "result": "ports_found" if candidates else "no_ports_found",
        },
    )
    return 0 if candidates else 2


if __name__ == "__main__":
    raise SystemExit(main())
