from __future__ import annotations

import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg
from isaaclab.envs import DirectRLEnv, DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils import math as math_utils
from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg


MT4_USD_PATH = "/home/spark-robotics/work/robotarm/mt4_isaac_lab_task/assets/usd/mt4_simplified_v2.usd"


@configclass
class MT4ReachEnvCfg(DirectRLEnvCfg):
    # simulation
    decimation = 2
    episode_length_s = 5.0

    # spaces
    action_space = 4
    observation_space = 26
    state_space = 0

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
                "shoulder": 1.20,
                "elbow": -1.05,
                "wrist_pitch": 0.75,
            },
        ),
        actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=["base_yaw", "shoulder", "elbow", "wrist_pitch"],
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
    success_radius = 0.035
    target_x_range = (0.16, 0.30)
    target_y_range = (-0.16, 0.16)
    target_z_range = (0.06, 0.18)

    # simplified pre-grasp geometry
    gripper_tip_offset_b = (0.06, 0.0, 0.0)
    gripper_forward_axis_b = (-1.0, 0.0, 0.0)
    pregrasp_standoff = 0.055
    approach_horizontal_weight = 0.25
    approach_down_weight = 1.0
    min_object_clearance = 0.030
    alignment_success = 0.65


class MT4ReachEnv(DirectRLEnv):
    cfg: MT4ReachEnvCfg

    def __init__(self, cfg: MT4ReachEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        self.joint_names = ["base_yaw", "shoulder", "elbow", "wrist_pitch"]
        self.joint_ids, self.joint_names_found = self.robot.find_joints(self.joint_names)
        self.ee_body_id = self.robot.find_bodies("wrist_link")[0][0]

        self.joint_lower = torch.tensor([-1.57, 0.05, -1.20, -1.20], device=self.device)
        self.joint_upper = torch.tensor([1.57, 1.45, 1.40, 1.20], device=self.device)

        self.home_joint_pos = torch.tensor([0.0, 1.20, -1.05, 0.75], device=self.device)

        self.actions = torch.zeros((self.num_envs, 4), device=self.device)
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
        self.pregrasp_targets = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_target = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_pregrasp = torch.zeros((self.num_envs, 3), device=self.device)
        self.distance = torch.zeros((self.num_envs,), device=self.device)
        self.pregrasp_distance = torch.zeros((self.num_envs,), device=self.device)
        self.alignment = torch.zeros((self.num_envs,), device=self.device)
        self.clearance_error = torch.zeros((self.num_envs,), device=self.device)

        self._sample_targets(torch.arange(self.num_envs, device=self.device))

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

        pregrasp_reward = 1.0 / (1.0 + 40.0 * self.pregrasp_distance * self.pregrasp_distance)
        close_reward = torch.exp(-12.0 * self.pregrasp_distance)
        touch_ready_reward = torch.exp(-80.0 * torch.square(self.distance - self.cfg.pregrasp_standoff))
        alignment_reward = torch.clamp(0.5 * (self.alignment + 1.0), min=0.0, max=1.0)
        clearance_penalty = torch.clamp(self.cfg.min_object_clearance - self.distance, min=0.0)
        action_penalty = torch.sum(self.actions * self.actions, dim=-1)
        success = (
            (self.pregrasp_distance < self.cfg.success_radius)
            & (self.alignment > self.cfg.alignment_success)
            & (self.distance > self.cfg.min_object_clearance)
        )
        success_bonus = success.float() * 5.0

        reward = (
            2.0 * pregrasp_reward
            + 1.5 * close_reward
            + 1.0 * alignment_reward
            + 0.7 * touch_ready_reward
            + success_bonus
            - 5.0 * clearance_penalty
            - 0.01 * action_penalty
        )
        return reward

    def _get_dones(self):
        self._compute_intermediate_values()

        success = (
            (self.pregrasp_distance < self.cfg.success_radius)
            & (self.alignment > self.cfg.alignment_success)
            & (self.distance > self.cfg.min_object_clearance)
        )
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        # Training/evaluation logs.
        self.extras["log"] = {
            "mt4/success_rate": success.float().mean(),
            "mt4/mean_distance": self.distance.mean(),
            "mt4/mean_pregrasp_distance": self.pregrasp_distance.mean(),
            "mt4/mean_alignment": self.alignment.mean(),
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

        self.targets[env_ids, 0] = x
        self.targets[env_ids, 1] = y
        self.targets[env_ids, 2] = z

        self._update_target_markers()

    def _compute_intermediate_values(self):
        wrist_pos_w = self.robot.data.body_pos_w[:, self.ee_body_id, :]
        wrist_quat_w = self.robot.data.body_quat_w[:, self.ee_body_id, :]
        self.wrist_pos = wrist_pos_w - self.scene.env_origins

        tip_offset_b = torch.tensor(self.cfg.gripper_tip_offset_b, device=self.device).repeat(self.num_envs, 1)
        forward_axis_b = torch.tensor(self.cfg.gripper_forward_axis_b, device=self.device).repeat(self.num_envs, 1)
        self.gripper_tip_pos = self.wrist_pos + math_utils.quat_apply(wrist_quat_w, tip_offset_b)
        self.gripper_forward = math_utils.quat_apply(wrist_quat_w, forward_axis_b)
        self.gripper_forward = self.gripper_forward / torch.clamp(torch.linalg.norm(self.gripper_forward, dim=-1, keepdim=True), min=1e-6)

        radial_dir = self.targets.clone()
        radial_dir[:, 2] = 0.0
        fallback = torch.tensor([1.0, 0.0, 0.0], device=self.device).repeat(self.num_envs, 1)
        radial_norm = torch.linalg.norm(radial_dir, dim=-1, keepdim=True)
        radial_dir = torch.where(radial_norm > 1e-6, radial_dir / torch.clamp(radial_norm, min=1e-6), fallback)
        down_dir = torch.tensor([0.0, 0.0, -1.0], device=self.device).repeat(self.num_envs, 1)
        self.approach_dir = self.cfg.approach_horizontal_weight * radial_dir + self.cfg.approach_down_weight * down_dir
        self.approach_dir = self.approach_dir / torch.clamp(torch.linalg.norm(self.approach_dir, dim=-1, keepdim=True), min=1e-6)
        self.pregrasp_targets = self.targets - self.cfg.pregrasp_standoff * self.approach_dir

        self.to_target = self.targets - self.gripper_tip_pos
        self.to_pregrasp = self.pregrasp_targets - self.gripper_tip_pos
        self.distance = torch.linalg.norm(self.to_target, dim=-1)
        self.pregrasp_distance = torch.linalg.norm(self.to_pregrasp, dim=-1)
        target_dir = self.to_target / torch.clamp(self.distance.unsqueeze(-1), min=1e-6)
        self.alignment = torch.sum(self.gripper_forward * target_dir, dim=-1)
        self.clearance_error = torch.clamp(self.cfg.min_object_clearance - self.distance, min=0.0)

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
                (self.pregrasp_distance < self.cfg.success_radius)
                & (self.alignment > self.cfg.alignment_success)
                & (self.distance > self.cfg.min_object_clearance)
            )
            success_pos_w = target_pos_w.clone()
            success_pos_w[~success, 2] = -10.0
            self.success_markers.visualize(success_pos_w)
