# MT4 Pre-Grasp Reward Notes

현재 simplified v2 USD에는 별도 finger/gripper body가 없고 `wrist_link`까지만 articulation body로 존재합니다. 그래서 이 단계에서는 `wrist_link` 앞쪽에 가상 gripper tip을 두고, 실제 집기 전 단계인 pre-grasp 자세를 학습합니다.

## 시각 표시

- 빨간 공: target object center
- 파란 공: gripper tip이 멈춰야 하는 pre-grasp target
- 초록 공: 거리와 방향 조건을 만족한 성공 상태

## 보상 의도

- gripper tip이 target 중심을 관통하지 않고 target 앞 standoff 위치로 이동합니다.
- gripper forward axis가 target을 향하도록 정렬합니다.
- target에 너무 가까워지는 움직임은 clearance penalty로 억제합니다.
- 실제 gripper open/close는 아직 action에 포함하지 않고, 다음 grasp task에서 추가합니다.

## 다음 확장

1. 실제 finger link가 포함된 USD로 교체합니다.
2. gripper open/close action을 action space에 추가합니다.
3. target object를 visual marker가 아닌 rigid object로 바꿉니다.
4. contact/grasp success 조건을 추가합니다.
