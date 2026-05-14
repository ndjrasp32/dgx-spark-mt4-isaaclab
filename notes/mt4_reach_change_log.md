# MT4 Reach Task Change Log

## 2026-05-12 gripper_pitch axis and touch-aware reward

- Kept task name: `Isaac-MT4-Simplified-Reach-Direct-v0`.
- Added `assets/usd/mt4_simplified_v3.usd`, based on v2 plus:
  - new body: `gripper_link`
  - new revolute joint: `gripper_pitch`
  - joint limit: about `-68.75 deg` to `+68.75 deg`
- Updated the task to use 5 actions:
  - `base_yaw`
  - `shoulder`
  - `elbow`
  - `wrist_pitch`
  - `gripper_pitch`
- Updated observation size from `26` to `28`.
- The end-effector body is now `gripper_link` instead of `wrist_link`.
- Reward changes:
  - increased success bonus from `5.0` to `8.0`
  - reduced pure distance/pregrasp reward weights
  - increased alignment and touch-surface reward weights
  - added object-overlap penalty so the gripper tip should approach the target surface without passing through the target marker
- Target sampling changes:
  - target x range moved from `(0.16, 0.30)` to `(0.20, 0.32)`
  - target z range moved from `(0.06, 0.18)` to `(0.08, 0.18)`
  - targets too close to the robot base radius are resampled
- New logged metrics:
  - `mt4/mean_touch_error`
  - `mt4/mean_object_overlap`

Notes:
- The red target is still a visual marker, not a rigid object. This avoids the target being physically knocked away during reach training.
- Physical object dynamics should be added later in a separate grasp/lift task, after reach/touch behavior is stable.

## 2026-05-14 gripper pitch visual/reward alignment fix

- Found that `gripper_pitch` was controllable, but the added gripper geometry was attached along local `+X` while the task reward treats local `-X` as the gripper approach direction.
- Regenerated the gripper visual/collision geometry as a small fork-shaped tool extending along local `-X`.
- Updated `gripper_tip_offset_b` from local `+X` to local `-X`, so the reward tip, blue pre-grasp marker, and visible gripper now describe the same physical point.
- Added drive/PhysX joint APIs to the generated `gripper_pitch` joint so it matches the schema style of the existing MT4 revolute joints more closely.

## 2026-05-14 larger visible gripper module

- Enlarged the `gripper_link` visual/collision geometry so the whole gripper-bearing part is visible, not just a tiny tip at the wrist.
- The moving gripper link now includes:
  - a dark pitch housing at the wrist joint
  - a longer central carriage
  - two visible finger rails
  - blue fingertip pads
- Updated `gripper_tip_offset_b` to the new fingertip location so reward/marker geometry follows the visible fingertip module.

## 2026-05-14 gripper visual cleanup

- Hid gripper collision geometry from the viewport to reduce flickering/z-fighting between visual and collision cubes.
- Replaced the inner gripper-looking wrist block with a short cylindrical pitch hinge and narrow neck.
- Moved the visible fork fingers farther outward so the joint connection reads as a wrist/pitch module rather than another gripper.
- Updated `gripper_tip_offset_b` to the cleaned-up fingertip location.

## 2026-05-14 gripper joint placement and arm-like connector

- Confirmed the `gripper_pitch` joint is anchored at `wrist_link` local `+X = 0.06`, matching the end of the wrist link.
- Changed the visible gripper module to follow the same convention as the other MT4 arm links: the child link starts at the joint and extends along local `+X`.
- Replaced the inner gripper-like connector with a plain `mount_arm` and compact `tool_mount`; only the outermost elements are shaped as gripper fingers.
- Updated the fingertip offset and forward axis to local `+X` so reward/marker geometry follows the visible gripper tip.
