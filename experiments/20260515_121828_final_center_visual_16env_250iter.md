# 20260515_121828 final_center_visual_16env_250iter

## Summary

- timestamp: 2026-05-15T12:25:05
- checkpoint: `model_750.pt`
- checkpoint path: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-15_12-18-28/model_750.pt`
- plot snapshot: `/home/spark-robotics/work/robotarm/mt4_isaac_lab_task/logs/plots/20260515_121828_final_center_visual_16env_250iter`
- reward profile: `final_center_capture_visual`
- notes: GUI visual run from model_600 with final center capture reward. Stage3 insertion/touch became strong; stage4 final center success appeared but remained sparse, so next work should use a stage4-specific replay curriculum or slightly relaxed final radius.

## Metrics

| metric | value |
|---|---:|
| success_rate | 0.001953125 |
| stage1_alignment_ready_rate | 0.98828125 |
| pregrasp_entry_success_rate | 0.40625 |
| pregrasp_entry_ready_rate | 0.103515625 |
| pregrasp_entry_reached_rate | 0.986328125 |
| pregrasp_success_rate | 0.98828125 |
| pregrasp_hold_ready_rate | 0.791015625 |
| pregrasp_held_rate | 0.96875 |
| stage2_pregrasp_ready_rate | 0.96875 |
| stage2_alignment_ready_rate | 0.98828125 |
| stage3_insertion_ready_rate | 0.923828125 |
| stage3_touch_ready_rate | 0.90234375 |
| stage4_center_ready_rate | 0.001953125 |
| mean_pregrasp_entry_distance | 0.09985151141881943 |
| mean_pregrasp_distance | 0.07459090650081635 |
| mean_gripper_center_pregrasp_distance | 0.07459090650081635 |
| mean_touch_error | 0.019788116216659546 |
| mean_distance | 0.05730348080396652 |
| mean_insertion_alignment | 0.8966652154922485 |
| mean_target_contact_penalty | 0.0 |
| mean_pregrasp_center_progress | 0.935693085193634 |
| mean_best_target_center_distance | 0.11673150956630707 |
| mean_target_center_improvement | 0.00012233149027451873 |
| mean_pregrasp_line_error | 1.4439212492334264e-08 |

## Interpretation

- 선생님 관찰과 Codex 제안, 실제 그래프 해석은 이 아래에 이어서 적는다.
- 다음 push 전에는 이 파일을 실험 기록의 고정 스냅샷으로 본다.
