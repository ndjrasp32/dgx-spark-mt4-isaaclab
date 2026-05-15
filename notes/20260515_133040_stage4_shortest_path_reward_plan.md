# 20260515_133040 stage4 shortest-path reward plan

## 선생님 의견

- 마지막 stage에서 보상값을 다변화한다.
- 빨간 구체 중심까지의 최단거리 방향으로 접근하면 보상을 크게 준다.
- 돌아가면서 가까워지는 경우에는, 가까워지더라도 보상을 작게 준다.
- 빨간 구체 중심으로부터 동일한 거리권의 보상을 한 번 달성하면, 같은 거리권의 다른 위치에서는 같은 보상이 사라지도록 한다.
- 목적은 지속적으로 빨간 구체 중심 방향의 최단거리를 추구하게 만드는 것이다.

## Codex 제안

- 기존 `best_target_center_distance`는 이미 "이전보다 더 가까워졌을 때만 보상"하는 구조다.
- 이번 수정에서는 그 구조를 더 명확히 확장한다.
- `center_shortest_path_score`를 추가해, insertion line을 잘 지키고 gripper 방향이 맞을수록 거리 개선 보상이 커지게 한다.
- `target_center_shell_improvement`를 추가해, 빨간 구체 중심으로부터의 거리 구간을 5mm shell로 나눈다.
- 같은 shell에서는 이미 보상을 받았다면 다시 큰 보상을 받지 못한다.
- 더 안쪽 shell로 들어갔을 때만 shell improvement 보상이 열린다.

## 적용

- `stage4_shortest_path_weight` 추가
- `stage4_distance_shell_weight` 추가
- `center_distance_shell_size` 추가
- `mean_target_center_shell_improvement` 지표 추가
- `mean_center_shortest_path_score` 지표 추가
- plot/select/record 도구에 새 지표 반영

## 기대

- 돌아가는 접근은 `center_shortest_path_score`가 낮아져 같은 거리 개선이라도 보상이 작아진다.
- 같은 거리권에서 맴도는 행동은 shell 보상을 반복해서 받지 못한다.
- 더 안쪽 shell로 들어가는 행동이 강화되어 마지막 중심 정렬 성공률을 올리는 데 도움이 된다.

## 다음 실행

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage4_push_strong_replay_128_300.sh --seed 42
MT4_PLOT_LABEL=stage4_shortest_path_replay_128env_300iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
```

## 실행 결과

- run: `2026-05-15_13-31-34`
- best checkpoint: `model_1548.pt`
- `success_rate=0.000244140625`
- `stage3_touch_ready_rate=0.820556640625`
- `stage4_center_ready_rate=0.000244140625`
- `stage4_push_ready_rate=0.133544921875`
- `mean_center_push_progress=0.5709028840065002`
- `mean_best_center_push_progress=0.6485042572021484`
- `mean_target_center_shell_improvement=0.011962890625`
- `mean_center_shortest_path_score=0.6540575623512268`
- `mean_target_contact_penalty=0.0`
- plot snapshot: `logs/plots/20260515_133134_stage4_shortest_path_replay_128env_300iter`

## 평가

- 새 지표는 정상적으로 기록되었다.
- `mean_target_center_shell_improvement`가 0보다 커서, 더 안쪽 거리 shell에 들어갈 때만 보상이 열리는 구조가 작동했다.
- `mean_center_shortest_path_score`가 0.65 수준으로 유지되어, 경로 유지 조건도 학습 신호에 반영되었다.
- 이전 strong-push 실험보다 `stage4_push_ready_rate`와 `mean_center_push_progress`는 낮아졌다.
- 반대로 `stage3_touch_ready_rate`와 `pregrasp_held_rate`는 더 안정적으로 높아졌다.
- 즉, 이번 보상은 "무조건 더 깊게 밀기"보다 "경로를 유지하며 조심스럽게 접근하기"로 정책을 바꿨다.

## 다음 제안

- 이 방향은 교육적으로 설명하기 좋지만, 최종 성공률을 바로 크게 올리지는 못했다.
- 다음에는 shortest-path 보상은 유지하되, 마지막 0.57 이후 push를 다시 조금 강화하는 혼합형이 좋다.
- 예: `stage4_push_ready_progress=0.60`, `stage4_distance_shell_weight` 유지, `stage4_push_depth_weight`를 중간값으로 조정한다.
