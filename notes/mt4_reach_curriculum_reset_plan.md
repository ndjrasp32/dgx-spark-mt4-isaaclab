# MT4 Reach Curriculum Reset 설계

작성일: 2026-05-14

## 1. 왜 이 방법이 필요한가

지금까지의 Stage-B insertion 학습은 마지막 단계가 왜 어려운지 보여주었습니다.

- 파란 공 근처까지 가는 능력은 생겼다.
- 빨간 공 방향으로 들어갈 방향 정렬도 어느 정도 된다.
- 하지만 빨간 공 표면 근처의 정확한 깊이까지 들어가는 성공은 매우 드물다.

이 상황에서 같은 환경을 계속 학습하면, 로봇은 episode 대부분을 "파란 공 근처까지 가는 과정"에 씁니다. 정작 우리가 학습시키고 싶은 "파란 공 근처에서 빨간 공 쪽으로 안전하게 밀고 들어가는 마지막 0.04m"는 자주 경험하지 못합니다.

그래서 curriculum reset이 필요합니다.

## 2. 한 문장 설명

Policy A가 잘 도착한 pregrasp 순간을 저장해 두고, Stage-B 학습에서는 일부 episode를 그 상태에서 바로 시작하게 만듭니다.

즉, 학생들에게는 이렇게 말할 수 있습니다.

```text
마지막 동작을 배우게 하려면, 마지막 동작을 연습할 수 있는 출발점에서 자주 시작시켜야 한다.
```

## 3. 기존 방식과 curriculum reset 방식

| 구분 | 기존 Stage-B resume | Curriculum reset |
|---|---|---|
| 시작 상태 | 접힌 기본 자세 | 일부는 pregrasp 근처 상태 |
| 장점 | 실제 전체 task와 비슷함 | 마지막 삽입 동작을 자주 연습함 |
| 단점 | 마지막 단계 경험이 희소함 | replay 상태를 수집하고 관리해야 함 |
| 수업 의미 | 어려운 문제를 한 번에 풀기 | 어려운 문제의 연습 구간을 설계하기 |

## 4. 구현 흐름

### 4.1 Policy A 상태 수집

먼저 기존 policy를 실행합니다. 실행 중 다음 조건이 만족되는 순간을 저장합니다.

```text
pregrasp_distance < 0.110
insertion_alignment > 0.70
target_contact_penalty <= 0.0001
```

저장하는 값:

- `joint_pos`: 로봇팔 5개 관절 위치
- `joint_vel`: 로봇팔 5개 관절 속도
- `targets`: 빨간 공 위치
- `pregrasp_targets`: 파란 공 위치
- `touch_targets`: 빨간 공 표면 근처 목표 위치
- 평가 지표: pregrasp distance, alignment, touch error, contact penalty

실행 스크립트:

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/collect_pregrasp_states.sh
```

기본 저장 위치:

```text
data/pregrasp_states/latest.pt
```

### 4.2 Stage-B replay reset 학습

그 다음 Stage-B 학습을 할 때 reset mode를 바꿉니다.

```bash
MT4_REACH_RESET_MODE=pregrasp_replay
```

이 모드에서는 reset 때 모든 환경을 접힌 기본 자세에서 시작하지 않습니다. 일정 확률로 저장된 pregrasp 상태를 꺼내서 시작합니다.

기본값:

```text
MT4_REACH_REPLAY_PROB=0.75
MT4_REACH_REPLAY_JOINT_NOISE=0.025
MT4_REACH_REPLAY_TARGET_NOISE=0.004
```

의미:

- 75% episode는 pregrasp 근처에서 시작한다.
- 관절에 작은 noise를 넣어 외운 자세만 반복하지 않게 한다.
- target에도 작은 noise를 넣어 비슷하지만 조금 다른 상황을 만든다.

실행 스크립트:

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage_b_replay_reset_128_500.sh --seed 42
```

## 5. 왜 noise를 넣는가

저장된 상태를 그대로 반복하면 로봇은 특정 자세만 외울 수 있습니다. 실제 목표는 "비슷한 pregrasp 상황에서 빨간 공으로 안전하게 들어가는 방법"을 배우는 것입니다.

그래서 작은 noise를 추가합니다.

- 너무 작으면 외우기 쉬움
- 너무 크면 pregrasp 상태가 깨짐
- 지금은 교육용 초기값으로 `0.025 rad` 관절 noise와 `0.004 m` target noise를 사용

## 6. 성공 판단 기준

이번 curriculum reset 실험에서는 다음 지표를 봅니다.

좋은 신호:

- `stage3_touch_ready_rate`가 이전 Stage-B보다 증가
- `success_rate`가 이전 Stage-B보다 증가
- `mean_touch_error`가 더 감소
- `mean_target_contact_penalty`는 낮게 유지

나쁜 신호:

- `mean_target_contact_penalty`가 증가
- `stage2_alignment_ready_rate`가 크게 감소
- replay reset에서는 성공하지만 folded reset에서는 전혀 안 됨

## 7. 학생들에게 설명할 때의 비유

처음부터 전체 동작만 반복하는 것은 농구를 배울 때 매번 코트 반대편에서 드리블을 시작해서 마지막 슛을 연습하는 것과 비슷합니다. 슛이 약점이라면, 먼저 골대 가까이에서 슛을 많이 연습해야 합니다. 그 뒤에 드리블과 슛을 다시 연결합니다.

이 프로젝트에서는 마지막 삽입이 바로 그 "슛"입니다. 그래서 pregrasp 근처에서 시작하는 연습장을 따로 만들어 주는 것입니다.

## 8. 다음 실험 절차

주의: 2026-05-14 이후 파란 pregrasp marker 위치는 빨간 공과 로봇팔 베이스 중심축을 잇는 방사선 위에 놓이도록 수정했습니다. 따라서 이전 geometry에서 저장한 `data/pregrasp_states/latest.pt`는 새 학습에 그대로 쓰지 않는 것이 좋습니다. 새 geometry로 정책을 다시 확인한 뒤, 아래 1번부터 다시 수집합니다.

1. pregrasp replay 상태 수집

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/collect_pregrasp_states.sh
```

2. replay reset Stage-B 학습

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage_b_replay_reset_128_500.sh --seed 42
```

3. 그래프 생성과 best checkpoint 선택

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
```

4. 결과 기록

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label stage_b_replay_reset_seed42_128env_500iter \
  --seed 42 \
  --num-envs 128 \
  --max-iterations 500 \
  --reward-profile stage_b_replay_reset \
  --action-penalty 0.010 \
  --notes "Stage-B starts from collected pregrasp replay states to practice final insertion more often."
```

## 9. 중요한 한계

이 방법은 실제 로봇팔 제어로 바로 넘어가는 방법이 아닙니다. replay reset은 시뮬레이션 학습을 돕는 장치입니다.

실제 로봇팔에 적용하려면:

- Policy A가 실제로 pregrasp 상태까지 안정적으로 도달해야 한다.
- Policy B는 Policy A가 만든 실제 자세에서 이어받아도 동작해야 한다.
- 관절 속도와 힘 제한, emergency stop, 충돌 감지가 필요하다.

따라서 curriculum reset은 "마지막 동작을 먼저 잘 배우게 하는 훈련장"이고, 최종 목표는 다시 전체 task에서 연결해서 검증하는 것입니다.

## 10. 첫 실행 결과

2026-05-14에 첫 curriculum reset 실험을 실행했습니다.

상태 수집:

- 512개 pregrasp 상태 수집
- 평균 `pregrasp_distance=0.078574`
- 평균 `insertion_alignment=0.940773`
- 평균 `touch_error=0.044674`

학습 결과:

- selected checkpoint: `2026-05-14_20-22-06/model_800.pt`
- selected `success_rate=0.01123046875`
- selected `stage3_touch_ready_rate=0.014404296875`
- selected `mean_target_contact_penalty=0.0`

중요한 해석:

- `model_800.pt`의 높은 성공률은 학습 첫 checkpoint에서 나왔다.
- 이것은 "좋은 pregrasp 시작 상태를 주면 기존 정책도 성공 가능성이 생긴다"는 뜻이다.
- 학습 후반의 `model_1299.pt`는 `mean_touch_error=0.040830716490745544`로 더 가까워졌지만, 성공률은 `0.0009765625`로 낮았다.
- 즉 curriculum reset은 마지막 구간을 더 자주 연습하게 만드는 데 성공했지만, 아직 안정적인 성공 정책을 만든 것은 아니다.

다음 개선:

- replay start 비율을 `0.75`에서 `0.50`으로 낮춰 전체 task와 마지막 구간을 섞는다.
- best checkpoint 선택 기준을 success만이 아니라 touch-error와 stage3 gate를 함께 보도록 조정한다.
- final success를 더 작은 하위 조건으로 쪼개서 어느 gate가 병목인지 더 잘 보이게 한다.

## 11. 파란 marker 정렬 변경

선생님 관찰:

- 파란 공이 빨간 공과 집게 진입선에서 조금 틀어져 있으면, 집게 끝이 파란 공에 닿아도 빨간 공이 집게 사이로 자연스럽게 들어오지 않는다.
- 따라서 파란 공은 독립 target이 아니라 "빨간 공으로 들어가기 직전의 대기 지점"이어야 한다.

Codex 제안:

- 파란 marker를 빨간 공 위치에서 로봇팔 베이스 중심 방향으로 조금 당기고, 위쪽으로 조금 올린 위치로 계산한다.
- 이때 XY 좌표는 항상 베이스 중심축과 빨간 공을 잇는 직선 위에 놓이게 한다.
- 집게 끝이 파란 marker에 닿고, 삽입 방향 정렬이 맞고, 관절 속도가 낮은 상태를 `pregrasp_hold_ready`로 기록한다.

적용된 의미:

```text
빨간 공: 최종으로 집게 사이에 들어가야 할 목표
파란 공: 같은 진입선 위에서 잠깐 멈추는 pregrasp/hold 위치
```

새로 보는 지표:

- `mean_pregrasp_line_error`: 파란 marker가 베이스-빨간공 직선에서 벗어난 정도
- `pregrasp_hold_ready_rate`: 집게 끝이 파란 marker 근처에서 정렬된 채로 대기 가능한 비율
- `pregrasp_held_rate`: episode 안에서 위 대기 조건을 한 번이라도 만족한 비율

다음 replay reset 실험은 이 두 지표가 안정적으로 낮거나 높게 나오는지 먼저 확인한 뒤 진행합니다.
