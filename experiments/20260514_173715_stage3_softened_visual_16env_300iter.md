# 20260514_173715_stage3_softened_visual_16env_300iter

## Purpose

마지막 삽입 단계가 거의 성공으로 이어지지 않는 문제를 확인하기 위한 16-env visual training입니다.

이전 alignment-first 실험에서는 방향 정렬은 크게 좋아졌지만, 파란 공 이후 빨간 공 표면으로 들어가는 stage 3 신호가 매우 드물었습니다. 이번 실험은 stage 3 보상 gate와 성공 band를 조금 완화해서 마지막 진입 행동이 학습 신호로 나타나는지 확인했습니다.

## Teacher Idea

- 파란 공에 먼저 닿는 것보다, 빨간 공으로 들어갈 방향을 먼저 맞추는 것이 자연스럽다.
- 파란 공에 닿은 뒤 같은 방향으로 빨간 공에 천천히 진입해야 한다.
- 빨간 공은 실제 물체라고 생각해야 하므로, 진입 전 충돌하거나 뚫고 지나가면 벌점을 줘야 한다.

## Codex Suggestion

- alignment-first curriculum은 유지한다.
- stage 3 보상이 너무 늦게 켜지지 않도록 gate와 reward curve를 완화한다.
- best checkpoint 선택에서 `stage3_insertion_ready_rate`를 더 중요하게 본다.
- 충돌 벌점은 유지해서 낮은 contact penalty를 같이 확인한다.

## Command

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_visual_16_300.sh --seed 42
~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
```

## Best Checkpoint

```text
model_50.pt
/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-14_17-37-15/model_50.pt
```

## Metrics

```text
success_rate                  = 0.0
pregrasp_success_rate         = 0.236328125
stage2_alignment_ready_rate   = 0.97265625
stage3_insertion_ready_rate   = 0.03125
mean_pregrasp_distance        = 0.15286558866500854
mean_distance                 = 0.14324891567230225
mean_insertion_alignment      = 0.8894004821777344
mean_insertion_progress       = 0.71201491355896
mean_target_contact_penalty   = 0.0000073
```

## Interpretation

완전 성공한 정책은 아닙니다. 하지만 이전 실험과 비교하면 마지막 단계가 그래프에 잡히기 시작했습니다.

- 좋은 점:
  - 삽입 방향 정렬은 안정적입니다.
  - 파란 공 접근 성공률이 best checkpoint에서 약 23.6%까지 나타났습니다.
  - stage 3 readiness가 0보다 커졌습니다.
  - contact penalty가 거의 0이라 빨간 공을 심하게 뚫는 방식은 아직 주된 해결책이 아닙니다.
- 남은 문제:
  - final `success_rate`는 아직 낮습니다.
  - 후반 checkpoint들은 stage2는 안정적이지만 stage3가 다시 줄어드는 경향이 있습니다.
  - 마지막 touch/insertion 조건이 아직 민감합니다.

## Next Decision

다음 개선은 final success를 억지로 크게 완화하기보다, stage 3에서 lateral error와 touch error를 더 직접적으로 줄이는 방향이 좋습니다. 특히 파란 공에 도달한 뒤 target surface로 전진하는 속도를 보상하고, 옆으로 벗어난 경우를 더 명확히 감점하는 실험이 필요합니다.
