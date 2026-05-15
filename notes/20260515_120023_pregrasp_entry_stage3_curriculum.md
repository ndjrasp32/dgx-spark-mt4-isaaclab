# 20260515_120023 pregrasp entry and stage 3 curriculum

## 선생님 의견

- 기존 파란 marker 중앙 정렬은 생각보다 앞쪽에서 일어나 보였다.
- 파란 구체 전체를 하나의 영역으로 보고, 먼저 로봇팔과 가까운 표면 쪽 가운데 지점에 접근한 뒤 파란 구체 중앙으로 들어가는 흐름이 더 자연스럽다.
- 빨간 구체와 파란 구체는 로봇팔 베이스 축 기준으로 이미 정렬되어 있으므로, 파란 구체 중앙에 들어간 뒤에는 같은 방향을 유지하며 빨간 구체 방향으로 진입시키고 싶다.
- 마지막 진입은 stage 3 전용 curriculum으로 따로 많이 경험시키는 편이 좋다.

## Codex 제안

- 파란 marker 중앙은 그대로 두고, 보상 계산용으로 `pregrasp_entry_targets`를 추가한다.
- `pregrasp_entry_targets`는 파란 중앙에서 insertion 방향의 반대쪽으로 조금 물러난 지점이다.
- stage 2를 두 단계로 본다.
  - 2-A: 집게 중심이 파란 구체의 로봇팔 쪽 표면점에 접근한다.
  - 2-B: 같은 방향을 유지한 채 파란 구체 중앙으로 들어가고 잠깐 안정화한다.
- stage 3은 파란 중앙에서 빨간 구체 방향으로 진입하는 전용 학습으로 강화한다.
- observation/action 크기는 유지한다. 기존 `Isaac-MT4-Simplified-Reach-Direct-v0` train/play 명령 구조를 깨지 않기 위해서다.

## 적용 내용

- `pregrasp_entry_offset=0.030` 추가
- `pregrasp_entry_success_rate`, `pregrasp_entry_ready_rate`, `pregrasp_entry_reached_rate` 로그 추가
- `mean_pregrasp_entry_distance`, `mean_pregrasp_center_progress` 로그 추가
- stage 2 reward에 entry 접근 보상과 entry 이후 center progress 보상을 추가
- stage 2 center hold는 entry를 한 번 지나간 뒤에만 인정하도록 변경
- plot/select/record 도구가 새 지표를 CSV와 리포트에 포함하도록 수정

## 다음 실행 계획

1. 문법과 1 iteration smoke test로 environment가 깨지지 않았는지 확인한다.
2. 기존 best checkpoint로 pregrasp replay state를 다시 수집한다.
3. stage 3 replay-reset curriculum을 짧게 실행한다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/collect_pregrasp_states.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage_b_replay_reset_128_500.sh --seed 42
```

## 평가 기준

- `pregrasp_entry_success_rate`: 파란 구체 앞쪽 표면점까지 접근하는가
- `pregrasp_entry_reached_rate`: entry를 지나가는 episode가 충분히 생기는가
- `mean_pregrasp_center_progress`: entry에서 파란 중앙으로 들어가는가
- `stage2_pregrasp_ready_rate`: 파란 중앙에서 안정화되는가
- `stage3_insertion_ready_rate`: 중앙 이후 빨간 구체 방향 진입이 시작되는가
- `stage3_touch_ready_rate`와 `success_rate`: 최종 진입 성공으로 이어지는가

## 수업 설명 포인트

이번 수정은 "보상을 세게 주는 것"보다 "학생이 생각한 동작 순서를 물리적인 중간 목표로 다시 표현하는 것"에 가깝다.
성공률이 바로 오르지 않더라도, entry, center, insertion 지표가 순서대로 살아나는지 보면 어느 부분이 병목인지 설명할 수 있다.

## 1차 replay-reset 학습 결과

실행 중 첫 run은 `model_350.pt`까지만 저장되고 멈췄다. 이후 `model_350.pt`에서 이어받아 `2026-05-15_12-05-32` run으로 재개했다.

best checkpoint:

- `model_600.pt`

주요 지표:

- `pregrasp_entry_success_rate`: `0.939208984375`
- `pregrasp_entry_ready_rate`: `0.931396484375`
- `pregrasp_entry_reached_rate`: `0.933837890625`
- `pregrasp_success_rate`: `0.943603515625`
- `stage2_pregrasp_ready_rate`: `0.927490234375`
- `stage3_insertion_ready_rate`: `0.8701171875`
- `mean_pregrasp_center_progress`: `0.9594475030899048`
- `mean_insertion_progress`: checkpoint summary 기준 약 `0.4`대
- `stage3_touch_ready_rate`: `0.0`
- `success_rate`: `0.0`

해석:

- `entry -> center -> insertion` 순서 자체는 잘 살아났다.
- replay reset은 마지막 진입 구간을 자주 경험시키는 데 효과가 있었다.
- 아직 최종 성공이 나오지 않는 이유는 진입 시작이 아니라 마지막 깊이와 정밀 접촉 조건이다.
- 후반에는 action std가 커지고 alignment가 흔들려, 단순히 더 오래 학습하는 것보다 touch-depth 전용 보상/penalty 조정이 필요하다.

다음 제안:

- stage 3 touch-depth curriculum을 만든다.
- `stage3_touch_ready_rate`를 먼저 0.05 이상으로 올리는 것을 목표로 한다.
- action penalty 또는 entropy 쪽을 조정해, 진입 후 불필요하게 흔들리는 행동을 줄인다.
