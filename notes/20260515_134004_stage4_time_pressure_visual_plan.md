# 20260515_134004 stage4 time-pressure visual plan

## 선생님 의견

- 최종 성공 직전까지는 시간 벌점을 부과하는 방향이 맞다.
- stage4에 돌입하면 빨간 구체를 잡을 수 있는 위치까지 빠르게 진입해야 한다.
- 최단거리로 진입하면 정렬에도 도움이 될 수 있다.
- 성공 지점에 도착하면 시간 벌점을 제거하고, 더 이상의 보상/벌점을 없애고, 해당 성공 상태에서 학습 step을 종료하는 편이 맞다.
- 탐색 비율은 너무 줄인 것 같으니 아주 살짝만 올려본다.
- 설명만 듣기보다 GUI에서 직접 보면서 이해하는 것이 좋다.

## Codex 제안

- 기존 환경도 success가 되면 episode를 종료하지만, 성공 step에서 shaped reward가 함께 더해지고 있었다.
- 이번에는 success step에서는 terminal success bonus만 남기고, 추가 shaped reward/penalty를 더하지 않도록 정리한다.
- `stage3_ready` 이후를 stage4 진입 상태로 보고, 성공 전까지 `stage4_time_pressure`를 추가로 부과한다.
- 이 시간 압박은 stage4에 들어온 뒤 오래 맴돌수록 손해가 커지게 한다.
- 탐색은 급격히 늘리지 않고 `entropy_coef=0.0025`, `init_noise_std=0.40`, `action_scale=0.026`으로 살짝만 올린다.
- GUI 확인용 스크립트와 128 env 학습용 스크립트 설정을 같은 방향으로 맞춘다.

## 적용

- `stage4_time_penalty_weight` 추가
- `mean_stage4_time_pressure` 지표 추가
- success step에서는 `success_bonus`만 반환하도록 reward 정리
- `scripts/train_stage4_time_pressure_visual_16_120.sh` 추가
- `scripts/train_stage4_push_strong_replay_128_300.sh` 기본 탐색/시간압박 설정 조정

## 실행

GUI 확인:

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage4_time_pressure_visual_16_120.sh --seed 42
```

128 env 결과 확인:

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage4_push_strong_replay_128_300.sh --seed 42
MT4_PLOT_LABEL=20260515_134344_stage4_time_pressure_128env_300iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
```

## 실행 결과

- GUI 확인 run: `2026-05-15_13-40-54`
- 128 env 학습 run: `2026-05-15_13-43-44`
- best checkpoint: `model_1600.pt`
- `success_rate=0.00048828125`
- `stage3_touch_ready_rate=0.7861328125`
- `stage4_push_ready_rate=0.19921875`
- `mean_center_push_progress=0.6045380234718323`
- `mean_best_center_push_progress=0.668278157711029`
- `mean_center_shortest_path_score=0.673416256904602`
- `mean_stage4_time_pressure=0.4132959246635437`
- `mean_target_contact_penalty=0.0`

## 평가

- 시간 벌점 지표는 정상적으로 기록되었다.
- success step에서 추가 shaped reward/penalty를 제거하는 구조도 문법 검증과 학습 실행을 통과했다.
- 탐색을 아주 살짝 올린 결과, 이전 shortest-path-only 실험보다 `stage4_push_ready_rate`가 `0.1335 -> 0.1992`로 회복되었다.
- 다만 최종 성공률은 아직 매우 낮다.
- 현재 병목은 "파란 지점 도달과 정렬"이 아니라, 마지막 구간에서 빨간 구체 중심을 집게 중앙에 안정적으로 넣는 정밀 진입이다.
- 다음 개선은 stage4 terminal 직전의 성공 반경/집게 중심 위치 정의를 다시 확인하고, success 직전 상태를 더 많이 replay하는 방향이 좋다.
