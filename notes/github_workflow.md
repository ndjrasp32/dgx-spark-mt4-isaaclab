# MT4 IsaacLab GitHub Workflow

이 프로젝트의 기본 작업 repo는 다음 경로입니다.

```bash
cd ~/work/robotarm/mt4_isaac_lab_task
```

기본 push 대상은 `origin main`입니다.

```bash
git remote -v
git branch --show-current
```

IsaacLab upstream repo인 `~/work/isaac/src/IsaacLab`은 실행 환경으로 사용하고, 별도 요청 없이는 커밋하거나 push하지 않습니다.

## 작업 단위마다 반복할 절차

1. 변경은 가능하면 `~/work/robotarm/mt4_isaac_lab_task` 안에서만 진행합니다.
2. 검증 스크립트를 실행합니다.

```bash
~/work/robotarm/mt4_isaac_lab_task/scripts/verify_before_push.sh
```

3. 변경 내용을 확인합니다.

```bash
git status --short
git diff
```

4. 의미 있는 작업 단위로 커밋합니다.

```bash
git add <changed-files>
git commit -m "Describe the MT4 workflow change"
```

5. GitHub에 push합니다.

```bash
git push origin main
```

## 검증 기준

- Shell script 변경 시 `bash -n scripts/*.sh`가 통과해야 합니다.
- `scripts/plot_and_select_best.sh`가 실행되어 plot과 `best_checkpoint.txt`를 만들 수 있어야 합니다.
- 실험 결과를 보존할 때는 `scripts/record_experiment_result.sh`로 `experiments/mt4_reach_experiment_log.csv`에 기록합니다.
- `best_checkpoint.txt`가 비어 있거나 checkpoint 경로가 깨져 있으면 push 전에 고칩니다.
- `train_128_1000.sh`와 `play_best.sh`는 Isaac Sim 실행 시간이 길 수 있으므로 기본 자동 검증에서는 실행하지 않습니다.
