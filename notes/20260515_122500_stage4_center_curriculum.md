# 20260515_122500 stage4 center curriculum

## 선생님 의견

- 마지막 단계는 빨간 구체 중심이 집게 양 끝 사이 중앙에 들어오는 것이다.
- 한 번 보상받은 위치에서 계속 맴돌면 안 되므로, 빨간 구체 중심에 새롭게 더 가까워질 때만 보상을 주는 방식이 좋다.
- 빨간 구체는 나중에 실제로 집을 대상이므로, 팔 몸체가 부딪히는 것은 피해야 한다.
- 다만 집게 가운데로 빨간 구체가 들어오는 동작은 목표 자체이므로, 이 상황을 벌점으로 막으면 안 된다.
- 빨간 구체가 너무 크면 집게가 들어가기 전에 물체를 쳐버리는 것처럼 보여 수업 해석이 어려우므로 조금 작게 표현한다.

## Codex 제안

- 기존 stage3까지 잘 가는 checkpoint에서, 빨간 구체 근처에 이미 진입한 상태만 따로 수집한다.
- 수집한 상태로 replay reset을 걸어 마지막 중심 정렬만 많이 연습시킨다.
- `stage4_center` 학습 모드에서는 stage1/stage2 보상은 낮추고, center improvement와 center precision 보상을 크게 올린다.
- 초기 성공 샘플을 늘리기 위해 `final_center_success_radius`는 기본 `0.035m`로 완화하고, 안정화되면 다시 `0.025m`로 줄인다.
- 빨간 target marker와 task의 `target_radius`를 `0.035m`에서 `0.025m`로 줄이고, stage3 touch 기준 거리도 `0.040m`에서 `0.030m`로 줄인다.

## 충돌 벌점 기준

- 집게 link가 빨간 구체 중심을 포함하는 것은 허용한다.
- 이유: 최종 목표가 빨간 구체 중심을 집게 가운데에 넣는 것이기 때문이다.
- 집게가 아닌 다른 로봇팔 body가 빨간 구체에 접근하면 `target_contact_penalty`가 발생한다.
- 따라서 현재 벌점은 "집게로 목표를 감싸는 행동"이 아니라 "팔 몸체가 목표를 치는 행동"을 막는 역할이다.

## 실행 순서

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/collect_stage4_center_states.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage4_center_replay_128_300.sh --seed 42
MT4_PLOT_LABEL=stage4_center_replay_128env_300iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
```

## 볼 지표

- `stage4_center_ready_rate`: 마지막 중심 정렬 성공 비율
- `success_rate`: 최종 성공 비율
- `mean_best_target_center_distance`: episode 중 빨간 구체 중심에 가장 가까웠던 평균 거리
- `mean_target_center_improvement`: 이전 최단거리보다 더 가까워진 정도
- `mean_target_contact_penalty`: 집게 외 몸체 충돌 위험

## 2026-05-15 12:31 실행 결과

- source checkpoint: `2026-05-15_12-18-28/model_750.pt`
- replay state: `data/stage4_center_states/latest.pt`
- training run: `2026-05-15_12-31-14`
- plot snapshot: `logs/plots/20260515_123114_stage4_center_replay_128env_300iter`
- best checkpoint: `model_900.pt`

Stage-4 replay state 수집 결과:

- count: `512`
- `mean_center_dist=0.054908`
- `mean_progress=0.758300`
- `mean_touch=0.024908`
- `mean_align=0.878912`
- `mean_line=0.000000`

학습 결과:

- `stage1_alignment_ready_rate=0.972900390625`
- `pregrasp_entry_reached_rate=0.9375`
- `stage2_pregrasp_ready_rate=0.930419921875`
- `stage3_insertion_ready_rate=0.929931640625`
- `stage3_touch_ready_rate=0.9169921875`
- `stage4_center_ready_rate=0.000244140625`
- `success_rate=0.000244140625`
- `mean_distance=0.06427979469299316`
- `min_distance=0.03963880240917206`
- `mean_target_contact_penalty=0.0`

평가:

- 작은 빨간 구체 기준에서도 몸체 충돌 벌점은 0으로 유지되었다.
- stage 3 touch는 `0.91` 수준까지 올라가, 빨간 구체 근처 진입은 더 안정적이다.
- 하지만 stage 4 center success는 아직 매우 드물다.
- 후반으로 갈수록 action std가 커져 마지막 중심 정렬을 지나쳐 버리는 경향이 있다.

다음 제안:

- stage4에서는 action std 또는 entropy를 낮춰 마지막 몇 cm에서 덜 흔들리게 한다.
- replay state를 `mean_center_dist < 0.045` 수준으로 더 가까운 상태만 모으는 2차 수집을 시도한다.
- 최종 radius를 바로 줄이지 말고 `0.035m`에서 성공률을 먼저 올린 뒤 `0.025m`로 되돌린다.
