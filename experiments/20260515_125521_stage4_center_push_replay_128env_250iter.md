# 20260515_125521 stage4_center_push_replay_128env_250iter

## Summary

- timestamp: 2026-05-15T12:57:34
- checkpoint: `model_950.pt`
- checkpoint path: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-15_12-55-21/model_950.pt`
- plot snapshot: `/home/spark-robotics/work/robotarm/mt4_isaac_lab_task/logs/plots/20260515_125521_stage4_center_push_replay_128env_250iter`
- reward profile: `stage4_center_push`
- notes: Stage4 center-push reward: progress from pregrasp target toward red target center while maintaining insertion alignment and lateral accuracy. Best checkpoint selected before late drift.

## Metrics

| metric | value |
|---|---:|
| success_rate | 0.0 |
| stage1_alignment_ready_rate | 0.963134765625 |
| pregrasp_entry_success_rate | 0.929443359375 |
| pregrasp_entry_ready_rate | 0.370361328125 |
| pregrasp_entry_reached_rate | 0.842529296875 |
| pregrasp_success_rate | 0.93212890625 |
| pregrasp_hold_ready_rate | 0.842041015625 |
| pregrasp_held_rate | 0.842529296875 |
| stage2_pregrasp_ready_rate | 0.842529296875 |
| stage2_alignment_ready_rate | 0.963134765625 |
| stage3_insertion_ready_rate | 0.8388671875 |
| stage3_touch_ready_rate | 0.828857421875 |
| stage4_center_ready_rate | 0.0 |
| stage4_push_ready_rate | 0.729736328125 |
| mean_pregrasp_entry_distance | 0.10236390680074692 |
| mean_pregrasp_distance | 0.0765104591846466 |
| mean_gripper_center_pregrasp_distance | 0.0765104591846466 |
| mean_touch_error | 0.04022194445133209 |
| mean_distance | 0.07022193819284439 |
| mean_insertion_alignment | 0.8573260307312012 |
| mean_target_contact_penalty | 0.0 |
| mean_pregrasp_center_progress | 0.9319121837615967 |
| mean_center_push_progress | 0.5227710008621216 |
| mean_best_target_center_distance | 0.20205876231193542 |
| mean_target_center_improvement | 6.84746919432655e-05 |
| mean_pregrasp_line_error | 1.4079896359930899e-08 |

## Interpretation

- 선생님 의견:
  - 마지막 중심 근처까지 왔다면, 같은 자리에서 맴돌기보다 빨간 구체 중심 쪽으로 밀어 넣는 보상이 필요하다.
  - 최종 grasp 전에는 빨간 구체 중심이 집게 가운데에 들어와 있어야 한다.
- Codex 적용:
  - `center_push_progress`를 추가해 pregrasp 지점에서 빨간 구체 중심으로 진행한 정도를 측정했다.
  - `stage4_push_ready_rate`는 insertion alignment와 lateral error 조건을 유지하면서 이 push progress가 충분한지 본다.
  - 초기 `touch_targets -> targets` 기준은 보상이 너무 늦게 열려 거의 0이었고, 실행 중 `pregrasp_targets -> targets` 기준으로 수정했다.
- 결과 평가:
  - 최종 `success_rate`와 `stage4_center_ready_rate`는 0.0으로, 완전 성공은 아직 아니다.
  - `stage4_push_ready_rate=0.729736328125`, `mean_center_push_progress=0.5227710008621216`로 빨간 구체 방향 진행 신호는 살아났다.
  - `mean_target_contact_penalty=0.0`이라 빨간 구체와의 위험한 몸체 충돌은 관측되지 않았다.
  - 후반부에는 push progress가 올라가는 대신 touch/alignment가 일부 흔들려, 다음에는 push 보상을 자세 유지 조건에 더 단단히 묶는 편이 좋다.
- 다음 제안:
  - stage4 replay state를 빨간 구체 중심에 더 가까운 상태로 다시 수집한다.
  - 또는 `final_center_success_radius`를 임시 완화해서 성공 샘플을 늘린 뒤, 다시 기준을 줄이는 curriculum을 적용한다.
