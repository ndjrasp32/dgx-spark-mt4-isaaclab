# 2026-05-21 MT4 로봇팔 화성 로버 탑재 기기 강화학습 계획

## 목표

Mirobot MT4 로봇팔을 화성 탐사 로버에 탑재할 조작 장치의 축소 실험 플랫폼으로 사용한다. DGX SPARK에서 Isaac Lab 기반 디지털 트윈을 구성하고, 로버 임무에 필요한 기본 조작 동작을 강화학습으로 각각 학습한 뒤, 최종적으로 로버 운용 시스템과 연동 가능한 정책 구조를 만든다.

초기 목표는 실제 하드웨어를 바로 움직이는 것이 아니라, 로봇팔의 관절 각도, 모터 출력 범위, 원점 자세, 안전 한계를 먼저 검증하고, 그 결과를 디지털 트윈과 강화학습 환경에 반영하는 것이다.

## 핵심 원칙

1. 모든 미션은 같은 초기 자세에서 시작한다.
   - 초기 자세는 실제 MT4 전원 인가 후 기준 자세 또는 별도 캘리브레이션으로 정의한 home pose로 고정한다.
   - 학습 환경 reset도 이 자세를 기준으로 한다.

2. 모든 미션 완료 후 로봇팔은 다시 초기 자세로 복귀한다.
   - 실제 로버 운용에서는 다음 명령을 예측 가능하게 시작해야 하므로, 미션 종료 상태를 방치하지 않는다.
   - 정책은 `home -> mission -> home` 시퀀스를 기본 단위로 본다.

3. 개별 동작은 독립 미션으로 먼저 학습한다.
   - 물체 집기, 물체 놓기, 물체 쌓기, 물체 밀기, 물체 당기기를 각각 별도 task로 만든다.
   - 이후 rover planner 또는 mission sequencer가 필요한 정책을 선택해 호출하도록 설계한다.

4. 실제 로봇 이식 전에는 반드시 디지털 트윈에서 검증한다.
   - URDF/USD, joint limit, gripper 위치, end-effector 좌표계, action scaling이 실제 MT4와 일치해야 한다.
   - 디지털 트윈에서 안정적으로 성공한 정책만 하드웨어 검증 후보로 올린다.

5. 하드웨어 안전 검증은 강화학습보다 먼저 진행한다.
   - joint limit, home pose, 모터 출력/속도 제한, 비상 정지 절차를 먼저 확인한다.
   - 실제 로봇팔 테스트는 no-motion 검증, 저속 단일 관절 검증, 짧은 시퀀스 검증 순서로 진행한다.

## 1단계: 실제 MT4 캘리브레이션

목표는 강화학습 action이 실제 로봇팔에서 안전하게 해석될 수 있도록 기준값을 잡는 것이다.

확인 항목:

- 각 관절 이름과 실제 모터 축 대응
- 각 관절의 최소/최대 각도
- 전원 인가 직후 자세와 소프트웨어 home pose의 차이
- URDF/USD joint axis와 실제 움직임 방향 일치 여부
- gripper open/close 명령 범위
- 모터 출력, 속도, 가속도 제한
- 통신 연결, 명령 지연, 명령 실패 시 동작
- 비상 정지 및 안전 복구 절차

산출물:

- `home_pose` joint angle 표
- 안전 joint limit 표
- 실제 제어 명령과 Isaac Lab action mapping 표
- no-motion 검증 로그
- 저속 단일 관절 검증 로그

## 2단계: 디지털 트윈 환경 구축

목표는 실제 MT4를 최대한 보수적으로 반영한 Isaac Lab 병렬 학습 환경을 만드는 것이다.

구성 항목:

- 실제 MT4 URDF 또는 검증된 USD asset
- link, joint, mesh path 정리
- end-effector 및 gripper center 기준 frame 정의
- home pose reset 함수
- joint position/velocity 기반 observation
- task object의 pose, velocity, 접촉 상태 observation
- action clipping 및 rate limit
- 충돌체 단순화와 self-collision 검증
- Mars rover 탑재 상황을 가정한 작업 공간 제한

초기 디지털 트윈에서는 화성 환경을 과하게 복잡하게 만들지 않는다. 먼저 낮은 중력, 먼지, 지형 요철 같은 요소를 빼고 MT4 조작 안정성을 확보한 뒤, 이후 단계에서 rover deck, 샘플 컨테이너, 지형 경사, 낮은 중력 등을 하나씩 추가한다.

현재 레포 기준 초기 구현:

- `assets/usd/mt4_simplified_v4_two_finger.usd`
  - `mt4_simplified_v2.usd`를 기반으로 `gripper_pitch` 링크 뒤에 2손가락 그리퍼를 추가한다.
  - 좌/우 손가락은 각각 `left_finger_slide`, `right_finger_slide` 프리스매틱 조인트로 열고 닫는다.
  - 생성 명령: `scripts/create_two_finger_asset.sh`
- `source/mt4_reach_direct/mt4_mars_twin_env.py`
  - Mars gravity `-3.711 m/s^2`를 적용한다.
  - 샘플 큐브와 보조 큐브는 rigid body, collision, friction, damping을 가진 물리 오브젝트로 둔다.
  - action은 5개 팔 관절 delta와 1개 gripper open/close delta로 구성한다.
  - 모든 reset은 home pose와 gripper open 상태에서 시작한다.
- `tools/view_mt4_mars_twin.py`
  - Isaac Sim GUI에서 pick/place/stack/push/pull 트윈 장면을 바로 열고, scripted motion으로 관절과 그리퍼 개폐를 시연한다.
  - 실행 예: `scripts/view_mars_twin.sh --mission push --num_envs 1 --duration 120`

## 3단계: 개별 강화학습 미션

각 미션은 별도 task와 별도 checkpoint로 관리한다. 처음부터 하나의 거대한 정책으로 모든 동작을 학습시키지 않고, 성공 기준과 reward를 명확히 분리한다.

### 3.1 물체 집기

목표:

- home pose에서 시작해 목표 물체에 접근한다.
- gripper center를 물체 중심 또는 지정 grasp point에 정렬한다.
- 물체를 치거나 밀지 않고 안정적으로 잡는다.
- 일정 높이 이상 들어 올린 뒤 home pose로 복귀한다.

주요 reward:

- pregrasp 위치 접근 보상
- gripper 정렬 보상
- 조기 접촉 벌점
- grasp 성공 보상
- lift 성공 보상
- home 복귀 보상

성공 기준:

- 물체가 gripper에 안정적으로 잡힘
- lift 높이 기준 통과
- 복귀 후 joint pose가 home tolerance 안에 들어옴

### 3.2 물체 놓기

목표:

- 집은 물체를 지정 위치로 이동한다.
- 목표 위치에서 물체를 안정적으로 내려놓는다.
- gripper를 열고 물체와 분리한 뒤 home pose로 복귀한다.

주요 reward:

- 목표 위치 접근 보상
- 낮은 충격 속도 보상
- 놓은 뒤 object pose 안정성 보상
- gripper-object 분리 보상
- home 복귀 보상

성공 기준:

- 물체 중심이 목표 영역 안에 있음
- 물체가 쓰러지거나 튀지 않음
- 로봇팔이 home pose로 복귀함

### 3.3 물체 쌓기

목표:

- 첫 번째 물체 위에 두 번째 물체를 올린다.
- 쌓은 뒤 일정 시간 동안 안정적으로 유지한다.
- 작업 후 home pose로 복귀한다.

주요 reward:

- 상단 물체 목표 높이/위치 보상
- 접촉 안정성 보상
- 과도한 충돌 벌점
- stack 유지 시간 보상
- home 복귀 보상

성공 기준:

- 상단 물체가 지정된 support 영역 안에 있음
- 일정 시간 이상 stack이 무너지지 않음
- 복귀 후 다음 미션 시작 가능 상태가 됨

### 3.4 물체 밀기

목표:

- gripper 또는 지정 push tool point로 물체를 목표 방향으로 민다.
- 물체가 목표 위치 또는 목표 선을 통과하도록 한다.
- 작업 후 home pose로 복귀한다.

주요 reward:

- push 전 정렬 보상
- 목표 방향 이동 보상
- 불필요한 회전/이탈 벌점
- 과도한 충격 벌점
- home 복귀 보상

성공 기준:

- 물체가 목표 영역에 도달함
- 경로 이탈과 회전이 허용 범위 안에 있음
- 로봇팔이 home pose로 복귀함

### 3.5 물체 당기기

목표:

- gripper 또는 hook 형태의 도구로 물체를 잡거나 걸어 당긴다.
- 물체를 로버 쪽 또는 지정 회수 영역으로 이동시킨다.
- 작업 후 home pose로 복귀한다.

주요 reward:

- 접촉 전 정렬 보상
- 안정적인 hook/contact 유지 보상
- 목표 방향 이동 보상
- 놓침 또는 미끄러짐 벌점
- home 복귀 보상

성공 기준:

- 물체가 회수 영역 안에 들어옴
- 당기는 동안 접촉이 안정적으로 유지됨
- 복귀 후 다음 명령을 받을 수 있음

## 4단계: 정책 운용 구조

초기에는 미션별 독립 정책으로 관리한다.

예상 구조:

- `PickPolicy`: 물체 집기
- `PlacePolicy`: 물체 놓기
- `StackPolicy`: 물체 쌓기
- `PushPolicy`: 물체 밀기
- `PullPolicy`: 물체 당기기
- `HomePolicy` 또는 deterministic home controller: 초기 자세 복귀

로버 연동 시에는 상위 mission planner가 현재 작업 목표를 판단하고 필요한 정책을 호출한다. 예를 들어 샘플 수집은 `Pick -> Place -> Home`, 장애물 정리는 `Push -> Home`, 회수 작업은 `Pull -> Pick -> Place -> Home`처럼 조합할 수 있다.

## 5단계: 실험 기록과 평가 지표

각 학습 run은 날짜, task 이름, env 수, iteration, seed, reward 설정, checkpoint 경로를 기록한다.

공통 metric:

- success rate
- episode length
- home return success rate
- joint limit violation count
- action magnitude
- object position error
- object orientation error
- contact impulse
- collision count
- policy smoothness
- best checkpoint 선정 이유

미션별 metric:

- 집기: grasp success, lift height, object slip count
- 놓기: placement error, drop impact, post-release stability
- 쌓기: stack stability time, top object offset
- 밀기: push direction error, target crossing success
- 당기기: pull distance, contact 유지율, object recovery success

## 6단계: 개발 로드맵

1. MT4 캘리브레이션 문서화
   - home pose, joint limit, gripper range, action scaling을 먼저 확정한다.

2. 디지털 트윈 asset 검증
   - 실제 MT4 URDF/USD가 Isaac Sim에서 올바르게 움직이는지 확인한다.

3. home reset과 no-motion 안전 검증
   - 시뮬레이션과 실제 하드웨어 모두에서 home pose 기준을 맞춘다.

4. pick 전 단계 학습
   - reach, pregrasp, gripper alignment를 먼저 안정화한다.

5. pick/lift 학습
   - 실제 물체를 치지 않고 잡고 들어 올리는 정책을 만든다.

6. place 학습
   - 잡은 물체를 지정 위치에 낮은 충격으로 내려놓는다.

7. push/pull 학습
   - 로버 주변 샘플 또는 장애물을 이동시키는 동작을 학습한다.

8. stack 학습
   - 가장 난도가 높으므로 pick/place가 안정화된 뒤 진행한다.

9. rover mission sequencer 연동
   - 상위 명령이 정책을 선택하고, 각 미션 종료 후 home pose로 복귀하는 구조를 만든다.

10. sim-to-real 검증
    - action scale을 낮추고, 저속 replay부터 시작해 실제 MT4에서 단계적으로 검증한다.

## 바로 다음 작업

1. 현재 저장소의 MT4 URDF/USD, hardware, script 구조를 다시 확인한다.
2. 실제 로봇팔을 움직이지 않는 no-motion 검증 스크립트를 먼저 정리한다.
3. home pose와 joint limit 표를 문서화한다.
4. Isaac Lab task에서 reset이 항상 home pose로 들어가는지 확인한다.
5. 첫 번째 학습 목표를 `Pick` 전체가 아니라 `Reach/Pregrasp`로 좁혀 시작한다.

## 현재 판단

이 계획은 한 번에 전체 로버 조작 정책을 만들기보다, 안전 기준과 디지털 트윈 정확도를 먼저 고정한 뒤 미션별 정책을 누적하는 방식이 맞다. 특히 실제 하드웨어 이식을 목표로 하므로, 초기 자세 고정과 미션 후 home pose 복귀를 강화학습 task의 부가 기능이 아니라 필수 성공 조건으로 넣어야 한다.
