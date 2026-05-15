# 20260515_114719 stage_renumber_gripper_center_visual_16env_300iter

## Summary

- timestamp: 2026-05-15T11:53:28
- checkpoint: `model_299.pt`
- checkpoint path: `/home/spark-robotics/work/isaac/src/IsaacLab/logs/rsl_rl/mt4_simplified_reach_direct/2026-05-15_11-47-19/model_299.pt`
- plot snapshot: `/home/spark-robotics/work/robotarm/mt4_isaac_lab_task/logs/plots/20260515_114719_stage_renumber_gripper_center_visual_16env_300iter`
- reward profile: `stage_renumber_gripper_center`
- notes: Stage 2 uses the midpoint between gripper pads as the pregrasp point. Stage1 alignment is high and gripper-center pregrasp distance improved, but final insertion success remains low.

## Metrics

| metric | value |
|---|---:|
| success_rate | 0.0 |
| stage1_alignment_ready_rate | 0.98828125 |
| pregrasp_success_rate | 0.712890625 |
| pregrasp_hold_ready_rate | 0.2421875 |
| pregrasp_held_rate | 0.31640625 |
| stage2_pregrasp_ready_rate | 0.31640625 |
| stage2_alignment_ready_rate | 0.98828125 |
| stage3_insertion_ready_rate | 0.01171875 |
| stage3_touch_ready_rate | 0.0 |
| mean_pregrasp_distance | 0.10828651487827301 |
| mean_gripper_center_pregrasp_distance | 0.10828651487827301 |
| mean_touch_error | 0.10005106776952744 |
| mean_distance | 0.14005106687545776 |
| mean_insertion_alignment | 0.964180588722229 |
| mean_target_contact_penalty | 0.0 |
| mean_pregrasp_line_error | 1.2969819884744993e-08 |

## Interpretation

- 선생님 관찰:
  - 진입 전에 집게 끝 사이 가운데 지점이 파란색 영역 중앙과 일치해야 한다.
  - 그래야 빨간 구체가 집게 사이로 들어오는 마지막 동작이 자연스럽다.
- Codex 제안:
  - USD gripper pad의 가운데 위치를 기준으로 `gripper_center_offset_b=(0.158, 0.0, 0.0)`를 추가한다.
  - 기존 tool 호환을 위해 `gripper_tip_pos` 변수명은 유지하되, 보상 기준은 집게 패드 사이 중앙점으로 바꾼다.
  - `mean_gripper_center_pregrasp_distance`를 새로 기록해 파란 marker 중앙 접근 여부를 직접 확인한다.
- 결과 평가:
  - `pregrasp_success_rate=0.712890625`까지 올라와 파란 marker 접근 자체는 크게 개선되었다.
  - `stage2_pregrasp_ready_rate=0.31640625`로, 정렬 후 pregrasp 대기 조건도 실제로 발생했다.
  - `mean_gripper_center_pregrasp_distance=0.10828651487827301`로 아직 더 줄일 여지는 있지만, 이전처럼 stage 2가 완전히 막힌 상태는 아니다.
  - `stage3_insertion_ready_rate=0.01171875`, `success_rate=0.0`이라 최종 진입 성공은 아직 안정화되지 않았다.
  - `mean_target_contact_penalty=0.0`이므로 빨간 구체와의 부적절한 접촉보다는, pregrasp 상태에서 같은 방향을 유지하며 천천히 진입하는 부분이 병목이다.
- 다음 작업:
  - stage 3 전용 curriculum 또는 replay reset을 사용해 진입 동작을 더 많이 경험시키는 실험을 진행한다.
  - stage 3에서는 `insertion_progress` 보상을 강화하고, `insertion_lateral_error` 벌점을 키워 "옆으로 비껴가기"를 줄인다.
  - 학생 수업용으로는 이 결과를 "문제를 단계로 나누면 어떤 stage가 병목인지 그래프로 찾을 수 있다"는 사례로 사용한다.
