# 20260516_113838 gripper roll alignment result

## Run

- script: `scripts/train_stage4_relaxed_gate_128_300.sh`
- run: `2026-05-16_11-38-38`
- resume checkpoint: `2026-05-16_11-09-06/model_2698.pt`
- selected checkpoint: `model_2997.pt` (latest)
- 관련 plan: `notes/20260516_113500_gripper_roll_alignment_plan.md`

## 코드 변경 내용

| 항목 | 변경 |
|------|------|
| `observation_space` | 28 → 31 |
| 새 cfg | `gripper_side_axis_b = (0.0, 1.0, 0.0)` |
| 새 cfg | `gripper_roll_alignment_weight = 0.0` (stage4_center 기본 2.5) |
| 새 텐서 | `self.gripper_side`, `self.gripper_roll_alignment` |
| `_compute_intermediate_values` | gripper_side 및 roll_alignment 계산 추가 |
| `_get_observations` | `gripper_side` obs 추가 (마지막 3값) |
| `_get_rewards` | `gripper_roll_reward` 항 추가 |
| log | `mt4/mean_gripper_roll_alignment` 추가 |

## 실행 시 발견된 문제: resume + observation_space 불일치

**핵심 문제**: RSL-RL의 `--resume`은 체크포인트와 함께 저장된 runner params(네트워크 구조 포함)를 복원한다. 이전 체크포인트(`model_2698.pt`)는 `in_features=28`로 학습된 것이라, `observation_space=31`로 수정해도 네트워크는 여전히 28-dim으로 로드된다.

```
Actor Model: Linear(in_features=28, out_features=64, bias=True)  ← 여전히 28
```

결과:
- `gripper_roll_reward` (weight=2.5): reward에는 **적용됨** ✅
- `gripper_side` obs: 네트워크에 **전달 안 됨** ❌ (RSL-RL이 첫 28dim만 사용)
- `mean_gripper_roll_alignment` 로그: 계산은 됐으나 터미널 출력 미표시 (tensorboard에는 기록됨)

## Main Metrics (최종 iteration 기준)

- `success_rate ≈ 0.003-0.005`
- `moving_pregrasp_final_rate ≈ 0.86-0.92` (이전 0.75 대비 소폭 향상)
- `stage3_latched_rate ≈ 0.90-0.95` (이전 0.78 대비 향상)
- `mean_insertion_alignment ≈ 0.95` (이전과 유사)
- `stage4_center_ready_rate ≈ 0.002-0.004`
- `mean_distance ≈ 0.064-0.071`

## Interpretation

`gripper_roll_reward`가 reward에 적용된 덕분에 `stage3_latched_rate`와 `moving_pregrasp_final_rate`가 소폭 개선되었다. 그러나 `gripper_side` observation이 정책에 전달되지 않아 정책이 roll 방향을 명시적으로 인식하지 못한다.

obs=31이 온전히 적용되려면 새 체크포인트 없이 **처음부터(scratch)** 학습을 시작해야 한다. 또는 현재 체크포인트에서 `--resume` 없이 `--load_run`/`--checkpoint`만 쓰는 방식으로 네트워크를 재초기화하면서 가중치는 버리고 진행할 수 있다.

## Recommendation

obs=31이 온전히 적용되는 학습을 위해 두 가지 선택지:

**Option A — scratch 학습** (권장)
- `--resume` 제거, obs=31 네트워크 새로 초기화
- integrated 또는 stage_b 모드부터 처음 학습
- 시간이 오래 걸리지만 obs가 제대로 반영됨

**Option B — reward만 활용, obs는 포기**
- observation_space를 다시 28로 되돌림
- `gripper_roll_alignment_weight` reward만 남김
- 기존 체크포인트를 계속 활용하면서 reward 신호로만 roll 개선 유도
- 빠르지만 정책이 roll 상태를 observation으로 볼 수 없어 한계 있음

**Option C — 절충: obs 28 유지 + reward 유지 + 긴 학습**
- 현재 상태(네트워크 28-dim, roll reward 2.5 적용) 그대로 500-800 iteration 학습
- roll reward 효과가 있는지 GUI로 확인 후 scratch 여부 결정
