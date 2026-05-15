# 20260515_113646 Stage Renumber And Insertion Plan

## 선생님 관찰

- `mean_pregrasp_line_error`가 0으로 나오므로 파란 marker 위치는 의도대로 정렬된 것으로 본다.
- 성공률이 낮은 이유는 정렬 후 파란 marker까지는 도착하지만, 그 상태에서 빨간 공 방향으로 실제 진입을 시작하지 않기 때문으로 보인다.
- 그래프에는 stage 2와 stage 3은 있는데 stage 1이 없어서, 학생들에게 단계 흐름을 설명하기 어렵다.

## Codex 제안

stage 이름을 수업용 동작 순서와 맞춘다.

```text
Stage 1: 빨간 공으로 들어갈 방향 정렬
Stage 2: 정렬된 상태로 파란 pregrasp marker에 도착하고 잠깐 대기
Stage 3: 같은 방향을 유지하면서 빨간 공 쪽으로 천천히 진입
```

기존 `stage2_alignment_ready_rate`는 backward compatibility를 위해 남기지만, 새 그래프와 기록에서는 다음 지표를 우선 본다.

- `stage1_alignment_ready_rate`
- `stage2_pregrasp_ready_rate`
- `stage3_insertion_ready_rate`
- `stage3_touch_ready_rate`

## Reward 수정

이전 stage 3 보상은 삽입 경로에 잘 정렬되어 있으면 보상을 받을 수 있어서, 파란 marker 근처에서 멈춘 채 더 들어가지 않아도 점수를 얻을 가능성이 있었다.

새 stage 3는 다음 조건을 더 강하게 본다.

- `pregrasp_held`가 먼저 켜져야 stage 3 보상이 열린다.
- `insertion_progress > 0.15`가 되어야 stage 3 진입 준비로 기록한다.
- 최종 성공은 `insertion_progress > 0.65`까지 들어가야 인정한다.
- line reward는 progress와 곱해져서, 선 위에 가만히 있는 것보다 앞으로 들어가는 행동이 더 유리하다.
- 천천히 진입하는 동작을 위해 progress가 있는 상태에서 낮은 관절 속도도 보상한다.

## 다음 학습

먼저 짧은 시각 학습으로 새 stage 이름과 진입 보상이 실제로 동작하는지 확인한다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_visual_16_300.sh --seed 42
MT4_PLOT_LABEL=stage_renumber_insertion_visual_16env_300iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label stage_renumber_insertion_visual_16env_300iter \
  --seed 42 \
  --num-envs 16 \
  --max-iterations 300 \
  --reward-profile stage_renumber_insertion \
  --notes "Stage 1 alignment, Stage 2 pregrasp hold, Stage 3 insertion progress after radial marker alignment."
```

## 평가 기준

- `stage1_alignment_ready_rate`: 방향을 먼저 잡는가
- `stage2_pregrasp_ready_rate`: 파란 marker에서 정렬된 대기 조건을 만족하는가
- `stage3_insertion_ready_rate`: 대기 후 실제로 빨간 공 방향으로 진입을 시작하는가
- `stage3_touch_ready_rate`: 표면 근처 깊이까지 들어가는가
- `mean_target_contact_penalty`: 빨간 공을 뚫거나 몸체가 충돌하지 않는가

이번 실험에서 `stage2_pregrasp_ready_rate`는 있는데 `stage3_insertion_ready_rate`가 낮으면, 다음 수정은 stage 3 progress reward를 더 키우거나 pregrasp hold 조건을 조금 완화하는 방향이다.

## 1차 시각 학습 중간 진단

16 env 시각 학습을 약 120 iteration까지 확인했다.

관찰:

- `stage1_alignment_ready_rate`는 0.9 근처까지 올라갔다.
- `mean_pregrasp_line_error`는 계속 0이었다.
- 하지만 `stage2_pregrasp_ready_rate`, `pregrasp_hold_ready_rate`, `pregrasp_held_rate`는 계속 0이었다.
- `mean_insertion_progress`는 높게 나왔지만, 이것은 파란 marker에서 hold한 뒤 진입한 것이 아니라 멀리서 삽입 방향으로 투영된 값이 커진 것으로 해석된다.

해석:

- stage 1 alignment reward가 너무 쉽게 누적되어, 정책이 파란 marker에 실제로 접근하지 않아도 높은 episode reward를 얻을 수 있었다.
- 따라서 stage 1은 힌트 수준으로 낮추고, stage 2 pregrasp 접근/hold 보상을 앞으로 당겨야 한다.

추가 수정:

- `stage1_alignment_weight`: `3.4 -> 1.6`
- `stage2_pregrasp_weight`: `3.8 -> 8.0`
- `stage2_touch_weight`: `2.4 -> 5.0`
- `stage2_hold_weight`: `1.0 -> 3.0`
- `pregrasp_success_radius`: `0.095 -> 0.120`
- `pregrasp_hold_radius`: `0.050 -> 0.080`
- `pregrasp_hold_min_stability`: `0.65 -> 0.45`

다음 재실행에서는 먼저 `stage2_pregrasp_ready_rate`가 0보다 커지는지를 본다.

## gripper center 기준 추가

선생님 추가 의견:

- 진입 전에 집게 끝 사이 가운데 지점이 파란 marker 중앙과 일치해야 한다.
- 그래야 그 다음 stage에서 빨간 공이 집게 사이로 자연스럽게 들어올 수 있다.

적용:

- USD 기준 왼쪽/오른쪽 pad는 local `y=+/-0.034`에 있고, pad 중심은 대략 local `x=0.158`에 있다.
- reward 기준점을 `gripper_center_offset_b=(0.158, 0.0, 0.0)`로 두었다.
- 기존 코드 호환을 위해 `gripper_tip_pos` 변수명은 유지하지만, 이제 이 값은 "집게 패드 사이 중앙점"을 의미한다.
- `pregrasp_distance`는 이 gripper center와 파란 marker 중앙 사이 거리로 계산된다.
- 새 로그 `mean_gripper_center_pregrasp_distance`도 추가했다.

평가 기준:

- `mean_gripper_center_pregrasp_distance`가 줄어드는가
- `stage2_pregrasp_ready_rate`가 0보다 커지는가
- 이 조건이 생긴 뒤 `stage3_insertion_ready_rate`가 생기는가

## 2차 시각 학습 결과

실행:

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_visual_16_300.sh --seed 42
MT4_PLOT_LABEL=stage_renumber_gripper_center_visual_16env_300iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label stage_renumber_gripper_center_visual_16env_300iter \
  --seed 42 \
  --num-envs 16 \
  --max-iterations 300 \
  --reward-profile stage_renumber_gripper_center
```

결과:

- best checkpoint: `model_299.pt`
- `stage1_alignment_ready_rate`: `0.98828125`
- `pregrasp_success_rate`: `0.712890625`
- `stage2_pregrasp_ready_rate`: `0.31640625`
- `mean_gripper_center_pregrasp_distance`: `0.10828651487827301`
- `stage3_insertion_ready_rate`: `0.01171875`
- `stage3_touch_ready_rate`: `0.0`
- `success_rate`: `0.0`
- `mean_target_contact_penalty`: `0.0`

해석:

- 집게 끝 사이 중앙점을 pregrasp 기준으로 쓰자 파란 marker 접근은 확실히 개선되었다.
- stage 1 정렬은 충분히 쉬운 상태가 되었고, stage 2 pregrasp도 0이 아니라 유의미하게 발생한다.
- 하지만 stage 3 진입은 아직 드물고, 최종 성공은 나오지 않았다.
- 충돌 벌점은 거의 0이므로, 현재 병목은 안전 회피가 아니라 "pregrasp에서 정렬을 유지한 채 앞으로 밀어 넣기"다.

다음 제안:

- stage 3 전용 curriculum을 분리한다.
- 초기 상태를 pregrasp 근처로 리셋하거나 replay state를 사용해, 정책이 stage 3 진입만 더 자주 경험하게 만든다.
- stage 2를 통과한 뒤에는 `insertion_progress` 보상을 더 강하게 주고, 옆으로 벗어나는 `insertion_lateral_error` 벌점을 키운다.
- 최종 성공 조건은 유지하되, 학습 초기에는 stage 3 ready/touch를 중간 성공으로 기록해 학생들이 "어디까지 학습됐는지"를 볼 수 있게 한다.
