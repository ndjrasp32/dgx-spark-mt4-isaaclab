from __future__ import annotations

import argparse
import sys
from pathlib import Path


ISAACLAB_DIR = Path.home() / "work/isaac/src/IsaacLab"
PROJECT_DIR = Path.home() / "work/robotarm/mt4_isaac_lab_task"
RSL_RL_SCRIPT_DIR = ISAACLAB_DIR / "scripts/reinforcement_learning/rsl_rl"
sys.path.append(str(RSL_RL_SCRIPT_DIR))

from isaaclab.app import AppLauncher  # noqa: E402

import cli_args  # noqa: E402


parser = argparse.ArgumentParser(description="Collect MT4 pregrasp replay states from a trained RSL-RL policy.")
parser.add_argument("--num_envs", type=int, default=128, help="Number of parallel environments.")
parser.add_argument("--task", type=str, default="Isaac-MT4-Simplified-Reach-Direct-v0", help="IsaacLab task name.")
parser.add_argument(
    "--agent", type=str, default="rsl_rl_cfg_entry_point", help="RL agent configuration entry point."
)
parser.add_argument("--seed", type=int, default=42, help="Environment seed.")
parser.add_argument("--max_steps", type=int, default=20000, help="Maximum policy steps to scan.")
parser.add_argument("--min_states", type=int, default=512, help="Stop after this many replay states are collected.")
parser.add_argument("--cooldown_steps", type=int, default=20, help="Avoid collecting near-identical states repeatedly.")
parser.add_argument(
    "--output",
    type=Path,
    default=PROJECT_DIR / "data/pregrasp_states/latest.pt",
    help="Output .pt file for replay reset training.",
)
parser.add_argument(
    "--best_checkpoint_file",
    type=Path,
    default=PROJECT_DIR / "logs/plots/best_checkpoint.txt",
    help="Fallback checkpoint path file when --checkpoint is not provided.",
)
parser.add_argument("--pregrasp_distance", type=float, default=0.110, help="Maximum pregrasp distance to collect.")
parser.add_argument("--insertion_alignment", type=float, default=0.70, help="Minimum insertion alignment to collect.")
parser.add_argument(
    "--min_insertion_progress",
    type=float,
    default=None,
    help="Optional minimum insertion progress. Useful for collecting Stage-4 replay states.",
)
parser.add_argument(
    "--max_touch_error",
    type=float,
    default=None,
    help="Optional maximum touch depth error. Useful for collecting near-target insertion states.",
)
parser.add_argument(
    "--max_distance",
    type=float,
    default=None,
    help="Optional maximum gripper-center to red-target-center distance.",
)
parser.add_argument(
    "--pregrasp_line_error",
    type=float,
    default=0.005,
    help="Maximum XY line error between the blue pregrasp marker and the base-to-target radial line.",
)
parser.add_argument("--target_contact_penalty", type=float, default=1.0e-4, help="Maximum target contact penalty.")
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()

sys.argv = [sys.argv[0]] + hydra_args

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


import gymnasium as gym  # noqa: E402
import torch  # noqa: E402
from rsl_rl.runners import DistillationRunner, OnPolicyRunner  # noqa: E402

from isaaclab.envs import DirectMARLEnv, DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg, multi_agent_to_single_agent  # noqa: E402
from isaaclab.utils.assets import retrieve_file_path  # noqa: E402
from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper, handle_deprecated_rsl_rl_cfg  # noqa: E402

import importlib.metadata as metadata  # noqa: E402
import isaaclab_tasks  # noqa: F401, E402
from isaaclab_tasks.utils.hydra import hydra_task_config  # noqa: E402


installed_version = metadata.version("rsl-rl-lib")


def resolve_checkpoint() -> str:
    if args_cli.checkpoint:
        return retrieve_file_path(args_cli.checkpoint)

    if not args_cli.best_checkpoint_file.is_file():
        raise SystemExit(
            "[ERROR] No --checkpoint was provided and best_checkpoint.txt does not exist:\n"
            f"        {args_cli.best_checkpoint_file}\n"
            "        Run scripts/plot_and_select_best.sh first or pass --checkpoint."
        )

    checkpoint = args_cli.best_checkpoint_file.read_text(encoding="utf-8").strip()
    if not checkpoint:
        raise SystemExit(f"[ERROR] best checkpoint file is empty: {args_cli.best_checkpoint_file}")
    checkpoint_path = Path(checkpoint)
    if not checkpoint_path.is_file():
        raise SystemExit(
            "[ERROR] The checkpoint in best_checkpoint.txt does not exist:\n"
            f"        {checkpoint_path}\n"
            "        Re-run scripts/plot_and_select_best.sh or pass --checkpoint."
        )
    return str(checkpoint_path)


def append_rows(records: dict[str, list[torch.Tensor]], key: str, value: torch.Tensor) -> None:
    records.setdefault(key, []).append(value.detach().cpu())


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    agent_cfg = handle_deprecated_rsl_rl_cfg(agent_cfg, installed_version)

    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.seed = agent_cfg.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device

    checkpoint_path = resolve_checkpoint()
    print("[INFO] Collecting MT4 pregrasp replay states")
    print(f"[INFO] checkpoint = {checkpoint_path}")
    print(f"[INFO] output     = {args_cli.output}")

    env = gym.make(args_cli.task, cfg=env_cfg)
    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)

    base_env = env.unwrapped
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    if agent_cfg.class_name == "OnPolicyRunner":
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    elif agent_cfg.class_name == "DistillationRunner":
        runner = DistillationRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    else:
        raise ValueError(f"Unsupported runner class: {agent_cfg.class_name}")
    runner.load(checkpoint_path)
    policy = runner.get_inference_policy(device=env.unwrapped.device)

    obs = env.get_observations()
    cooldown = torch.zeros(args_cli.num_envs, dtype=torch.int32, device=base_env.device)
    records: dict[str, list[torch.Tensor]] = {}
    collected = 0

    for step in range(args_cli.max_steps):
        with torch.inference_mode():
            actions = policy(obs)
            obs, _, dones, _ = env.step(actions)
            if hasattr(policy, "reset"):
                policy.reset(dones)

        base_env._compute_intermediate_values()
        ready = (
            (base_env.pregrasp_distance < args_cli.pregrasp_distance)
            & (base_env.insertion_alignment > args_cli.insertion_alignment)
            & base_env.pregrasp_held
            & (base_env.pregrasp_line_error <= args_cli.pregrasp_line_error)
            & (base_env.target_contact_penalty <= args_cli.target_contact_penalty)
            & (cooldown <= 0)
        )
        if args_cli.min_insertion_progress is not None:
            ready = ready & (base_env.insertion_progress >= args_cli.min_insertion_progress)
        if args_cli.max_touch_error is not None:
            ready = ready & (base_env.touch_error <= args_cli.max_touch_error)
        if args_cli.max_distance is not None:
            ready = ready & (base_env.distance <= args_cli.max_distance)
        ready_ids = torch.nonzero(ready, as_tuple=False).squeeze(-1)

        if len(ready_ids) > 0:
            remaining = args_cli.min_states - collected
            ready_ids = ready_ids[:remaining]
            joint_pos = base_env.robot.data.joint_pos[ready_ids][:, base_env.joint_ids]
            joint_vel = base_env.robot.data.joint_vel[ready_ids][:, base_env.joint_ids]

            append_rows(records, "joint_pos", joint_pos)
            append_rows(records, "joint_vel", joint_vel)
            append_rows(records, "targets", base_env.targets[ready_ids])
            append_rows(records, "pregrasp_targets", base_env.pregrasp_targets[ready_ids])
            append_rows(records, "touch_targets", base_env.touch_targets[ready_ids])
            append_rows(records, "pregrasp_distance", base_env.pregrasp_distance[ready_ids].unsqueeze(-1))
            append_rows(records, "insertion_alignment", base_env.insertion_alignment[ready_ids].unsqueeze(-1))
            append_rows(records, "pregrasp_line_error", base_env.pregrasp_line_error[ready_ids].unsqueeze(-1))
            append_rows(records, "target_contact_penalty", base_env.target_contact_penalty[ready_ids].unsqueeze(-1))
            append_rows(records, "touch_error", base_env.touch_error[ready_ids].unsqueeze(-1))
            append_rows(records, "distance", base_env.distance[ready_ids].unsqueeze(-1))
            append_rows(records, "insertion_progress", base_env.insertion_progress[ready_ids].unsqueeze(-1))

            cooldown[ready_ids] = args_cli.cooldown_steps
            collected += len(ready_ids)

        cooldown = torch.clamp(cooldown - 1, min=0)
        if step % 500 == 0 or collected >= args_cli.min_states:
            print(f"[INFO] step={step} collected={collected}/{args_cli.min_states}")
        if collected >= args_cli.min_states:
            break

    env.close()

    if collected == 0:
        raise SystemExit("[ERROR] Collected 0 pregrasp states. Try a better checkpoint or looser thresholds.")

    output = {key: torch.cat(values, dim=0) for key, values in records.items()}
    output["metadata"] = {
        "checkpoint": checkpoint_path,
        "task": args_cli.task,
        "seed": args_cli.seed,
        "num_envs": args_cli.num_envs,
        "max_steps": args_cli.max_steps,
        "requested_min_states": args_cli.min_states,
        "collected_states": collected,
        "pregrasp_distance_threshold": args_cli.pregrasp_distance,
        "insertion_alignment_threshold": args_cli.insertion_alignment,
        "pregrasp_line_error_threshold": args_cli.pregrasp_line_error,
        "target_contact_penalty_threshold": args_cli.target_contact_penalty,
        "min_insertion_progress_threshold": args_cli.min_insertion_progress,
        "max_touch_error_threshold": args_cli.max_touch_error,
        "max_distance_threshold": args_cli.max_distance,
        "joint_names": list(base_env.joint_names),
    }

    args_cli.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(output, args_cli.output)
    print("[OK] saved pregrasp replay states")
    print(f"     path      = {args_cli.output}")
    print(f"     count     = {collected}")
    print(f"     mean_dist = {output['pregrasp_distance'].mean().item():.6f}")
    print(f"     mean_align= {output['insertion_alignment'].mean().item():.6f}")
    print(f"     mean_line = {output['pregrasp_line_error'].mean().item():.6f}")
    print(f"     mean_touch= {output['touch_error'].mean().item():.6f}")
    print(f"     mean_center_dist= {output['distance'].mean().item():.6f}")
    print(f"     mean_progress   = {output['insertion_progress'].mean().item():.6f}")

    if collected < args_cli.min_states:
        raise SystemExit(f"[ERROR] Only collected {collected}/{args_cli.min_states} states.")


if __name__ == "__main__":
    main()
    simulation_app.close()
