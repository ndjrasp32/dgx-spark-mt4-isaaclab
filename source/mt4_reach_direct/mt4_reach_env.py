from __future__ import annotations

import os

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
    observation_space = 28
    state_space = 0

    # "integrated" keeps the original staged reach reward. "stage_b_insertion" is a
    # curriculum profile used after the approach/pregrasp policy already works.
    training_mode = "integrated"

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
                radius=0.035,
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
                radius=0.045,
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
                radius=0.025,
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
    gripper_tip_offset_b = (0.166, 0.0, 0.0)
    gripper_forward_axis_b = (1.0, 0.0, 0.0)
    target_radius = 0.035
    desired_touch_distance = 0.040
    touch_success_band = 0.045
    pregrasp_standoff = 0.080
    pregrasp_success_radius = 0.095
    approach_horizontal_weight = 1.0
    approach_down_weight = 1.0
    min_object_clearance = 0.035
    min_robot_target_clearance = 0.045
    max_success_overlap = 0.003
    alignment_success = 0.62
    insertion_alignment_success = 0.70

    # staged reward weights for classroom tuning
    stage1_alignment_weight = 3.4
    stage1_wrong_way_weight = 1.0
    stage2_pregrasp_weight = 3.8
    stage2_touch_weight = 2.4
    stage2_hold_weight = 1.0
    stage3_line_weight = 3.4
    stage3_touch_weight = 5.0
    stage3_progress_weight = 3.0
    stage3_depth_weight = 5.0
    pregrasp_bonus_weight = 1.2
    success_bonus_weight = 18.0
    target_contact_penalty_weight = 70.0
    wrong_way_penalty_weight = 0.8
    action_penalty_weight = 0.012
    joint_velocity_penalty_weight = 0.0004
    time_penalty_weight = 0.004


class MT4ReachEnv(DirectRLEnv):
    cfg: MT4ReachEnvCfg

    def __init__(self, cfg: MT4ReachEnvCfg, render_mode: str | None = None, **kwargs):
        self.training_mode = self._apply_training_mode_cfg(cfg)
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
        self.gripper_tip_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.gripper_forward = torch.zeros((self.num_envs, 3), device=self.device)
        self.approach_dir = torch.zeros((self.num_envs, 3), device=self.device)
        self.desired_gripper_dir = torch.zeros((self.num_envs, 3), device=self.device)
        self.desired_pregrasp_dir = torch.zeros((self.num_envs, 3), device=self.device)
        self.desired_insertion_dir = torch.zeros((self.num_envs, 3), device=self.device)
        self.pregrasp_targets = torch.zeros((self.num_envs, 3), device=self.device)
        self.touch_targets = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_target = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_pregrasp = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_touch = torch.zeros((self.num_envs, 3), device=self.device)
        self.distance = torch.zeros((self.num_envs,), device=self.device)
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
        self.insertion_progress = torch.zeros((self.num_envs,), device=self.device)

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
            cfg.pregrasp_success_radius = 0.110
            cfg.success_radius = 0.065
            cfg.touch_success_band = 0.055
            cfg.stage1_alignment_weight = 2.4
            cfg.stage1_wrong_way_weight = 0.8
            cfg.stage2_pregrasp_weight = 2.0
            cfg.stage2_touch_weight = 1.2
            cfg.stage2_hold_weight = 0.6
            cfg.stage3_line_weight = 4.8
            cfg.stage3_touch_weight = 7.0
            cfg.stage3_progress_weight = 5.5
            cfg.stage3_depth_weight = 9.0
            cfg.pregrasp_bonus_weight = 0.5
            cfg.success_bonus_weight = 28.0
            cfg.target_contact_penalty_weight = 100.0
            cfg.action_penalty_weight = 0.010
            cfg.time_penalty_weight = 0.006
            return "stage_b_insertion"

        raise ValueError(
            "Unsupported MT4_REACH_TRAINING_MODE. "
            "Use 'integrated' or 'stage_b_insertion'. "
            f"Received: {mode!r}"
        )

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
            ],
            dim=-1,
        )

        return {"policy": obs}

    def _get_rewards(self):
        self._compute_intermediate_values()

        insertion_alignment_reward = torch.clamp(0.5 * (self.insertion_alignment + 1.0), min=0.0, max=1.0)
        alignment_gate = torch.clamp((self.insertion_alignment - 0.10) / 0.90, min=0.0, max=1.0)
        pregrasp_reward = 1.0 / (1.0 + 55.0 * self.pregrasp_distance * self.pregrasp_distance)
        pregrasp_touch_reward = torch.exp(-650.0 * self.pregrasp_distance * self.pregrasp_distance)
        pregrasp_gate = torch.exp(-120.0 * self.pregrasp_distance * self.pregrasp_distance)
        wrong_way_penalty = torch.clamp(-self.insertion_alignment, min=0.0)
        stage3_gate = alignment_gate * pregrasp_gate
        touch_ready_reward = torch.exp(-360.0 * self.touch_target_distance * self.touch_target_distance)
        touch_depth_reward = 1.0 / (1.0 + 220.0 * self.touch_error * self.touch_error)
        insertion_line_reward = torch.exp(-520.0 * self.insertion_lateral_error * self.insertion_lateral_error)
        action_penalty = torch.sum(self.actions * self.actions, dim=-1)
        joint_vel = self.robot.data.joint_vel[:, self.joint_ids]
        joint_velocity_penalty = torch.sum(joint_vel * joint_vel, dim=-1)
        time_fraction = self.episode_length_buf.float() / max(float(self.max_episode_length), 1.0)
        pregrasp_success = self.pregrasp_distance < self.cfg.pregrasp_success_radius
        stage2_ready = self.insertion_alignment > self.cfg.insertion_alignment_success
        stage3_ready = stage2_ready & pregrasp_success & (self.insertion_lateral_error < self.cfg.touch_success_band)
        success = (
            (self.touch_target_distance < self.cfg.success_radius)
            & stage3_ready
            & (self.touch_error < self.cfg.touch_success_band)
            & (self.object_overlap <= self.cfg.max_success_overlap)
            & (self.body_target_clearance_error <= 1e-4)
        )
        pregrasp_bonus = pregrasp_success.float() * self.cfg.pregrasp_bonus_weight
        success_bonus = success.float() * self.cfg.success_bonus_weight

        reward = (
            self.cfg.stage1_alignment_weight * insertion_alignment_reward
            + alignment_gate * (
                self.cfg.stage2_pregrasp_weight * pregrasp_reward
                + self.cfg.stage2_touch_weight * pregrasp_touch_reward
                + self.cfg.stage2_hold_weight * insertion_alignment_reward
            )
            + stage3_gate * (
                self.cfg.stage3_line_weight * insertion_line_reward
                + self.cfg.stage3_touch_weight * touch_ready_reward
                + self.cfg.stage3_progress_weight * self.insertion_progress
                + self.cfg.stage3_depth_weight * touch_depth_reward
            )
            + pregrasp_bonus
            + success_bonus
            - self.cfg.target_contact_penalty_weight * self.target_contact_penalty
            - self.cfg.stage1_wrong_way_weight * wrong_way_penalty
            - self.cfg.action_penalty_weight * action_penalty
            - self.cfg.joint_velocity_penalty_weight * joint_velocity_penalty
            - self.cfg.time_penalty_weight * time_fraction
        )
        return reward

    def _get_dones(self):
        self._compute_intermediate_values()

        success = (
            (self.touch_target_distance < self.cfg.success_radius)
            & (self.pregrasp_distance < self.cfg.pregrasp_success_radius)
            & (self.insertion_alignment > self.cfg.insertion_alignment_success)
            & (self.touch_error < self.cfg.touch_success_band)
            & (self.insertion_lateral_error < self.cfg.touch_success_band)
            & (self.object_overlap <= self.cfg.max_success_overlap)
            & (self.body_target_clearance_error <= 1e-4)
        )
        pregrasp_success = self.pregrasp_distance < self.cfg.pregrasp_success_radius
        stage2_ready = self.insertion_alignment > self.cfg.insertion_alignment_success
        stage3_ready = stage2_ready & pregrasp_success & (self.insertion_lateral_error < self.cfg.touch_success_band)
        stage3_touch_ready = stage3_ready & (self.touch_error < self.cfg.touch_success_band)
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        # Training/evaluation logs.
        self.extras["log"] = {
            "mt4/training_mode_stage_b": torch.tensor(
                1.0 if self.training_mode == "stage_b_insertion" else 0.0, device=self.device
            ),
            "mt4/success_rate": success.float().mean(),
            "mt4/pregrasp_success_rate": pregrasp_success.float().mean(),
            "mt4/stage2_alignment_ready_rate": stage2_ready.float().mean(),
            "mt4/stage3_insertion_ready_rate": stage3_ready.float().mean(),
            "mt4/stage3_touch_ready_rate": stage3_touch_ready.float().mean(),
            "mt4/mean_distance": self.distance.mean(),
            "mt4/mean_pregrasp_distance": self.pregrasp_distance.mean(),
            "mt4/mean_touch_target_distance": self.touch_target_distance.mean(),
            "mt4/mean_insertion_lateral_error": self.insertion_lateral_error.mean(),
            "mt4/mean_alignment": self.alignment.mean(),
            "mt4/mean_pregrasp_alignment": self.pregrasp_alignment.mean(),
            "mt4/mean_insertion_alignment": self.insertion_alignment.mean(),
            "mt4/mean_touch_error": self.touch_error.mean(),
            "mt4/mean_object_overlap": self.object_overlap.mean(),
            "mt4/mean_body_target_clearance_error": self.body_target_clearance_error.mean(),
            "mt4/mean_target_contact_penalty": self.target_contact_penalty.mean(),
            "mt4/mean_insertion_progress": self.insertion_progress.mean(),
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
        self._sample_targets(env_ids)

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
        down_dir = torch.tensor([0.0, 0.0, -1.0], device=self.device).repeat(len(env_ids), 1)
        approach_dir = self.cfg.approach_horizontal_weight * radial_dir + self.cfg.approach_down_weight * down_dir
        approach_dir = approach_dir / torch.clamp(torch.linalg.norm(approach_dir, dim=-1, keepdim=True), min=1e-6)

        # The blue sphere is the first-stage waypoint: above and slightly robot-side of the red target.
        # From blue to red, the desired insertion motion follows approach_dir at roughly 45 degrees.
        self.approach_dir[env_ids] = approach_dir
        self.pregrasp_targets[env_ids] = targets - self.cfg.pregrasp_standoff * approach_dir
        self.touch_targets[env_ids] = targets - self.cfg.desired_touch_distance * approach_dir
        desired_pregrasp_dir = self.pregrasp_targets[env_ids]
        desired_pregrasp_dir = desired_pregrasp_dir / torch.clamp(
            torch.linalg.norm(desired_pregrasp_dir, dim=-1, keepdim=True), min=1e-6
        )
        self.desired_pregrasp_dir[env_ids] = desired_pregrasp_dir
        self.desired_insertion_dir[env_ids] = approach_dir
        self.desired_gripper_dir[env_ids] = desired_pregrasp_dir

    def _compute_intermediate_values(self):
        wrist_pos_w = self.robot.data.body_pos_w[:, self.ee_body_id, :]
        wrist_quat_w = self.robot.data.body_quat_w[:, self.ee_body_id, :]
        self.wrist_pos = wrist_pos_w - self.scene.env_origins

        tip_offset_b = torch.tensor(self.cfg.gripper_tip_offset_b, device=self.device).repeat(self.num_envs, 1)
        forward_axis_b = torch.tensor(self.cfg.gripper_forward_axis_b, device=self.device).repeat(self.num_envs, 1)
        self.gripper_tip_pos = self.wrist_pos + math_utils.quat_apply(wrist_quat_w, tip_offset_b)
        self.gripper_forward = math_utils.quat_apply(wrist_quat_w, forward_axis_b)
        self.gripper_forward = self.gripper_forward / torch.clamp(torch.linalg.norm(self.gripper_forward, dim=-1, keepdim=True), min=1e-6)

        self.to_target = self.targets - self.gripper_tip_pos
        self.to_pregrasp = self.pregrasp_targets - self.gripper_tip_pos
        self.to_touch = self.touch_targets - self.gripper_tip_pos
        self.distance = torch.linalg.norm(self.to_target, dim=-1)
        self.pregrasp_distance = torch.linalg.norm(self.to_pregrasp, dim=-1)
        self.touch_target_distance = torch.linalg.norm(self.to_touch, dim=-1)
        self.touch_error = torch.abs(self.distance - self.cfg.desired_touch_distance)
        self.object_overlap = torch.clamp(self.cfg.target_radius - self.distance, min=0.0)
        body_pos = self.robot.data.body_pos_w - self.scene.env_origins.unsqueeze(1)
        body_to_target = body_pos - self.targets.unsqueeze(1)
        body_target_distance = torch.linalg.norm(body_to_target, dim=-1)
        min_body_target_distance = torch.min(body_target_distance, dim=-1).values
        self.body_target_clearance_error = torch.clamp(
            self.cfg.min_robot_target_clearance - min_body_target_distance, min=0.0
        )
        self.target_contact_penalty = self.object_overlap + self.body_target_clearance_error
        insertion_axis = torch.sum(self.to_touch * self.approach_dir, dim=-1, keepdim=True) * self.approach_dir
        insertion_lateral = self.to_touch - insertion_axis
        self.insertion_lateral_error = torch.linalg.norm(insertion_lateral, dim=-1)
        self.pregrasp_alignment = torch.sum(self.gripper_forward * self.desired_pregrasp_dir, dim=-1)
        self.insertion_alignment = torch.sum(self.gripper_forward * self.desired_insertion_dir, dim=-1)
        self.alignment = self.insertion_alignment
        self.clearance_error = torch.clamp(self.cfg.min_object_clearance - self.distance, min=0.0)
        insertion_path_length = max(self.cfg.pregrasp_standoff - self.cfg.desired_touch_distance, 1e-6)
        raw_progress = torch.sum((self.gripper_tip_pos - self.pregrasp_targets) * self.approach_dir, dim=-1)
        self.insertion_progress = torch.clamp(raw_progress / insertion_path_length, min=0.0, max=1.0)

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
                (self.touch_target_distance < self.cfg.success_radius)
                & (self.pregrasp_distance < self.cfg.pregrasp_success_radius)
                & (self.insertion_alignment > self.cfg.insertion_alignment_success)
                & (self.touch_error < self.cfg.touch_success_band)
                & (self.insertion_lateral_error < self.cfg.touch_success_band)
                & (self.object_overlap <= self.cfg.max_success_overlap)
                & (self.body_target_clearance_error <= 1e-4)
            )
            success_pos_w = target_pos_w.clone()
            success_pos_w[~success, 2] = -10.0
            self.success_markers.visualize(success_pos_w)
