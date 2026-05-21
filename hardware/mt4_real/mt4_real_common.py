from __future__ import annotations

import datetime as _dt
import importlib
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOG_DIR = REPO_ROOT / "logs" / "real_mt4"
SAFE_JOINTS = ("base_yaw", "shoulder", "elbow", "wrist_pitch", "gripper_pitch")


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def write_jsonl(command_type: str, payload: dict[str, Any], log_dir: Path | None = None) -> Path:
    log_root = log_dir or DEFAULT_LOG_DIR
    log_root.mkdir(parents=True, exist_ok=True)
    day = _dt.datetime.now().strftime("%Y%m%d")
    path = log_root / f"{day}_commands.jsonl"
    record = {
        "timestamp": now_iso(),
        "command_type": command_type,
        **payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return path


def load_yaml_config(path: str | os.PathLike[str]) -> dict[str, Any]:
    config_path = Path(path)
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required for MT4 calibration config parsing. "
            "Install it in the active environment with: python3 -m pip install pyyaml"
        ) from exc
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at top of {config_path}")
    return data


def serial_candidates() -> list[dict[str, str]]:
    try:
        from serial.tools import list_ports  # type: ignore
    except ImportError:
        return []

    candidates: list[dict[str, str]] = []
    for port in list_ports.comports():
        device = str(port.device)
        if _looks_like_serial_device(device):
            candidates.append(
                {
                    "device": device,
                    "description": str(port.description or ""),
                    "hwid": str(port.hwid or ""),
                }
            )
    return candidates


def _looks_like_serial_device(device: str) -> bool:
    prefixes = (
        "/dev/ttyUSB",
        "/dev/ttyACM",
        "/dev/serial/by-id/",
        "COM",
    )
    return device.startswith(prefixes)


def import_sdk_objects() -> dict[str, Any]:
    result: dict[str, Any] = {
        "wlkatapython_import": False,
        "mt4_uart_found": False,
        "mt4_uart_source": None,
        "MT4_UART": None,
    }

    try:
        wlkatapython = importlib.import_module("wlkatapython")
        result["wlkatapython_import"] = True
        mt4_uart = getattr(wlkatapython, "MT4_UART", None)
        if mt4_uart is not None:
            result["mt4_uart_found"] = True
            result["mt4_uart_source"] = "wlkatapython.MT4_UART"
            result["MT4_UART"] = mt4_uart
            return result
    except Exception as exc:
        result["wlkatapython_error"] = repr(exc)

    try:
        mt4_module = importlib.import_module("MT4_robot.MT4_UART")
        mt4_uart = getattr(mt4_module, "MT4_UART", None)
        if mt4_uart is not None:
            result["mt4_uart_found"] = True
            result["mt4_uart_source"] = "MT4_robot.MT4_UART.MT4_UART"
            result["MT4_UART"] = mt4_uart
    except Exception as exc:
        result["mt4_robot_error"] = repr(exc)

    return result


def validate_calibration_config(config: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if not config.get("serial_port"):
        issues.append("serial_port is missing")
    if int(config.get("baudrate", 0)) != 115200:
        issues.append("baudrate must be 115200")
    if list(config.get("joint_order", [])) != list(SAFE_JOINTS):
        issues.append(f"joint_order must be {list(SAFE_JOINTS)}")
    if bool(config.get("dry_run_default")) is not True:
        issues.append("dry_run_default must be true")
    if float(config.get("max_delta_deg_per_command", 999.0)) > 1.0:
        issues.append("max_delta_deg_per_command must be <= 1.0")

    joint_sign = config.get("joint_sign", {})
    joint_offset = config.get("joint_offset_deg", {})
    for joint in SAFE_JOINTS:
        if int(joint_sign.get(joint, 0)) != 1:
            issues.append(f"joint_sign.{joint} must start at 1")
        if float(joint_offset.get(joint, 999.0)) != 0.0:
            issues.append(f"joint_offset_deg.{joint} must start at 0.0")
    return issues
