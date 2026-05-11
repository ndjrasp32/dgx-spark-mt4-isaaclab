# MT4 로봇팔 강화학습 학생 실습 가이드

## 수업 목표

MT4 simplified reach task를 이용해 강화학습의 핵심 흐름을 관찰합니다. 학생들은 같은 로봇팔과 같은 목표 task에서 reward, penalty, 학습량을 바꾸며 정책이 어떻게 달라지는지 비교합니다.

최종 확장 방향은 우주 탐사 로버에 들어갈 로봇팔을 가정하고, 목표 탐색, 접근, 집기, 회피, 쌓기 동작으로 task를 나누어 학습시키는 것입니다.

## 현재 baseline task

- Task: `Isaac-MT4-Simplified-Reach-Direct-v0`
- 목표: wrist/end-effector가 임의 target position에 가까워지기
- Action: 4개 관절의 target delta
- Observation: 관절 위치/속도, end-effector 위치, target 위치, target 방향 벡터
- 기본 학습 조건: `128 envs`, `1000 iterations`, `seed 42`

## 교사용 baseline 실행 순서

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_128_1000.sh --seed 42
~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label baseline_seed42 \
  --seed 42 \
  --num-envs 128 \
  --max-iterations 1000 \
  --reward-profile baseline \
  --action-penalty 0.01 \
  --notes "teacher baseline"
~/work/robotarm/mt4_isaac_lab_task/scripts/play_best.sh --num_envs 1 --real-time
```

## 학생 실습에서 바꿀 값

처음에는 한 번에 하나만 바꿉니다.

- `max_iterations`: 학습량이 부족하거나 충분할 때 그래프가 어떻게 달라지는지 확인
- `reward weight`: target에 가까워지는 보상을 키우거나 줄여 행동 차이 관찰
- `action_penalty`: 움직임을 아끼는 정책과 적극적으로 움직이는 정책 비교

## 결과 해석 기준

- `success_rate`: 목표 근처에 도달한 병렬 환경의 비율
- `mean_distance`: 목표와 wrist 사이 평균 거리
- `mean_reward`: 전체 보상 흐름
- `episode_length`: 에피소드가 너무 빨리 끝나거나 길게 끌리는지 확인

좋은 정책은 success rate만 높다고 끝나지 않습니다. 실제 로봇팔 이식 후보는 mean distance가 낮고, 움직임이 과격하지 않으며, play 화면에서 안정적으로 반복되는 정책이어야 합니다.

## 확장 로드맵

1. Reach 안정화: 목표점 접근을 반복적으로 성공시킵니다.
2. Pre-grasp: 물체 바로 앞의 안전한 접근 위치까지 이동합니다.
3. Grasp: gripper 제어를 추가하고 잡기 성공 조건을 정의합니다.
4. Avoid: 자기 충돌, 바닥, 장애물 회피 penalty를 추가합니다.
5. Stack: 물체를 집어서 목표 위치에 쌓는 long-horizon task로 확장합니다.

## 실제 로봇팔 이식 전 안전 기준

- 관절 limit과 속도 limit을 시뮬레이션과 실제 제어 코드 양쪽에서 제한합니다.
- 첫 실제 구동은 낮은 속도와 작은 동작 범위에서 시작합니다.
- emergency stop 절차를 학생들이 먼저 설명할 수 있어야 합니다.
- 시뮬레이션에서 안정적인 정책만 실제 로봇으로 이동합니다.
