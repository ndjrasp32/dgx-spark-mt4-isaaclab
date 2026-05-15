# 20260515_152644 blue marker step gate plan

## Teacher Observation

- 파란 구체가 빨간 구체 근처로 가면서 순식간에 사라지는 것처럼 보인다.
- 실제로는 집게의 가운데가 파란 구체 중심에 맞아야 하는데, 한쪽 집게 다리만 닿아도 진행되는 것처럼 보인다.
- 파란 구체를 조금 작게 만들고, 파란 구체를 여러 번 재생성하면서 빨간 구체 방향으로 천천히 유도해야 한다.

## Diagnosis

- 거리 계산 자체는 이미 `gripper_tip_pos`라는 legacy 이름을 쓰지만, 실제 값은 `gripper_center_pos`이다. 즉, 정책 기준점은 집게 양쪽 패드 사이의 가운데다.
- 문제는 moving pregrasp 단계 간 간격보다 통과 반경이 너무 컸다는 점이다.
- 이전 blue-center 기본값은 `steps=3`, `step_radius=0.060`이었다. 파란 구체 한 단계 간 이동 거리가 약 0.03-0.04m 수준이라, 한 단계가 성공하면 다음 단계도 바로 성공 범위 안에 들어갈 수 있었다.

## Codex Proposal

- 파란 구체 시각 반경을 `0.025 -> 0.016`으로 줄인다.
- blue-center curriculum 기본값을 `steps=5`, `step_radius=0.018`, `hold_steps=8`로 바꾼다.
- 집게 중심점이 현재 파란 구체 중심 근처에 일정 프레임 유지될 때만 다음 파란 구체를 생성한다.
- 새 지표를 추가한다:
  - `moving_pregrasp_step_ready_rate`: 현재 파란 구체 중심에 들어온 비율
  - `mean_moving_pregrasp_hold_progress`: 다음 파란 구체로 넘어가기 위한 유지 진행도

## Expected Effect

- 파란 구체가 한 번에 빨간 구체 중심으로 튀지 않고, 경로 안내점처럼 단계적으로 이동한다.
- 한쪽 집게 다리가 아니라 집게 가운데 지점이 파란 구체 중심에 맞아야 다음 단계로 넘어간다.
- 학습 그래프에서 `moving_pregrasp_final_rate`만 보는 것이 아니라, 각 step에서 제대로 멈추고 있는지 `moving_pregrasp_step_ready_rate`와 `mean_moving_pregrasp_hold_progress`를 함께 확인할 수 있다.

## Next Test

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/play_stage4_blue_center_best.sh
```

이 시연은 기존 checkpoint를 새 step gate 환경에서 보여주는 확인용이다. 실제 성능 평가는 새 기준으로 짧은 재학습을 돌린 뒤 그래프와 함께 봐야 한다.
