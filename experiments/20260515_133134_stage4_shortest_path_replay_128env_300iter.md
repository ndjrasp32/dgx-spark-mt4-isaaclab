# 20260515_133134 stage4_shortest_path_replay_128env_300iter

## Summary

- timestamp: 2026-05-15T13:34:14
- checkpoint: `model_1548.pt`
- checkpoint path: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-15_13-31-34/model_1548.pt`
- plot snapshot: `/home/spark-robotics/work/robotarm/mt4_isaac_lab_task/logs/plots/20260515_133134_stage4_shortest_path_replay_128env_300iter`
- reward profile: `stage4_shortest_path_shell`
- notes: Stage4 diversified reward: distance improvement is scaled by shortest-path score, and red-target distance shells pay only when the policy reaches a closer shell. Improved stage3/touch stability and path score, but push-ready remains low.

## Metrics

| metric | value |
|---|---:|
| success_rate | 0.000244140625 |
| stage1_alignment_ready_rate | 0.986328125 |
| pregrasp_entry_success_rate | 0.917236328125 |
| pregrasp_entry_ready_rate | 0.23388671875 |
| pregrasp_entry_reached_rate | 0.870361328125 |
| pregrasp_success_rate | 0.986328125 |
| pregrasp_hold_ready_rate | 0.81884765625 |
| pregrasp_held_rate | 0.870361328125 |
| stage2_pregrasp_ready_rate | 0.870361328125 |
| stage2_alignment_ready_rate | 0.986328125 |
| stage3_insertion_ready_rate | 0.826416015625 |
| stage3_touch_ready_rate | 0.820556640625 |
| stage4_center_ready_rate | 0.000244140625 |
| stage4_push_ready_rate | 0.133544921875 |
| mean_pregrasp_entry_distance | 0.09961579740047455 |
| mean_pregrasp_distance | 0.07236537337303162 |
| mean_gripper_center_pregrasp_distance | 0.07236537337303162 |
| mean_touch_error | 0.028495822101831436 |
| mean_distance | 0.05849582329392433 |
| mean_insertion_alignment | 0.9077466726303101 |
| mean_target_contact_penalty | 0.0 |
| mean_pregrasp_center_progress | 0.986328125 |
| mean_center_push_progress | 0.5709028840065002 |
| mean_best_center_push_progress | 0.6485042572021484 |
| mean_center_push_improvement | 0.0008456815266981721 |
| mean_best_target_center_distance | 0.17202475666999817 |
| mean_target_center_improvement | 6.186078826431185e-05 |
| mean_target_center_shell_improvement | 0.011962890625 |
| mean_center_shortest_path_score | 0.6540575623512268 |
| mean_pregrasp_line_error | 1.3253376174304776e-08 |

## Interpretation

- 선생님 의견:
  - 마지막 stage에서 최단거리로 가까워지는 경우와 돌아가며 가까워지는 경우를 다르게 보상한다.
  - 빨간 구체 중심으로부터 같은 거리권의 보상은 한 번만 열리게 해서, 같은 거리에서 맴도는 행동을 줄인다.
- Codex 적용:
  - `center_shortest_path_score`를 추가해 insertion line과 gripper alignment가 좋을수록 거리 개선 보상이 커지게 했다.
  - `target_center_shell_improvement`를 추가해 빨간 구체 중심으로부터의 5mm 거리 shell을 더 안쪽으로 갱신할 때만 보상을 주었다.
  - 기존 center improvement 보상도 shortest-path score에 따라 25~100%로 조절되게 바꾸었다.
- 결과 평가:
  - `mean_target_center_shell_improvement=0.011962890625`로 shell 갱신 보상은 실제로 발생했다.
  - `mean_center_shortest_path_score=0.6540575623512268`로 직선 경로/정렬 조건이 보상에 반영되었다.
  - `stage3_touch_ready_rate=0.820556640625`로 접근과 touch 준비는 비교적 안정적이다.
  - `stage4_push_ready_rate=0.133544921875`, `mean_center_push_progress=0.5709028840065002`로 strong-push 실험보다 깊게 밀어 넣는 성향은 줄었다.
  - `success_rate=0.000244140625`로 최종 성공은 여전히 드물다.
  - `mean_target_contact_penalty=0.0`이라 안전 벌점은 발생하지 않았다.
- 다음 제안:
  - shortest-path/shell 보상은 유지한다.
  - 다만 마지막 push가 약해졌으므로, 다음 실험에서는 push depth 보상을 약간 되돌려 `경로 유지 + 마지막 밀어 넣기`의 혼합형으로 조정한다.
