# 20260514_190155 Stage-B Insertion 128env 500iter

## 목적

통합 정책에서 마지막 touch-depth가 병목으로 남았기 때문에, 기존 best checkpoint에서 이어받아 `Policy B: 삽입 깊이 정밀화`를 초기 학습했다.

## 실행

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage_b_insertion_128_500.sh --seed 42
~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label stage_b_insertion_seed42_128env_500iter \
  --seed 42 \
  --num-envs 128 \
  --max-iterations 500 \
  --reward-profile stage_b_insertion \
  --action-penalty 0.010 \
  --notes "Resume from touch-depth best checkpoint; Stage-B narrows targets and emphasizes final insertion depth."
```

## 출발 checkpoint

```text
/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-14_18-42-19/model_550.pt
```

## 선택된 best checkpoint

```text
/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-14_19-01-55/model_800.pt
```

선택 이유:

- success rate가 0.01보다 낮아서, selector가 balanced pregrasp distance and alignment 기준으로 골랐다.
- `mean_touch_error`가 이전 touch-depth run의 selected checkpoint보다 작아졌다.
- contact penalty는 0으로 유지되었다.

## 주요 결과

| metric | value |
|---|---:|
| success_rate | 0.000244140625 |
| pregrasp_success_rate | 0.878662109375 |
| stage2_alignment_ready_rate | 0.93603515625 |
| stage3_insertion_ready_rate | 0.000244140625 |
| stage3_touch_ready_rate | 0.000244140625 |
| mean_pregrasp_distance | 0.09452423453330994 |
| mean_touch_error | 0.05733250454068184 |
| mean_distance | 0.09733249247074127 |
| mean_insertion_alignment | 0.861351728439331 |
| mean_target_contact_penalty | 0.0 |
| mean_insertion_progress | 0.8214305639266968 |
| min_distance | 0.06380301713943481 |

## 해석

Stage-B 초기 학습은 긍정 신호와 한계를 동시에 보여준다.

긍정 신호:

- `mean_touch_error`가 `0.0901 -> 0.0573`으로 줄었다.
- `mean_distance`가 `0.1301 -> 0.0973`으로 줄었다.
- `pregrasp_success_rate`와 `stage2_alignment_ready_rate`가 높게 유지되었다.
- `mean_target_contact_penalty=0.0`이라 빨간 공을 뚫는 방식으로 reward를 얻지는 않았다.

한계:

- 최종 `stage3_touch_ready_rate`와 `success_rate`는 여전히 매우 낮다.
- `stage3_insertion_ready_rate`가 크게 떨어졌다. 즉, touch-depth를 좁히는 과정에서 stage3 gate 조건을 안정적으로 만족하지 못했다.
- 학습 초반에는 성공률이 더 높게 튀는 구간이 있었지만, 긴 학습 후에는 안정적인 성공으로 수렴하지 않았다.

## 다음 판단

단순히 Stage-B reward를 강하게 주는 것만으로는 마지막 삽입 동작이 안정화되지 않았다. 다음 단계는 다음 중 하나가 적절하다.

1. Stage-B reset을 실제 pregrasp 근처 자세에서 시작하는 curriculum을 추가한다.
2. Stage-B success gate를 `stage3_insertion_ready`와 `touch-depth`로 더 분리해서, line alignment가 무너졌을 때 바로 알 수 있게 한다.
3. 실제 rigid target과 contact sensor는 다음 grasp/lift task로 넘기되, 현재 reach task에서는 안전한 pregrasp policy를 우선 확정한다.

교육적으로는 좋은 사례다. 그래프가 보여주는 결론은 "문제를 나누는 것만으로 충분하지 않고, 나눈 문제의 시작 상태도 같이 설계해야 한다"이다.

## 그래프

고정 저장 위치:

```text
logs/plots/20260514_190155_stage_b_insertion_128env_500iter/
```
