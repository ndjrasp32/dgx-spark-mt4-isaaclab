# 20260515_105947 Radial Pregrasp Training Plan

## 현재 상태

파란 pregrasp marker는 이제 빨간 target과 로봇팔 베이스 중심축을 잇는 직선 위에 놓인다. 또한 집게 끝이 파란 marker 근처에서 방향을 맞추고 속도가 낮아진 순간을 `pregrasp_held`로 기록한다.

이 변경은 task geometry와 reward gate를 바꾼 것이므로, 이전 checkpoint와 replay state는 참고용으로만 본다. 새 기준으로 최소 한 번은 다시 시각 학습을 돌려야 한다.

## 1단계: 짧은 시각 학습

목표:

- 파란 marker가 빨간 공의 진입선 위에 보이는지 확인
- 16개 병렬 로봇팔이 같은 기준으로 움직이는지 확인
- `mean_pregrasp_line_error`가 0에 가깝게 유지되는지 확인
- `pregrasp_hold_ready_rate` 또는 `pregrasp_held_rate`가 생기는지 확인

실행:

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_visual_16_300.sh --seed 42
MT4_PLOT_LABEL=radial_pregrasp_visual_16env_300iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label radial_pregrasp_visual_16env_300iter \
  --seed 42 \
  --num-envs 16 \
  --max-iterations 300 \
  --reward-profile radial_pregrasp_hold \
  --notes "Visual check for radial blue pregrasp marker, hold gate, and safe insertion alignment."
```

통과 기준:

- 화면에서 파란 공이 빨간 공과 베이스 중심선을 기준으로 틀어져 보이지 않는다.
- `mean_pregrasp_line_error`가 0에 가깝다.
- `mean_insertion_alignment`가 양수 방향으로 올라간다.
- `mean_target_contact_penalty`가 낮게 유지된다.

## 2단계: full baseline 재학습

1단계가 납득되면 128 env / 1000 iter로 새 baseline을 만든다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_128_1000.sh --seed 42
MT4_PLOT_LABEL=radial_pregrasp_128env_1000iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label radial_pregrasp_128env_1000iter \
  --seed 42 \
  --num-envs 128 \
  --max-iterations 1000 \
  --reward-profile radial_pregrasp_hold \
  --notes "Full baseline after aligning blue pregrasp marker with the base-to-red radial line."
```

평가 기준:

- `pregrasp_held_rate`: 파란 marker에서 대기 조건이 생기는가
- `stage3_insertion_ready_rate`: 대기 후 삽입 경로로 들어갈 준비가 되는가
- `stage3_touch_ready_rate`: 빨간 공 표면 근처까지 도달하는가
- `success_rate`: 최종 성공이 반복적으로 생기는가
- `mean_target_contact_penalty`: 빨간 공 충돌을 피하는가

## 3단계: replay reset 재수집

full baseline에서 pregrasp hold가 생기면, 기존 `data/pregrasp_states/latest.pt`를 새 기준으로 다시 만든다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/collect_pregrasp_states.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage_b_replay_reset_128_500.sh --seed 42
MT4_PLOT_LABEL=radial_stage_b_replay_reset_128env_500iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
```

이 단계의 목적은 처음부터 전체 동작을 다시 배우는 것이 아니라, 파란 marker에서 멈춘 뒤 빨간 공 방향으로 들어가는 마지막 구간을 더 자주 연습시키는 것이다.

## 권장 순서

오늘 바로 진행한다면 1단계만 먼저 실행하는 편이 좋다. 시각적으로 marker와 hold gate가 맞는지 확인한 뒤에야 2단계 긴 학습 결과를 믿을 수 있다.
