# 20260516_144748 safe_stage4_entry_smoke_seed42

## Summary

- timestamp: 2026-05-16T14:52:34
- checkpoint: `model_429.pt`
- checkpoint path: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-16_14-47-48/model_429.pt`
- plot snapshot: latest only
- reward profile: `safe-stage4-blue-funnel`
- notes: Safe stage4 replay start and early target contact penalty smoke test. Final success remains 0, but overshoot metric is stable and checkpoint selection now accounts for early contact and overshoot.

## Metrics

| metric | value |
|---|---:|
| success_rate | 0.0 |
| stage1_alignment_ready_rate | 0.917724609375 |
| stage1_latched_rate | 0.985107421875 |
| pregrasp_entry_success_rate | 0.050537109375 |
| pregrasp_entry_ready_rate | 0.0 |
| pregrasp_entry_reached_rate | 0.01025390625 |
| pregrasp_success_rate | 0.537109375 |
| pregrasp_hold_ready_rate | 0.0 |
| pregrasp_held_rate | 0.01025390625 |
| stage2_pregrasp_ready_rate | 0.01025390625 |
| stage2_latched_rate | 0.01025390625 |
| stage2_alignment_ready_rate | 0.917724609375 |
| stage3_insertion_ready_rate | 0.00439453125 |
| stage3_latched_rate | 0.01025390625 |
| stage3_touch_ready_rate | 0.00341796875 |
| stage4_center_ready_rate | 0.0 |
| blue_final_center_ready_rate | 0.0 |
| stage4_push_ready_rate | 0.00439453125 |
| mean_pregrasp_entry_distance | 0.14309607446193695 |
| mean_pregrasp_distance | 0.1232295036315918 |
| mean_gripper_center_pregrasp_distance | 0.1232295036315918 |
| mean_touch_error | 0.09307977557182312 |
| mean_distance | 0.09307977557182312 |
| mean_insertion_alignment | 0.90558260679245 |
| mean_target_contact_penalty | 0.0 |
| mean_early_target_contact_penalty | 0.005612771026790142 |
| mean_pregrasp_center_progress | 0.8508323431015015 |
| mean_center_push_progress | 0.693770170211792 |
| mean_center_push_overshoot | 0.009491397999227047 |
| mean_best_center_push_progress | 0.4167340397834778 |
| mean_center_push_improvement | 2.9845978133380413e-07 |
| mean_best_target_center_distance | 0.990229606628418 |
| mean_target_center_improvement | 0.0 |
| mean_target_center_shell_improvement | 0.0 |
| mean_center_shortest_path_score | 0.2191498577594757 |
| mean_stage4_time_pressure | 0.0034122720826417208 |
| mean_stage3_time_preserve | 0.00023744796635583043 |
| mean_terminal_success_quality | 0.0 |
| mean_near_terminal_reward | 0.0005565059254877269 |
| mean_stage_latch_reward | 0.1875564157962799 |
| mean_progressive_stage_weight | 0.9955581426620483 |
| mean_moving_pregrasp_fraction | 0.0 |
| moving_pregrasp_final_rate | 0.0 |
| moving_pregrasp_step_ready_rate | 0.0 |
| mean_moving_pregrasp_hold_progress | 0.0 |
| mean_moving_pregrasp_reward | 0.0 |
| mean_moving_pregrasp_funnel_reward | 0.0 |
| mean_moving_pregrasp_exp_reward | 0.00013582529209088534 |
| mean_moving_pregrasp_shell_improvement | 0.0 |
| mean_best_moving_pregrasp_distance | 0.990362286567688 |
| mean_final_insertion_reward | 0.0 |
| mean_pregrasp_line_error | 1.4925868541126874e-08 |
| mean_gripper_roll_alignment | -0.1110425665974617 |

## Interpretation

- 선생님 관찰과 Codex 제안, 실제 그래프 해석은 이 아래에 이어서 적는다.
- 다음 push 전에는 이 파일을 실험 기록의 고정 스냅샷으로 본다.
