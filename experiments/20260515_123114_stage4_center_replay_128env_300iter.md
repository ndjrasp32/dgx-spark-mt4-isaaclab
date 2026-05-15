# 20260515_123114 stage4_center_replay_128env_300iter

## Summary

- timestamp: 2026-05-15T12:33:44
- checkpoint: `model_900.pt`
- checkpoint path: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-15_12-31-14/model_900.pt`
- plot snapshot: `/home/spark-robotics/work/robotarm/mt4_isaac_lab_task/logs/plots/20260515_123114_stage4_center_replay_128env_300iter`
- reward profile: `stage4_center_replay_small_target`
- notes: Stage4 replay reset with smaller red target radius 0.025m and relaxed final center radius 0.035m. Stage3 touch improved strongly and target contact penalty stayed zero, but stage4 center success remained sparse; next step should reduce action std/exploration or collect states closer to the red center.

## Metrics

| metric | value |
|---|---:|
| success_rate | 0.000244140625 |
| stage1_alignment_ready_rate | 0.972900390625 |
| pregrasp_entry_success_rate | 0.954345703125 |
| pregrasp_entry_ready_rate | 0.660888671875 |
| pregrasp_entry_reached_rate | 0.9375 |
| pregrasp_success_rate | 0.957763671875 |
| pregrasp_hold_ready_rate | 0.930419921875 |
| pregrasp_held_rate | 0.9375 |
| stage2_pregrasp_ready_rate | 0.930419921875 |
| stage2_alignment_ready_rate | 0.972900390625 |
| stage3_insertion_ready_rate | 0.929931640625 |
| stage3_touch_ready_rate | 0.9169921875 |
| stage4_center_ready_rate | 0.000244140625 |
| mean_pregrasp_entry_distance | 0.09372089803218842 |
| mean_pregrasp_distance | 0.06618805229663849 |
| mean_gripper_center_pregrasp_distance | 0.06618805229663849 |
| mean_touch_error | 0.03427979350090027 |
| mean_distance | 0.06427979469299316 |
| mean_insertion_alignment | 0.8609586954116821 |
| mean_target_contact_penalty | 0.0 |
| mean_pregrasp_center_progress | 0.9701886177062988 |
| mean_best_target_center_distance | 0.10723148286342621 |
| mean_target_center_improvement | 4.2013802158180624e-05 |
| mean_pregrasp_line_error | 1.3118444996962353e-08 |

## Interpretation

- 선생님 관찰과 Codex 제안, 실제 그래프 해석은 이 아래에 이어서 적는다.
- 다음 push 전에는 이 파일을 실험 기록의 고정 스냅샷으로 본다.
