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

## 2026-05-14 45-degree pregrasp waypoint and two-stage reward

- Kept the red sphere as the random final object/target marker.
- Changed the blue sphere into a deterministic pregrasp waypoint derived from the red sphere:
  - red target is sampled randomly within the configured target range
  - approach direction is computed from the robot base toward the target plus downward motion
  - horizontal and downward weights are both `1.0`, so the desired insertion path is roughly 45 degrees from above
  - blue pregrasp marker is placed at `target - pregrasp_standoff * approach_dir`
  - touch/contact marker target is placed at `target - desired_touch_distance * approach_dir`
- Reward is now staged:
  - stage 1 rewards reaching the blue pregrasp waypoint
  - stage 2 is gated by stage 1 and rewards alignment with the 45-degree approach direction plus moving toward the red target surface
- Added/updated logged metrics:
  - `mt4/pregrasp_success_rate`
  - `mt4/mean_touch_target_distance`
  - `mt4/mean_insertion_lateral_error`
- Relaxed the final success thresholds slightly so early experiments can show measurable improvement while still penalizing overlap with the target marker.

## 2026-05-14 base-to-blue gripper direction fix

- The first 45-degree pregrasp training run showed that the arm reduced distance, but learned a negative alignment direction.
- Changed the alignment target from the blue-to-red insertion vector to the robot-base-to-blue waypoint direction.
- This means the visible gripper should first point from the robot body toward the blue pregrasp sphere, instead of rotating to the opposite side.
- Added a small always-on alignment reward and wrong-way penalty so the policy receives direction feedback before it is already close to the blue sphere.
- Relaxed early educational thresholds slightly:
  - `success_radius`: `0.040 -> 0.045`
  - `pregrasp_success_radius`: `0.050 -> 0.075`

## 2026-05-14 staged pregrasp, alignment, and insertion reward

- Reframed the reach task as a three-stage classroom problem:
  - stage 1: move the visible gripper tip to the blue pregrasp marker
  - stage 2: once near blue, align with the blue-to-red 45-degree insertion direction
  - stage 3: move along that insertion line toward the red target surface without penetrating the red target
- Split direction metrics:
  - `pregrasp_alignment`: robot-base-to-blue direction for the initial approach
  - `insertion_alignment`: blue-to-red direction for the final object approach
  - `alignment`: active alignment, using pregrasp direction before stage 1 and insertion direction after stage 1
- Increased stage 1 distance/touch reward so the policy should prioritize reaching the blue marker before trying to solve final insertion.
- Added target-contact safety shaping:
  - gripper-tip overlap with the red sphere is penalized
  - robot link centers too close to the red sphere are penalized as a distance-based collision approximation
  - combined metric is logged as `mt4/mean_target_contact_penalty`
- Added small joint-velocity and time penalties to discourage slow dithering and overly aggressive motion.
- Added stage-specific logs for graph analysis:
  - `mt4/stage2_alignment_ready_rate`
  - `mt4/stage3_insertion_ready_rate`
  - `mt4/mean_pregrasp_alignment`
  - `mt4/mean_insertion_alignment`
  - `mt4/mean_body_target_clearance_error`
  - `mt4/mean_target_contact_penalty`
  - `mt4/mean_insertion_progress`
- Added `notes/mt4_reach_stage_reward_plan.md` so the reasoning can be shared with students.

## 2026-05-14 shortened gripper mount geometry

- Visual inspection showed that the gripper width was acceptable, but the straight mount section before the split fingers was too long.
- Shortened the simplified `gripper_link` geometry so the wrist-to-tip length is less likely to block pregrasp approach:
  - `mount_arm` total length: about `0.110 m -> 0.060 m`
  - `tool_mount` moved closer to the wrist
  - finger rails shortened while keeping the same left/right spacing
  - visual fingertip/bridge position moved from about `0.248 m` to `0.166 m`
- Updated the reward/marker fingertip offset:
  - `gripper_tip_offset_b`: `(0.242, 0.0, 0.0) -> (0.166, 0.0, 0.0)`
- Regenerated `assets/usd/mt4_simplified_v3.usd` from the v3 gripper-axis script.
- This change invalidates old reach checkpoints as a fair baseline, because the end-effector geometry and measured fingertip location changed.

## 2026-05-14 alignment-first staged reward

- A short 16-env visual run with the shortened gripper showed:
  - pregrasp distance improved substantially
  - occasional `pregrasp_success_rate` appeared
  - `mean_insertion_alignment` stayed negative, so the policy could reach toward blue while still pointing the gripper opposite the desired red-object insertion direction
- Reordered the reward curriculum:
  - old order: reach blue -> align for insertion -> enter red target approach path
  - new order: align for insertion -> reach blue while keeping that direction -> enter red target approach path
- Changed active `mt4/mean_alignment` to track `insertion_alignment` directly.
- `mt4/stage2_alignment_ready_rate` now means the policy has found the insertion direction, even before it reaches the blue pregrasp marker.
- Pregrasp reward is now gated by insertion alignment, so the arm should avoid learning a folded or reversed pose that can touch blue but cannot continue into the red target.

## 2026-05-14 stage 3 insertion reward softening

- Teacher observation:
  - Alignment-first training made `mean_insertion_alignment` strongly positive, but final success was still almost absent.
  - This suggested that the policy could find the correct insertion direction, yet the reward for actually entering from blue toward red was too hard to reach.
- Codex suggestion:
  - Keep the teacher's alignment-first curriculum.
  - Make the final insertion signal visible earlier by relaxing the stage 3 gate and widening the classroom success band slightly.
  - Keep the red target contact penalty active so "success" is not rewarded by simply driving through the red marker.
- Code changes:
  - `success_radius`: `0.045 -> 0.055`
  - `touch_success_band`: `0.026 -> 0.045`
  - `pregrasp_success_radius`: `0.075 -> 0.095`
  - `stage3_line_weight`: `2.2 -> 3.4`
  - `stage3_touch_weight`: `3.2 -> 4.0`
  - `stage3_progress_weight`: `1.2 -> 1.6`
  - relaxed the pregrasp gate and insertion/touch reward curves so stage 3 gives useful gradients before the gripper is already almost perfect.
- Tooling changes:
  - checkpoint summaries and experiment logs now include `pregrasp_success_rate`, `stage2_alignment_ready_rate`, and `stage3_insertion_ready_rate`.
  - best checkpoint selection gives extra weight to stage 3 readiness when sparse final success is still rare.
- Evaluation target:
  - The next 16-env visual run should show whether `stage3_insertion_ready_rate` and `success_rate` appear more consistently without increasing `mean_target_contact_penalty`.

### Result: 20260514_173715_stage3_softened_visual_16env_300iter

- Visual training completed for 16 envs, 300 iterations, seed 42.
- Best checkpoint selected by the balanced stage-aware rule: `model_50.pt`.
- Best checkpoint metrics:
  - `success_rate`: `0.0`
  - `pregrasp_success_rate`: `0.236328125`
  - `stage2_alignment_ready_rate`: `0.97265625`
  - `stage3_insertion_ready_rate`: `0.03125`
  - `mean_insertion_alignment`: `0.8894004821777344`
  - `mean_distance`: `0.14324891567230225`
  - `mean_target_contact_penalty`: `0.0000073`
- Interpretation:
  - This is not yet a solved final grasp-preparation policy.
  - It is an improvement over the previous alignment-only result because stage 3 readiness now appears in the selected checkpoint.
  - The remaining bottleneck is final touch/insertion precision, not broad insertion direction.

### Result: 20260514_174710_stage3_softened_128env_1000iter

- Full baseline completed for 128 envs, 1000 iterations, seed 42.
- Best checkpoint selected by the balanced stage-aware rule: `model_650.pt`.
- Best checkpoint metrics:
  - `success_rate`: `0.0`
  - `pregrasp_success_rate`: `0.85986328125`
  - `stage2_alignment_ready_rate`: `0.9150390625`
  - `stage3_insertion_ready_rate`: `0.688720703125`
  - `mean_insertion_alignment`: `0.8350418210029602`
  - `mean_distance`: `0.11983174830675125`
  - `mean_target_contact_penalty`: `0.0`
- Additional checkpoint observation:
  - highest checkpoint `success_rate` was `0.000732421875` at `model_300.pt`
- Interpretation:
  - The final stage improved substantially compared with the 16-env run.
  - The policy now often reaches the blue waypoint and enters the insertion corridor.
  - Final success remains sparse because touch-depth precision near the red target surface is still not learned reliably.

## 2026-05-14 touch-depth precision reward

- Teacher observation:
  - The policy can reach the insertion corridor, but it still does not move reliably to the exact red target surface depth.
  - The red target must remain safe; collision/contact penalty should not be removed just to increase success.
- Codex suggestion:
  - Reduce the reward for simply staying near the blue pregrasp marker.
  - Increase stage 3 progress/touch-depth reward.
  - Add `stage3_touch_ready_rate` so the graph separates "in the insertion corridor" from "at the correct surface depth".
- Code changes:
  - `pregrasp_bonus_weight`: `3.0 -> 1.2`
  - `stage3_touch_weight`: `4.0 -> 5.0`
  - `stage3_progress_weight`: `1.6 -> 3.0`
  - added `stage3_depth_weight = 5.0`
  - added inverse touch-depth reward based on `mean_touch_error`
  - added plot/checkpoint/experiment-log support for `stage3_touch_ready_rate` and `mean_touch_error`

### Result: 20260514_184219_touch_depth_128env_1000iter

- Full baseline completed for 128 envs, 1000 iterations, seed 42.
- Best checkpoint selected by the balanced stage-aware rule: `model_550.pt`.
- Best checkpoint metrics:
  - `success_rate`: `0.001708984375`
  - `pregrasp_success_rate`: `0.783935546875`
  - `stage2_alignment_ready_rate`: `0.896484375`
  - `stage3_insertion_ready_rate`: `0.69189453125`
  - `stage3_touch_ready_rate`: `0.001708984375`
  - `mean_touch_error`: `0.09006259590387344`
  - `mean_target_contact_penalty`: `0.0`
- Interpretation:
  - This experiment improved selected-checkpoint success slightly.
  - It did not solve final touch-depth precision.
  - The next step should be curriculum or a separate insertion-depth subtask, not only larger scalar reward weights.
