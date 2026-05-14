# MT4 Reach Decision Log

이 파일은 MT4 reach task를 개선하면서 나온 아이디어를 구분해서 기록합니다. 수업에서는 "문제를 관찰하고, 가설을 세우고, 실험하고, 결과를 보고 다시 고치는 과정"을 보여주는 용도로 사용합니다.

## 2026-05-14 집게 길이 문제

- 선생님 관찰:
  - 집게 너비는 괜찮지만, 집게가 갈라지기 전 기둥 부분이 너무 길어서 목표에 접근하기 어렵다.
- Codex 제안:
  - 실제 집기 구현 전 단계이므로 gripper mount visual/collision 길이를 줄이고, reward에서 사용하는 fingertip offset도 같은 위치로 맞춘다.
- 적용:
  - `assets/usd/mt4_simplified_v3.usd` 재생성
  - `gripper_tip_offset_b`를 짧아진 tip 위치에 맞춤
- 결과:
  - 시각적으로는 아쉽지만 학습 가능한 단순 모델에 더 가까워졌다.
  - old checkpoint와 직접 비교하기 어려우므로 이후 실험은 새 baseline으로 본다.

## 2026-05-14 단계 순서 변경

- 선생님 관찰:
  - 파란 공에 먼저 닿아도 `insertion_alignment`가 음수이면 다음 단계로 이어지지 않는다.
  - 애초에 빨간 공으로 들어갈 방향을 먼저 찾고, 그 방향으로 파란 공에 접촉하는 편이 자연스럽다.
- Codex 제안:
  - reward 순서를 `파란 공 접촉 -> 삽입 정렬`에서 `삽입 정렬 -> 정렬 유지 상태에서 파란 공 접촉`으로 바꾼다.
  - stage별 지표를 분리해서 어느 단계에서 막히는지 그래프로 확인한다.
- 적용:
  - active alignment를 insertion direction 중심으로 변경
  - pregrasp reward를 alignment gate 뒤에 배치
  - `stage2_alignment_ready_rate`, `stage3_insertion_ready_rate`를 추가 기록
- 결과:
  - 16-env 300-iter 실험에서 `mean_insertion_alignment`가 약 `0.97`까지 올라갔다.
  - 다만 final success는 거의 없어서 stage 3가 다음 병목으로 남았다.

## 2026-05-14 마지막 삽입 단계 완화

- 선생님 목표:
  - 집게 끝이 파란 공에 닿고, 같은 각도로 빨간 공 방향으로 진입해서 집게 사이에 빨간 공이 들어가는 마지막 단계를 성공시키고 싶다.
  - 빨간 공은 진입 전 충돌하면 안 되므로 벌점이 필요하다.
- Codex 제안:
  - alignment-first 구조는 유지한다.
  - stage 3 보상 gate와 성공 band를 조금 완화해서, final insertion 학습 신호가 너무 늦게 켜지는 문제를 줄인다.
  - 충돌 벌점은 유지해 "뚫고 지나가기"를 성공으로 보지 않게 한다.
  - best checkpoint 선택 기준에 stage 3 readiness를 더 강하게 반영한다.
- 적용:
  - `success_radius`, `touch_success_band`, `pregrasp_success_radius`를 교육용 초기 실험에 맞게 완화
  - stage 3 line/touch/progress 보상 가중치 증가
  - checkpoint summary와 experiment log에 stage별 준비율 추가
- 평가 계획:
  - 16-env visual training으로 먼저 확인
  - 성공률이 높지 않아도 `stage3_insertion_ready_rate`가 이전보다 늘면 개선으로 판단
  - `mean_target_contact_penalty`가 증가하면 안전 보상 또는 target clearance를 다시 조정
- 결과:
  - `20260514_173715_stage3_softened_visual_16env_300iter` 실험을 완료했다.
  - best checkpoint는 `model_50.pt`로 선택되었다.
  - `stage2_alignment_ready_rate=0.97265625`, `stage3_insertion_ready_rate=0.03125`, `pregrasp_success_rate=0.236328125`.
  - `mean_target_contact_penalty`는 거의 0이라 충돌 회피 조건은 크게 깨지지 않았다.
  - 최종 `success_rate`는 아직 낮으므로, 마지막 삽입 정밀도는 다음 개선 대상으로 남았다.

## 2026-05-14 128-env full baseline

- 선생님 목표:
  - 시각 실험에서 가능성이 보였으니, 더 많은 병렬 환경과 학습량으로 마지막 단계를 실제로 더 안정화한다.
- Codex 제안:
  - 같은 보상 설정을 유지하고 `128 env / 1000 iter`로 확장한다.
  - 최종 성공률이 희소할 수 있으므로 stage 3 readiness와 safety metric을 함께 본다.
- 적용:
  - `train_128_1000.sh --seed 42`
  - `plot_and_select_best.sh`
  - `record_experiment_result.sh`
- 결과:
  - best checkpoint는 `model_650.pt`.
  - `pregrasp_success_rate=0.85986328125`
  - `stage2_alignment_ready_rate=0.9150390625`
  - `stage3_insertion_ready_rate=0.688720703125`
  - `mean_target_contact_penalty=0.0`
  - checkpoint 기준 최고 `success_rate`는 `model_300.pt`의 `0.000732421875`였다.
- 해석:
  - 파란 공 도달, 삽입 방향 정렬, 삽입 경로 진입은 크게 개선되었다.
  - final success는 아직 낮다.
  - 다음 병목은 "경로를 찾는 것"이 아니라 빨간 공 표면 근처의 touch depth 정밀도다.

## 2026-05-14 touch-depth precision experiment

- 선생님 목표:
  - 파란 공 이후 같은 각도로 빨간 공 쪽으로 조금 더 들어가는 마지막 단계를 학습한다.
  - 빨간 공을 뚫는 방식은 피해야 한다.
- Codex 제안:
  - pregrasp에 머무는 보상을 줄이고, stage 3의 progress/touch-depth 보상을 강화한다.
  - `stage3_ready`와 `stage3_touch_ready`를 분리해 "삽입 경로 진입"과 "표면 깊이 도달"을 따로 평가한다.
- 적용:
  - `pregrasp_bonus_weight`: `3.0 -> 1.2`
  - `stage3_touch_weight`: `4.0 -> 5.0`
  - `stage3_progress_weight`: `1.6 -> 3.0`
  - `stage3_depth_weight = 5.0` 추가
  - `mt4/stage3_touch_ready_rate` 기록 추가
- 결과:
  - best checkpoint는 `model_550.pt`.
  - `success_rate=0.001708984375`
  - `stage3_insertion_ready_rate=0.69189453125`
  - `stage3_touch_ready_rate=0.001708984375`
  - `mean_touch_error=0.09006259590387344`
  - `mean_target_contact_penalty=0.0`
- 해석:
  - 성공률은 이전 selected baseline보다 약간 좋아졌지만, touch-depth는 아직 희소하다.
  - 단순히 보상 가중치를 더 주는 방식만으로는 빨간 공 표면 깊이를 안정적으로 학습시키기 어렵다.
  - 다음에는 curriculum 또는 stage B 전용 삽입 학습으로 문제를 더 작게 나누는 편이 좋다.

## 2026-05-14 단계형 정책 분리

- 선생님 질문:
  - 문제를 나눈다는 것은, 특정 조건이 충족되면 진입 학습만 진행한 정책을 실행한다는 뜻인지 확인했다.
- Codex 제안:
  - 맞다. 수업용으로는 하나의 거대한 행동을 `Policy A: 접근/정렬`과 `Policy B: 삽입 깊이`로 분리해서 설명하는 편이 좋다.
  - 당장 새 task 이름을 만들지 않고, 기존 task 이름은 유지한 채 `MT4_REACH_TRAINING_MODE=stage_b_insertion` 환경변수로 Stage-B curriculum을 켠다.
  - Stage-B는 이전 best checkpoint에서 resume하여 이미 배운 접근 능력을 출발점으로 삼고, 마지막 touch-depth 보상을 더 강하게 학습한다.
- 적용:
  - `notes/mt4_reach_staged_policy_curriculum.md` 문서 추가
  - `scripts/train_stage_b_insertion_128_500.sh` 추가
  - `MT4_REACH_TRAINING_MODE=stage_b_insertion` 보상 profile 추가
- 평가 계획:
  - `stage3_touch_ready_rate`, `mean_touch_error`, `success_rate`, `mean_target_contact_penalty`를 중심으로 본다.
  - 성공률이 크게 오르지 않아도 touch-ready와 touch-error가 좋아지면 다음 curriculum 설계의 근거로 삼는다.
- 결과:
  - `20260514_190155_stage_b_insertion_128env_500iter` 초기 학습을 완료했다.
  - best checkpoint는 `model_800.pt`.
  - `mean_touch_error=0.05733250454068184`로 이전 touch-depth selected checkpoint의 `0.09006259590387344`보다 좋아졌다.
  - `mean_target_contact_penalty=0.0`이라 안전 벌점은 유지되었다.
  - 하지만 `stage3_touch_ready_rate=0.000244140625`, `success_rate=0.000244140625`로 안정적인 성공에는 아직 도달하지 못했다.
- 해석:
  - Stage-B reward profile은 거리와 touch-depth를 줄이는 데는 효과가 있었다.
  - 그러나 실제로 마지막 gate를 안정적으로 통과하려면, Stage-B를 단순 resume이 아니라 pregrasp 근처 상태에서 시작하는 curriculum으로 설계해야 한다.
