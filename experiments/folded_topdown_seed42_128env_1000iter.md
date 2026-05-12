# Folded Top-Down MT4 Reach Baseline

## Run

- Task: `Isaac-MT4-Simplified-Reach-Direct-v0`
- Run label: `folded_topdown_seed42_128env_1000iter`
- Seed: `42`
- Environments: `128`
- Iterations: `1000`
- Home pose: `base_yaw=0.0`, `shoulder=1.20`, `elbow=-1.05`, `wrist_pitch=0.75`
- Approach: mostly top-down, slightly angled from outside the robot base

## Selected checkpoint

- Checkpoint: `model_999.pt`
- Selection reason: balanced pre-grasp distance and alignment
- Path: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-12_15-39-39/model_999.pt`

## Metrics

- `success_rate`: `0.000732421875`
- `mean_pregrasp_distance`: `0.07545068114995956`
- `mean_distance`: `0.09776797145605087`
- `mean_alignment`: `0.7838757038116455`
- `min_distance`: `0.042414985597133636`
- `mean_reward`: `1012.410888671875`

## Video

- Project copy: `logs/videos/folded_topdown_seed42_model999.mp4`
- IsaacLab source: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-12_15-39-39/videos/play/rl-video-step-0.mp4`

## Interpretation

The policy learned a visibly meaningful folded-home, top-down pre-grasp behavior. It does not yet satisfy the strict success condition often, but the final checkpoint keeps a much better approach direction than the closest-distance checkpoint.

For the next tuning pass, increase the importance of alignment and reduce excessive action exploration so the arm keeps the gripper orientation stable while approaching the object.
