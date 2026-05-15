# 20260515_120532 pregrasp_entry_stage3_replay_128env_450iter

## Summary

- timestamp: 2026-05-15T12:08:57
- checkpoint: `model_600.pt`
- checkpoint path: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-15_12-05-32/model_600.pt`
- plot snapshot: `/home/spark-robotics/work/robotarm/mt4_isaac_lab_task/logs/plots/20260515_120532_pregrasp_entry_stage3_replay_128env_450iter`
- reward profile: `pregrasp_entry_stage3_replay`
- notes: Pregrasp entry->center->insertion curriculum with replay reset. Best checkpoint reached high stage3 insertion readiness, but final touch/success remains low.

## Metrics

| metric | value |
|---|---:|
| success_rate | 0.0 |
| stage1_alignment_ready_rate | 0.98046875 |
| pregrasp_entry_success_rate | 0.939208984375 |
| pregrasp_entry_ready_rate | 0.931396484375 |
| pregrasp_entry_reached_rate | 0.933837890625 |
| pregrasp_success_rate | 0.943603515625 |
| pregrasp_hold_ready_rate | 0.927490234375 |
| pregrasp_held_rate | 0.929931640625 |
| stage2_pregrasp_ready_rate | 0.927490234375 |
| stage2_alignment_ready_rate | 0.98046875 |
| stage3_insertion_ready_rate | 0.8701171875 |
| stage3_touch_ready_rate | 0.0 |
| mean_pregrasp_entry_distance | 0.06754179298877716 |
| mean_pregrasp_distance | 0.04315996170043945 |
| mean_gripper_center_pregrasp_distance | 0.04315996170043945 |
| mean_touch_error | 0.0533212348818779 |
| mean_distance | 0.09332123398780823 |
| mean_insertion_alignment | 0.856013834476471 |
| mean_target_contact_penalty | 0.0 |
| mean_pregrasp_center_progress | 0.9594475030899048 |
| mean_pregrasp_line_error | 1.4129777348159678e-08 |

## Interpretation

- 선생님 관찰:
  - 파란 구체 중앙만 바로 맞추는 것보다, 로봇팔 쪽 표면점에서 파란 중앙으로 들어간 뒤 같은 방향으로 빨간 구체에 진입하는 편이 더 자연스럽다.
  - 마지막 진입은 stage 3 전용 curriculum으로 따로 많이 경험시키는 것이 좋다.
- Codex 제안:
  - `pregrasp_entry_targets`를 추가해 파란 구체를 `entry -> center -> insertion` 흐름으로 나눈다.
  - replay reset을 사용해 좋은 pregrasp 근처에서 시작하는 episode를 늘린다.
  - stage 3에서는 성공률보다 먼저 `stage3_insertion_ready_rate`, `mean_pregrasp_center_progress`, `mean_insertion_progress`를 본다.
- 결과 평가:
  - best checkpoint는 마지막 `model_799.pt`가 아니라 `model_600.pt`였다.
  - `pregrasp_entry_reached_rate=0.933837890625`, `stage2_pregrasp_ready_rate=0.927490234375`로 entry와 파란 중앙 대기는 안정적으로 형성되었다.
  - `stage3_insertion_ready_rate=0.8701171875`, `mean_pregrasp_center_progress=0.9594475030899048`로 빨간 구체 방향 진입 시작도 크게 개선되었다.
  - `stage3_touch_ready_rate=0.0`, `success_rate=0.0`이라 마지막 깊이와 정밀 접촉은 아직 성공하지 못했다.
  - 후반으로 갈수록 action std가 커지고 alignment가 무너지는 경향이 있어, 더 오래 돌리는 것보다 마지막 접촉 조건을 따로 안정화하는 편이 좋아 보인다.
- 다음 작업:
  - stage 3의 마지막 5cm 정도만 다루는 touch-depth curriculum을 만든다.
  - action std가 너무 커지는 것을 막기 위해 entropy 또는 action penalty를 조금 더 조정한다.
  - 성공 조건은 유지하되, `stage3_touch_ready_rate`를 중간 목표로 삼아 먼저 0.05 이상으로 올리는 실험을 한다.
