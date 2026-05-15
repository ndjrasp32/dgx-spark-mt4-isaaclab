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

## 2026-05-14 curriculum reset 설계

- 선생님 의견:
  - 방법은 좋아 보이지만 구현과 설명이 어려워질 수 있다.
  - 일단 성공을 목표로 하되, 왜 이 방법을 쓰는지 학생들이 이해할 수 있게 구체적인 설명이 필요하다.
- Codex 제안:
  - Policy A가 좋은 pregrasp 상태에 도달한 순간을 `.pt` 파일로 수집한다.
  - Stage-B reset에서 일정 비율의 환경을 그 pregrasp 상태로 시작시킨다.
  - 관절과 target에 작은 noise를 넣어 외우기가 아니라 근처 상황 적응을 학습시킨다.
- 적용:
  - `tools/collect_mt4_pregrasp_states.py` 추가
  - `scripts/collect_pregrasp_states.sh` 추가
  - `MT4_REACH_RESET_MODE=pregrasp_replay` 추가
  - `scripts/train_stage_b_replay_reset_128_500.sh` 추가
  - `notes/mt4_reach_curriculum_reset_plan.md` 추가
- 평가 계획:
  - 먼저 `collect_pregrasp_states.sh`로 최소 512개 pregrasp 상태를 수집한다.
  - 이후 replay reset Stage-B를 128 env / 500 iter로 학습한다.
  - 이전 Stage-B와 비교해 `stage3_touch_ready_rate`, `success_rate`, `mean_touch_error`, `mean_target_contact_penalty`를 본다.
- 결과:
  - 512개 pregrasp 상태를 수집했다.
  - 수집 상태 평균은 `pregrasp_distance=0.078574`, `insertion_alignment=0.940773`, `touch_error=0.044674`.
  - replay reset Stage-B 학습을 실행했고, selector는 `model_800.pt`를 선택했다.
  - 선택 checkpoint의 `success_rate=0.01123046875`, `stage3_touch_ready_rate=0.014404296875`, `mean_target_contact_penalty=0.0`.
  - 후반 `model_1299.pt`는 `mean_touch_error=0.040830716490745544`까지 낮아졌지만 성공률은 `0.0009765625`였다.
- 해석:
  - 좋은 pregrasp 시작 상태를 제공하면 성공 가능성이 즉시 커진다.
  - 하지만 학습이 진행되면서 안정 성공으로 수렴하지는 않았다.
  - 다음에는 replay 비율을 줄이고, checkpoint 선택 기준을 success와 touch precision으로 분리해야 한다.

## 2026-05-14 pregrasp marker radial alignment 수정

- 선생님 관찰:
  - 파란 구체 위치가 조금 틀어져 보이면 집게가 빨간 구체 안으로 정확히 들어가지 못한다.
  - 파란 구체는 로봇팔 베이스 가운데 축 기준으로 빨간 구체와 일직선상에 있어야 한다.
  - 집게 끄트머리가 파란 구체에 정확히 닿고 잠깐 멈춘 뒤, 다음 행동으로 빨간 구체를 집게 영역 안에 넣어야 한다.
- Codex 제안:
  - 파란 pregrasp marker를 `target - horizontal_offset * radial_dir + vertical_offset * up_dir`로 명시 계산한다.
  - 이렇게 하면 파란 구체의 XY 위치가 항상 베이스 중심에서 빨간 구체로 향하는 선 위에 놓인다.
  - `mean_pregrasp_line_error`를 로그로 추가해 marker가 radial line에서 벗어나는지 확인한다.
  - `pregrasp_hold_ready_rate`와 hold reward를 추가해, 파란 구체를 스치고 지나가는 것이 아니라 집게 끝이 닿고 멈춘 상태를 보상한다.
  - `pregrasp_held_rate`를 추가해 episode 중 한 번이라도 안정 대기 조건을 만족했는지 따로 기록한다.
  - 빨간 구체 진입 보상은 `pregrasp_held`가 켜진 뒤에 본격적으로 열리도록 하여, "닿고 멈춘 뒤 진입" 순서를 더 분명하게 만든다.
- 적용:
  - `pregrasp_horizontal_offset=0.075`, `pregrasp_vertical_offset=0.075`
  - `pregrasp_hold_radius=0.050`
  - `pregrasp_hold_ready_rate`, `pregrasp_held_rate`, `mean_pregrasp_line_error` 기록 추가
  - checkpoint summary/record/select 도구에 새 지표 반영
- 주의:
  - pregrasp geometry가 바뀌었으므로 이전 replay state 파일은 새 marker 위치와 완전히 맞지 않을 수 있다.
  - 다음 curriculum reset 실험 전에 `collect_pregrasp_states.sh`로 replay 상태를 다시 수집하는 것이 좋다.
- 검증:
  - 2 env / 1 iteration headless smoke 학습으로 환경 생성과 reward log 출력을 확인했다.
  - smoke log에서 `mt4/mean_pregrasp_line_error=0.0000`으로 파란 marker가 의도한 radial line 위에 놓이는 것을 확인했다.
  - smoke run은 plot/select가 최신 run으로 오해하지 않도록 삭제했다.

## 2026-05-15 timestamp 파일 정리 규칙

- 선생님 의견:
  - GitHub에서 notes, logs, graphs가 쌓이면 어떤 것이 최신인지 구분하기 어렵다.
  - 파일 이름 앞에 날짜와 시간을 넣으면 문제 해결 순서와 실험 흐름을 더 쉽게 추적할 수 있다.
- Codex 제안:
  - `logs/plots/mt4_*.png`와 `best_checkpoint.txt`는 빠른 확인용 latest로 유지한다.
  - 대신 `plot_and_select_best.sh`가 끝날 때마다 `logs/plots/YYYYMMDD_HHMMSS_label/` snapshot 디렉터리를 자동 생성한다.
  - `record_experiment_result.sh`는 누적 CSV index를 유지하면서 `experiments/YYYYMMDD_HHMMSS_label.md`와 one-row metrics CSV를 같이 만든다.
  - 새 note는 `notes/YYYYMMDD_HHMMSS_topic.md` 형식으로 만든다.
- 적용:
  - `notes/20260515_105638_file_naming_workflow.md` 추가
  - `scripts/plot_and_select_best.sh`에 timestamp snapshot 생성 추가
  - `tools/record_mt4_experiment.py`에 timestamp report/metrics CSV 생성 추가
  - `scripts/verify_before_push.sh`는 smoke 검증 때 snapshot이 불필요하게 늘지 않도록 `MT4_SKIP_PLOT_SNAPSHOT=1`을 사용한다.
- 다음 학습 제안:
  - 새 radial pregrasp marker 기준으로 바로 긴 학습을 돌리기보다, 먼저 16 env / 300 iter 시각 학습을 실행한다.
  - `mean_pregrasp_line_error`, `pregrasp_hold_ready_rate`, `pregrasp_held_rate`, `mean_target_contact_penalty`를 기준으로 geometry와 보상 흐름을 평가한다.

## 2026-05-15 stage renumber와 insertion progress 강화

- 선생님 의견:
  - `mean_pregrasp_line_error=0`이므로 marker 위치보다는 마지막 진입이 병목으로 보인다.
  - 정렬한 각도 그대로 파란 구체 위치까지는 가는데, 빨간 구체 방향으로 들어가지 않는 상태 같다.
  - stage 2와 stage 3은 보이지만 stage 1이 없어, 단계 설명과 그래프 이름을 다시 맞추는 편이 좋다.
- Codex 제안:
  - stage를 수업 동작 순서대로 다시 정의한다.
  - Stage 1은 삽입 방향 정렬, Stage 2는 파란 pregrasp marker 대기, Stage 3은 실제 진입으로 둔다.
  - stage 3 보상은 단순히 삽입선 위에 있는 것보다 `insertion_progress`를 만들어 앞으로 들어가는 행동에 더 큰 점수를 주도록 조정한다.
- 적용:
  - `mt4/stage1_alignment_ready_rate` 추가
  - `mt4/stage2_pregrasp_ready_rate` 추가
  - 기존 `mt4/stage2_alignment_ready_rate`는 이전 그래프/도구 호환용으로 유지
  - `stage3_insertion_ready_rate`는 `pregrasp_held` 이후 `insertion_progress > 0.15`가 되어야 켜짐
  - 최종 success는 `insertion_progress > 0.65`까지 들어가야 인정
  - stage 3 line reward는 progress와 연결하고, 천천히 들어가는 동작을 위해 progress 상태의 낮은 관절 속도 보상을 추가
- 다음 실행:
  - `notes/20260515_113646_stage_renumber_insertion_plan.md`의 16 env / 300 iter 시각 학습부터 진행한다.
- 1차 시각 학습 중간 평가:
  - 약 120 iteration까지 확인한 결과 `stage1_alignment_ready_rate`는 높게 올라갔지만 `stage2_pregrasp_ready_rate`는 계속 0이었다.
  - 정책이 파란 marker에 가지 않고도 alignment reward를 누적하는 것으로 판단해 run을 중단했다.
  - stage 1 보상은 낮추고, stage 2 pregrasp 접근/hold 보상과 반경을 강화/완화했다.
- 추가 보정:
  - 선생님은 진입 전에 집게 끝 사이 가운데 지점이 파란 marker 중앙과 맞아야 한다고 제안했다.
  - USD의 gripper pad 위치를 기준으로 `gripper_center_offset_b=(0.158, 0.0, 0.0)`를 추가했다.
  - 기존 `gripper_tip_pos`는 도구 호환을 위해 이름은 유지하지만, 실제로는 gripper center point로 사용한다.
  - `mean_gripper_center_pregrasp_distance`를 기록해 이 기준점이 파란 marker에 접근하는지 확인한다.
- 2차 시각 학습 결과:
  - 16 env / 300 iter, seed 42로 실행했다.
  - best checkpoint는 `model_299.pt`였다.
  - `stage1_alignment_ready_rate=0.98828125`, `pregrasp_success_rate=0.712890625`, `stage2_pregrasp_ready_rate=0.31640625`.
  - `mean_gripper_center_pregrasp_distance=0.10828651487827301`로 집게 중앙 기준 pregrasp 접근은 개선되었다.
  - `stage3_insertion_ready_rate=0.01171875`, `stage3_touch_ready_rate=0.0`, `success_rate=0.0`이라 최종 진입은 아직 병목이다.
  - `mean_target_contact_penalty=0.0`이므로 현재는 충돌 회피보다 "정렬을 유지한 진입"을 더 많이 학습시키는 것이 우선이다.
- 다음 Codex 제안:
  - stage 3 전용 curriculum을 도입한다.
  - pregrasp 근처에서 시작하는 replay/reset을 사용해 마지막 진입 동작 표본을 늘린다.
  - stage 3에서는 `insertion_progress` 보상을 강화하고 `insertion_lateral_error` 벌점을 키운다.
  - 학생 설명에서는 이 실험을 "성공률 하나만 보지 말고 단계별 지표로 병목을 찾는 과정"으로 사용한다.

## 2026-05-15 pregrasp entry와 stage 3 curriculum

- 선생님 의견:
  - 파란 구체 중앙 정렬이 생각보다 너무 앞쪽에서 진행된다.
  - 파란 구체의 로봇팔 쪽 표면점에서 파란 구체 중앙으로 들어간 뒤, 그 방향 그대로 빨간 구체 쪽으로 진입하는 흐름이 더 자연스럽다.
  - 마지막 진입은 stage 3 전용 curriculum으로 따로 많이 경험시키자.
- Codex 제안:
  - 파란 marker 중앙은 유지하고, 보상 계산용 `pregrasp_entry_targets`를 추가한다.
  - stage 2를 entry 접근과 center hold로 나눈다.
  - `pregrasp_entry_success_rate`, `pregrasp_entry_ready_rate`, `pregrasp_entry_reached_rate`, `mean_pregrasp_entry_distance`, `mean_pregrasp_center_progress`를 기록한다.
  - 기존 task 이름과 observation/action 크기는 유지한다.
- 적용:
  - `pregrasp_entry_offset=0.030`
  - entry 접근 보상과 entry 이후 center progress 보상 추가
  - center hold는 entry를 한 번 지나간 뒤에만 인정
  - plot/select/record 도구에 새 지표 추가
- 다음 실행:
  - `collect_pregrasp_states.sh`로 새 geometry 기준 replay state를 다시 수집한다.
  - `train_stage_b_replay_reset_128_500.sh --seed 42`로 stage 3 replay-reset curriculum을 실행한다.
- 실행 결과:
  - 새 geometry 기준 replay state 512개를 수집했다.
  - 수집 상태 평균은 `mean_dist=0.081110`, `mean_align=0.974888`, `mean_line=0.000000`이었다.
  - 첫 replay-reset run은 `model_350.pt`까지만 저장되어 중단되었고, `model_350.pt`에서 이어받아 재개했다.
  - 재개 run의 best checkpoint는 `model_600.pt`였다.
  - `pregrasp_entry_reached_rate=0.933837890625`, `stage2_pregrasp_ready_rate=0.927490234375`, `stage3_insertion_ready_rate=0.8701171875`.
  - `stage3_touch_ready_rate=0.0`, `success_rate=0.0`이므로 진입 시작은 해결됐지만 마지막 깊이/정밀 접촉이 다음 병목이다.
- 다음 Codex 제안:
  - stage 3 touch-depth curriculum으로 마지막 5cm 구간을 따로 강화한다.
  - action std가 후반에 커지는 현상이 있어 action penalty 또는 entropy 관련 설정을 조정한다.
  - 다음 실험 목표는 최종 성공률보다 먼저 `stage3_touch_ready_rate`를 0.05 이상으로 올리는 것이다.

## 2026-05-15 final center capture curriculum

- 선생님 의견:
  - 파란 구체 중앙까지 도착하면 마지막 단계가 trigger되어야 한다.
  - 빨간 구체 중앙 방향으로 가까워질수록 보상을 주되, 이미 보상받은 거리에서는 같은 보상을 반복하지 않아 빙빙 도는 행동을 줄이고 싶다.
  - 최종 목표는 집게를 닫기 전 빨간 구체 중심이 집게 가운데에 정확히 들어와 있는 상태다.
  - 로봇팔 몸체가 빨간 구체와 부딪히는 것은 계속 피해야 한다.
- Codex 제안:
  - episode별 `best_target_center_distance`를 저장한다.
  - stage 3 이후 집게 중앙이 빨간 중심에 새롭게 더 가까워진 경우에만 `target_center_improvement` 보상을 준다.
  - 집게 링크는 목표 중심을 포함할 수 있게 허용하고, 다른 링크의 목표 접근은 충돌 벌점으로 유지한다.
  - 최종 성공은 `final_center_success_radius` 안에 들어온 경우로 판단하고, 성공 시 시간 벌점을 제거한다.
- 적용:
  - `final_center_success_radius=0.025`
  - `stage4_center_ready_rate` 추가
  - `mean_best_target_center_distance`, `mean_target_center_improvement` 추가
  - stage 4 center improvement/precision reward 추가
  - plot/select/record 도구에 stage 4 지표 추가
- 실행 방식:
  - 이번 실험은 영상으로 학습 장면을 보면서 진행한다.
  - 터미널 iteration별 score를 그대로 확인하고, 대화에서는 단계별 지표 해설을 병행한다.
- 실행 결과:
  - Isaac Sim GUI에서 16 env 병렬 학습을 실행했다.
  - run은 `2026-05-15_12-18-28`, best checkpoint는 `model_750.pt`였다.
  - `stage1_alignment_ready_rate=0.98828125`, `pregrasp_entry_reached_rate=0.986328125`, `stage2_pregrasp_ready_rate=0.96875`.
  - `stage3_insertion_ready_rate=0.923828125`, `stage3_touch_ready_rate=0.90234375`까지 올라가 진입 단계는 크게 개선되었다.
  - 새 마지막 지표인 `stage4_center_ready_rate=0.001953125`, `success_rate=0.001953125`가 처음 발생했다.
  - `mean_target_contact_penalty=0.0`이라 충돌 회피는 유지되고 있다.
- 평가:
  - 현재 병목은 정렬/접근이 아니라 빨간 구체 중심을 집게 중앙에 넣는 마지막 정밀 단계다.
  - 다음에는 stage 4 전용 replay reset 또는 완화된 center radius로 성공 샘플을 더 자주 만든 뒤, 다시 기준을 엄격하게 줄이는 방식이 좋다.

## 2026-05-15 stage 4 center replay와 target 크기 조정

- 선생님 의견:
  - 빨간 구체는 최종적으로 집게가 집을 대상이다.
  - 잡기 전에 집게나 팔이 빨간 구체를 쳐버리면 실제 물체는 움직여 버린다.
  - 따라서 빨간 구체를 조금 작게 표현해, 진입 전 충돌처럼 보이는 상황을 줄이는 편이 좋다.
- Codex 제안:
  - 빨간 target marker와 task의 `target_radius`를 `0.035m`에서 `0.025m`로 줄인다.
  - stage3 touch 기준인 `desired_touch_distance`도 `0.040m`에서 `0.030m`로 줄여 작은 물체 표면 근처를 목표로 한다.
  - stage4 전용 replay state 수집 스크립트와 stage4 center 학습 스크립트를 추가한다.
  - 집게 링크가 빨간 구체 중심을 포함하는 것은 최종 grasp-ready pose로 허용하고, 집게가 아닌 몸체 link의 접근은 `target_contact_penalty`로 계속 벌점 처리한다.
- 적용:
  - `scripts/collect_stage4_center_states.sh` 추가
  - `scripts/train_stage4_center_replay_128_300.sh` 추가
  - `MT4_REACH_TRAINING_MODE=stage4_center` 추가
  - `target_radius=0.025`, `desired_touch_distance=0.030` 적용
- 실행 결과:
  - `data/stage4_center_states/latest.pt`에 512개 stage4 replay state를 수집했다.
  - 수집 상태 평균은 `mean_center_dist=0.054908`, `mean_progress=0.758300`, `mean_touch=0.024908`이었다.
  - stage4 replay 학습 run은 `2026-05-15_12-31-14`이고, best checkpoint는 `model_900.pt`였다.
  - `stage3_touch_ready_rate=0.9169921875`로 빨간 구체 근처 진입은 더 강해졌다.
  - `stage4_center_ready_rate=0.000244140625`, `success_rate=0.000244140625`로 마지막 중심 정렬은 아직 드물다.
  - `mean_target_contact_penalty=0.0`이라 집게 외 몸체 충돌 회피는 유지되었다.
- 평가:
  - 빨간 구체를 작게 만든 것은 안전/시각 해석에는 도움이 된다.
  - 하지만 작은 목표일수록 마지막 중심 정렬 난이도는 올라간다.
  - 후반 action std가 커져 마지막 중심을 지나치는 경향이 있으므로, 다음에는 stage4에서 exploration을 줄이는 설정이 필요하다.

## 2026-05-15 stage 4 center-push reward

- 선생님 의견:
  - 마지막 중심 근처에 중심점이 잘 잡힌 상태라면, 거기서 멈추거나 맴돌지 말고 빨간 구체 중심 쪽으로 밀어 넣는 방향이 좋다.
  - 최종적으로 집게를 움직여 잡기 전, 빨간 구체 중심이 집게 가운데에 정확히 들어와 있어야 한다.
- Codex 제안:
  - 마지막 단계에 `center_push_progress`를 추가해, pregrasp 지점에서 빨간 구체 중심 방향으로 들어가는 진행률을 측정한다.
  - 이 보상은 insertion alignment와 lateral error 조건을 함께 만족할 때만 크게 주어, 아무 방향으로 밀어 넣는 행동을 막는다.
  - 처음에는 `touch_targets -> targets` 진행률을 쓰려 했지만 보상이 너무 늦게 열려 거의 0으로 나왔다.
  - 그래서 `pregrasp_targets -> targets` 전체 경로 기준 진행률로 바꾸었다.
- 적용:
  - `stage4_center_push_weight` 추가
  - `stage4_push_ready_rate` 추가
  - `mean_center_push_progress` 추가
  - `scripts/train_stage4_center_push_replay_128_250.sh` 추가
  - plot/select/record 도구에 center-push 지표 추가
- 실행 결과:
  - run은 `2026-05-15_12-55-21`, best checkpoint는 `model_950.pt`였다.
  - `stage3_touch_ready_rate=0.828857421875`
  - `stage4_push_ready_rate=0.729736328125`
  - `mean_center_push_progress=0.5227710008621216`
  - `stage4_center_ready_rate=0.0`, `success_rate=0.0`
  - `mean_target_contact_penalty=0.0`으로 충돌 벌점은 발생하지 않았다.
- 평가:
  - 중심으로 밀어 넣는 중간 지표는 의미 있게 생겼다.
  - 그러나 최종 중심 성공은 아직 나오지 않았다.
  - 보상이 강해지면서 후반에는 touch/alignment가 일부 흔들렸으므로, 다음에는 push 보상과 자세 유지 보상을 더 강하게 결합하거나 stage4 replay state를 더 정밀한 위치에서 다시 수집하는 것이 좋다.

## 2026-05-15 stronger stage 4 push

- 선생님 의견:
  - 마지막 단계만 잘 잡으면 1차적으로는 충분히 의미 있다.
  - 중심 근처에서 빨간 구체 쪽으로 더 확실히 밀어 넣는 행동이 필요하다.
- Codex 제안:
  - 단순히 push weight만 키우면 자세가 흔들릴 수 있다.
  - 그래서 episode 중 이전보다 더 안쪽으로 들어갔을 때만 보상하는 `center_push_improvement`를 추가한다.
  - replay reset에서는 시작 progress를 기준점으로 저장하고, 그 이후 더 들어간 만큼만 improvement로 본다.
  - `center_push_progress > 0.5` 이후 구간에는 depth reward를 추가해 마지막 절반 구간을 더 강하게 학습시킨다.
- 적용:
  - `mean_best_center_push_progress` 추가
  - `mean_center_push_improvement` 추가
  - `stage4_center_push_improvement_weight`, `stage4_center_push_depth_weight` 추가
  - `scripts/train_stage4_push_strong_replay_128_300.sh` 추가
- 평가 예정:
  - 다음 학습에서는 `stage4_push_ready_rate`보다 `mean_best_center_push_progress`와 `stage4_center_ready_rate`를 함께 본다.
  - push 기준은 0.65로 높였기 때문에 push-ready rate가 낮아져도, 실제 중심 진입이 늘면 개선으로 본다.
- 실행 결과:
  - run은 `2026-05-15_13-03-24`, best checkpoint는 `model_1249.pt`였다.
  - `mean_center_push_progress=0.6130448579788208`
  - `mean_best_center_push_progress=0.6594560146331787`
  - `stage4_push_ready_rate=0.264892578125`
  - `stage4_center_ready_rate=0.000244140625`, `success_rate=0.000244140625`
  - `mean_target_contact_penalty=0.0`
- 평가:
  - 이전보다 빨간 구체 중심 방향으로 더 깊이 들어가는 행동은 강화되었다.
  - 하지만 마지막 성공률은 여전히 매우 낮다.
  - 이제 병목은 push 자체보다, push 중 lateral error와 중심 거리 정밀도를 동시에 유지하는 것이다.

## 2026-05-15 stage 4 shortest-path reward idea

- 선생님 의견:
  - 마지막 stage 보상을 다변화한다.
  - 최단거리 방향으로 빨간 구체 중심에 가까워지는 경우에는 보상을 크게 준다.
  - 돌아가며 가까워지는 경우에는 보상을 작게 준다.
  - 동일한 거리권의 보상은 한 번 달성하면 사라지게 해서, 같은 거리에서 맴도는 행동을 줄인다.
- Codex 제안:
  - 기존 `best_target_center_distance`는 이미 "이전보다 더 가까워질 때만 보상"하는 역할을 한다.
  - 여기에 `center_shortest_path_score`를 곱해, insertion line과 gripper alignment를 지키는 접근일수록 보상을 크게 만든다.
  - 빨간 구체 중심으로부터의 거리를 5mm shell로 나누고, 더 안쪽 shell로 들어갈 때만 `target_center_shell_improvement`를 준다.
- 적용:
  - `stage4_shortest_path_weight` 추가
  - `stage4_distance_shell_weight` 추가
  - `center_distance_shell_size` 추가
  - `mean_target_center_shell_improvement` 추가
  - `mean_center_shortest_path_score` 추가
- 평가 예정:
  - 다음 학습에서는 `mean_center_shortest_path_score`, `mean_target_center_shell_improvement`, `stage4_center_ready_rate`를 함께 본다.
  - 성공률이 바로 오르지 않더라도, 같은 거리권에서 맴도는 행동이 줄고 더 안쪽 shell로 들어가는 빈도가 늘면 개선으로 본다.
- 실행 결과:
  - run은 `2026-05-15_13-31-34`, best checkpoint는 `model_1548.pt`였다.
  - `stage3_touch_ready_rate=0.820556640625`
  - `stage4_center_ready_rate=0.000244140625`, `success_rate=0.000244140625`
  - `stage4_push_ready_rate=0.133544921875`
  - `mean_center_push_progress=0.5709028840065002`
  - `mean_target_center_shell_improvement=0.011962890625`
  - `mean_center_shortest_path_score=0.6540575623512268`
  - `mean_target_contact_penalty=0.0`
- 평가:
  - 최단거리/shell 보상은 실제 로그에 잡혔다.
  - 정책은 무조건 깊게 밀기보다 경로와 정렬을 더 유지하는 방향으로 바뀌었다.
  - 단점은 push-ready와 push progress가 이전 strong-push보다 낮아졌다는 점이다.
  - 다음은 shortest-path 구조를 유지하되 마지막 push depth를 다시 조금 올리는 혼합형이 좋다.

## 2026-05-15 stage 4 time pressure and slight exploration

- 선생님 의견:
  - 최종 성공 직전까지 시간 벌점을 줘야 한다.
  - stage4에 들어오면 빨간 구체를 잡을 수 있는 위치까지 최단거리로 들어가야 한다.
  - 성공 지점에 도착하면 시간 벌점을 제거하고, 추가 보상/벌점을 더하지 않고 종료하는 것이 맞다.
  - 탐색 비율은 아주 살짝 올려 조심스러움이 너무 강해지지 않게 한다.
  - GUI로 직접 확인한다.
- Codex 제안:
  - `stage3_ready` 이후를 stage4 진입으로 보고 `stage4_time_pressure`를 추가한다.
  - success step에서는 shaped reward를 더하지 않고 terminal `success_bonus`만 반환한다.
  - 탐색은 `entropy_coef=0.0025`, `init_noise_std=0.40`, `action_scale=0.026` 정도로 조금만 올린다.
  - 같은 보상 설정으로 GUI 16 env와 headless 128 env를 비교한다.
- 적용:
  - `stage4_time_penalty_weight` 추가
  - `mean_stage4_time_pressure` 추가
  - `scripts/train_stage4_time_pressure_visual_16_120.sh` 추가
- 실행 결과:
  - GUI 확인 run은 `2026-05-15_13-40-54`였다.
  - 128 env 학습 run은 `2026-05-15_13-43-44`였다.
  - best checkpoint는 `model_1600.pt`였다.
  - `success_rate=0.00048828125`
  - `stage3_touch_ready_rate=0.7861328125`
  - `stage4_push_ready_rate=0.19921875`
  - `mean_center_push_progress=0.6045380234718323`
  - `mean_best_center_push_progress=0.668278157711029`
  - `mean_center_shortest_path_score=0.673416256904602`
  - `mean_stage4_time_pressure=0.4132959246635437`
  - `mean_target_contact_penalty=0.0`
- 평가:
  - 시간 벌점은 stage4 이후 오래 머무르는 행동을 구분하는 지표로 정상 동작했다.
  - 탐색을 아주 조금 올린 결과, shortest-path-only 실험보다 `stage4_push_ready_rate`가 회복되었다.
  - 그러나 최종 성공률은 아직 낮다.
  - 현재 문제는 파란 지점 접근보다 빨간 구체 중심을 집게 중앙에 넣는 마지막 정밀 진입이다.
  - 다음 제안은 성공 직전 상태를 더 많이 replay하거나, terminal 성공 반경/집게 중심 정의를 재검토하는 것이다.

## 2026-05-15 stage 4 low-exploration visual run plan

- 선생님 의견:
  - `stage4_center_ready_rate`가 빨간 구체가 집게 가운데 들어온 상태라면 지금 목표에서는 성공으로 봐야 한다.
  - 성공하는 시점의 정책을 더 따라가되, 더 나은 선택 가능성도 남기기 위해 탐색을 너무 낮추지는 않는다.
  - GUI로 보면서 확인하고, 가능하면 낮은 해상도 학습 영상을 GitHub에 함께 남긴다.
- Codex 제안:
  - checkpoint에 저장된 policy std가 바로 덮어쓰이므로 `init_noise_std`만 낮추는 것은 효과가 제한적이다.
  - 대신 stage4에서 `action_scale=0.030`으로 실제 관절 목표 변화량을 줄이고, `action_penalty=0.018`로 과한 움직임을 더 억제한다.
  - PPO entropy는 `0.003`으로 낮춰 후속 학습에서 탐색이 더 커지는 것을 줄인다.
  - IsaacLab train.py의 `--video` 기능으로 학습 영상을 만들고, `ffmpeg`로 640px 폭의 저해상도 mp4를 `logs/videos/`에 복사한다.
- 적용:
  - `scripts/train_stage4_center_visual_low_exploration_16_120.sh` 추가
  - `scripts/copy_latest_training_video_lowres.sh` 추가
  - `MT4_REACH_ACTION_SCALE`, `MT4_REACH_ACTION_PENALTY` 환경변수 지원 추가
- 영상 확인:
  - IsaacLab train.py의 `--video` 옵션으로 mp4 생성이 가능함을 확인했다.
  - `--video_interval=1`은 매 step마다 영상을 만들어 GUI 학습이 지나치게 느려지므로, 기본값을 `100000`으로 바꿔 첫 구간만 녹화하도록 조정했다.
  - 짧은 확인 영상은 `logs/videos/20260515_124112_stage4_center_low_exploration_videos.mp4`에 저장했다.
  - 중단된 확인용 run은 plot/select가 최신 run으로 오해하지 않도록 IsaacLab logs에서 삭제했다.

## 2026-05-15 relaxed success curriculum

- 선생님 의견:
  - 최종 성공 기준을 약간 완화해서 일단 성공률을 만들고, 그 다음 조건을 엄격화하는 방향이 좋다.
- Codex 제안:
  - 현재 strict 실험은 `final_center_success_radius=0.035m`라 성공 신호가 너무 드물다.
  - 이전 best의 `mean_distance`가 약 `0.052m`였으므로, 먼저 `0.055m`로 완화해 성공 신호를 만든다.
  - 이후 `0.045m`, `0.040m`, `0.035m` 순서로 줄인다.
- 적용:
  - `scripts/train_stage4_relaxed_success_128_300.sh` 추가
  - 기본 `MT4_REACH_FINAL_CENTER_RADIUS=0.055`
  - 기존 strict/time-pressure 스크립트는 유지
- 실행 결과:
  - run은 `2026-05-15_13-49-56`, best checkpoint는 `model_1600.pt`였다.
  - `success_rate=0.028564453125`
  - `stage4_center_ready_rate=0.041259765625`
  - `stage3_touch_ready_rate=0.13330078125`
  - `stage2_pregrasp_ready_rate=0.135009765625`
  - `mean_center_push_progress=0.5714872479438782`
  - `mean_center_shortest_path_score=0.6061863899230957`
  - `mean_target_contact_penalty=0.0`
- 평가:
  - 성공률을 만드는 데는 성공했다.
  - 다만 완화 조건을 너무 쉽게 이용하면서 stage2/stage3 품질이 낮은 checkpoint가 선택되었다.
  - 다음 실험은 `0.045m`로 줄이되, 성공률만 보지 않고 `stage3_touch_ready_rate`와 함께 선택해야 한다.

## 2026-05-15 relaxed 0.045 curriculum result

- 선생님 의견:
  - 최종 성공률은 아직 낮다.
  - 뒷 단계 보상 조건이 앞 단계 행동에 영향을 준다면, 앞 단계와 뒷 단계의 가중치를 다르게 둘 수 있다.
  - 시간 소모에 따른 가중치도 단계별로 다르게 줄 수 있다.
- Codex 제안:
  - 먼저 `0.045m` 성공 반경을 실험한다.
  - `0.055m`에서 생긴 성공 신호를 완전히 잃지 않으면서 stage3 품질이 회복되는지 확인한다.
  - 가중치 조정은 이번 결과를 본 뒤 다음 후보로 분리한다.
- 실행 결과:
  - run은 `2026-05-15_13-55-22`, best checkpoint는 `model_1600.pt`였다.
  - `success_rate=0.014404296875`
  - `stage4_center_ready_rate=0.014404296875`
  - `stage4_push_ready_rate=0.05615234375`
  - `stage3_touch_ready_rate=0.366943359375`
  - `stage2_pregrasp_ready_rate=0.377685546875`
  - `mean_center_push_progress=0.5669831037521362`
  - `mean_center_shortest_path_score=0.6251078248023987`
  - `mean_target_contact_penalty=0.0`
- 평가:
  - `0.055m`보다 성공률은 낮아졌지만 stage3 품질은 좋아졌다.
  - `0.055m`: 성공률은 높지만 stage3가 약하다.
  - `0.045m`: 성공률은 남아 있고 stage3 품질도 더 낫다.
  - 다음에는 stage3 보상과 stage4 보상/시간 벌점을 단계별로 분리하는 실험이 타당하다.

## 2026-05-15 stage weighted balance experiment

- 선생님 의견:
  - 뒤쪽 결과가 앞쪽 결과에 영향을 미치면 전체 틀이 흐트러질 수 있다.
  - 앞쪽 결과는 유지하고 시간이 흐르면 가중치를 조금 더 주는 방식을 고려한다.
  - 너무 크면 최종 성공을 피하고 시간을 끌 수 있으니 주의한다.
  - 최종 성공 보상은 조금 키우되, 최단거리 루트 자체를 망치지 않아야 한다.
  - 최종 성공했을 때만 마지막 stage 품질 가중치를 주는 방법도 가능하다.
- Codex 제안:
  - `stage3_time_preserve`를 작게 추가해 stage3 정렬/접촉 품질을 시간이 지나도 유지하게 한다.
  - `stage4_time_penalty`도 함께 올려 시간을 끄는 행동은 손해가 되게 한다.
  - 성공 step에서는 terminal success bonus와 `terminal_success_quality`만 준다.
  - terminal quality는 성공했을 때만 적용해 실패 step의 stage4 보상이 앞 단계를 과하게 흔들지 않게 한다.
- 적용:
  - `stage3_time_preserve_weight` 추가
  - `terminal_success_quality_weight` 추가
  - `MT4_REACH_SUCCESS_BONUS` 환경변수 추가
  - `mean_stage3_time_preserve`, `mean_terminal_success_quality` 지표 추가
  - `scripts/train_stage4_weighted_balance_128_300.sh` 추가
- 실행 결과:
  - run은 `2026-05-15_14-08-19`, best checkpoint는 `model_1600.pt`였다.
  - `success_rate=0.01318359375`
  - `stage4_center_ready_rate=0.01318359375`
  - `stage4_push_ready_rate=0.05078125`
  - `stage3_touch_ready_rate=0.37158203125`
  - `stage2_pregrasp_ready_rate=0.38134765625`
  - `mean_stage3_time_preserve=0.07407005876302719`
  - `mean_terminal_success_quality=0.0`
- 평가:
  - 이전 `0.045m` 실험과 비교해 성공률은 거의 유지되고 stage3 touch는 소폭 개선되었다.
  - 학습 후반 stage3는 더 안정되었지만 final success는 다시 낮아졌다.
  - 따라서 앞 단계 보존 가중치는 방향이 맞지만, 마지막 중심 진입을 직접 강화하는 보상이 더 필요하다.

## 2026-05-15 near-terminal reward experiment

- 선생님 의견:
  - 최종 성공 직전까지는 시간 벌점을 유지하고, 성공하면 추가 보상/벌점을 멈추는 방식이 좋다.
  - 마지막 단계에서는 빨간 구체 중심으로 최단거리 진입을 유도하되, 앞 단계 결과가 흐트러지면 안 된다.
  - 탐색 비율은 너무 낮추지 말고 아주 조금 올려 더 나은 체크포인트를 찾게 한다.
  - 보상과 벌점 항목이 너무 많아지면 상충될 수 있다는 우려가 있다.
- Codex 제안:
  - 새 보상을 많이 추가하지 않고 `near_terminal_reward` 하나만 추가한다.
  - 성공 반경은 `0.045m`로 유지하고, 그 바깥 `0.050m` 안쪽에 들어온 상태만 작은 bridge reward로 보상한다.
  - 이 보상은 stage3가 준비되어 있고, 빨간 구체와 충돌하지 않으며, 최단거리 방향과 push progress가 모두 괜찮을 때만 커진다.
  - `stage3_time_preserve_weight`는 `1.6 -> 1.2`로 낮춰 마지막 진입을 지나치게 막지 않게 한다.
  - entropy는 `0.0025 -> 0.0030`으로 조금만 올린다.
- 적용:
  - `near_terminal_weight`, `near_terminal_radius` 환경변수 추가
  - `mean_near_terminal_reward` 로그 추가
  - `scripts/train_stage4_near_terminal_128_300.sh` 추가
  - plot/select/experiment record 도구가 새 지표를 읽도록 업데이트
- 평가 기준:
  - `success_rate`가 유지 또는 상승하는가
  - `stage3_touch_ready_rate`가 크게 떨어지지 않는가
  - `mean_near_terminal_reward`가 생기는가
  - `mean_target_contact_penalty`가 0에 가깝게 유지되는가
- 실행 결과:
  - run은 `2026-05-15_14-18-24`, best checkpoint는 `model_1600.pt`였다.
  - `success_rate=0.01416015625`
  - `stage3_touch_ready_rate=0.370849609375`
  - `stage4_center_ready_rate=0.01416015625`
  - `stage4_push_ready_rate=0.037841796875`
  - `mean_near_terminal_reward=0.034814152866601944`
  - `mean_stage3_time_preserve=0.07492419332265854`
  - `mean_stage4_time_pressure=0.13307860493659973`
  - `mean_target_contact_penalty=0.0`
- 평가:
  - near-terminal 지표는 정상적으로 기록되었고, 충돌 벌점은 0으로 유지되었다.
  - 하지만 best checkpoint가 run 시작점인 `model_1600.pt`로 선택되어, 이번 추가 학습 자체가 최종 성공률을 더 끌어올렸다고 보기는 어렵다.
  - 학습 중반에는 stage3 touch가 0.7-0.8까지 올라갔지만 final success는 거의 사라졌다.
  - 다음 구조는 선생님이 제안한 stage latch와 progressive stage weighting이 적절하다.

## 2026-05-15 stage latch + progressive weighting idea

- 선생님 의견:
  - 앞 스테이지를 완수한 시점에서 다음 스테이지에 진입한다.
  - 후반 스테이지 성공에 가까워질수록 해당 스테이지를 확보한 점수에 더 강한 가중치를 부과한다.
- Codex 해석:
  - 이 방식은 reward 항목을 무작정 늘리는 것보다 낫다.
  - 보상을 항상 켜두는 것이 아니라, stage gate를 통과한 뒤에만 후속 보상이 의미를 갖기 때문이다.
  - 현재 `pregrasp_held`처럼 일부 latch는 이미 있으므로, stage1/stage2/stage3 latch를 명확히 분리하고 로그로 볼 수 있게 만드는 것이 다음 개선이다.
- 주의점:
  - stage 유지 보상이 너무 크면 로봇팔이 앞 stage에 머무를 수 있다.
  - progressive weight는 작게 시작하고, success 시에는 기존처럼 terminal reward만 남겨야 한다.
  - 학생 설명에서는 "문제를 순서대로 잠금 해제하는 강화학습"으로 표현하면 이해하기 쉽다.

## 2026-05-15 stage latch + progressive weighting result

- branch:
  - `experiment/stage-latch-progressive-weighting`
- 선생님 의견:
  - 앞 스테이지를 완수하면 다음 스테이지에 진입하고, 후반 스테이지 성공에 가까워질수록 확보한 stage 점수의 가중치를 강하게 준다.
  - 이를 통해 뒤쪽 보상이 앞쪽 행동을 흐트러뜨리지 않도록 한다.
- Codex 제안:
  - stage 조건을 매 순간 다시 계산되는 ready 값과 episode 중 한 번 확보되면 유지되는 latched 값으로 분리한다.
  - `stage_latch_reward`와 `progressive_stage_weight`를 작게 추가하고, 새 metric으로 효과를 관찰한다.
- 실행 결과:
  - run은 `2026-05-15_14-36-12`, best checkpoint는 `model_1600.pt`였다.
  - `success_rate=0.013671875`
  - `stage1_latched_rate=0.941162109375`
  - `stage2_latched_rate=0.37158203125`
  - `stage3_latched_rate=0.37158203125`
  - `stage3_touch_ready_rate=0.3564453125`
  - `stage4_center_ready_rate=0.013671875`
  - `stage4_push_ready_rate=0.044189453125`
  - `mean_stage_latch_reward=0.330735445022583`
  - `mean_progressive_stage_weight=1.0618454217910767`
  - `mean_target_contact_penalty=0.0`
- 평가:
  - latch 지표는 정상적으로 작동했고, 빨간 구체 접촉 벌점도 0으로 유지되었다.
  - 앞 단계 보존에는 도움이 되었지만, 추가 학습 후반의 최종 center 성공률은 오히려 약해졌다.
  - 다음 실험은 latch 보상 자체를 키우기보다, `stage3_latched` 이후에만 작동하는 final insertion 전용 보상을 분리해야 한다.

## 2026-05-15 guided blue final insertion experiment

- 선생님 의견:
  - 파란 구체에 정렬된 상태로 도착하면, 파란 구체 위치를 빨간 구체 방향으로 조금씩 옮긴다.
  - 이 과정을 두세 번 반복하면, 마지막 최종 스테이지는 더 가까운 상태에서 시작할 수 있다.
- Codex 제안:
  - 기존 task를 새로 만들지 않고, 파란 구체를 moving guide로 확장한다.
  - 파란 구체는 빨간 중심까지 들어가지 않고 touch path의 70%까지만 3단계로 이동한다.
  - 파란 guide 단계를 끝낸 뒤에만 final insertion reward를 켠다.
- 적용:
  - `MT4_REACH_MOVING_PREGRASP=1`
  - `MT4_REACH_MOVING_PREGRASP_STEPS=3`
  - `MT4_REACH_MOVING_PREGRASP_FINAL_FRACTION=0.70`
  - `MT4_REACH_FINAL_INSERTION_WEIGHT=48.0`
  - `mean_moving_pregrasp_fraction`, `moving_pregrasp_final_rate`, `mean_final_insertion_reward` 지표 추가
- 실행 결과:
  - run은 `2026-05-15_14-54-32`였다.
  - strict success 기준 best는 `model_1600.pt`였다.
  - 후반 guided-progress 관찰용 checkpoint는 `model_1899.pt`가 더 의미 있다.
  - `model_1899.pt`:
    - `success_rate=0.0009765625`
    - `stage3_latched_rate=0.75146484375`
    - `stage3_touch_ready_rate=0.682373046875`
    - `stage4_push_ready_rate=0.451416015625`
    - `mean_center_push_progress=0.6830252408981323`
    - `moving_pregrasp_final_rate=0.548583984375`
    - `mean_final_insertion_reward=0.04587549716234207`
    - `mean_target_contact_penalty=0.0`
- 평가:
  - 선생님 아이디어는 효과가 있었다. 파란 구체를 따라 빨간 구체 쪽으로 들어가는 비율과 push ready 지표가 크게 올라갔다.
  - 그러나 strict final center success는 아직 낮다.
  - 다음에는 `0.045m` 성공 반경을 아주 약간 완화하거나, strict success와 guided-progress checkpoint 선택 기준을 분리해야 한다.

## 2026-05-15 blue center curriculum experiment

- 선생님 의견:
  - 파란 구체의 최종 위치를 빨간 구체 중심점으로 잡으면, 마지막에 따로 밀어 넣는 동작을 만들지 않아도 된다.
  - 파란 구체로 가야 할 경로를 만들어 주면, 빨간 구체 중심으로 들어가는 것이 곧 최종 성공 경로가 될 수 있다.
- Codex 제안:
  - 기존 guided-blue 구조는 유지하되, 파란 구체의 최종 목표를 `touch`와 `center` 중 고를 수 있게 한다.
  - `center` 모드에서는 `desired_touch_distance=0.0`으로 두어, 파란 목표와 빨간 중심이 같아지도록 한다.
  - 단, gripper center만 red center로 들어가는 것을 허용하고, 다른 로봇팔 링크가 target에 닿으면 계속 벌점을 받도록 둔다.
- 적용:
  - `MT4_REACH_MOVING_PREGRASP_GOAL=center`
  - `MT4_REACH_MOVING_PREGRASP_FINAL_FRACTION=1.0`
  - `MT4_REACH_DESIRED_TOUCH_DISTANCE=0.0`
  - `scripts/train_stage4_blue_center_128_300.sh`
- 실행 결과:
  - run은 `2026-05-15_15-05-58`이었다.
  - best checkpoint는 `model_2000.pt`였다.
  - `success_rate=0.0009765625`
  - `stage4_center_ready_rate=0.0009765625`
  - `stage4_push_ready_rate=0.394287109375`
  - `moving_pregrasp_final_rate=0.842041015625`
  - `mean_moving_pregrasp_fraction=0.84521484375`
  - `mean_distance=0.061940357089042664`
  - `mean_target_contact_penalty=0.0`
- 평가:
  - 파란 구체를 빨간 중심까지 보내는 안내 curriculum은 잘 작동했다.
  - 충돌 벌점은 0으로 유지되어 안전 조건도 깨지지 않았다.
  - 그러나 평균 거리가 `final_center_radius=0.050`보다 바깥인 약 0.062m에 머물러 strict final success는 거의 생기지 않았다.
  - 다음 단계는 최종 성공 반경을 잠시 0.060으로 완화해 성공 사례를 만들고, 이후 성공 반경을 다시 줄이는 terminal-center curriculum으로 가는 것이 좋다.

## 2026-05-15 blue marker step gate adjustment

- 선생님 의견:
  - 파란 구체가 순식간에 사라져서 빨간 구체를 향해 단계적으로 진입하는 느낌이 약하다.
  - 집게 한쪽 다리가 아니라 집게의 딱 중간 지점이 파란 구체 중심과 일치해야 한다.
  - 파란 구체를 더 작게 만들고, 파란 구체를 재생성하면서 빨간 구체 방향으로 유도해야 한다.
- Codex 진단:
  - 코드상 기준점은 이미 집게 중심점이다. `gripper_tip_pos`라는 legacy 변수명만 남아 있고 실제 값은 `gripper_center_pos`다.
  - 다만 기존 `steps=3`, `step_radius=0.060`은 단계 간 거리보다 통과 반경이 커서, 파란 구체가 너무 빨리 다음 단계로 넘어갈 수 있었다.
- 적용:
  - 파란 marker radius를 `0.025 -> 0.016`으로 줄였다.
  - blue-center 기본값을 `steps=5`, `step_radius=0.018`, `hold_steps=8`로 조정했다.
  - 집게 중심점이 현재 파란 구체 중심 근처에 일정 프레임 머물러야 다음 파란 구체로 넘어가도록 `moving_pregrasp_hold_count`를 추가했다.
  - `moving_pregrasp_step_ready_rate`, `mean_moving_pregrasp_hold_progress` 지표를 추가했다.
- 기대:
  - 파란 구체가 사라지는 것이 아니라, 빨간 구체 중심까지 더 촘촘하게 재생성되는 안내점처럼 보일 것이다.
  - 한쪽 finger가 스치는 행동보다 집게 가운데를 맞추는 행동이 더 명확히 요구된다.
