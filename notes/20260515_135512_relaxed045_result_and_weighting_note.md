# 20260515_135512 relaxed 0.045 result and weighting note

## 선생님 의견

- `0.055m` 완화 성공 기준으로 성공률은 생겼지만, 아직 최종 성공률은 너무 낮다.
- 뒷 단계 보상 조건이 앞 단계 행동에 영향을 준다면, 앞 단계와 뒷 단계의 가중치를 다르게 둘 수 있다.
- 시간 소모에 따른 가중치도 단계별로 다르게 줄 수 있다.

## Codex 제안

- `0.055m` 다음 단계로 `0.045m`를 실험한다.
- 목표는 성공률을 완전히 잃지 않으면서 stage3 품질을 회복하는 것이다.
- 가중치 조정은 바로 섞기보다, 이번 `0.045m` 결과를 본 뒤 다음 실험 후보로 분리한다.

## 실행

```bash
MT4_REACH_FINAL_CENTER_RADIUS=0.045 \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/train_stage4_relaxed_success_128_300.sh --seed 42

MT4_PLOT_LABEL=20260515_135512_stage4_relaxed045_128env_300iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
```

## 실행 결과

- run: `2026-05-15_13-55-22`
- best checkpoint: `model_1600.pt`
- success reason: `highest meaningful success_rate`
- `success_rate=0.014404296875`
- `stage4_center_ready_rate=0.014404296875`
- `stage4_push_ready_rate=0.05615234375`
- `stage3_touch_ready_rate=0.366943359375`
- `stage2_pregrasp_ready_rate=0.377685546875`
- `mean_distance=0.06843922287225723`
- `mean_center_push_progress=0.5669831037521362`
- `mean_center_shortest_path_score=0.6251078248023987`
- `mean_target_contact_penalty=0.0`

## `0.055m` 실험과 비교

- `0.055m`는 `success_rate=0.028564453125`로 성공률은 더 높았다.
- 하지만 `stage3_touch_ready_rate=0.13330078125`라 앞 단계 품질이 낮았다.
- `0.045m`는 `success_rate=0.014404296875`로 성공률은 줄었지만, `stage3_touch_ready_rate=0.366943359375`로 좋아졌다.
- 따라서 `0.045m`가 교육용 curriculum 중간 단계로 더 균형이 좋다.

## 다음 가중치 후보

뒷 단계 보상이 앞 단계 행동을 끌어당기는 현상이 보인다. 후반 iteration에서는 stage3가 좋아지지만 final success가 사라지는 경향이 있었다.

다음 실험 후보:

- stage3 유지 보상은 일정 수준 이상 유지한다.
- stage4 성공 보상은 성공 반경이 작아질수록 점진적으로 키운다.
- stage4 시간 벌점은 stage3가 준비된 뒤에만 강하게 적용한다.
- stage3 준비 전에는 시간 벌점을 약하게 둬서, 앞 단계가 급하게 무너지는 것을 막는다.

수업에서는 이것을 "앞 단계는 자세를 만드는 보상, 뒤 단계는 목표를 끝내는 보상, 시간 벌점은 준비가 끝난 뒤 강해지는 압박"으로 설명할 수 있다.
