from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

from isaaclab.app import AppLauncher


TASK_BY_MISSION = {
    "pick": "Isaac-MT4-Mars-Twin-Pick-Direct-v0",
    "place": "Isaac-MT4-Mars-Twin-Place-Direct-v0",
    "stack": "Isaac-MT4-Mars-Twin-Stack-Direct-v0",
    "push": "Isaac-MT4-Mars-Twin-Push-Direct-v0",
    "pull": "Isaac-MT4-Mars-Twin-Pull-Direct-v0",
}

PROJECT_DIR = Path.home() / "work/robotarm/mt4_isaac_lab_task"
ASSET_PATH = PROJECT_DIR / "assets/usd/mt4_simplified_v4_two_finger.usd"
sys.path.append(str(PROJECT_DIR / "source"))

parser = argparse.ArgumentParser(description="Open the MT4 Mars rover two-finger-gripper twin in Isaac Lab.")
parser.add_argument("--mission", choices=sorted(TASK_BY_MISSION), default="push")
parser.add_argument("--task", default=None, help="Override the Gym task id.")
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--duration", type=float, default=120.0)
parser.add_argument("--scripted_motion", action=argparse.BooleanOptionalAction, default=True)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import gymnasium as gym  # noqa: E402
import torch  # noqa: E402

import mt4_reach_direct  # noqa: F401, E402
from isaaclab_tasks.utils.parse_cfg import parse_env_cfg  # noqa: E402


def scripted_action(t: float, num_envs: int, device: str) -> torch.Tensor:
    action = torch.zeros((num_envs, 6), device=device)
    action[:, 0] = 0.55 * math.sin(0.80 * t)
    action[:, 1] = 0.25 * math.sin(0.55 * t + 0.40)
    action[:, 2] = 0.35 * math.sin(0.70 * t + 1.20)
    action[:, 3] = 0.25 * math.sin(0.90 * t + 2.00)
    action[:, 4] = 0.35 * math.sin(0.65 * t + 0.70)
    action[:, 5] = 1.0 if int(t / 2.5) % 2 == 0 else -1.0
    return action


def main() -> int:
    if not ASSET_PATH.is_file():
        raise SystemExit(
            "[ERROR] two-finger MT4 USD was not found:\n"
            f"        {ASSET_PATH}\n"
            "        Generate it first with:\n"
            f"        {PROJECT_DIR}/scripts/create_two_finger_asset.sh"
        )

    task = args.task if args.task is not None else TASK_BY_MISSION[args.mission]
    env_cfg = parse_env_cfg(
        task,
        device=args.device if args.device is not None else "cuda:0",
        num_envs=args.num_envs,
        use_fabric=False,
    )
    env_cfg.episode_length_s = max(args.duration, 1.0)
    env = gym.make(task, cfg=env_cfg)
    env.reset()

    unwrapped = env.unwrapped
    unwrapped.sim.set_camera_view(eye=[0.50, -0.58, 0.42], target=[0.16, 0.02, 0.10])

    print(f"[INFO] Running {task}", flush=True)
    print("[INFO] Green marker is the mission goal. Yellow marker is the home-pose reference.", flush=True)
    print("[INFO] The blue two-finger gripper is driven by a scripted open/close action.", flush=True)

    actions = torch.zeros((args.num_envs, unwrapped.cfg.action_space), device=unwrapped.device)
    start = time.time()
    while simulation_app.is_running() and time.time() - start < args.duration:
        if args.scripted_motion:
            actions = scripted_action(time.time() - start, args.num_envs, unwrapped.device)
        env.step(actions)

    env.close()
    return 0


try:
    raise SystemExit(main())
finally:
    simulation_app.close()
