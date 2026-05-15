# 20260515_105638 File Naming Workflow

## 목표

GitHub에서 실험이 쌓였을 때, 어떤 파일이 먼저 만들어졌고 어떤 실험이 최신인지 바로 알 수 있도록 파일 이름 앞에 날짜와 시간을 붙인다.

기본 형식:

```text
YYYYMMDD_HHMMSS_short_label.ext
```

예시:

```text
20260515_105638_file_naming_workflow.md
20260515_113000_radial_pregrasp_visual_16env_300iter.md
20260515_113000_radial_pregrasp_visual_16env_300iter_metrics.csv
logs/plots/20260515_113000_radial_pregrasp_visual_16env_300iter/
```

## 앞으로의 규칙

- `notes/`에 새 문서를 만들 때는 날짜/시간을 앞에 붙인다.
- `experiments/`의 개별 실험 기록은 날짜/시간을 앞에 붙인다.
- `logs/plots/`의 루트 파일은 latest 용도로 유지한다.
- `logs/plots/YYYYMMDD_HHMMSS_label/` 디렉터리는 push 가능한 고정 스냅샷으로 본다.
- `experiments/mt4_reach_experiment_log.csv`는 전체 실험 index 역할만 한다.

## 스크립트 변경

`scripts/plot_and_select_best.sh`는 실행이 끝나면 자동으로 plot snapshot 디렉터리를 만든다.

```bash
MT4_PLOT_LABEL=radial_pregrasp_visual_16env_300iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
```

생성 예시:

```text
logs/plots/20260515_113000_radial_pregrasp_visual_16env_300iter/
```

`scripts/record_experiment_result.sh`는 기존 누적 CSV에 한 줄을 추가하면서, 같은 timestamp와 label을 가진 개별 보고서도 만든다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label radial_pregrasp_visual_16env_300iter \
  --seed 42 \
  --num-envs 16 \
  --max-iterations 300 \
  --reward-profile radial_pregrasp_hold \
  --notes "Blue marker is aligned on the base-to-red radial line; verify pregrasp hold before insertion."
```

생성 예시:

```text
experiments/20260515_113000_radial_pregrasp_visual_16env_300iter.md
experiments/20260515_113000_radial_pregrasp_visual_16env_300iter_metrics.csv
```

## latest와 snapshot의 차이

`logs/plots/mt4_*.png`는 가장 최근 plot 결과가 계속 덮어써지는 latest 파일이다. 빠르게 확인할 때 사용한다.

반대로 `logs/plots/YYYYMMDD_HHMMSS_label/` 안의 파일은 그 실험 시점의 결과를 보존하는 snapshot이다. GitHub에서 수업용 흐름을 설명할 때는 snapshot 디렉터리와 `experiments/YYYYMMDD_HHMMSS_label.md`를 함께 본다.

## 다음 학습 제안

파일 정리 규칙을 적용한 뒤, 바로 긴 학습으로 가지 않고 새 radial pregrasp marker가 화면에서 맞는지 16 env / 300 iter 시각 학습으로 먼저 확인한다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/train_visual_16_300.sh --seed 42
MT4_PLOT_LABEL=radial_pregrasp_visual_16env_300iter \
  ~/work/robotarm/mt4_isaac_lab_task/scripts/plot_and_select_best.sh
~/work/robotarm/mt4_isaac_lab_task/scripts/record_experiment_result.sh \
  --run-label radial_pregrasp_visual_16env_300iter \
  --seed 42 \
  --num-envs 16 \
  --max-iterations 300 \
  --reward-profile radial_pregrasp_hold \
  --notes "Check whether blue pregrasp marker stays on the base-to-red radial line and whether pregrasp_held_rate appears."
```

판단 기준:

- `mean_pregrasp_line_error`가 0에 가깝게 유지되는가
- `mean_insertion_alignment`가 양수로 올라가는가
- `pregrasp_hold_ready_rate` 또는 `pregrasp_held_rate`가 0보다 커지는가
- 빨간 공과 로봇팔 충돌 벌점이 낮게 유지되는가

이 기준이 납득되면 128 env / 1000 iter full 학습으로 넘어간다.
