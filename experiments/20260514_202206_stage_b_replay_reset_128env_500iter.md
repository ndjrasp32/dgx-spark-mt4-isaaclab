# 20260514_202206 Stage-B Replay Reset 128env 500iter

## 목적

Stage-B insertion 학습에서 마지막 touch-depth 성공이 희소하게 나타나는 문제를 줄이기 위해 curriculum reset을 적용했다. Policy A가 pregrasp 조건을 만족한 순간의 상태를 수집하고, Stage-B 학습 reset에서 일부 환경을 그 상태로 시작시켰다.

## 수집

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/collect_pregrasp_states.sh
```

수집 결과:

| item | value |
|---|---:|
| collected_states | 512 |
| mean_pregrasp_distance | 0.078574 |
| mean_insertion_alignment | 0.940773 |
| mean_touch_error | 0.044674 |

저장 파일:

```text
data/pregrasp_states/latest.pt
```

## 학습 실행

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage_b_replay_reset_128_500.sh --seed 42
~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label stage_b_replay_reset_seed42_128env_500iter \
  --seed 42 \
  --num-envs 128 \
  --max-iterations 500 \
  --reward-profile stage_b_replay_reset \
  --action-penalty 0.010 \
  --notes "Stage-B replay reset starts from collected pregrasp states; highest success appears at replay-initial checkpoint, while later training lowers touch error but success remains sparse."
```

## 선택된 best checkpoint

```text
/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-14_20-22-06/model_800.pt
```

Selector 선택 이유:

- `success_rate=0.01123046875`로 의미 있는 성공률이 가장 높았다.
- 다만 이 checkpoint는 replay reset 학습의 첫 checkpoint라서, 학습으로 새로 얻은 성능이라기보다 "좋은 pregrasp 상태에서 시작했을 때 기존 정책도 성공할 수 있음"을 보여주는 값으로 해석해야 한다.

## 주요 결과

| metric | selected model_800 | late model_1299 |
|---|---:|---:|
| success_rate | 0.01123046875 | 0.0009765625 |
| stage3_touch_ready_rate | 0.014404296875 | 0.0009765625 |
| mean_touch_error | 0.12020038068294525 | 0.040830716490745544 |
| mean_distance | 0.16020037233829498 | 0.08083072304725647 |
| mean_target_contact_penalty | 0.0 | 0.0 |

## 해석

좋아진 점:

- curriculum reset은 마지막 구간을 훨씬 자주 경험하게 만들었다.
- 학습 후반의 `mean_touch_error`는 `0.0408`까지 내려갔다.
- `mean_target_contact_penalty=0.0`이라 빨간 공을 뚫고 지나가는 방식으로 학습하지는 않았다.
- replay reset 시작점에서는 성공률이 `0.0112`까지 나타났다.

아쉬운 점:

- 성공률이 학습 후반까지 안정적으로 유지되지는 않았다.
- selector가 고른 `model_800.pt`는 "replay 초기 조건에서 성공 가능"을 보여주지만, policy가 추가 학습으로 안정화되었다는 뜻은 아니다.
- 후반 checkpoint는 더 가까워졌지만 성공 gate를 자주 통과하지 못했다.

## 다음 제안

다음은 두 갈래로 판단한다.

1. 데모용:
   - replay reset 조건에서 `model_800.pt`를 시각적으로 확인한다.
   - 이것은 "좋은 pregrasp 상태가 주어지면 마지막 삽입 성공 가능성이 생긴다"를 보여주는 용도다.

2. 학습 개선용:
   - replay probability를 `0.75 -> 0.50`으로 낮춰 folded start와 replay start를 섞는다.
   - `stage3_touch_ready`만 성공으로 너무 강하게 보지 말고, `mean_touch_error`와 `insertion_lateral_error`를 함께 보는 선택 기준을 만든다.
   - 실제 성공을 높이려면 final success gate를 더 작은 하위 gate로 나누는 것이 필요하다.

## 그래프

고정 저장 위치:

```text
logs/plots/20260514_202206_stage_b_replay_reset_128env_500iter/
```
