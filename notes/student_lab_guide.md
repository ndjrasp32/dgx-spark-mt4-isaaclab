# MT4 로봇팔 강화학습 학생 실습 가이드

## 수업 목표

MT4 simplified reach task를 이용해 강화학습의 핵심 흐름을 관찰합니다. 학생들은 같은 로봇팔과 같은 목표 task에서 reward, penalty, 학습량을 바꾸며 정책이 어떻게 달라지는지 비교합니다.

최종 확장 방향은 우주 탐사 로버에 들어갈 로봇팔을 가정하고, 목표 탐색, 접근, 집기, 회피, 쌓기 동작으로 task를 나누어 학습시키는 것입니다.

## 현재 baseline task

- Task: `Isaac-MT4-Simplified-Reach-Direct-v0`
- 목표: 접힌 home 자세에서 출발해, 가상 gripper tip이 target 위쪽 pre-grasp 지점에 가까워지고, gripper 축이 target을 향하도록 정렬하기
- Action: 4개 관절의 target delta
- Observation: 관절 위치/속도, 가상 gripper tip 위치, target 위치, pre-grasp 위치, gripper 방향 벡터
- 기본 학습 조건: `128 envs`, `1000 iterations`, `seed 42`
- Home joint pose: `base_yaw=0.0`, `shoulder=1.20`, `elbow=-1.05`, `wrist_pitch=0.75`
- 접근 방향: 물체를 위에서 아래로 집기 좋도록 거의 수직 하강하되, 로봇팔 바깥쪽에서 살짝 비스듬히 접근
- 빨간 공: 실제 물체/목표점
- 파란 공: 집게 끝이 멈춰야 하는 pre-grasp 지점
- 초록 공: pre-grasp 거리와 방향 조건을 만족한 성공 표시

Home pose 또는 접근 방향을 바꾼 뒤에는 이전 checkpoint가 로드되더라도 같은 의미의 baseline이 아닙니다. 새 조건으로 다시 학습한 뒤 checkpoint를 선택합니다.

## 교사용 baseline 실행 순서

실시간 그래프를 먼저 띄우면 학습 중에도 reward와 distance 변화를 볼 수 있습니다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/tensorboard_mt4.sh
```

브라우저에서는 `http://spark-da91:6006/` 또는 DGX IP의 `http://<DGX_IP>:6006/`로 접속합니다.

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

VNC 화면에서 play 창이 보이지 않고 `Authorization required` 또는 `GLFW initialization failed`가 나오면, VNC 터미널에서 아래 명령을 먼저 실행합니다.

```bash
xhost +SI:localuser:spark-robotics
```

그 다음 같은 사용자로 `play_best.sh`를 다시 실행합니다.

## 학생 실습에서 바꿀 값

처음에는 한 번에 하나만 바꿉니다.

- `max_iterations`: 학습량이 부족하거나 충분할 때 그래프가 어떻게 달라지는지 확인
- `reward weight`: target에 가까워지는 보상을 키우거나 줄여 행동 차이 관찰
- `action_penalty`: 움직임을 아끼는 정책과 적극적으로 움직이는 정책 비교
- `approach_horizontal_weight`: 위에서 내려오는 접근을 얼마나 비스듬하게 만들지 비교

## 결과 해석 기준

- `success_rate`: 목표 근처에 도달한 병렬 환경의 비율
- `mean_pregrasp_distance`: 가상 gripper tip과 pre-grasp 지점 사이 평균 거리
- `mean_distance`: 가상 gripper tip과 실제 target 사이 평균 거리
- `mean_alignment`: gripper 축이 target을 향하는 정도
- `mean_reward`: 전체 보상 흐름
- `episode_length`: 에피소드가 너무 빨리 끝나거나 길게 끌리는지 확인

좋은 정책은 success rate만 높다고 끝나지 않습니다. 실제 로봇팔 이식 후보는 mean distance가 낮고, 움직임이 과격하지 않으며, play 화면에서 안정적으로 반복되는 정책이어야 합니다.

학습 장면 자체를 보여줄 때는 병렬 환경을 작게 줄인 visual demo를 사용합니다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_visual_16_300.sh --seed 42
```

best checkpoint를 한 로봇팔로만 볼 때는 아래 명령을 사용합니다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/play_best_single.sh
```

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
