from pathlib import Path
import csv

PLOTS_DIR = Path.home() / "work/robotarm/mt4_isaac_lab_task/logs/plots"
CSV_PATH = PLOTS_DIR / "mt4_checkpoint_summary.csv"
OUT_PATH = PLOTS_DIR / "best_checkpoint.txt"

if not CSV_PATH.exists():
    raise SystemExit(f"[ERROR] CSV not found: {CSV_PATH}")

rows = []
with CSV_PATH.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        def to_float(x):
            if x is None or x == "" or x == "None":
                return None
            try:
                return float(x)
            except Exception:
                return None

        row["_success_rate"] = to_float(row.get("success_rate"))
        row["_mean_distance"] = to_float(row.get("mean_distance"))
        row["_mean_reward"] = to_float(row.get("mean_reward"))
        rows.append(row)

if not rows:
    raise SystemExit("[ERROR] no rows in checkpoint summary")

# success_rate가 거의 0에 가까운 reach 초기 실험에서는 우연한 초기 성공이
# best checkpoint를 왜곡할 수 있다. 이 경우 mean_distance를 우선한다.
rows_with_success = [r for r in rows if r["_success_rate"] is not None]
max_success_rate = max((r["_success_rate"] for r in rows_with_success), default=None)

if rows_with_success and max_success_rate is not None and max_success_rate >= 0.01:
    best = max(
        rows_with_success,
        key=lambda r: (
            r["_success_rate"],
            -9999.0 if r["_mean_distance"] is None else -r["_mean_distance"],
            -9999.0 if r["_mean_reward"] is None else r["_mean_reward"],
        ),
    )
    reason = "highest meaningful success_rate"
else:
    rows_with_distance = [r for r in rows if r["_mean_distance"] is not None]
    if rows_with_distance:
        best = min(
            rows_with_distance,
            key=lambda r: (
                r["_mean_distance"],
                -9999.0 if r["_success_rate"] is None else -r["_success_rate"],
                -9999.0 if r["_mean_reward"] is None else -r["_mean_reward"],
            ),
        )
        reason = "lowest mean_distance because success_rate is below 0.01"
    else:
        rows_with_reward = [r for r in rows if r["_mean_reward"] is not None]
        if rows_with_reward:
            best = max(rows_with_reward, key=lambda r: r["_mean_reward"])
            reason = "highest mean_reward"
        else:
            # fallback: latest iteration
            best = max(rows, key=lambda r: int(r.get("iteration", 0)))
            reason = "latest checkpoint fallback"

print("========== BEST MT4 CHECKPOINT ==========")
print("reason        =", reason)
print("checkpoint    =", best.get("checkpoint"))
print("iteration     =", best.get("iteration"))
print("success_rate  =", best.get("success_rate"))
print("mean_distance =", best.get("mean_distance"))
print("min_distance  =", best.get("min_distance"))
print("mean_reward   =", best.get("mean_reward"))
print("path          =", best.get("path"))

OUT_PATH.write_text(best.get("path", "") + "\n", encoding="utf-8")
print()
print("[OK] wrote", OUT_PATH)
