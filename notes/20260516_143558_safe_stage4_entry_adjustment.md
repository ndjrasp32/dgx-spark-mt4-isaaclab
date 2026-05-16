# 2026-05-16 14:35 Safe Stage-4 Entry Adjustment

## 문제 관찰

사용자 관찰:
- 빨간 구체는 나중에 실제 목표 물체가 될 예정이므로, 진입 전에 로봇팔이나 집게가 먼저 치면 안 된다.
- GUI 시연에서 시작 직후 빨간 구체를 뚫고 들어가는 모습이 자주 보였다.
- 집게 사이에 물체가 들어간 상태가 아니라, 지나친 상태인데도 멈추는 경우가 있었다.

Codex 분석:
- 기존 `data/stage4_center_states/latest.pt` replay state는 빨간 구체 중심과 평균 약 5.5cm, 최소 약 3.8cm 거리에서 시작했다.
- 즉 마지막 단계 학습 시작점이 이미 너무 안쪽이라, “멀리서 안전하게 진입”하는 과정을 학습하기 어렵다.
- 기존 보상은 최종 중심 도달을 강조하지만, 최종 진입 허용 전 빨간 구체를 건드리지 말라는 규칙이 약했다.

## 반영한 해결 방향

1. Stage-4 시작 데이터를 더 안전한 지점에서 따로 수집한다.
   - 새 스크립트: `scripts/collect_stage4_safe_entry_states.sh`
   - 기본 필터:
     - alignment >= 0.70
     - insertion progress 0.18-0.58
     - red target center distance 0.075-0.150m
   - 의도: 정렬은 되어 있지만 빨간 구체를 아직 건드리지 않는 시작점 확보.

2. Stage-4 학습 스크립트가 안전 시작 데이터를 사용하도록 분리한다.
   - 새 스크립트: `scripts/train_stage4_smooth_blue_funnel_128_300.sh`
   - 기본 state file: `data/stage4_safe_entry_states/latest.pt`
   - blue guide는 8단계로 더 촘촘히 이동한다.

3. 최종 진입 전 빨간 구체 접근 벌점을 추가한다.
   - `MT4_REACH_EARLY_TARGET_CLEARANCE`
   - `MT4_REACH_EARLY_TARGET_CONTACT_PENALTY`
   - 최종 진입 조건이 갖춰지기 전 빨간 구체 중심에 너무 가까워지면 벌점.

4. 지나쳐서 멈추는 행동을 줄인다.
   - raw center push progress를 따로 기록한다.
   - `MT4_REACH_STAGE4_SUCCESS_MIN_PROGRESS`
   - `MT4_REACH_STAGE4_SUCCESS_MAX_PROGRESS`
   - `MT4_REACH_STAGE4_OVERSHOOT_PENALTY`
   - 성공은 목표 중심 근처뿐 아니라, 진입 진행도가 허용 범위 안에 있을 때만 인정한다.

5. 시각 확인을 쉽게 한다.
   - 파란 guide marker radius를 `0.016 -> 0.011`로 줄여, 집게 가운데 정렬 여부를 더 분명하게 보게 했다.
   - 새 GUI 시연 스크립트: `scripts/play_stage4_smooth_blue_funnel_best.sh`

## 다음 검증 순서

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/collect_stage4_safe_entry_states.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage4_smooth_blue_funnel_128_300.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
DEMO_SECONDS=120 ~/work/robotarm/mt4_isaac_lab_task/scripts/play_stage4_smooth_blue_funnel_best.sh
```

## 기대 관찰

- 시작 직후 빨간 구체를 뚫는 행동이 줄어든다.
- 파란 guide가 빨간 구체 바깥에서부터 더 촘촘히 이동한다.
- 집게 가운데점이 guide 중심을 따라가고, 마지막에만 빨간 구체 중심 방향으로 들어간다.
- 지나쳐서 멈추는 경우는 overshoot penalty와 progress band 때문에 점수가 낮아진다.

## 추가 수정

- 첫 학습 시도에서 `mean_center_push_overshoot`가 비정상적으로 커지는 문제가 발견되었다.
- 원인: moving blue guide가 빨간 중심으로 이동하면 현재 blue marker와 target 사이 거리가 거의 0이 되고, 그 값을 progress 분모로 사용했다.
- 수정: center push progress는 현재 이동 중인 blue marker가 아니라 최초 pregrasp start marker에서 red target까지의 전체 경로를 기준으로 계산한다.

## 짧은 검증 결과

실행:

```bash
MT4_MAX_ITERATIONS=80 ~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage4_smooth_blue_funnel_128_300.sh
MT4_SKIP_PLOT_SNAPSHOT=1 ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh --run-label safe_stage4_entry_smoke_seed42 --seed 42 --num-envs 128 --max-iterations 80
```

결과 요약:

- 선택 checkpoint: `model_429.pt`
- `success_rate`: `0.0`
- `stage1_alignment_ready_rate`: 약 `0.918`
- `pregrasp_success_rate`: 약 `0.537`
- `mean_alignment`: 약 `0.906`
- `mean_center_push_progress`: 약 `0.694`
- `mean_center_push_overshoot`: 약 `0.0095`
- `mean_early_target_contact_penalty`: 약 `0.0056`

해석:

- 최종 성공률은 아직 만들어지지 않았다.
- 다만 이전처럼 overshoot 수치가 폭주하지 않고, 빨간 구체 조기 접촉 벌점이 별도 지표로 잡히기 시작했다.
- 현재 bottleneck은 `moving_pregrasp_final_rate = 0.0`으로, 파란 guide가 최종 진입 지점까지 단계적으로 진행되지 못하는 점이다.
- 다음 튜닝은 성공 조건을 무작정 낮추기보다, 빨간 구체 바깥에서 시작한 상태가 guide를 따라 안쪽으로 안정적으로 이동하도록 `moving_pregrasp` 단계 진행 조건을 완화하는 쪽이 좋다.
