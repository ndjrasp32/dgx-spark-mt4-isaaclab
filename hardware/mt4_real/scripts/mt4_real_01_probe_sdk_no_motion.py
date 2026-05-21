#!/usr/bin/env python3
from __future__ import annotations

import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from hardware.mt4_real.mt4_real_common import import_sdk_objects, serial_candidates, write_jsonl


def main() -> int:
    print(f"python: {platform.python_version()} ({sys.executable})")

    pyserial_ok = False
    try:
        import serial  # noqa: F401

        pyserial_ok = True
        print("pyserial: OK")
    except Exception as exc:
        print(f"pyserial: FAIL ({exc!r})")

    sdk = import_sdk_objects()
    if sdk.get("wlkatapython_import"):
        print("wlkatapython: OK")
    else:
        print(f"wlkatapython: FAIL ({sdk.get('wlkatapython_error', 'not importable')})")

    if sdk.get("mt4_uart_found"):
        print(f"MT4_UART: OK ({sdk.get('mt4_uart_source')})")
    else:
        print("MT4_UART: FAIL")

    candidates = serial_candidates()
    if candidates:
        print("candidate ports: " + ", ".join(port["device"] for port in candidates))
    else:
        print("candidate ports: none")
    print("motion: not attempted")

    ok = pyserial_ok and bool(sdk.get("wlkatapython_import")) and bool(sdk.get("mt4_uart_found"))
    write_jsonl(
        "sdk_probe",
        {
            "dry_run": True,
            "motion": "not_attempted",
            "pyserial": "OK" if pyserial_ok else "FAIL",
            "wlkatapython": "OK" if sdk.get("wlkatapython_import") else "FAIL",
            "mt4_uart": "OK" if sdk.get("mt4_uart_found") else "FAIL",
            "candidate_ports": [port["device"] for port in candidates],
            "result": "ok" if ok else "failed",
        },
    )
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
