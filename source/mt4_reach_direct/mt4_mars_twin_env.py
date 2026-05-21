from __future__ import annotations

from pathlib import Path

import torch

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import Articulation, ArticulationCfg, RigidObject, RigidObjectCfg
from isaaclab.envs import DirectRLEnv, DirectRLEnvCfg
from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils import math as math_utils


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MT4_TWO_FINGER_USD_PATH = str(PROJECT_ROOT / "assets/usd/mt4_simplified_v4_two_finger.usd")
MARS_GRAVITY = (0.0, 0.0, -3.711)

ARM_JOINT_NAMES = ("base_yaw", "shoulder", "elbow", "wrist_pitch", "gripper_pitch")
SIM_JOINT_NAMES = ARM_JOINT_NAMES + ("left_finger_slide", "right_finger_slide")
HOME_ARM_JOINT_POS = (0.0, 1.44, -1.19, 1.19, 0.0)
ARM_JOINT_LOWER = (-1.57, 0.05, -1.20, -1.20, -1.20)
ARM_JOINT_UPPER = (1.57, 1.45, 1.40, 1.20, 1.20)


def _cube_cfg(
    prim_path: str,
    color: tuple[float, float, float],
    emissive: tuple[float, float, float],
) -> RigidObjectCfg:
    return RigidObjectCfg(
        prim_path=prim_path,
        spawn=sim_utils.CuboidCfg(
            size=(0.04, 0.04, 0.04),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                solver_position_iteration_count=16,
                solver_velocity_iteration_count=2,
                max_depenetration_velocity=1.5,
                max_linear_velocity=0.6,
                max_angular_velocity=180.0,
                linear_damping=0.35,
                angular_damping=0.35,
            ),
            collision_props=sim_utils.CollisionPropertiesCfg(
                collision_enabled=True,
                contact_offset=0.004,
                rest_offset=0.0,
            ),
            mass_props=sim_utils.MassPropertiesCfg(mass=0.08),
            physics_material=sim_utils.RigidBodyMaterialCfg(
                static_friction=1.0,
                dynamic_friction=0.75,
                restitution=0.02,
            ),
            visual_material=sim_utils.PreviewSurfaceCfg(
                diffuse_color=(*color, 1.0),
                emissive_color=emissive,
            ),
        ),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.24, 0.0, 0.02), rot=(1.0, 0.0, 0.0, 0.0)),
    )


@configclass
class MT4MarsTwinEnvCfg(DirectRLEnvCfg):
    decimation = 2
    episode_length_s = 10.0

    action_space = 6
    observation_space = 44
    state_space = 0

    mission_type = "push"

    sim: sim_utils.SimulationCfg = sim_utils.SimulationCfg(
        dt=1 / 120,
        render_interval=decimation,
        gravity=MARS_GRAVITY,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            static_friction=0.95,
            dynamic_friction=0.75,
            restitution=0.02,
        ),
    )

    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=16,
        env_spacing=0.9,
        replicate_physics=True,
    )

    robot_cfg: ArticulationCfg = ArticulationCfg(
        prim_path="/World/envs/env_.*/Robot",
        spawn=sim_utils.UsdFileCfg(
            usd_path=MT4_TWO_FINGER_USD_PATH,
            activate_contact_sensors=False,
            collision_props=sim_utils.CollisionPropertiesCfg(
                collision_enabled=True,
                contact_offset=0.004,
                rest_offset=0.0,
            ),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                max_depenetration_velocity=4.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,
                solver_position_iteration_count=12,
                solver_velocity_iteration_count=2,
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
                "left_finger_slide": 0.0,
                "right_finger_slide": 0.0,
            },
        ),
        actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=list(ARM_JOINT_NAMES),
                stiffness=2200.0,
                damping=280.0,
                effort_limit=1500.0,
                velocity_limit=1.5,
            ),
            "gripper": ImplicitActuatorCfg(
                joint_names_expr=["left_finger_slide", "right_finger_slide"],
                stiffness=1800.0,
                damping=90.0,
                effort_limit=80.0,
                velocity_limit=0.08,
            ),
        },
    )

    sample_cube_cfg: RigidObjectCfg = _cube_cfg(
        "/World/envs/env_.*/SampleCube",
        color=(1.0, 0.08, 0.04),
        emissive=(0.12, 0.0, 0.0),
    )
    support_cube_cfg: RigidObjectCfg = _cube_cfg(
        "/World/envs/env_.*/SupportCube",
        color=(0.05, 0.22, 1.0),
        emissive=(0.0, 0.02, 0.12),
    )

    goal_marker_cfg = VisualizationMarkersCfg(
        prim_path="/Visuals/MT4MarsTwinGoals",
        markers={
            "goal": sim_utils.SphereCfg(
                radius=0.018,
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(0.05, 1.0, 0.15),
                    emissive_color=(0.0, 0.25, 0.03),
                ),
            ),
        },
    )

    home_marker_cfg = VisualizationMarkersCfg(
        prim_path="/Visuals/MT4MarsTwinHome",
        markers={
            "home": sim_utils.SphereCfg(
                radius=0.012,
                visual_material=sim_utils.PreviewSurfaceCfg(
                    diffuse_color=(1.0, 0.85, 0.05),
                    emissive_color=(0.20, 0.12, 0.0),
                ),
            ),
        },
    )

    cube_size = 0.04
    arm_action_scale = 0.035
    gripper_action_scale = 0.08
    gripper_max_close = 0.014
    home_tolerance = 0.08
    object_goal_tolerance = 0.055
    lift_height = 0.10
    stack_height_tolerance = 0.035

    target_x_range = (0.19, 0.31)
    target_y_range = (-0.13, 0.13)
    min_target_base_radius = 0.16

    ee_body_name = "gripper_link"
    gripper_center_offset_b = (0.158, 0.0, 0.0)
    gripper_forward_axis_b = (1.0, 0.0, 0.0)

    reach_weight = 1.2
    object_goal_weight = 4.0
    home_weight = 3.0
    mission_bonus_weight = 10.0
    success_bonus_weight = 25.0
    action_penalty_weight = 0.015
    joint_velocity_penalty_weight = 0.0004


@configclass
class MT4MarsTwinPickEnvCfg(MT4MarsTwinEnvCfg):
    mission_type = "pick"


@configclass
class MT4MarsTwinPlaceEnvCfg(MT4MarsTwinEnvCfg):
    mission_type = "place"


@configclass
class MT4MarsTwinStackEnvCfg(MT4MarsTwinEnvCfg):
    mission_type = "stack"


@configclass
class MT4MarsTwinPushEnvCfg(MT4MarsTwinEnvCfg):
    mission_type = "push"


@configclass
class MT4MarsTwinPullEnvCfg(MT4MarsTwinEnvCfg):
    mission_type = "pull"


class MT4MarsTwinEnv(DirectRLEnv):
    cfg: MT4MarsTwinEnvCfg

    def __init__(self, cfg: MT4MarsTwinEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)

        self.arm_joint_names = list(ARM_JOINT_NAMES)
        self.sim_joint_names = list(SIM_JOINT_NAMES)
        self.arm_joint_ids, _ = self.robot.find_joints(self.arm_joint_names)
        self.sim_joint_ids, _ = self.robot.find_joints(self.sim_joint_names)
        self.ee_body_id = self.robot.find_bodies(self.cfg.ee_body_name)[0][0]

        self.arm_joint_lower = torch.tensor(ARM_JOINT_LOWER, device=self.device)
        self.arm_joint_upper = torch.tensor(ARM_JOINT_UPPER, device=self.device)
        self.home_arm_joint_pos = torch.tensor(HOME_ARM_JOINT_POS, device=self.device)

        self.actions = torch.zeros((self.num_envs, self.cfg.action_space), device=self.device)
        self.arm_joint_targets = self.home_arm_joint_pos.repeat(self.num_envs, 1)
        self.gripper_close_targets = torch.zeros((self.num_envs, 1), device=self.device)
        self.sim_joint_targets = self._compose_sim_joint_pos()

        self.gripper_center_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.gripper_forward = torch.zeros((self.num_envs, 3), device=self.device)
        self.sample_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.support_pos = torch.zeros((self.num_envs, 3), device=self.device)
        self.mission_goal = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_goal = torch.zeros((self.num_envs, 3), device=self.device)
        self.to_sample = torch.zeros((self.num_envs, 3), device=self.device)
        self.home_error = torch.zeros((self.num_envs,), device=self.device)
        self.object_goal_distance = torch.zeros((self.num_envs,), device=self.device)
        self.gripper_sample_distance = torch.zeros((self.num_envs,), device=self.device)

        self.goal_markers = VisualizationMarkers(self.cfg.goal_marker_cfg)
        self.home_markers = VisualizationMarkers(self.cfg.home_marker_cfg)
        self._sample_mission_scene(torch.arange(self.num_envs, device=self.device))

    def _setup_scene(self):
        self.robot = Articulation(self.cfg.robot_cfg)
        self.scene.articulations["robot"] = self.robot
        self.sample_cube = RigidObject(self.cfg.sample_cube_cfg)
        self.scene.rigid_objects["sample_cube"] = self.sample_cube
        self.support_cube = RigidObject(self.cfg.support_cube_cfg)
        self.scene.rigid_objects["support_cube"] = self.support_cube

        ground_cfg = sim_utils.GroundPlaneCfg(
            physics_material=sim_utils.RigidBodyMaterialCfg(
                static_friction=0.95,
                dynamic_friction=0.75,
                restitution=0.02,
            )
        )
        ground_cfg.func("/World/defaultGroundPlane", ground_cfg)

        light_cfg = sim_utils.DomeLightCfg(intensity=1800.0, color=(0.85, 0.84, 0.80))
        light_cfg.func("/World/Light", light_cfg)

        self.scene.clone_environments(copy_from_source=False)
        self.scene.filter_collisions(global_prim_paths=["/World/defaultGroundPlane"])

    def _pre_physics_step(self, actions: torch.Tensor):
        self.actions = actions.clamp(-1.0, 1.0)
        self.arm_joint_targets = self.arm_joint_targets + self.cfg.arm_action_scale * self.actions[:, :5]
        self.arm_joint_targets = torch.max(torch.min(self.arm_joint_targets, self.arm_joint_upper), self.arm_joint_lower)
        self.gripper_close_targets = self.gripper_close_targets + self.cfg.gripper_action_scale * self.actions[:, 5:6]
        self.gripper_close_targets = torch.clamp(self.gripper_close_targets, 0.0, 1.0)
        self.sim_joint_targets = self._compose_sim_joint_pos()

    def _apply_action(self):
        self.robot.set_joint_position_target(self.sim_joint_targets, joint_ids=self.sim_joint_ids)

    def _get_observations(self):
        self._compute_intermediate_values()

        joint_pos = self.robot.data.joint_pos[:, self.sim_joint_ids]
        joint_vel = self.robot.data.joint_vel[:, self.sim_joint_ids]
        sample_vel = self.sample_cube.data.root_lin_vel_w
        support_vel = self.support_cube.data.root_lin_vel_w
        home_delta = self.arm_joint_targets - self.home_arm_joint_pos

        obs = torch.cat(
            [
                joint_pos,
                0.1 * joint_vel,
                self.gripper_center_pos,
                self.gripper_forward,
                self.sample_pos,
                sample_vel,
                self.support_pos,
                support_vel,
                self.mission_goal,
                self.to_goal,
                home_delta,
                self.gripper_close_targets,
            ],
            dim=-1,
        )
        return {"policy": obs}

    def _get_rewards(self):
        self._compute_intermediate_values()

        mission_success = self._mission_success()
        home_ready = self.home_error < self.cfg.home_tolerance
        reach_reward = torch.exp(-70.0 * self.gripper_sample_distance * self.gripper_sample_distance)
        object_goal_reward = torch.exp(-80.0 * self.object_goal_distance * self.object_goal_distance)
        home_reward = torch.exp(-20.0 * self.home_error * self.home_error) * mission_success.float()
        action_penalty = torch.sum(self.actions * self.actions, dim=-1)
        joint_vel = self.robot.data.joint_vel[:, self.sim_joint_ids]
        joint_velocity_penalty = torch.sum(joint_vel * joint_vel, dim=-1)

        return (
            self.cfg.reach_weight * reach_reward
            + self.cfg.object_goal_weight * object_goal_reward
            + self.cfg.home_weight * home_reward
            + self.cfg.mission_bonus_weight * mission_success.float()
            + self.cfg.success_bonus_weight * (mission_success & home_ready).float()
            - self.cfg.action_penalty_weight * action_penalty
            - self.cfg.joint_velocity_penalty_weight * joint_velocity_penalty
        )

    def _get_dones(self):
        self._compute_intermediate_values()

        mission_success = self._mission_success()
        home_ready = self.home_error < self.cfg.home_tolerance
        success = mission_success & home_ready
        time_out = self.episode_length_buf >= self.max_episode_length - 1

        self.extras["log"] = {
            f"mars_twin/{self.cfg.mission_type}_mission_success_rate": mission_success.float().mean(),
            f"mars_twin/{self.cfg.mission_type}_success_home_rate": success.float().mean(),
            "mars_twin/mean_object_goal_distance": self.object_goal_distance.mean(),
            "mars_twin/mean_gripper_sample_distance": self.gripper_sample_distance.mean(),
            "mars_twin/mean_home_error": self.home_error.mean(),
            "mars_twin/mean_gripper_close": self.gripper_close_targets.mean(),
        }

        self._update_markers()
        return success, time_out

    def _reset_idx(self, env_ids: torch.Tensor | None):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES

        super()._reset_idx(env_ids)
        self.robot.reset(env_ids)
        self.sample_cube.reset(env_ids)
        self.support_cube.reset(env_ids)

        self.arm_joint_targets[env_ids] = self.home_arm_joint_pos
        self.gripper_close_targets[env_ids] = 0.0
        self.sim_joint_targets[env_ids] = self._compose_sim_joint_pos()[env_ids]

        joint_pos = self.robot.data.default_joint_pos[env_ids].clone()
        joint_vel = self.robot.data.default_joint_vel[env_ids].clone()
        joint_pos[:, self.sim_joint_ids] = self.sim_joint_targets[env_ids]
        joint_vel[:, self.sim_joint_ids] = 0.0
        self.robot.write_joint_state_to_sim(joint_pos, joint_vel, env_ids=env_ids)

        self._sample_mission_scene(env_ids)

    def _sample_mission_scene(self, env_ids: torch.Tensor):
        n = len(env_ids)
        x = torch.empty(n, device=self.device).uniform_(*self.cfg.target_x_range)
        y = torch.empty(n, device=self.device).uniform_(*self.cfg.target_y_range)

        for _ in range(4):
            radial = torch.sqrt(x * x + y * y)
            too_close = radial < self.cfg.min_target_base_radius
            if not torch.any(too_close):
                break
            count = int(too_close.sum().item())
            x[too_close] = torch.empty(count, device=self.device).uniform_(*self.cfg.target_x_range)
            y[too_close] = torch.empty(count, device=self.device).uniform_(*self.cfg.target_y_range)

        sample_pos = torch.stack([x, y, torch.full_like(x, self.cfg.cube_size * 0.5)], dim=-1)
        support_pos = sample_pos + torch.tensor([0.0, 0.09, 0.0], device=self.device)
        goal = sample_pos.clone()

        if self.cfg.mission_type == "pick":
            goal[:, 2] = self.cfg.lift_height
        elif self.cfg.mission_type == "place":
            goal[:, 0] = torch.clamp(sample_pos[:, 0] + 0.08, max=0.34)
            goal[:, 1] = torch.clamp(sample_pos[:, 1] - 0.04, min=-0.16)
        elif self.cfg.mission_type == "stack":
            support_pos = sample_pos.clone()
            sample_pos[:, 1] -= 0.09
            goal = support_pos.clone()
            goal[:, 2] = self.cfg.cube_size * 1.5
        elif self.cfg.mission_type == "pull":
            goal[:, 0] = torch.clamp(sample_pos[:, 0] - 0.09, min=0.12)
        else:
            goal[:, 0] = torch.clamp(sample_pos[:, 0] + 0.09, max=0.36)

        self.mission_goal[env_ids] = goal
        self._write_object_pose(self.sample_cube, sample_pos, env_ids)
        self._write_object_pose(self.support_cube, support_pos, env_ids)
        self._update_markers()

    def _write_object_pose(self, obj: RigidObject, pos_env: torch.Tensor, env_ids: torch.Tensor):
        root_state = obj.data.default_root_state[env_ids].clone()
        root_state[:, :3] = pos_env + self.scene.env_origins[env_ids]
        root_state[:, 3:7] = torch.tensor((1.0, 0.0, 0.0, 0.0), device=self.device)
        root_state[:, 7:] = 0.0
        obj.write_root_state_to_sim(root_state, env_ids=env_ids)

    def _compute_intermediate_values(self):
        ee_pos_w = self.robot.data.body_pos_w[:, self.ee_body_id, :]
        ee_quat_w = self.robot.data.body_quat_w[:, self.ee_body_id, :]
        ee_pos = ee_pos_w - self.scene.env_origins

        center_offset_b = torch.tensor(self.cfg.gripper_center_offset_b, device=self.device).repeat(self.num_envs, 1)
        forward_axis_b = torch.tensor(self.cfg.gripper_forward_axis_b, device=self.device).repeat(self.num_envs, 1)
        self.gripper_center_pos = ee_pos + math_utils.quat_apply(ee_quat_w, center_offset_b)
        self.gripper_forward = math_utils.quat_apply(ee_quat_w, forward_axis_b)
        self.gripper_forward = self.gripper_forward / torch.clamp(
            torch.linalg.norm(self.gripper_forward, dim=-1, keepdim=True), min=1e-6
        )

        self.sample_pos = self.sample_cube.data.root_pos_w - self.scene.env_origins
        self.support_pos = self.support_cube.data.root_pos_w - self.scene.env_origins
        self.to_sample = self.sample_pos - self.gripper_center_pos
        self.to_goal = self.mission_goal - self.sample_pos
        self.gripper_sample_distance = torch.linalg.norm(self.to_sample, dim=-1)
        self.object_goal_distance = torch.linalg.norm(self.to_goal, dim=-1)
        self.home_error = torch.linalg.norm(self.arm_joint_targets - self.home_arm_joint_pos, dim=-1)

    def _mission_success(self) -> torch.Tensor:
        if self.cfg.mission_type == "pick":
            return self.sample_pos[:, 2] > self.cfg.lift_height
        if self.cfg.mission_type == "stack":
            horizontal_error = torch.linalg.norm((self.sample_pos - self.support_pos)[:, :2], dim=-1)
            height_error = torch.abs((self.sample_pos[:, 2] - self.support_pos[:, 2]) - self.cfg.cube_size)
            return (horizontal_error < self.cfg.object_goal_tolerance) & (height_error < self.cfg.stack_height_tolerance)
        return self.object_goal_distance < self.cfg.object_goal_tolerance

    def _update_markers(self):
        if not hasattr(self, "goal_markers"):
            return
        goal_pos_w = self.mission_goal + self.scene.env_origins
        self.goal_markers.visualize(goal_pos_w)
        home_pos_w = self.scene.env_origins + torch.tensor((0.13, 0.0, 0.16), device=self.device)
        self.home_markers.visualize(home_pos_w)

    def _compose_sim_joint_pos(self) -> torch.Tensor:
        close = self.gripper_close_targets * self.cfg.gripper_max_close
        left = -close
        right = close
        return torch.cat([self.arm_joint_targets, left, right], dim=-1)
