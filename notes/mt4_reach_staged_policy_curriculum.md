# MT4 Reach 단계형 정책 학습 계획

작성일: 2026-05-14

이 문서는 MT4 simplified reach task를 하나의 정책으로 끝까지 학습시키는 방식과, 조건이 충족되면 다음 정책으로 넘기는 단계형 방식을 구분하기 위해 작성했습니다. 수업에서는 "문제를 잘게 나누면 무엇이 좋아지는가"를 설명하는 자료로 사용할 수 있습니다.

## 1. 지금까지의 결론

현재 task 이름은 계속 유지합니다.

```text
Isaac-MT4-Simplified-Reach-Direct-v0
```

지금까지의 통합 학습은 다음 단계까지는 의미 있는 개선을 보였습니다.

- 빨간 공으로 들어갈 45도 접근 방향 정렬
- 파란 pregrasp 공 근처로 이동
- 파란 공에서 빨간 공 방향으로 들어가는 경로 진입
- 빨간 공과 로봇팔이 겹치는 행동을 줄이는 안전 벌점 유지

하지만 마지막 병목이 남았습니다.

- `stage3_insertion_ready_rate`는 좋아졌지만 `stage3_touch_ready_rate`와 `success_rate`는 매우 낮습니다.
- 즉, "경로로 들어가는 것"은 어느 정도 되었지만 "빨간 공 표면 근처의 정확한 깊이까지 들어가는 것"이 아직 어렵습니다.

## 2. 선생님 의견

선생님이 제안한 동작 구조는 다음과 같습니다.

1. 집게 끝이 파란색 구체에 닿도록 한다.
2. 파란색 구체에 닿은 상태에서 빨간색 구체로 들어갈 수 있도록 같은 각도로 정렬한다.
3. 정렬이 완료되면 천천히 빨간색 구체 방향으로 진행해서 빨간색 구체가 집게 사이에 들어가게 한다.

추가 조건은 다음과 같습니다.

- 빨간색 구체는 실제 물체라고 생각한다.
- 진입 전에는 로봇팔 몸체나 집게가 빨간 공과 닿으면 안 된다.
- 너무 오래 걸리면 안 되므로 시간 벌점이 필요하다.
- 마지막 단계가 너무 어려우면 문제를 나누어 학습하는 편이 낫다.

## 3. Codex 제안

현재 결과를 보면 하나의 정책이 모든 단계를 동시에 배우는 방식은 마지막 정밀 삽입에서 학습 신호가 희소해집니다. 그래서 다음처럼 나누는 것을 제안합니다.

### Policy A: 접근과 정렬

Policy A는 기존 통합 task에서 학습한 정책입니다.

목표:

- 접힌 자세에서 시작한다.
- 빨간 공 위치를 보고, 로봇팔 기준 45도 접근 방향을 만든다.
- 그 방향을 유지하며 파란 pregrasp 공 근처까지 이동한다.
- 빨간 공과 충돌하지 않는다.

Policy A가 다음 단계로 넘어갈 수 있는 조건:

```text
pregrasp_distance < pregrasp_success_radius
insertion_alignment > insertion_alignment_success
target_contact_penalty ~= 0
```

### Policy B: 삽입 깊이 정밀화

Policy B는 Policy A가 이미 만든 자세에서 이어받는다고 가정하고, 마지막 진입 깊이를 더 강하게 학습합니다.

목표:

- 파란 공 근처에서 시작한 정책이라고 보고, 빨간 공 방향으로 천천히 들어간다.
- 삽입 경로에서 옆으로 벗어나지 않는다.
- 빨간 공 중심을 뚫지 않고, 표면 근처의 목표 깊이에 맞춘다.
- 접촉/겹침 벌점을 유지한다.

학습 구현:

- 새 task 이름을 만들지 않는다.
- `Isaac-MT4-Simplified-Reach-Direct-v0`를 그대로 사용한다.
- 환경변수로 학습 모드만 바꾼다.

```bash
MT4_REACH_TRAINING_MODE=stage_b_insertion
```

이 모드에서는 목표 범위를 조금 좁히고, stage 3의 line/progress/touch-depth 보상을 더 강하게 줍니다. 기존 best checkpoint에서 이어받아 학습하므로, 이미 배운 접근/정렬 능력을 출발점으로 삼습니다.

## 4. 두 방식의 차이

| 구분 | 통합 정책 | 단계형 정책 |
|---|---|---|
| 정책 개수 | 1개 | 2개 이상 |
| 장점 | 실행 구조가 단순함 | 실패 원인을 단계별로 분석하기 쉬움 |
| 단점 | 마지막 성공 신호가 희소하면 학습이 막힘 | 단계 전환 조건을 잘 설계해야 함 |
| 현재 용도 | baseline과 시각 데모 | 마지막 삽입 단계 안정화 |

수업에서는 통합 정책을 먼저 보여주고, 그래프에서 마지막 단계가 왜 막히는지 확인한 뒤, 단계형 정책으로 문제를 줄이는 과정을 보여주는 것이 좋습니다.

## 5. 이번 초기 학습 계획

이번 초기 학습은 Policy B를 처음 시도하는 실험입니다.

출발점:

```text
2026-05-14_18-42-19/model_550.pt
```

실행:

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage_b_insertion_128_500.sh --seed 42
~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label stage_b_insertion_seed42_128env_500iter \
  --seed 42 \
  --num-envs 128 \
  --max-iterations 500 \
  --reward-profile stage_b_insertion \
  --notes "Resume from touch-depth best checkpoint and emphasize final insertion depth."
```

## 6. 평가 기준

성공률 하나만 보지 않습니다. 특히 초기 학습에서는 다음 순서로 봅니다.

1. `stage3_insertion_ready_rate`가 유지되는가
2. `stage3_touch_ready_rate`가 이전보다 커지는가
3. `mean_touch_error`가 줄어드는가
4. `mean_target_contact_penalty`가 낮게 유지되는가
5. `success_rate`가 반복적으로 0보다 커지는가

좋은 결과:

- `stage3_touch_ready_rate`가 올라간다.
- `mean_touch_error`가 내려간다.
- 충돌 벌점은 낮게 유지된다.

좋지 않은 결과:

- `pregrasp_success_rate`가 크게 떨어진다.
- `mean_target_contact_penalty`가 올라간다.
- 정책이 빨간 공을 뚫는 방식으로 reward를 얻으려 한다.

## 7. 다음 선택지

초기 Stage-B 학습이 좋아지면:

- Policy A 체크포인트와 Policy B 체크포인트를 나누어 저장한다.
- play/demo에서 A 조건이 충족되면 B 정책으로 전환하는 구조를 만든다.

초기 Stage-B 학습이 좋아지지 않으면:

- Stage-B reset을 실제 pregrasp 근처 자세로 시작하게 만드는 curriculum을 추가한다.
- 빨간 공을 rigid object로 바꾸고 contact sensor 기반 penalty를 넣는다.
- insertion 전용 task를 별도 환경으로 분리하되, 학생용 문서에서는 task 분해 사례로 설명한다.

## 8. 초기 학습 결과

2026-05-14에 Stage-B 초기 학습을 실행했습니다.

```text
run: 2026-05-14_19-01-55
best: model_800.pt
```

핵심 결과:

- `mean_touch_error`: `0.0901 -> 0.0573`
- `mean_distance`: `0.1301 -> 0.0973`
- `pregrasp_success_rate`: `0.8787`
- `stage2_alignment_ready_rate`: `0.9360`
- `mean_target_contact_penalty`: `0.0`
- `success_rate`: `0.000244`
- `stage3_touch_ready_rate`: `0.000244`

해석:

- Stage-B reward profile은 빨간 공 표면 근처로 더 가까워지는 데 도움이 되었다.
- 하지만 안정적인 성공률로 이어지지는 않았다.
- 다음 개선은 reward 가중치만 더 키우는 것이 아니라, Stage-B가 실제로 pregrasp 근처에서 시작하도록 reset/curriculum을 설계하는 것이다.
