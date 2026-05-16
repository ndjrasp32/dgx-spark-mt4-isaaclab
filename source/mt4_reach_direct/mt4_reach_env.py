from __future__ import annotations

import os
from pathlib import Path

import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.envs import DirectRLEnv, DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils import math as math_utils
from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg


MT4_USD_PATH = "/home/spark-robotics/work/robotarm/mt4_isaac_lab_task/assets/usd/mt4_simplified_v3.usd"


@configclass
class MT4ReachEnvCfg(DirectRLEnvCfg):
    # simulation
    decimation = 2
    episode_length_s = 5.0

    # spaces
    action_space = 5
    observation_space = 31
    state_space = 0

    # "integrated" keeps the original staged reach reward. "stage_b_insertion" is a
    # curriculum profile used after the approach/pregrasp policy already works.
    training_mode = "integrated"
    reset_mode = "default"

    # physics
    sim: sim_utils.SimulationCfg = sim_utils.SimulationCfg(
        dt=1 / 120,
        render_interval=decimation,
    )

    # scene
    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=64,
        env_spacing=0.85,
        replicate_physics=True,
    )

    # robot
    robot_cfg: ArticulationCfg = ArticulationCfg(
        prim_path="/World/envs/env_.*/Robot",
        spawn=sim_utils.UsdFileCfg(
            usd_path=MT4_USD_PATH,
            activate_contact_sensors=False,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=5.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=1,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.0),
            joint_pos={
                "base_yaw": 0.0,
                "shoulder": 1.44,
                "elbow": -1.19,
                "wrist_pitch": 1.19,
                "gripper_pitch": 0.0,
            },
        ),
        actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=["base_yaw", "shoulder", "elbow", "wrist_pitch", "gripper_pitch"],
                stiffness=2200.0,
                damping=280.0,
                effort_limit=1500.0,
                velocity_limit=1.5,
            )
        },
    )

    # visual target marker
    target_marker_cfg = VisualizationMarkersCfg(
        prim_path="/Visuals/MT4ReachTargets",
        markers={
            "target": sim_utils.SphereCfg(
                radius=0.025,
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(1.0, 0.05, 0.05),
                    emissive_color=(0.25, 0.0, 0.0),
                ),
            ),
        },
    )

    # success marker: shown at target position only when wrist is close enough.
    success_marker_cfg = VisualizationMarkersCfg(
        prim_path="/Visuals/MT4ReachSuccess",
        markers={
            "success": sim_utils.SphereCfg(
                radius=0.035,
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(0.05, 1.0, 0.05),
                    emissive_color=(0.0, 0.35, 0.0),
                ),
            ),
        },
    )

    # blue marker: where the virtual gripper tip should stop before grasping.
    pregrasp_marker_cfg = VisualizationMarkersCfg(
        prim_path="/Visuals/MT4PregraspTargets",
        markers={
            "pregrasp": sim_utils.SphereCfg(
                radius=0.011,
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(0.05, 0.25, 1.0),
                    emissive_color=(0.0, 0.05, 0.35),
                ),
            ),
        },
    )

    # task
    action_scale = 0.045
    success_radius = 0.055
    target_x_range = (0.20, 0.32)
    target_y_range = (-0.16, 0.16)
    target_z_range = (0.08, 0.18)
    min_target_base_radius = 0.18

    # simplified pre-grasp geometry
    gripper_center_offset_b = (0.158, 0.0, 0.0)
    gripper_tip_offset_b = (0.166, 0.0, 0.0)
    gripper_forward_axis_b = (1.0, 0.0, 0.0)
    gripper_side_axis_b = (0.0, 1.0, 0.0)
    target_radius = 0.025
    desired_touch_distance = 0.030
    touch_success_band = 0.045
    pregrasp_standoff = 0.080
    pregrasp_horizontal_offset = 0.075
    pregrasp_vertical_offset = 0.075
    pregrasp_entry_offset = 0.030
    pregrasp_entry_success_radius = 0.110
    pregrasp_entry_hold_radius = 0.085
    pregrasp_success_radius = 0.120
    pregrasp_hold_radius = 0.080
    pregrasp_hold_velocity_scale = 0.08
    pregrasp_hold_min_stability = 0.45
    stage3_insertion_start_progress = 0.10
    stage3_insertion_success_progress = 0.55
    final_center_success_radius = 0.025
    final_center_improvement_scale = 0.010
    approach_horizontal_weight = 1.0
    approach_down_weight = 1.0
    min_object_clearance = 0.035
    min_robot_target_clearance = 0.045
    max_success_overlap = 0.003
    alignment_success = 0.62
    insertion_alignment_success = 0.70

    # staged reward weights for classroom tuning
    stage1_alignment_weight = 1.6
    stage1_wrong_way_weight = 1.2
    stage2_entry_weight = 5.0
    stage2_entry_touch_weight = 3.0
    stage2_pregrasp_weight = 8.0
    stage2_touch_weight = 5.0
    stage2_hold_weight = 3.0
    stage2_center_progress_weight = 2.0
    stage3_line_weight = 2.4
    stage3_touch_weight = 7.0
    stage3_progress_weight = 6.0
    stage3_depth_weight = 8.0
    stage3_slow_weight = 0.8
    stage4_center_improvement_weight = 24.0
    stage4_center_precision_weight = 10.0
    stage4_center_push_weight = 16.0
    stage4_center_push_improvement_weight = 20.0
    stage4_center_push_depth_weight = 8.0
    stage4_shortest_path_weight = 18.0
    stage4_distance_shell_weight = 14.0
    stage3_time_preserve_weight = 0.0
    terminal_success_quality_weight = 0.0
    near_terminal_weight = 0.0
    near_terminal_radius = 0.050
    stage_latch_weight = 0.0
    progressive_stage_weight = 0.0
    moving_pregrasp_enabled = False
    moving_pregrasp_goal_mode = "touch"
    moving_pregrasp_step_count = 3
    moving_pregrasp_final_fraction = 0.70
    moving_pregrasp_step_radius = 0.055
    moving_pregrasp_hold_steps = 1
    moving_pregrasp_reward_weight = 0.0
    moving_pregrasp_funnel_weight = 0.0
    moving_pregrasp_funnel_depth = 0.090
    moving_pregrasp_funnel_min_radius = 0.020
    moving_pregrasp_funnel_max_radius = 0.070
    moving_pregrasp_exp_weight = 0.30
    moving_pregrasp_shell_weight = 0.25
    moving_pregrasp_shell_size = 0.005
    moving_pregrasp_exp_scale = 0.035
    final_insertion_weight = 0.0
    center_push_improvement_scale = 0.020
    center_distance_shell_size = 0.005
    stage4_push_ready_progress = 0.60
    stage4_success_min_progress = 0.78
    stage4_success_max_progress = 1.08
    early_target_clearance = 0.055
    early_target_contact_penalty_weight = 160.0
    stage4_overshoot_penalty_weight = 18.0
    gripper_roll_alignment_weight = 0.0
    pregrasp_bonus_weight = 2.5
    success_bonus_weight = 18.0
    target_contact_penalty_weight = 70.0
    wrong_way_penalty_weight = 0.8
    action_penalty_weight = 0.012
    joint_velocity_penalty_weight = 0.0004
    time_penalty_weight = 0.004
    stage4_time_penalty_weight = 0.030

    # pregrasp replay reset curriculum
    pregrasp_replay_state_file = "/home/spark-robotics/work/robotarm/mt4_isaac_lab_task/data/pregrasp_states/latest.pt"
    pregrasp_replay_probability = 0.75
    pregrasp_replay_joint_noise = 0.025
    pregrasp_replay_target_noise = 0.004
    pregrasp_replay_joint_velocity_scale = 0.25


class MT4ReachEnv(DirectRLEnv):
    cfg: MT4ReachEnvCfg

    def __init__(self, cfg: MT4ReachEnvCfg, render_mode: str | None = None, **kwargs):
        self.training_mode = self._apply_training_mode_cfg(cfg)
        self.reset_mode = self._apply_reset_mode_cfg(cfg)
        super().__init__(cfg, render_mode, **kwargs)

        self.joint_names = ["base_yaw", "shoulder", "elbow", "wrist_pitch", "gripper_pitch"]
        self.joint_ids, self.joint_names_found = self.robot.find_joints(self.joint_names)
        self.ee_body_id = self.robot.find_bodies("gripper_link")[0][0]

        self.joint_lower = torch.tensor([-1.57, 0.05, -1.20, -1.20, -1.20], device=self.device)
        self.joint_upper = torch.tensor([1.57, 1.45, 1.40, 1.20, 1.20], device=self.device)

        self.home_joint_pos = torch.tensor([0.0, 1.44, -1.19, 1.19, 0.0], device=self.device)

        self.actions = torch.zeros((self.num_envs, 5), device=self.device)
        self.joint_targets = self.home_joint_pos.repeat(self.num_envs, 1)

        self.targets = torch.zeros((self.num_envs, 3), device=self.device)

        # Red target spheres shown in GUI/play mode.
        # The policy already receives target coordinates; this marker only makes them visible.
        self.target_markers = VisualizationMarkers(self.cfg.target_marker_cfg)
        self.success_markers = VisualizationMarkers(self.cfg.success_marker_cfg)
        self.pregrasp_markers = VisualizationMarkers(self.cfg.pregrasp_marker_cfg)

        self.wrist_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.gripper_center_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.gripper_tip_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.gripper_forward = torch.zeros((self.num_envs, 3), device=self.device)
        self.gripper_side = torch.zeros((self.num_envs, 3), device=self.device)
        self.gripper_roll_alignment = torch.zeros((self.num_envs,), device=self.device)
        self.approach_dir = torch.zeros((self.num_envs, 3), device=self.device)
        self.desired_gripper_dir = torch.zeros((self.num_envs, 3), device=self.device)
        self.desired_pregrasp_dir = torch.zeros((self.num_envs, 3), device=self.device)
        self.desired_insertion_dir = torch.zeros((self.num_envs, 3), device=self.device)
        self.pregrasp_entry_targets = torch.zeros((self.num_envs, 3), device=self.device)
        self.pregrasp_start_targets = torch.zeros((self.num_envs, 3), device=self.device)
        self.pregrasp_goal_targets = torch.zeros((self.num_envs, 3), device=self.device)
        self.pregrasp_targets = torch.zeros((self.num_envs, 3), device=self.device)
        self.touch_targets = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_target = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_pregrasp_entry = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_pregrasp = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_touch = torch.zeros((self.num_envs, 3), device=self.device)
        self.distance = torch.zeros((self.num_envs,), device=self.device)
        self.pregrasp_entry_distance = torch.zeros((self.num_envs,), device=self.device)
        self.pregrasp_distance = torch.zeros((self.num_envs,), device=self.device)
        self.touch_target_distance = torch.zeros((self.num_envs,), device=self.device)
        self.insertion_lateral_error = torch.zeros((self.num_envs,), device=self.device)
        self.alignment = torch.zeros((self.num_envs,), device=self.device)
        self.pregrasp_alignment = torch.zeros((self.num_envs,), device=self.device)
        self.insertion_alignment = torch.zeros((self.num_envs,), device=self.device)
        self.clearance_error = torch.zeros((self.num_envs,), device=self.device)
        self.touch_error = torch.zeros((self.num_envs,), device=self.device)
        self.object_overlap = torch.zeros((self.num_envs,), device=self.device)
        self.body_target_clearance_error = torch.zeros((self.num_envs,), device=self.device)
        self.target_contact_penalty = torch.zeros((self.num_envs,), device=self.device)
        self.pregrasp_center_progress = torch.zeros((self.num_envs,), device=self.device)
        self.insertion_progress = torch.zeros((self.num_envs,), device=self.device)
        self.center_push_progress = torch.zeros((self.num_envs,), device=self.device)
        self.center_push_progress_raw = torch.zeros((self.num_envs,), device=self.device)
        self.center_push_overshoot = torch.zeros((self.num_envs,), device=self.device)
        self.early_target_contact_penalty = torch.zeros((self.num_envs,), device=self.device)
        self.best_center_push_progress = torch.zeros((self.num_envs,), device=self.device)
        self.center_push_improvement = torch.zeros((self.num_envs,), device=self.device)
        self.best_target_center_distance = torch.full((self.num_envs,), 10.0, device=self.device)
        self.target_center_improvement = torch.zeros((self.num_envs,), device=self.device)
        self.best_target_center_shell = torch.full((self.num_envs,), 999.0, device=self.device)
        self.target_center_shell_improvement = torch.zeros((self.num_envs,), device=self.device)
        self.center_shortest_path_score = torch.zeros((self.num_envs,), device=self.device)
        self.stage4_time_pressure = torch.zeros((self.num_envs,), device=self.device)
        self.stage3_time_preserve = torch.zeros((self.num_envs,), device=self.device)
        self.terminal_success_quality = torch.zeros((self.num_envs,), device=self.device)
        self.near_terminal_reward = torch.zeros((self.num_envs,), device=self.device)
        self.stage_latch_reward = torch.zeros((self.num_envs,), device=self.device)
        self.progressive_stage_weight = torch.zeros((self.num_envs,), device=self.device)
        self.moving_pregrasp_stage = torch.zeros((self.num_envs,), dtype=torch.long, device=self.device)
        self.moving_pregrasp_fraction = torch.zeros((self.num_envs,), device=self.device)
        self.moving_pregrasp_hold_count = torch.zeros((self.num_envs,), dtype=torch.long, device=self.device)
        self.moving_pregrasp_step_ready = torch.zeros((self.num_envs,), dtype=torch.bool, device=self.device)
        self.moving_pregrasp_reward = torch.zeros((self.num_envs,), device=self.device)
        self.moving_pregrasp_funnel_reward = torch.zeros((self.num_envs,), device=self.device)
        self.moving_pregrasp_exp_reward = torch.zeros((self.num_envs,), device=self.device)
        self.moving_pregrasp_shell_improvement = torch.zeros((self.num_envs,), device=self.device)
        self.best_moving_pregrasp_distance = torch.full((self.num_envs,), 10.0, device=self.device)
        self.best_moving_pregrasp_shell = torch.full((self.num_envs,), 999.0, device=self.device)
        self.final_insertion_reward = torch.zeros((self.num_envs,), device=self.device)
        self.pregrasp_line_error = torch.zeros((self.num_envs,), device=self.device)
        self.pregrasp_entry_reached = torch.zeros((self.num_envs,), dtype=torch.bool, device=self.device)
        self.pregrasp_held = torch.zeros((self.num_envs,), dtype=torch.bool, device=self.device)
        self.stage1_latched = torch.zeros((self.num_envs,), dtype=torch.bool, device=self.device)
        self.stage2_latched = torch.zeros((self.num_envs,), dtype=torch.bool, device=self.device)
        self.stage3_latched = torch.zeros((self.num_envs,), dtype=torch.bool, device=self.device)
        self.pregrasp_replay_states: dict[str, torch.Tensor] | None = self._load_pregrasp_replay_states()

        self._sample_targets(torch.arange(self.num_envs, device=self.device))

    @staticmethod
    def _apply_training_mode_cfg(cfg: MT4ReachEnvCfg) -> str:
        mode = os.environ.get("MT4_REACH_TRAINING_MODE", cfg.training_mode).strip().lower()
        cfg.training_mode = mode

        if mode in ("", "integrated", "full"):
            return "integrated"

        if mode in ("stage_b", "stage_b_insertion", "insertion"):
            # Stage B assumes the policy already has a usable pregrasp behavior.
            # It narrows the classroom target range and increases the learning
            # signal for moving from the blue pregrasp marker toward the red target.
            cfg.target_x_range = (0.22, 0.30)
            cfg.target_y_range = (-0.10, 0.10)
            cfg.target_z_range = (0.10, 0.16)
            cfg.pregrasp_entry_success_radius = 0.100
            cfg.pregrasp_entry_hold_radius = 0.080
            cfg.pregrasp_success_radius = 0.120
            cfg.pregrasp_hold_radius = 0.080
            cfg.success_radius = 0.065
            cfg.touch_success_band = 0.055
            cfg.stage1_alignment_weight = 1.2
            cfg.stage1_wrong_way_weight = 1.0
            cfg.stage2_entry_weight = 4.0
            cfg.stage2_entry_touch_weight = 2.0
            cfg.stage2_pregrasp_weight = 6.0
            cfg.stage2_touch_weight = 4.0
            cfg.stage2_hold_weight = 3.0
            cfg.stage2_center_progress_weight = 3.0
            cfg.stage3_line_weight = 2.8
            cfg.stage3_touch_weight = 10.0
            cfg.stage3_progress_weight = 9.0
            cfg.stage3_depth_weight = 12.0
            cfg.stage3_slow_weight = 1.2
            cfg.stage4_center_improvement_weight = 36.0
            cfg.stage4_center_precision_weight = 14.0
            cfg.pregrasp_bonus_weight = 0.5
            cfg.success_bonus_weight = 28.0
            cfg.target_contact_penalty_weight = 100.0
            cfg.action_penalty_weight = 0.010
            cfg.time_penalty_weight = 0.006
            return "stage_b_insertion"

        if mode in ("stage4", "stage4_center", "final_center"):
            # Stage 4 starts from near-insertion replay states and concentrates
            # the reward signal on placing the target center between the gripper tips.
            cfg.target_x_range = (0.22, 0.30)
            cfg.target_y_range = (-0.10, 0.10)
            cfg.target_z_range = (0.10, 0.16)
            cfg.pregrasp_entry_success_radius = 0.110
            cfg.pregrasp_entry_hold_radius = 0.090
            cfg.pregrasp_success_radius = 0.120
            cfg.pregrasp_hold_radius = 0.085
            cfg.success_radius = 0.065
            cfg.touch_success_band = 0.060
            cfg.stage3_insertion_start_progress = 0.10
            cfg.action_scale = float(os.environ.get("MT4_REACH_ACTION_SCALE", "0.030"))
            cfg.final_center_success_radius = float(
                os.environ.get("MT4_REACH_FINAL_CENTER_RADIUS", "0.035")
            )
            cfg.final_center_improvement_scale = float(
                os.environ.get("MT4_REACH_FINAL_CENTER_IMPROVEMENT_SCALE", "0.006")
            )
            cfg.stage1_alignment_weight = 0.8
            cfg.stage1_wrong_way_weight = 1.0
            cfg.stage2_entry_weight = 2.0
            cfg.stage2_entry_touch_weight = 1.0
            cfg.stage2_pregrasp_weight = 3.0
            cfg.stage2_touch_weight = 2.0
            cfg.stage2_hold_weight = 2.0
            cfg.stage2_center_progress_weight = 2.0
            cfg.stage3_line_weight = 3.2
            cfg.stage3_touch_weight = 12.0
            cfg.stage3_progress_weight = 8.0
            cfg.stage3_depth_weight = 12.0
            cfg.stage3_slow_weight = 1.4
            cfg.stage4_center_improvement_weight = 64.0
            cfg.stage4_center_precision_weight = 32.0
            cfg.stage4_center_push_weight = float(os.environ.get("MT4_REACH_STAGE4_PUSH_WEIGHT", "64.0"))
            cfg.stage4_center_push_improvement_weight = float(
                os.environ.get("MT4_REACH_STAGE4_PUSH_IMPROVEMENT_WEIGHT", "88.0")
            )
            cfg.stage4_center_push_depth_weight = float(
                os.environ.get("MT4_REACH_STAGE4_PUSH_DEPTH_WEIGHT", "36.0")
            )
            cfg.stage4_shortest_path_weight = float(
                os.environ.get("MT4_REACH_STAGE4_SHORTEST_PATH_WEIGHT", "36.0")
            )
            cfg.stage4_distance_shell_weight = float(
                os.environ.get("MT4_REACH_STAGE4_DISTANCE_SHELL_WEIGHT", "28.0")
            )
            cfg.stage3_time_preserve_weight = float(
                os.environ.get("MT4_REACH_STAGE3_TIME_PRESERVE_WEIGHT", "0.0")
            )
            cfg.terminal_success_quality_weight = float(
                os.environ.get("MT4_REACH_TERMINAL_SUCCESS_QUALITY_WEIGHT", "0.0")
            )
            cfg.near_terminal_weight = float(
                os.environ.get("MT4_REACH_NEAR_TERMINAL_WEIGHT", "0.0")
            )
            cfg.near_terminal_radius = float(
                os.environ.get("MT4_REACH_NEAR_TERMINAL_RADIUS", "0.050")
            )
            cfg.stage_latch_weight = float(
                os.environ.get("MT4_REACH_STAGE_LATCH_WEIGHT", "0.0")
            )
            cfg.progressive_stage_weight = float(
                os.environ.get("MT4_REACH_PROGRESSIVE_STAGE_WEIGHT", "0.0")
            )
            cfg.moving_pregrasp_enabled = os.environ.get(
                "MT4_REACH_MOVING_PREGRASP", "0"
            ).strip().lower() in ("1", "true", "yes", "on")
            cfg.moving_pregrasp_goal_mode = os.environ.get(
                "MT4_REACH_MOVING_PREGRASP_GOAL", cfg.moving_pregrasp_goal_mode
            ).strip().lower()
            if cfg.moving_pregrasp_goal_mode not in ("touch", "center"):
                raise ValueError(
                    "Unsupported MT4_REACH_MOVING_PREGRASP_GOAL. "
                    "Use 'touch' or 'center'. "
                    f"Received: {cfg.moving_pregrasp_goal_mode!r}"
                )
            cfg.desired_touch_distance = float(
                os.environ.get("MT4_REACH_DESIRED_TOUCH_DISTANCE", str(cfg.desired_touch_distance))
            )
            cfg.moving_pregrasp_step_count = int(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_STEPS", "3")
            )
            cfg.moving_pregrasp_final_fraction = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_FINAL_FRACTION", "0.70")
            )
            cfg.moving_pregrasp_step_radius = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_STEP_RADIUS", "0.080")
            )
            cfg.moving_pregrasp_hold_steps = int(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_HOLD_STEPS", "2")
            )
            cfg.moving_pregrasp_reward_weight = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_REWARD_WEIGHT", "20.0")
            )
            cfg.moving_pregrasp_funnel_weight = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_FUNNEL_WEIGHT", "0.0")
            )
            cfg.moving_pregrasp_funnel_depth = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_FUNNEL_DEPTH", "0.090")
            )
            cfg.moving_pregrasp_funnel_min_radius = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_FUNNEL_MIN_RADIUS", "0.020")
            )
            cfg.moving_pregrasp_funnel_max_radius = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_FUNNEL_MAX_RADIUS", "0.070")
            )
            cfg.moving_pregrasp_exp_weight = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_EXP_WEIGHT", "0.30")
            )
            cfg.moving_pregrasp_shell_weight = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_SHELL_WEIGHT", "0.25")
            )
            cfg.moving_pregrasp_shell_size = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_SHELL_SIZE", "0.005")
            )
            cfg.moving_pregrasp_exp_scale = float(
                os.environ.get("MT4_REACH_MOVING_PREGRASP_EXP_SCALE", "0.035")
            )
            cfg.final_insertion_weight = float(
                os.environ.get("MT4_REACH_FINAL_INSERTION_WEIGHT", "0.0")
            )
            cfg.center_push_improvement_scale = float(
                os.environ.get("MT4_REACH_CENTER_PUSH_IMPROVEMENT_SCALE", "0.012")
            )
            cfg.center_distance_shell_size = float(
                os.environ.get("MT4_REACH_CENTER_DISTANCE_SHELL_SIZE", "0.005")
            )
            cfg.stage4_push_ready_progress = float(
                os.environ.get("MT4_REACH_STAGE4_PUSH_READY_PROGRESS", "0.60")
            )
            cfg.stage4_success_min_progress = float(
                os.environ.get("MT4_REACH_STAGE4_SUCCESS_MIN_PROGRESS", "0.78")
            )
            cfg.stage4_success_max_progress = float(
                os.environ.get("MT4_REACH_STAGE4_SUCCESS_MAX_PROGRESS", "1.08")
            )
            cfg.early_target_clearance = float(
                os.environ.get("MT4_REACH_EARLY_TARGET_CLEARANCE", "0.055")
            )
            cfg.early_target_contact_penalty_weight = float(
                os.environ.get("MT4_REACH_EARLY_TARGET_CONTACT_PENALTY", "160.0")
            )
            cfg.stage4_overshoot_penalty_weight = float(
                os.environ.get("MT4_REACH_STAGE4_OVERSHOOT_PENALTY", "18.0")
            )
            cfg.gripper_roll_alignment_weight = float(
                os.environ.get("MT4_REACH_GRIPPER_ROLL_WEIGHT", "2.5")
            )
            cfg.pregrasp_bonus_weight = 0.2
            cfg.success_bonus_weight = float(os.environ.get("MT4_REACH_SUCCESS_BONUS", "48.0"))
            cfg.target_contact_penalty_weight = 120.0
            cfg.action_penalty_weight = float(os.environ.get("MT4_REACH_ACTION_PENALTY", "0.018"))
            cfg.time_penalty_weight = 0.003
            cfg.stage4_time_penalty_weight = float(
                os.environ.get("MT4_REACH_STAGE4_TIME_PENALTY", "0.045")
            )
            return "stage4_center"

        raise ValueError(
            "Unsupported MT4_REACH_TRAINING_MODE. "
            "Use 'integrated', 'stage_b_insertion', or 'stage4_center'. "
            f"Received: {mode!r}"
        )

    @staticmethod
    def _apply_reset_mode_cfg(cfg: MT4ReachEnvCfg) -> str:
        mode = os.environ.get("MT4_REACH_RESET_MODE", cfg.reset_mode).strip().lower()
        cfg.reset_mode = mode

        if mode in ("", "default", "folded"):
            return "default"

        if mode in ("pregrasp_replay", "replay"):
            cfg.pregrasp_replay_state_file = os.environ.get(
                "MT4_REACH_PREGRASP_STATE_FILE", cfg.pregrasp_replay_state_file
            )
            cfg.pregrasp_replay_probability = float(
                os.environ.get("MT4_REACH_REPLAY_PROB", str(cfg.pregrasp_replay_probability))
            )
            cfg.pregrasp_replay_joint_noise = float(
                os.environ.get("MT4_REACH_REPLAY_JOINT_NOISE", str(cfg.pregrasp_replay_joint_noise))
            )
            cfg.pregrasp_replay_target_noise = float(
                os.environ.get("MT4_REACH_REPLAY_TARGET_NOISE", str(cfg.pregrasp_replay_target_noise))
            )
            cfg.pregrasp_replay_joint_velocity_scale = float(
                os.environ.get(
                    "MT4_REACH_REPLAY_JOINT_VELOCITY_SCALE",
                    str(cfg.pregrasp_replay_joint_velocity_scale),
                )
            )
            return "pregrasp_replay"

        raise ValueError(
            "Unsupported MT4_REACH_RESET_MODE. "
            "Use 'default' or 'pregrasp_replay'. "
            f"Received: {mode!r}"
        )

    def _load_pregrasp_replay_states(self) -> dict[str, torch.Tensor] | None:
        if self.reset_mode != "pregrasp_replay":
            return None

        path = Path(self.cfg.pregrasp_replay_state_file).expanduser()
        if not path.is_file():
            raise FileNotFoundError(
                "MT4 pregrasp replay reset was requested, but the state file does not exist:\n"
                f"  {path}\n"
                "Run scripts/collect_pregrasp_states.sh first, or set MT4_REACH_PREGRASP_STATE_FILE."
            )

        data = torch.load(path, map_location="cpu", weights_only=False)
        required = ("joint_pos", "joint_vel", "targets")
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Invalid pregrasp replay state file: missing keys {missing} in {path}")

        states = {key: data[key].to(device=self.device, dtype=torch.float32) for key in required}
        if states["joint_pos"].ndim != 2 or states["joint_pos"].shape[1] != len(self.joint_names):
            raise ValueError(f"Invalid joint_pos shape in {path}: expected [N, {len(self.joint_names)}]")
        if states["targets"].ndim != 2 or states["targets"].shape[1] != 3:
            raise ValueError(f"Invalid targets shape in {path}: expected [N, 3]")
        if states["joint_pos"].shape[0] == 0:
            raise ValueError(f"No pregrasp replay states in {path}")

        return states

    def _setup_scene(self):
        self.robot = Articulation(self.cfg.robot_cfg)
        self.scene.articulations["robot"] = self.robot

        # simple ground
        ground_cfg = sim_utils.GroundPlaneCfg()
        ground_cfg.func("/World/defaultGroundPlane", ground_cfg)

        # light
        light_cfg = sim_utils.DomeLightCfg(intensity=1800.0, color=(0.85, 0.85, 0.85))
        light_cfg.func("/World/Light", light_cfg)

        self.scene.clone_environments(copy_from_source=False)
        self.scene.filter_collisions(global_prim_paths=["/World/defaultGroundPlane"])

    def _pre_physics_step(self, actions: torch.Tensor):
        self.actions = actions.clamp(-1.0, 1.0)

        self.joint_targets = self.joint_targets + self.cfg.action_scale * self.actions
        self.joint_targets = torch.max(torch.min(self.joint_targets, self.joint_upper), self.joint_lower)

    def _apply_action(self):
        self.robot.set_joint_position_target(self.joint_targets, joint_ids=self.joint_ids)

    def _get_observations(self):
        self._compute_intermediate_values()

        joint_pos = self.robot.data.joint_pos[:, self.joint_ids]
        joint_vel = self.robot.data.joint_vel[:, self.joint_ids]

        obs = torch.cat(
            [
                joint_pos,
                0.1 * joint_vel,
                self.gripper_tip_pos,
                self.targets,
                self.to_target,
                self.pregrasp_targets,
                self.to_pregrasp,
                self.gripper_forward,
                self.gripper_side,
            ],
            dim=-1,
        )

        return {"policy": obs}

    def _get_rewards(self):
        self._compute_intermediate_values()

        insertion_alignment_reward = torch.clamp(0.5 * (self.insertion_alignment + 1.0), min=0.0, max=1.0)
        gripper_roll_reward = torch.clamp(0.5 * (self.gripper_roll_alignment + 1.0), min=0.0, max=1.0)
        alignment_gate = torch.clamp((self.insertion_alignment - 0.10) / 0.90, min=0.0, max=1.0)
        pregrasp_entry_reward = 1.0 / (1.0 + 55.0 * self.pregrasp_entry_distance * self.pregrasp_entry_distance)
        pregrasp_entry_touch_reward = torch.exp(-650.0 * self.pregrasp_entry_distance * self.pregrasp_entry_distance)
        pregrasp_reward = 1.0 / (1.0 + 55.0 * self.pregrasp_distance * self.pregrasp_distance)
        pregrasp_touch_reward = torch.exp(-650.0 * self.pregrasp_distance * self.pregrasp_distance)
        pregrasp_center_progress_reward = torch.clamp(self.pregrasp_center_progress, min=0.0, max=1.0)
        wrong_way_penalty = torch.clamp(-self.insertion_alignment, min=0.0)
        touch_ready_reward = torch.exp(-360.0 * self.touch_target_distance * self.touch_target_distance)
        touch_depth_reward = 1.0 / (1.0 + 220.0 * self.touch_error * self.touch_error)
        insertion_line_reward = torch.exp(-520.0 * self.insertion_lateral_error * self.insertion_lateral_error)
        insertion_progress_reward = torch.clamp(self.insertion_progress, min=0.0, max=1.0)
        center_push_progress_reward = torch.clamp(self.center_push_progress, min=0.0, max=1.0)
        center_push_depth_reward = torch.clamp((self.center_push_progress - 0.50) / 0.40, min=0.0, max=1.0)
        center_push_reward = center_push_progress_reward * insertion_line_reward * insertion_alignment_reward
        center_shortest_path_score = insertion_line_reward * insertion_alignment_reward
        self.center_shortest_path_score = center_shortest_path_score
        center_precision_reward = torch.exp(-900.0 * self.distance * self.distance)
        action_penalty = torch.sum(self.actions * self.actions, dim=-1)
        joint_vel = self.robot.data.joint_vel[:, self.joint_ids]
        joint_velocity_penalty = torch.sum(joint_vel * joint_vel, dim=-1)
        hold_stability_reward = torch.exp(-self.cfg.pregrasp_hold_velocity_scale * joint_velocity_penalty)
        insertion_slow_reward = torch.exp(-0.04 * joint_velocity_penalty) * insertion_progress_reward
        pregrasp_hold_reward = (
            pregrasp_touch_reward
            * insertion_alignment_reward
            * hold_stability_reward
        )
        pregrasp_entry_ready = (
            (self.pregrasp_entry_distance < self.cfg.pregrasp_entry_hold_radius)
            & (self.insertion_alignment > self.cfg.insertion_alignment_success)
            & (hold_stability_reward > self.cfg.pregrasp_hold_min_stability)
        )
        self.pregrasp_entry_reached = self.pregrasp_entry_reached | pregrasp_entry_ready
        pregrasp_hold_ready = (
            (self.pregrasp_distance < self.cfg.pregrasp_hold_radius)
            & self.pregrasp_entry_reached
            & (self.insertion_alignment > self.cfg.insertion_alignment_success)
            & (hold_stability_reward > self.cfg.pregrasp_hold_min_stability)
        )
        self.pregrasp_held = self.pregrasp_held | pregrasp_hold_ready
        time_fraction = self.episode_length_buf.float() / max(float(self.max_episode_length), 1.0)
        pregrasp_entry_success = self.pregrasp_entry_distance < self.cfg.pregrasp_entry_success_radius
        pregrasp_success = self.pregrasp_distance < self.cfg.pregrasp_success_radius
        stage1_ready = self.insertion_alignment > self.cfg.insertion_alignment_success
        stage2_ready = stage1_ready & self.pregrasp_held
        stage3_ready = (
            stage2_ready
            & (self.insertion_lateral_error < self.cfg.touch_success_band)
            & (self.insertion_progress > self.cfg.stage3_insertion_start_progress)
        )
        center_best_initialized = self.best_target_center_distance < 9.0
        center_distance_improvement = torch.where(
            stage3_ready & center_best_initialized,
            torch.clamp(self.best_target_center_distance - self.distance, min=0.0),
            torch.zeros_like(self.distance),
        )
        self.target_center_improvement = center_distance_improvement
        center_push_improvement = torch.where(
            stage3_ready,
            torch.clamp(self.center_push_progress - self.best_center_push_progress, min=0.0),
            torch.zeros_like(self.center_push_progress),
        )
        self.center_push_improvement = center_push_improvement
        center_push_improvement_reward = torch.clamp(
            center_push_improvement / max(float(self.cfg.center_push_improvement_scale), 1e-6),
            min=0.0,
            max=1.0,
        )
        center_improvement_reward = torch.clamp(
            center_distance_improvement / max(float(self.cfg.final_center_improvement_scale), 1e-6),
            min=0.0,
            max=1.0,
        )
        center_distance_shell = torch.floor(
            self.distance / max(float(self.cfg.center_distance_shell_size), 1e-6)
        )
        shell_initialized = self.best_target_center_shell < 998.0
        center_shell_improvement = torch.where(
            stage3_ready & shell_initialized,
            torch.clamp(self.best_target_center_shell - center_distance_shell, min=0.0),
            torch.zeros_like(center_distance_shell),
        )
        self.target_center_shell_improvement = center_shell_improvement
        center_shell_reward = torch.clamp(center_shell_improvement, min=0.0, max=4.0) / 4.0
        center_shortest_improvement_reward = center_improvement_reward * center_shortest_path_score
        center_new_best_reward = torch.where(
            center_distance_improvement > 1e-5,
            center_precision_reward * center_shortest_path_score,
            torch.zeros_like(center_precision_reward),
        )
        self.best_target_center_distance = torch.where(
            stage3_ready,
            torch.minimum(self.best_target_center_distance, self.distance),
            self.best_target_center_distance,
        )
        self.best_target_center_shell = torch.where(
            stage3_ready,
            torch.minimum(self.best_target_center_shell, center_distance_shell),
            self.best_target_center_shell,
        )
        self.best_center_push_progress = torch.where(
            stage3_ready,
            torch.maximum(self.best_center_push_progress, self.center_push_progress),
            self.best_center_push_progress,
        )
        moving_pregrasp_step_count = max(int(self.cfg.moving_pregrasp_step_count), 1)
        final_center_ready = (
            stage3_ready
            & (self.center_push_progress_raw >= self.cfg.stage4_success_min_progress)
            & (self.center_push_progress_raw <= self.cfg.stage4_success_max_progress)
            & (self.distance < self.cfg.final_center_success_radius)
            & (self.body_target_clearance_error <= 1e-4)
        )
        if self.cfg.moving_pregrasp_enabled and self.cfg.moving_pregrasp_goal_mode == "center":
            blue_final_center_ready = (
                (self.moving_pregrasp_stage >= moving_pregrasp_step_count)
                & (self.pregrasp_distance < self.cfg.final_center_success_radius)
                & (self.insertion_alignment > self.cfg.insertion_alignment_success)
                & (self.insertion_lateral_error < self.cfg.touch_success_band)
                & (self.center_push_progress_raw >= self.cfg.stage4_success_min_progress)
                & (self.center_push_progress_raw <= self.cfg.stage4_success_max_progress)
                & (self.body_target_clearance_error <= 1e-4)
            )
        else:
            blue_final_center_ready = torch.zeros_like(final_center_ready, dtype=torch.bool)
        success = final_center_ready | blue_final_center_ready
        final_center_precision = torch.clamp(
            1.0 - self.distance / max(float(self.cfg.final_center_success_radius), 1e-6),
            min=0.0,
            max=1.0,
        )
        terminal_success_quality = success.float() * (
            0.45 * center_shortest_path_score
            + 0.30 * center_push_progress_reward
            + 0.25 * final_center_precision
        )
        near_terminal_margin = max(
            float(self.cfg.near_terminal_radius - self.cfg.final_center_success_radius),
            1e-6,
        )
        near_terminal_progress = torch.clamp(
            (float(self.cfg.near_terminal_radius) - self.distance) / near_terminal_margin,
            min=0.0,
            max=1.0,
        )
        near_terminal_ready = (
            stage3_ready
            & (~success)
            & (self.distance < self.cfg.near_terminal_radius)
            & (self.body_target_clearance_error <= 1e-4)
        )
        near_terminal_reward = (
            near_terminal_ready.float()
            * near_terminal_progress
            * (0.50 + 0.50 * center_shortest_path_score)
            * (0.50 + 0.50 * center_push_progress_reward)
        )
        stage3_time_preserve = (
            stage3_ready.float()
            * (~success).float()
            * time_fraction
            * insertion_line_reward
            * insertion_alignment_reward
            * touch_ready_reward
        )
        stage4_progress_factor = (
            self.stage3_latched.float()
            * center_push_progress_reward
            * center_shortest_path_score
        )
        progressive_stage_weight = 1.0 + self.cfg.progressive_stage_weight * stage4_progress_factor
        stage_latch_reward = (
            0.20 * self.stage1_latched.float() * insertion_alignment_reward
            + 0.30 * self.stage2_latched.float() * pregrasp_hold_reward
            + 0.50
            * self.stage3_latched.float()
            * insertion_line_reward
            * insertion_alignment_reward
            * touch_ready_reward
        ) * progressive_stage_weight
        moving_pregrasp_stage_progress = self.moving_pregrasp_stage.float() / float(moving_pregrasp_step_count)
        moving_pregrasp_reward = (
            moving_pregrasp_stage_progress
            * pregrasp_touch_reward
            * insertion_alignment_reward
            * (0.50 + 0.50 * center_shortest_path_score)
        )
        funnel_depth = max(float(self.cfg.moving_pregrasp_funnel_depth), 1e-6)
        funnel_min_radius = max(float(self.cfg.moving_pregrasp_funnel_min_radius), 1e-6)
        funnel_max_radius = max(float(self.cfg.moving_pregrasp_funnel_max_radius), funnel_min_radius)
        blue_axis = torch.sum(self.to_pregrasp * self.approach_dir, dim=-1)
        blue_lateral = self.to_pregrasp - blue_axis.unsqueeze(-1) * self.approach_dir
        blue_lateral_error = torch.linalg.norm(blue_lateral, dim=-1)
        blue_axis_clamped = torch.clamp(blue_axis, min=0.0, max=funnel_depth)
        blue_axis_fraction = blue_axis_clamped / funnel_depth
        blue_allowed_radius = funnel_min_radius + blue_axis_fraction * (funnel_max_radius - funnel_min_radius)
        blue_lateral_reward = torch.exp(
            -torch.square(blue_lateral_error / torch.clamp(blue_allowed_radius, min=1e-6))
        )
        blue_depth_reward = torch.clamp(1.0 - blue_axis_clamped / funnel_depth, min=0.0, max=1.0)
        blue_front_gate = ((blue_axis >= -0.010) & (blue_axis <= funnel_depth)).float()
        blue_exp_scale = max(float(self.cfg.moving_pregrasp_exp_scale), 1e-6)
        blue_exp_reward = torch.exp(-torch.square(self.pregrasp_distance / blue_exp_scale))
        blue_shell = torch.floor(
            self.pregrasp_distance / max(float(self.cfg.moving_pregrasp_shell_size), 1e-6)
        )
        blue_shell_initialized = self.best_moving_pregrasp_shell < 998.0
        blue_shell_improvement = torch.where(
            self.stage2_latched & blue_shell_initialized,
            torch.clamp(self.best_moving_pregrasp_shell - blue_shell, min=0.0),
            torch.zeros_like(blue_shell),
        )
        self.moving_pregrasp_shell_improvement = blue_shell_improvement
        blue_shell_reward = torch.clamp(blue_shell_improvement, min=0.0, max=4.0) / 4.0
        self.best_moving_pregrasp_distance = torch.where(
            self.stage2_latched,
            torch.minimum(self.best_moving_pregrasp_distance, self.pregrasp_distance),
            self.best_moving_pregrasp_distance,
        )
        self.best_moving_pregrasp_shell = torch.where(
            self.stage2_latched,
            torch.minimum(self.best_moving_pregrasp_shell, blue_shell),
            self.best_moving_pregrasp_shell,
        )
        blue_base_weight = max(
            0.0,
            1.0 - float(self.cfg.moving_pregrasp_exp_weight) - float(self.cfg.moving_pregrasp_shell_weight),
        )
        self.moving_pregrasp_exp_reward = blue_exp_reward
        moving_pregrasp_funnel_reward = (
            self.stage2_latched.float()
            * blue_front_gate
            * insertion_alignment_reward
            * (0.50 + 0.50 * center_shortest_path_score)
            * (
                blue_base_weight * (0.60 * blue_lateral_reward + 0.40 * blue_depth_reward)
                + float(self.cfg.moving_pregrasp_exp_weight) * blue_exp_reward
                + float(self.cfg.moving_pregrasp_shell_weight) * blue_shell_reward
            )
        )
        final_insertion_gate = self.stage3_latched.float()
        if self.cfg.moving_pregrasp_enabled:
            final_insertion_gate = final_insertion_gate * (
                self.moving_pregrasp_stage >= moving_pregrasp_step_count
            ).float()
        final_approach_ready = (
            stage3_ready
            & (self.insertion_alignment > self.cfg.insertion_alignment_success)
            & (self.insertion_lateral_error < self.cfg.touch_success_band)
            & (self.center_push_progress_raw >= self.cfg.stage4_success_min_progress)
            & (self.center_push_progress_raw <= self.cfg.stage4_success_max_progress)
        )
        early_target_contact_penalty = torch.where(
            final_approach_ready,
            torch.zeros_like(self.distance),
            torch.clamp(float(self.cfg.early_target_clearance) - self.distance, min=0.0),
        )
        final_insertion_reward = final_insertion_gate * (
            0.40 * center_push_reward
            + 0.30 * center_push_improvement_reward * center_shortest_path_score
            + 0.20 * center_shell_reward * center_shortest_path_score
            + 0.10 * near_terminal_reward
        )
        pregrasp_bonus = pregrasp_success.float() * self.cfg.pregrasp_bonus_weight
        success_bonus = success.float() * self.cfg.success_bonus_weight
        success_reward = success_bonus + self.cfg.terminal_success_quality_weight * terminal_success_quality
        stage4_time_pressure = stage3_ready.float() * time_fraction * (~success).float()

        shaping_reward = (
            self.cfg.stage1_alignment_weight * insertion_alignment_reward
            + self.cfg.gripper_roll_alignment_weight * gripper_roll_reward
            + alignment_gate * (
                self.cfg.stage2_entry_weight * pregrasp_entry_reward
                + self.cfg.stage2_entry_touch_weight * pregrasp_entry_touch_reward
                + self.pregrasp_entry_reached.float()
                * (
                    self.cfg.stage2_pregrasp_weight * pregrasp_reward
                    + self.cfg.stage2_touch_weight * pregrasp_touch_reward
                    + self.cfg.stage2_hold_weight * pregrasp_hold_reward
                    + self.cfg.stage2_center_progress_weight * pregrasp_center_progress_reward
                )
            )
            + (alignment_gate * self.pregrasp_held.float()) * (
                self.cfg.stage3_line_weight * insertion_line_reward * (0.25 + 0.75 * insertion_progress_reward)
                + self.cfg.stage3_touch_weight * touch_ready_reward
                + self.cfg.stage3_progress_weight * insertion_progress_reward
                + self.cfg.stage3_depth_weight * touch_depth_reward
                + self.cfg.stage3_slow_weight * insertion_slow_reward
                + self.cfg.stage3_time_preserve_weight * stage3_time_preserve
                + self.cfg.stage_latch_weight * stage_latch_reward
                + self.cfg.moving_pregrasp_reward_weight * moving_pregrasp_reward
                + self.cfg.moving_pregrasp_funnel_weight * moving_pregrasp_funnel_reward
                + self.cfg.final_insertion_weight * final_insertion_reward
                + self.cfg.stage4_center_improvement_weight
                * center_improvement_reward
                * (0.25 + 0.75 * center_shortest_path_score)
                + self.cfg.stage4_shortest_path_weight * center_shortest_improvement_reward
                + self.cfg.stage4_distance_shell_weight
                * center_shell_reward
                * center_shortest_path_score
                + self.cfg.stage4_center_precision_weight * center_new_best_reward
                + self.cfg.stage4_center_push_weight * center_push_reward
                + self.cfg.stage4_center_push_improvement_weight
                * center_push_improvement_reward
                * insertion_line_reward
                * insertion_alignment_reward
                + self.cfg.stage4_center_push_depth_weight
                * center_push_depth_reward
                * insertion_line_reward
                * insertion_alignment_reward
                + self.cfg.near_terminal_weight * near_terminal_reward
            )
            + pregrasp_bonus
            + pregrasp_entry_success.float() * 0.5
            - self.cfg.target_contact_penalty_weight * self.target_contact_penalty
            - self.cfg.early_target_contact_penalty_weight * early_target_contact_penalty
            - self.cfg.stage4_overshoot_penalty_weight * self.center_push_overshoot * stage3_ready.float()
            - self.cfg.stage1_wrong_way_weight * wrong_way_penalty
            - self.cfg.action_penalty_weight * action_penalty
            - self.cfg.joint_velocity_penalty_weight * joint_velocity_penalty
            - self.cfg.time_penalty_weight * time_fraction * (~success).float()
            - self.cfg.stage4_time_penalty_weight * stage4_time_pressure
        )
        reward = torch.where(success, success_reward, shaping_reward)
        self.stage3_time_preserve = stage3_time_preserve
        self.terminal_success_quality = terminal_success_quality
        self.near_terminal_reward = near_terminal_reward
        self.stage_latch_reward = stage_latch_reward
        self.progressive_stage_weight = progressive_stage_weight
        self.moving_pregrasp_reward = moving_pregrasp_reward
        self.moving_pregrasp_funnel_reward = moving_pregrasp_funnel_reward
        self.final_insertion_reward = final_insertion_reward
        self.early_target_contact_penalty = early_target_contact_penalty
        self.stage4_time_pressure = stage4_time_pressure
        return reward

    def _get_dones(self):
        self._compute_intermediate_values()

        success = (
            self.pregrasp_held
            & (self.insertion_alignment > self.cfg.insertion_alignment_success)
            & (self.insertion_lateral_error < self.cfg.touch_success_band)
            & (self.insertion_progress > self.cfg.stage3_insertion_start_progress)
            & (self.distance < self.cfg.final_center_success_radius)
            & (self.body_target_clearance_error <= 1e-4)
        )
        pregrasp_entry_success = self.pregrasp_entry_distance < self.cfg.pregrasp_entry_success_radius
        pregrasp_success = self.pregrasp_distance < self.cfg.pregrasp_success_radius
        joint_vel = self.robot.data.joint_vel[:, self.joint_ids]
        joint_velocity_penalty = torch.sum(joint_vel * joint_vel, dim=-1)
        hold_stability_reward = torch.exp(-self.cfg.pregrasp_hold_velocity_scale * joint_velocity_penalty)
        pregrasp_entry_ready = (
            (self.pregrasp_entry_distance < self.cfg.pregrasp_entry_hold_radius)
            & (self.insertion_alignment > self.cfg.insertion_alignment_success)
            & (hold_stability_reward > self.cfg.pregrasp_hold_min_stability)
        )
        self.pregrasp_entry_reached = self.pregrasp_entry_reached | pregrasp_entry_ready
        pregrasp_hold_ready = (
            (self.pregrasp_distance < self.cfg.pregrasp_hold_radius)
            & self.pregrasp_entry_reached
            & (self.insertion_alignment > self.cfg.insertion_alignment_success)
            & (hold_stability_reward > self.cfg.pregrasp_hold_min_stability)
        )
        self.pregrasp_held = self.pregrasp_held | pregrasp_hold_ready
        stage1_ready = self.insertion_alignment > self.cfg.insertion_alignment_success
        stage2_ready = stage1_ready & self.pregrasp_held
        stage3_ready = (
            stage2_ready
            & (self.insertion_lateral_error < self.cfg.touch_success_band)
            & (self.insertion_progress > self.cfg.stage3_insertion_start_progress)
        )
        self.stage1_latched = self.stage1_latched | stage1_ready
        self.stage2_latched = self.stage2_latched | (self.stage1_latched & self.pregrasp_held)
        self.stage3_latched = self.stage3_latched | (
            self.stage2_latched
            & (self.insertion_lateral_error < self.cfg.touch_success_band)
            & (self.insertion_progress > self.cfg.stage3_insertion_start_progress)
        )
        self._advance_moving_pregrasp(stage1_ready, hold_stability_reward)
        moving_pregrasp_step_count = max(int(self.cfg.moving_pregrasp_step_count), 1)
        if self.cfg.moving_pregrasp_enabled and self.cfg.moving_pregrasp_goal_mode == "center":
            blue_final_center_ready = (
                (self.moving_pregrasp_stage >= moving_pregrasp_step_count)
                & (self.pregrasp_distance < self.cfg.final_center_success_radius)
                & (self.insertion_alignment > self.cfg.insertion_alignment_success)
                & (self.insertion_lateral_error < self.cfg.touch_success_band)
                & (self.center_push_progress_raw >= self.cfg.stage4_success_min_progress)
                & (self.center_push_progress_raw <= self.cfg.stage4_success_max_progress)
                & (self.body_target_clearance_error <= 1e-4)
            )
        else:
            blue_final_center_ready = torch.zeros_like(success, dtype=torch.bool)
        success = success | blue_final_center_ready
        stage3_touch_ready = (
            stage3_ready
            & (self.insertion_progress > self.cfg.stage3_insertion_success_progress)
            & (self.touch_error < self.cfg.touch_success_band)
        )
        stage4_center_ready = (
            stage3_ready
            & (self.center_push_progress_raw >= self.cfg.stage4_success_min_progress)
            & (self.center_push_progress_raw <= self.cfg.stage4_success_max_progress)
            & (self.distance < self.cfg.final_center_success_radius)
            & (self.body_target_clearance_error <= 1e-4)
        )
        stage4_push_ready = (
            stage3_ready
            & (self.center_push_progress > self.cfg.stage4_push_ready_progress)
            & (self.insertion_lateral_error < self.cfg.touch_success_band)
        )
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        # Training/evaluation logs.
        self.extras["log"] = {
            "mt4/training_mode_stage_b": torch.tensor(
                1.0 if self.training_mode == "stage_b_insertion" else 0.0, device=self.device
            ),
            "mt4/training_mode_stage4": torch.tensor(
                1.0 if self.training_mode == "stage4_center" else 0.0, device=self.device
            ),
            "mt4/reset_mode_pregrasp_replay": torch.tensor(
                1.0 if self.reset_mode == "pregrasp_replay" else 0.0, device=self.device
            ),
            "mt4/success_rate": success.float().mean(),
            "mt4/stage1_alignment_ready_rate": stage1_ready.float().mean(),
            "mt4/stage1_latched_rate": self.stage1_latched.float().mean(),
            "mt4/pregrasp_entry_success_rate": pregrasp_entry_success.float().mean(),
            "mt4/pregrasp_entry_ready_rate": pregrasp_entry_ready.float().mean(),
            "mt4/pregrasp_entry_reached_rate": self.pregrasp_entry_reached.float().mean(),
            "mt4/pregrasp_success_rate": pregrasp_success.float().mean(),
            "mt4/pregrasp_hold_ready_rate": pregrasp_hold_ready.float().mean(),
            "mt4/pregrasp_held_rate": self.pregrasp_held.float().mean(),
            "mt4/stage2_pregrasp_ready_rate": stage2_ready.float().mean(),
            "mt4/stage2_latched_rate": self.stage2_latched.float().mean(),
            "mt4/stage2_alignment_ready_rate": stage1_ready.float().mean(),
            "mt4/stage3_insertion_ready_rate": stage3_ready.float().mean(),
            "mt4/stage3_latched_rate": self.stage3_latched.float().mean(),
            "mt4/stage3_touch_ready_rate": stage3_touch_ready.float().mean(),
            "mt4/stage4_center_ready_rate": stage4_center_ready.float().mean(),
            "mt4/blue_final_center_ready_rate": blue_final_center_ready.float().mean(),
            "mt4/stage4_push_ready_rate": stage4_push_ready.float().mean(),
            "mt4/mean_distance": self.distance.mean(),
            "mt4/mean_pregrasp_entry_distance": self.pregrasp_entry_distance.mean(),
            "mt4/mean_pregrasp_distance": self.pregrasp_distance.mean(),
            "mt4/mean_gripper_center_pregrasp_distance": self.pregrasp_distance.mean(),
            "mt4/mean_touch_target_distance": self.touch_target_distance.mean(),
            "mt4/mean_insertion_lateral_error": self.insertion_lateral_error.mean(),
            "mt4/mean_alignment": self.alignment.mean(),
            "mt4/mean_pregrasp_alignment": self.pregrasp_alignment.mean(),
            "mt4/mean_insertion_alignment": self.insertion_alignment.mean(),
            "mt4/mean_touch_error": self.touch_error.mean(),
            "mt4/mean_object_overlap": self.object_overlap.mean(),
            "mt4/mean_body_target_clearance_error": self.body_target_clearance_error.mean(),
            "mt4/mean_target_contact_penalty": self.target_contact_penalty.mean(),
            "mt4/mean_early_target_contact_penalty": self.early_target_contact_penalty.mean(),
            "mt4/mean_pregrasp_center_progress": self.pregrasp_center_progress.mean(),
            "mt4/mean_insertion_progress": self.insertion_progress.mean(),
            "mt4/mean_center_push_progress": self.center_push_progress.mean(),
            "mt4/mean_center_push_overshoot": self.center_push_overshoot.mean(),
            "mt4/mean_best_center_push_progress": self.best_center_push_progress.mean(),
            "mt4/mean_center_push_improvement": self.center_push_improvement.mean(),
            "mt4/mean_best_target_center_distance": torch.clamp(
                self.best_target_center_distance, max=1.0
            ).mean(),
            "mt4/mean_target_center_improvement": self.target_center_improvement.mean(),
            "mt4/mean_target_center_shell_improvement": self.target_center_shell_improvement.mean(),
            "mt4/mean_center_shortest_path_score": self.center_shortest_path_score.mean(),
            "mt4/mean_stage4_time_pressure": getattr(
                self, "stage4_time_pressure", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_stage3_time_preserve": getattr(
                self, "stage3_time_preserve", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_terminal_success_quality": getattr(
                self, "terminal_success_quality", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_near_terminal_reward": getattr(
                self, "near_terminal_reward", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_stage_latch_reward": getattr(
                self, "stage_latch_reward", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_progressive_stage_weight": getattr(
                self, "progressive_stage_weight", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_moving_pregrasp_fraction": self.moving_pregrasp_fraction.mean(),
            "mt4/moving_pregrasp_final_rate": (
                self.moving_pregrasp_stage >= max(int(self.cfg.moving_pregrasp_step_count), 1)
            ).float().mean(),
            "mt4/moving_pregrasp_step_ready_rate": getattr(
                self, "moving_pregrasp_step_ready", torch.zeros_like(success, dtype=torch.bool)
            ).float().mean(),
            "mt4/mean_moving_pregrasp_hold_progress": (
                self.moving_pregrasp_hold_count.float()
                / max(float(max(int(self.cfg.moving_pregrasp_hold_steps), 1)), 1.0)
            ).clamp(max=1.0).mean(),
            "mt4/mean_moving_pregrasp_reward": getattr(
                self, "moving_pregrasp_reward", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_moving_pregrasp_funnel_reward": getattr(
                self, "moving_pregrasp_funnel_reward", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_moving_pregrasp_exp_reward": getattr(
                self, "moving_pregrasp_exp_reward", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_moving_pregrasp_shell_improvement": getattr(
                self, "moving_pregrasp_shell_improvement", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_best_moving_pregrasp_distance": torch.clamp(
                getattr(self, "best_moving_pregrasp_distance", torch.zeros_like(self.distance)),
                max=1.0,
            ).mean(),
            "mt4/mean_final_insertion_reward": getattr(
                self, "final_insertion_reward", torch.zeros_like(self.distance)
            ).mean(),
            "mt4/mean_pregrasp_line_error": self.pregrasp_line_error.mean(),
            "mt4/mean_gripper_roll_alignment": self.gripper_roll_alignment.mean(),
            "mt4/min_distance": self.distance.min(),
        }

        return success, time_out

    def _reset_idx(self, env_ids: torch.Tensor | None):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES

        super()._reset_idx(env_ids)

        self.robot.reset(env_ids)

        joint_pos = self.robot.data.default_joint_pos[env_ids].clone()
        joint_vel = self.robot.data.default_joint_vel[env_ids].clone()

        joint_pos[:, self.joint_ids] = self.home_joint_pos
        joint_vel[:, self.joint_ids] = 0.0

        self.robot.write_joint_state_to_sim(joint_pos, joint_vel, env_ids=env_ids)

        self.joint_targets[env_ids] = self.home_joint_pos
        self.best_target_center_distance[env_ids] = 10.0
        self.target_center_improvement[env_ids] = 0.0
        self.best_center_push_progress[env_ids] = 0.0
        self.center_push_improvement[env_ids] = 0.0
        self.best_target_center_shell[env_ids] = 999.0
        self.target_center_shell_improvement[env_ids] = 0.0
        self.center_shortest_path_score[env_ids] = 0.0
        self.stage4_time_pressure[env_ids] = 0.0
        self.early_target_contact_penalty[env_ids] = 0.0
        self.center_push_progress_raw[env_ids] = 0.0
        self.center_push_overshoot[env_ids] = 0.0
        self.stage3_time_preserve[env_ids] = 0.0
        self.terminal_success_quality[env_ids] = 0.0
        self.near_terminal_reward[env_ids] = 0.0
        self.stage_latch_reward[env_ids] = 0.0
        self.progressive_stage_weight[env_ids] = 0.0
        self.moving_pregrasp_stage[env_ids] = 0
        self.moving_pregrasp_fraction[env_ids] = 0.0
        self.moving_pregrasp_hold_count[env_ids] = 0
        self.moving_pregrasp_step_ready[env_ids] = False
        self.moving_pregrasp_reward[env_ids] = 0.0
        self.moving_pregrasp_funnel_reward[env_ids] = 0.0
        self.moving_pregrasp_exp_reward[env_ids] = 0.0
        self.moving_pregrasp_shell_improvement[env_ids] = 0.0
        self.best_moving_pregrasp_distance[env_ids] = 10.0
        self.best_moving_pregrasp_shell[env_ids] = 999.0
        self.final_insertion_reward[env_ids] = 0.0
        self.pregrasp_entry_reached[env_ids] = False
        self.pregrasp_held[env_ids] = False
        self.stage1_latched[env_ids] = False
        self.stage2_latched[env_ids] = False
        self.stage3_latched[env_ids] = False
        self._sample_targets(env_ids)
        self._apply_pregrasp_replay_reset(env_ids)

    def _apply_pregrasp_replay_reset(self, env_ids: torch.Tensor):
        if self.pregrasp_replay_states is None or len(env_ids) == 0:
            return

        replay_prob = min(max(float(self.cfg.pregrasp_replay_probability), 0.0), 1.0)
        replay_mask = torch.rand(len(env_ids), device=self.device) < replay_prob
        if not torch.any(replay_mask):
            return

        replay_env_ids = env_ids[replay_mask]
        state_count = self.pregrasp_replay_states["joint_pos"].shape[0]
        sample_ids = torch.randint(0, state_count, (len(replay_env_ids),), device=self.device)

        replay_joint_pos = self.pregrasp_replay_states["joint_pos"][sample_ids].clone()
        replay_joint_vel = self.pregrasp_replay_states["joint_vel"][sample_ids].clone()
        replay_targets = self.pregrasp_replay_states["targets"][sample_ids].clone()

        if self.cfg.pregrasp_replay_joint_noise > 0.0:
            replay_joint_pos += self.cfg.pregrasp_replay_joint_noise * torch.randn_like(replay_joint_pos)
        if self.cfg.pregrasp_replay_target_noise > 0.0:
            replay_targets += self.cfg.pregrasp_replay_target_noise * torch.randn_like(replay_targets)

        replay_joint_pos = torch.max(torch.min(replay_joint_pos, self.joint_upper), self.joint_lower)
        replay_joint_vel = replay_joint_vel * float(self.cfg.pregrasp_replay_joint_velocity_scale)

        joint_pos = self.robot.data.joint_pos[replay_env_ids].clone()
        joint_vel = self.robot.data.joint_vel[replay_env_ids].clone()
        joint_pos[:, self.joint_ids] = replay_joint_pos
        joint_vel[:, self.joint_ids] = replay_joint_vel

        self.robot.write_joint_state_to_sim(joint_pos, joint_vel, env_ids=replay_env_ids)
        self.joint_targets[replay_env_ids] = replay_joint_pos
        self.targets[replay_env_ids] = replay_targets
        self._compute_target_geometry(replay_env_ids)
        self._compute_intermediate_values()
        self.best_center_push_progress[replay_env_ids] = self.center_push_progress[replay_env_ids]
        self._update_target_markers()

    def _sample_targets(self, env_ids: torch.Tensor):
        n = len(env_ids)

        x = torch.empty(n, device=self.device).uniform_(*self.cfg.target_x_range)
        y = torch.empty(n, device=self.device).uniform_(*self.cfg.target_y_range)
        z = torch.empty(n, device=self.device).uniform_(*self.cfg.target_z_range)

        for _ in range(4):
            radial = torch.sqrt(x * x + y * y)
            too_close = radial < self.cfg.min_target_base_radius
            if not torch.any(too_close):
                break
            count = int(too_close.sum().item())
            x[too_close] = torch.empty(count, device=self.device).uniform_(*self.cfg.target_x_range)
            y[too_close] = torch.empty(count, device=self.device).uniform_(*self.cfg.target_y_range)

        self.targets[env_ids, 0] = x
        self.targets[env_ids, 1] = y
        self.targets[env_ids, 2] = z

        self._compute_target_geometry(env_ids)
        self._update_target_markers()

    def _compute_target_geometry(self, env_ids: torch.Tensor | None = None):
        if env_ids is None:
            env_ids = torch.arange(self.num_envs, device=self.device)

        targets = self.targets[env_ids]
        radial_dir = targets.clone()
        radial_dir[:, 2] = 0.0
        fallback = torch.tensor([1.0, 0.0, 0.0], device=self.device).repeat(len(env_ids), 1)
        radial_norm = torch.linalg.norm(radial_dir, dim=-1, keepdim=True)
        radial_dir = torch.where(radial_norm > 1e-6, radial_dir / torch.clamp(radial_norm, min=1e-6), fallback)
        up_dir = torch.tensor([0.0, 0.0, 1.0], device=self.device).repeat(len(env_ids), 1)

        # The blue marker is intentionally constructed on the base-center -> red-target radial line.
        # XY: move toward the robot base along radial_dir. Z: move upward. This keeps the gripper approach
        # centered on the red target instead of introducing a sideways marker offset.
        pregrasp_targets = (
            targets
            - self.cfg.pregrasp_horizontal_offset * radial_dir
            + self.cfg.pregrasp_vertical_offset * up_dir
        )
        approach_dir = targets - pregrasp_targets
        approach_dir = approach_dir / torch.clamp(torch.linalg.norm(approach_dir, dim=-1, keepdim=True), min=1e-6)
        pregrasp_entry_targets = pregrasp_targets - self.cfg.pregrasp_entry_offset * approach_dir

        self.approach_dir[env_ids] = approach_dir
        self.pregrasp_entry_targets[env_ids] = pregrasp_entry_targets
        self.pregrasp_start_targets[env_ids] = pregrasp_targets
        if self.cfg.moving_pregrasp_goal_mode == "center":
            self.pregrasp_goal_targets[env_ids] = targets
        else:
            self.pregrasp_goal_targets[env_ids] = targets - self.cfg.desired_touch_distance * approach_dir
        if self.cfg.moving_pregrasp_enabled:
            fraction = self.moving_pregrasp_fraction[env_ids].unsqueeze(-1)
            pregrasp_targets = pregrasp_targets + fraction * (
                self.pregrasp_goal_targets[env_ids] - pregrasp_targets
            )
            pregrasp_entry_targets = pregrasp_targets - self.cfg.pregrasp_entry_offset * approach_dir
            self.pregrasp_entry_targets[env_ids] = pregrasp_entry_targets
        self.pregrasp_targets[env_ids] = pregrasp_targets
        self.touch_targets[env_ids] = self.pregrasp_goal_targets[env_ids]
        desired_pregrasp_dir = approach_dir
        self.desired_pregrasp_dir[env_ids] = desired_pregrasp_dir
        self.desired_insertion_dir[env_ids] = approach_dir
        self.desired_gripper_dir[env_ids] = desired_pregrasp_dir

    def _advance_moving_pregrasp(self, stage1_ready: torch.Tensor, hold_stability_reward: torch.Tensor):
        if not self.cfg.moving_pregrasp_enabled:
            return

        step_count = max(int(self.cfg.moving_pregrasp_step_count), 1)
        final_fraction = min(max(float(self.cfg.moving_pregrasp_final_fraction), 0.0), 1.0)
        hold_steps = max(int(self.cfg.moving_pregrasp_hold_steps), 1)
        current_step_reached = (
            stage1_ready
            & (self.pregrasp_distance < self.cfg.moving_pregrasp_step_radius)
            & (hold_stability_reward > self.cfg.pregrasp_hold_min_stability)
        )
        self.moving_pregrasp_step_ready = current_step_reached
        self.moving_pregrasp_hold_count = torch.where(
            current_step_reached,
            torch.clamp(self.moving_pregrasp_hold_count + 1, max=hold_steps),
            torch.zeros_like(self.moving_pregrasp_hold_count),
        )
        can_advance = (
            current_step_reached
            & (self.moving_pregrasp_hold_count >= hold_steps)
            & (self.moving_pregrasp_stage < step_count)
        )
        if not torch.any(can_advance):
            return

        env_ids = torch.nonzero(can_advance, as_tuple=False).squeeze(-1)
        self.moving_pregrasp_stage[env_ids] += 1
        self.moving_pregrasp_hold_count[env_ids] = 0
        self.moving_pregrasp_step_ready[env_ids] = False
        self.best_moving_pregrasp_distance[env_ids] = 10.0
        self.best_moving_pregrasp_shell[env_ids] = 999.0
        self.moving_pregrasp_shell_improvement[env_ids] = 0.0
        self.moving_pregrasp_fraction[env_ids] = (
            self.moving_pregrasp_stage[env_ids].float() / float(step_count)
        ) * final_fraction
        self._compute_target_geometry(env_ids)
        self._update_target_markers()

    def _compute_intermediate_values(self):
        wrist_pos_w = self.robot.data.body_pos_w[:, self.ee_body_id, :]
        wrist_quat_w = self.robot.data.body_quat_w[:, self.ee_body_id, :]
        self.wrist_pos = wrist_pos_w - self.scene.env_origins

        center_offset_b = torch.tensor(self.cfg.gripper_center_offset_b, device=self.device).repeat(self.num_envs, 1)
        forward_axis_b = torch.tensor(self.cfg.gripper_forward_axis_b, device=self.device).repeat(self.num_envs, 1)
        side_axis_b = torch.tensor(self.cfg.gripper_side_axis_b, device=self.device).repeat(self.num_envs, 1)
        self.gripper_center_pos = self.wrist_pos + math_utils.quat_apply(wrist_quat_w, center_offset_b)
        # Keep the legacy variable name for existing observations/tools. It now represents
        # the midpoint between the two gripper pads, which is the point that must meet blue.
        self.gripper_tip_pos = self.gripper_center_pos
        self.gripper_forward = math_utils.quat_apply(wrist_quat_w, forward_axis_b)
        self.gripper_forward = self.gripper_forward / torch.clamp(torch.linalg.norm(self.gripper_forward, dim=-1, keepdim=True), min=1e-6)
        self.gripper_side = math_utils.quat_apply(wrist_quat_w, side_axis_b)
        self.gripper_side = self.gripper_side / torch.clamp(torch.linalg.norm(self.gripper_side, dim=-1, keepdim=True), min=1e-6)
        world_up = torch.tensor([0.0, 0.0, 1.0], device=self.device).repeat(self.num_envs, 1)
        up_along_approach = torch.sum(world_up * self.approach_dir, dim=-1, keepdim=True) * self.approach_dir
        up_perp = world_up - up_along_approach
        up_perp_norm = torch.linalg.norm(up_perp, dim=-1, keepdim=True)
        up_perp = torch.where(up_perp_norm > 1e-6, up_perp / torch.clamp(up_perp_norm, min=1e-6), world_up)
        self.gripper_roll_alignment = torch.sum(self.gripper_side * up_perp, dim=-1)

        self.to_target = self.targets - self.gripper_tip_pos
        self.to_pregrasp_entry = self.pregrasp_entry_targets - self.gripper_tip_pos
        self.to_pregrasp = self.pregrasp_targets - self.gripper_tip_pos
        self.to_touch = self.touch_targets - self.gripper_tip_pos
        self.distance = torch.linalg.norm(self.to_target, dim=-1)
        self.pregrasp_entry_distance = torch.linalg.norm(self.to_pregrasp_entry, dim=-1)
        self.pregrasp_distance = torch.linalg.norm(self.to_pregrasp, dim=-1)
        self.touch_target_distance = torch.linalg.norm(self.to_touch, dim=-1)
        self.touch_error = torch.abs(self.distance - self.cfg.desired_touch_distance)
        self.object_overlap = torch.clamp(self.cfg.target_radius - self.distance, min=0.0)
        body_pos = self.robot.data.body_pos_w - self.scene.env_origins.unsqueeze(1)
        body_to_target = body_pos - self.targets.unsqueeze(1)
        body_target_distance = torch.linalg.norm(body_to_target, dim=-1)
        # The gripper link is allowed to contain the visual target center for the
        # final grasp-ready pose. Other links should still avoid the target.
        body_target_distance[:, self.ee_body_id] = 10.0
        min_body_target_distance = torch.min(body_target_distance, dim=-1).values
        self.body_target_clearance_error = torch.clamp(
            self.cfg.min_robot_target_clearance - min_body_target_distance, min=0.0
        )
        self.target_contact_penalty = self.body_target_clearance_error
        insertion_axis = torch.sum(self.to_touch * self.approach_dir, dim=-1, keepdim=True) * self.approach_dir
        insertion_lateral = self.to_touch - insertion_axis
        self.insertion_lateral_error = torch.linalg.norm(insertion_lateral, dim=-1)
        self.pregrasp_alignment = torch.sum(self.gripper_forward * self.desired_pregrasp_dir, dim=-1)
        self.insertion_alignment = torch.sum(self.gripper_forward * self.desired_insertion_dir, dim=-1)
        self.alignment = self.insertion_alignment
        self.clearance_error = torch.clamp(self.cfg.min_object_clearance - self.distance, min=0.0)
        target_xy = self.targets[:, :2]
        pregrasp_xy = self.pregrasp_targets[:, :2]
        radial_norm = torch.linalg.norm(target_xy, dim=-1, keepdim=True)
        radial_unit = target_xy / torch.clamp(radial_norm, min=1e-6)
        pregrasp_projection = torch.sum(pregrasp_xy * radial_unit, dim=-1, keepdim=True) * radial_unit
        self.pregrasp_line_error = torch.linalg.norm(pregrasp_xy - pregrasp_projection, dim=-1)
        entry_to_center_length = torch.linalg.norm(self.pregrasp_targets - self.pregrasp_entry_targets, dim=-1)
        raw_center_progress = torch.sum((self.gripper_tip_pos - self.pregrasp_entry_targets) * self.approach_dir, dim=-1)
        self.pregrasp_center_progress = torch.clamp(
            raw_center_progress / torch.clamp(entry_to_center_length, min=1e-6), min=0.0, max=1.0
        )
        insertion_path_length = torch.linalg.norm(self.touch_targets - self.pregrasp_targets, dim=-1)
        raw_progress = torch.sum((self.gripper_tip_pos - self.pregrasp_targets) * self.approach_dir, dim=-1)
        self.insertion_progress = torch.clamp(raw_progress / torch.clamp(insertion_path_length, min=1e-6), min=0.0, max=1.0)
        center_path_length = torch.linalg.norm(self.targets - self.pregrasp_start_targets, dim=-1)
        raw_center_push = torch.sum((self.gripper_tip_pos - self.pregrasp_start_targets) * self.approach_dir, dim=-1)
        self.center_push_progress_raw = raw_center_push / torch.clamp(center_path_length, min=1e-6)
        self.center_push_progress = torch.clamp(
            self.center_push_progress_raw, min=0.0, max=1.0
        )
        self.center_push_overshoot = torch.clamp(
            self.center_push_progress_raw - float(self.cfg.stage4_success_max_progress),
            min=0.0,
        )

    def _update_target_markers(self):
        if not hasattr(self, "target_markers"):
            return

        # targets are stored in local env coordinates, so add env origins for world positions.
        target_pos_w = self.targets + self.scene.env_origins
        self.target_markers.visualize(target_pos_w)

        if hasattr(self, "pregrasp_markers"):
            pregrasp_pos_w = self.pregrasp_targets + self.scene.env_origins
            self.pregrasp_markers.visualize(pregrasp_pos_w)

        if hasattr(self, "success_markers"):
            # If success, show green marker at target.
            # If not success, hide marker far below the ground.
            success = (
                self.pregrasp_held
                & (self.insertion_alignment > self.cfg.insertion_alignment_success)
                & (self.insertion_lateral_error < self.cfg.touch_success_band)
                & (self.insertion_progress > self.cfg.stage3_insertion_start_progress)
                & (self.center_push_progress_raw >= self.cfg.stage4_success_min_progress)
                & (self.center_push_progress_raw <= self.cfg.stage4_success_max_progress)
                & (self.distance < self.cfg.final_center_success_radius)
                & (self.body_target_clearance_error <= 1e-4)
            )
            if self.cfg.moving_pregrasp_enabled and self.cfg.moving_pregrasp_goal_mode == "center":
                step_count = max(int(self.cfg.moving_pregrasp_step_count), 1)
                blue_final_center_ready = (
                    (self.moving_pregrasp_stage >= step_count)
                    & (self.pregrasp_distance < self.cfg.final_center_success_radius)
                    & (self.insertion_alignment > self.cfg.insertion_alignment_success)
                    & (self.insertion_lateral_error < self.cfg.touch_success_band)
                    & (self.center_push_progress_raw >= self.cfg.stage4_success_min_progress)
                    & (self.center_push_progress_raw <= self.cfg.stage4_success_max_progress)
                    & (self.body_target_clearance_error <= 1e-4)
                )
                success = success | blue_final_center_ready
            success_pos_w = target_pos_w.clone()
            success_pos_w[~success, 2] = -10.0
            self.success_markers.visualize(success_pos_w)
