# 20260515_150245 blue center curriculum plan

## Teacher Idea

- 파란 구체의 최종 위치를 빨간 구체 중심점으로 잡는다.
- 그러면 마지막에 별도의 "밀어 넣기"를 학습시키는 대신, 파란 구체를 따라가는 경로 자체가 최종 성공 경로가 된다.
- 빨간 구체에 가까워질수록 점수가 올라가고, 이미 달성한 거리 보상은 다시 주지 않는 방식과 비슷하게 만들 수 있다.

## Codex Proposal

기존 guided-blue 실험은 파란 구체를 red target 앞의 safe touch 지점까지만 이동시켰다. 이번 실험은 goal mode를 추가해 파란 구체의 최종 목표를 red center로 바꾼다.

- `MT4_REACH_MOVING_PREGRASP_GOAL=touch`: 기존 방식, 빨간 구체 앞 표면 근처까지 안내
- `MT4_REACH_MOVING_PREGRASP_GOAL=center`: 새 방식, 빨간 구체 중심까지 안내

새 방식은 "집게 중심이 빨간 구체 중심과 일치"를 grasp-ready pose로 본다. 실제 물체가 있을 때는 이것이 물체를 치는 동작이 아니라, 물체가 집게 사이에 들어오는 상태로 해석되어야 한다.

## Safety Interpretation

- gripper center는 red center에 들어갈 수 있다.
- 다른 로봇팔 body는 계속 red target과 clearance를 유지해야 한다.
- `mean_target_contact_penalty`가 올라가면 실패한 설계로 본다.

## Initial Parameters

- `MT4_REACH_MOVING_PREGRASP_GOAL=center`
- `MT4_REACH_MOVING_PREGRASP_FINAL_FRACTION=1.0`
- `MT4_REACH_DESIRED_TOUCH_DISTANCE=0.0`
- `MT4_REACH_FINAL_CENTER_RADIUS=0.050`
- `MT4_REACH_NEAR_TERMINAL_RADIUS=0.060`
- `MT4_REACH_MOVING_PREGRASP_STEP_RADIUS=0.060`
- `MT4_REACH_MOVING_PREGRASP_REWARD_WEIGHT=14.0`
- `MT4_REACH_FINAL_INSERTION_WEIGHT=32.0`

## Test Command

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage4_blue_center_128_300.sh --seed 42
```

## What To Watch

- `moving_pregrasp_final_rate`: 파란 구체가 red center까지 이동되는 비율
- `stage4_center_ready_rate`: gripper center가 red center 성공 반경에 들어가는 비율
- `success_rate`: 최종 성공률
- `mean_target_contact_penalty`: 다른 링크가 빨간 구체를 건드리는지 여부

## Expected Result

좋은 결과라면 `moving_pregrasp_final_rate`와 `stage4_center_ready_rate`가 함께 올라간다. `moving_pregrasp_final_rate`만 올라가고 `stage4_center_ready_rate`가 낮으면, 파란 구체를 중심까지 보내는 안내는 되었지만 마지막 정밀 제어는 아직 부족한 것이다.

## Result

- run: `2026-05-15_15-05-58`
- best checkpoint: `model_2000.pt`
- plot snapshot: `logs/plots/20260515_150558_20260515_150245_stage4_blue_center_128env_300iter`
- experiment report: `experiments/20260515_150558_20260515_150245_stage4_blue_center_128env_300iter.md`

### Best Checkpoint Metrics

- `success_rate=0.0009765625`
- `stage1_latched_rate=0.987548828125`
- `pregrasp_entry_success_rate=0.958984375`
- `pregrasp_success_rate=0.979736328125`
- `stage2_latched_rate=0.8515625`
- `stage3_latched_rate=0.8515625`
- `stage4_center_ready_rate=0.0009765625`
- `stage4_push_ready_rate=0.394287109375`
- `mean_distance=0.061940357089042664`
- `mean_touch_error=0.061940357089042664`
- `moving_pregrasp_final_rate=0.842041015625`
- `mean_moving_pregrasp_fraction=0.84521484375`
- `mean_target_contact_penalty=0.0`

## Interpretation

- 선생님 아이디어의 핵심인 "파란 구체를 빨간 구체 중심까지 보내서 최종 경로를 안내한다"는 부분은 잘 작동했다. best checkpoint에서 `moving_pregrasp_final_rate`가 약 0.842까지 올라갔다.
- 안전 조건도 유지되었다. `mean_target_contact_penalty=0.0`이라 빨간 구체를 다른 링크가 건드리는 문제는 이번 결과에서는 나타나지 않았다.
- 하지만 엄격한 최종 성공률은 아직 낮다. `stage4_center_ready_rate`와 `success_rate`가 약 0.001에 머물렀고, 평균 거리는 약 0.062m로 `final_center_radius=0.050` 바깥에 있다.
- 따라서 이번 실험은 "경로를 만드는 curriculum"으로는 의미가 있지만, 마지막 중심 진입을 성공시키기 위해서는 별도의 terminal-center 학습이 필요하다.

## Next Proposal

- 다음 실험은 `final_center_radius`를 0.060 정도로 완화해 먼저 성공률을 만들고, 성공 사례가 생기면 다시 0.050 또는 0.045로 엄격화한다.
- 또는 `moving_pregrasp_final_rate`가 충분히 높은 checkpoint에서 시작해, stage4 terminal-center 전용으로 짧게 추가 학습한다.
- 학생 설명에서는 이번 결과를 "안내 목표를 잘 따라가도 최종 성공 조건이 너무 엄격하면 성공률이 낮게 기록될 수 있다"는 사례로 쓰기 좋다.
