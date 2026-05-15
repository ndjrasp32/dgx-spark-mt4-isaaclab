# 20260515_125300 stage4 center push plan

## 선생님 의견

- 마지막 중심 근처에 중심점이 잘 잡힌 상태라면, 더 이상 맴돌지 말고 빨간 구체 중심 쪽으로 밀어 넣는 방향이 좋을 수 있다.
- 마지막 단계가 어렵기 때문에, 정렬만 계속 보상하기보다 "들어가는 행동" 자체를 더 명확히 만들어야 한다.

## Codex 제안

- `targets`는 빨간 구체 중심이다.
- 처음에는 `touch_targets -> targets` 방향 진행률을 보상하려 했지만, 실제 초반 로그에서 이 값이 거의 0으로 나왔다.
- 이유는 정책이 아직 touch 지점 이후로 넘어가기 전에 push 보상이 거의 열리지 않았기 때문이다.
- 그래서 `pregrasp_targets -> targets` 전체 삽입 경로 진행률을 `center_push_progress`로 계산한다.
- 이렇게 하면 기존 stage3 지점에서도 마지막 중심 방향으로 더 밀어 넣는 보상이 열린다.
- stage4에서는 정렬과 lateral error가 유지된 상태에서 `center_push_progress`가 커질수록 보상한다.
- 이 보상은 성공 조건을 바꾸지 않는다. 최종 성공은 계속 `stage4_center_ready_rate`와 `success_rate`로 본다.

## 기대 효과

- 정책이 빨간 구체 근처에서 멈추거나 맴도는 행동을 줄인다.
- `stage3_touch_ready_rate` 이후 `mean_center_push_progress`가 올라가는지 확인할 수 있다.
- `stage4_push_ready_rate`가 먼저 올라가고, 그 다음 `stage4_center_ready_rate`가 올라가는 흐름을 기대한다.

## 실행

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage4_center_push_replay_128_250.sh --seed 42
MT4_PLOT_LABEL=stage4_center_push_replay_128env_250iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label stage4_center_push_replay_128env_250iter \
  --seed 42 \
  --num-envs 128 \
  --max-iterations 250 \
  --reward-profile stage4_center_push \
  --action-penalty 0.018 \
  --notes "Stage4 center-push reward: reward progress from touch target toward red target center while maintaining alignment and lateral accuracy."
```

## 결과

- run: `2026-05-15_12-55-21`
- best checkpoint: `model_950.pt`
- `success_rate=0.0`
- `stage3_touch_ready_rate=0.828857421875`
- `stage4_center_ready_rate=0.0`
- `stage4_push_ready_rate=0.729736328125`
- `mean_center_push_progress=0.5227710008621216`
- `mean_target_contact_penalty=0.0`
- plot snapshot: `logs/plots/20260515_125521_stage4_center_push_replay_128env_250iter`

## 해석

- 이번 실험은 최종 성공을 바로 만들지는 못했다.
- 하지만 `stage4_push_ready_rate`가 0.72 수준으로 측정되어, 정렬과 lateral 조건을 어느 정도 유지한 상태에서 빨간 구체 방향으로 밀어 넣는 중간 행동은 학습 신호로 잡혔다.
- 처음 구현한 `touch_targets -> targets` 기준 진행률은 거의 0으로 나와서 보상이 너무 늦게 열렸다.
- 수정한 `pregrasp_targets -> targets` 기준 진행률은 정책이 touch 지점까지 완전히 도달하기 전에도 빨간 구체 중심 방향으로 가는 행동을 보상할 수 있었다.
- 후반에는 `mean_center_push_progress`가 올라가는 대신 `stage3_touch_ready_rate`와 alignment가 다소 흔들렸다. 즉, 밀어 넣는 보상은 강하게 먹히지만 기존 접근 자세를 일부 희생하는 경향이 있다.

## 다음 제안

- center-push 보상은 유지하되, stage3 touch/alignment 유지 보상을 조금 더 강하게 묶어야 한다.
- 마지막 성공률을 올리려면 stage4 전용 replay state를 빨간 구체 중심에 더 가까운 상태로 다시 수집하거나, `final_center_success_radius`를 임시로 완화한 뒤 다시 줄이는 curriculum이 필요하다.
- 수업에서는 이번 결과를 "좋은 중간 지표가 생겼지만 최종 성공 조건은 아직 통과하지 못한 사례"로 보여주기 좋다.
