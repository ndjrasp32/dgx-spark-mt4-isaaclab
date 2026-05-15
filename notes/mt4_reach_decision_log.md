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
