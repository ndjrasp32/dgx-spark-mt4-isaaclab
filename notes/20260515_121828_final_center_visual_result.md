# 20260515_121828 final center visual result

## 선생님 의견

- 이번 단계는 영상으로 학습 장면을 보면서 확인하고 싶다.
- iteration별 점수 상황도 터미널에서 바로 보여야 한다.
- 빨간 구체 중심이 집게 양 끝 사이 중앙에 정확히 들어오는 것을 마지막 성공으로 보고 싶다.
- 같은 위치에서 반복 보상을 받으며 맴돌지 않도록, 이전보다 더 가까워졌을 때만 보상하는 방식이 좋다.

## Codex 제안

- Isaac Sim GUI에서 16개 병렬 환경을 띄워 짧은 시각 학습을 먼저 실행한다.
- stage별 지표를 터미널에서 보면서 어디까지 학습됐는지 해설한다.
- `best_target_center_distance`를 episode별로 저장하고, 빨간 구체 중심에 새롭게 더 가까워졌을 때만 `target_center_improvement` 보상을 준다.
- 선택 기준에는 기존 success뿐 아니라 `stage3_touch_ready_rate`, `stage4_center_ready_rate`, `mean_best_target_center_distance`를 같이 반영한다.

## 실행

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

## 결과

- run: `2026-05-15_12-18-28`
- plot snapshot: `logs/plots/20260515_121828_final_center_visual_16env_250iter`
- experiment report: `experiments/20260515_121828_final_center_visual_16env_250iter.md`
- best checkpoint: `model_750.pt`
- best checkpoint path: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-15_12-18-28/model_750.pt`

주요 지표:

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

## 평가

이번 실험은 최종 성공률만 보면 아직 낮다. 하지만 단계별로 보면 의미 있는 개선이 있다.

- Stage 1 정렬은 거의 항상 성공한다.
- Stage 2 파란 구체 중심 대기도 안정적으로 열렸다.
- Stage 3 빨간 구체 방향 진입과 touch 준비는 `0.90` 수준까지 올라갔다.
- Stage 4 빨간 구체 중심을 집게 중앙에 넣는 성공은 드물지만 처음으로 발생했다.

즉, 이제 병목은 전체 접근이나 방향 정렬이 아니라 마지막 몇 cm의 중심 정렬이다.

## 다음 제안

- stage 4 전용 replay reset을 추가해 빨간 구체 중심 근처에서 시작하는 상황을 더 많이 보여준다.
- 처음에는 `final_center_success_radius`를 약간 완화해 성공 샘플을 늘리고, 이후 다시 좁힌다.
- `mean_best_target_center_distance`와 `min_distance`가 줄어드는지 먼저 보고, 성공률은 그 다음 지표로 본다.
