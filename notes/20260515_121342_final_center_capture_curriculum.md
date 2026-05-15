# 20260515_121342 final center capture curriculum

## 선생님 의견

- 파란 구체 중앙까지 도착하면 마지막 단계가 trigger되어야 한다.
- 마지막 단계에서는 빨간 구체 중앙 방향으로 가까워질수록 보상을 주고 싶다.
- 하지만 같은 위치에서 반복해서 보상을 받으면 빙빙 돌 수 있으므로, 이미 보상받은 거리에서는 같은 보상을 다시 주지 않는 편이 좋다.
- 최종 목적은 나중에 집게를 닫아 잡기 위한 자세다. 따라서 빨간 구체 중심이 집게 양 끝 사이 중앙에 정확히 들어와야 한다.
- 빨간 구체와 로봇팔 몸체의 부적절한 충돌은 계속 피해야 한다.

## Codex 제안

- episode마다 `best_target_center_distance`를 저장한다.
- stage 3이 열린 뒤 집게 중앙이 빨간 구체 중심에 더 가까워진 경우에만 `target_center_improvement` 보상을 준다.
- 같은 거리에서 머무르거나 빙빙 도는 행동에는 같은 보상이 반복 지급되지 않는다.
- 집게 링크 자체는 빨간 marker 중심을 포함할 수 있게 허용한다. 이것은 실제 grasp 준비 자세를 표현하기 위해서다.
- 대신 gripper link가 아닌 다른 로봇팔 body가 빨간 marker에 가까워지는 것은 계속 `target_contact_penalty`로 벌점 처리한다.
- 최종 성공은 `distance < final_center_success_radius`이고, 이때 시간 벌점은 제거된다.

## 적용 내용

- `final_center_success_radius=0.025`
- `best_target_center_distance`와 `target_center_improvement` 추가
- `stage4_center_ready_rate` 로그 추가
- `mean_best_target_center_distance`, `mean_target_center_improvement` 로그 추가
- stage 4 center improvement reward 추가
- final center success에서는 time penalty를 적용하지 않음
- plot/select/record 도구에 stage 4 지표 추가

## 영상 학습 실행 계획

이번 단계는 화면으로 보면서 확인한다.

```bash
cd ~/work/isaac/src/IsaacLab
unset CMEEL_PREFIX
export DISPLAY=:1
export MT4_REACH_TRAINING_MODE=stage_b_insertion
export MT4_REACH_RESET_MODE=pregrasp_replay
export MT4_REACH_PREGRASP_STATE_FILE=~/work/robotarm/mt4_isaac_lab_task/data/pregrasp_states/latest.pt
export MT4_REACH_REPLAY_PROB=0.80
export MT4_REACH_REPLAY_JOINT_NOISE=0.012
export MT4_REACH_REPLAY_TARGET_NOISE=0.003
./isaaclab.sh -p scripts/reinforcement_learning/rsl_rl/train.py \
  --task Isaac-MT4-Simplified-Reach-Direct-v0 \
  --num_envs 16 \
  --max_iterations 250 \
  --resume \
  --load_run 2026-05-15_12-05-32 \
  --checkpoint model_600.pt \
  --seed 42
```

터미널에서 볼 지표:

- `stage3_insertion_ready_rate`: 파란 중앙 이후 진입 시작
- `stage4_center_ready_rate`: 빨간 중심이 집게 중앙에 들어온 비율
- `mean_best_target_center_distance`: episode 중 빨간 중심에 가장 가까워진 평균 거리
- `mean_target_center_improvement`: 새로 가까워진 정도
- `mean_target_contact_penalty`: 집게 외 몸체 충돌 위험

## 기대하는 해석

- `stage3_insertion_ready_rate`는 이미 높으므로 유지되는지 본다.
- `stage4_center_ready_rate`가 0보다 커지면 마지막 중심 정렬이 시작된 것이다.
- `mean_best_target_center_distance`가 줄어들면 집게 중앙 안으로 빨간 구체가 들어오는 방향이다.
- `mean_target_center_improvement`가 초반에 높다가 줄어드는 것은 자연스럽다. 더 가까워질 새 거리가 줄어들기 때문이다.

## 2026-05-15 12:18 GUI 학습 결과

- run: `2026-05-15_12-18-28`
- label: `final_center_visual_16env_250iter`
- 실행 방식: Isaac Sim GUI에서 16 env 병렬 학습을 보면서 진행
- 시작 checkpoint: `2026-05-15_12-05-32/model_600.pt`
- 선택된 best checkpoint: `model_750.pt`

주요 결과:

- `stage1_alignment_ready_rate=0.98828125`
- `pregrasp_entry_reached_rate=0.986328125`
- `stage2_pregrasp_ready_rate=0.96875`
- `stage3_insertion_ready_rate=0.923828125`
- `stage3_touch_ready_rate=0.90234375`
- `stage4_center_ready_rate=0.001953125`
- `success_rate=0.001953125`
- `mean_distance=0.05730348080396652`
- `min_distance=0.030794596299529076`
- `mean_target_contact_penalty=0.0`
- `mean_pregrasp_line_error=0.000000014439212492334264`

해석:

- 파란 구체 entry, 파란 구체 중심 대기, 빨간 구체 방향 진입까지는 상당히 안정화되었다.
- 빨간 구체 중심을 집게 중앙에 정확히 넣는 마지막 단계는 처음으로 열렸지만 아직 드물다.
- `target_contact_penalty=0.0`이므로 현재 병목은 충돌 회피가 아니라 마지막 중심 정렬의 정밀도다.
- 다음 실험은 stage 4 전용 reset/curriculum을 추가하거나 `final_center_success_radius`를 아주 조금 완화해 성공 사례를 더 자주 만들고, 그 뒤 다시 엄격하게 줄이는 방식이 적절하다.
