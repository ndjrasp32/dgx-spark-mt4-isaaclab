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
        row["_pregrasp_success_rate"] = to_float(row.get("pregrasp_success_rate"))
        row["_stage2_alignment_ready_rate"] = to_float(row.get("stage2_alignment_ready_rate"))
        row["_stage3_insertion_ready_rate"] = to_float(row.get("stage3_insertion_ready_rate"))
        row["_stage3_touch_ready_rate"] = to_float(row.get("stage3_touch_ready_rate"))
        row["_mean_pregrasp_distance"] = to_float(row.get("mean_pregrasp_distance"))
        row["_mean_touch_error"] = to_float(row.get("mean_touch_error"))
        row["_mean_distance"] = to_float(row.get("mean_distance"))
        row["_mean_alignment"] = to_float(row.get("mean_alignment"))
        row["_mean_pregrasp_alignment"] = to_float(row.get("mean_pregrasp_alignment"))
        row["_mean_insertion_alignment"] = to_float(row.get("mean_insertion_alignment"))
        row["_mean_target_contact_penalty"] = to_float(row.get("mean_target_contact_penalty"))
        row["_mean_insertion_progress"] = to_float(row.get("mean_insertion_progress"))
        row["_mean_reward"] = to_float(row.get("mean_reward"))
        row["_primary_distance"] = row["_mean_pregrasp_distance"]
        if row["_primary_distance"] is None:
            row["_primary_distance"] = row["_mean_distance"]
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
            -9999.0 if r["_primary_distance"] is None else -r["_primary_distance"],
            -9999.0 if r["_mean_alignment"] is None else r["_mean_alignment"],
            -9999.0 if r["_mean_reward"] is None else r["_mean_reward"],
        ),
    )
    reason = "highest meaningful success_rate"
else:
    rows_with_distance = [r for r in rows if r["_primary_distance"] is not None]
    if rows_with_distance:
        rows_with_alignment = [
            r for r in rows_with_distance
            if r["_mean_alignment"] is not None and r["_mean_alignment"] >= 0.65
        ]
        if rows_with_alignment:
            def balanced_score(r):
                distance = r["_primary_distance"]
                target_distance = r["_mean_distance"]
                target_standoff_error = abs((target_distance or 0.055) - 0.055)
                touch_error = r["_mean_touch_error"] or target_standoff_error
                success = r["_success_rate"] or 0.0
                pregrasp_success = r["_pregrasp_success_rate"] or 0.0
                stage2_ready = r["_stage2_alignment_ready_rate"] or 0.0
                stage3_ready = r["_stage3_insertion_ready_rate"] or 0.0
                stage3_touch_ready = r["_stage3_touch_ready_rate"] or 0.0
                alignment = r["_mean_alignment"] or 0.0
                pregrasp_alignment = r["_mean_pregrasp_alignment"] or alignment
                insertion_alignment = r["_mean_insertion_alignment"] or alignment
                contact_penalty = r["_mean_target_contact_penalty"] or 0.0
                insertion_progress = r["_mean_insertion_progress"] or 0.0
                reward = r["_mean_reward"] or 0.0
                return (
                    -distance
                    -0.25 * target_standoff_error
                    -0.40 * touch_error
                    +0.05 * pregrasp_alignment
                    +0.08 * insertion_alignment
                    +0.50 * pregrasp_success
                    +0.35 * stage2_ready
                    +1.50 * stage3_ready
                    +2.50 * stage3_touch_ready
                    +0.10 * insertion_progress
                    +10.0 * success
                    -5.0 * contact_penalty
                    +0.000001 * reward
                )

            best = max(rows_with_alignment, key=balanced_score)
            reason = "best balanced pregrasp distance and alignment because success_rate is below 0.01"
        else:
            best = min(
                rows_with_distance,
                key=lambda r: (
                    r["_primary_distance"],
                    -9999.0 if r["_success_rate"] is None else -r["_success_rate"],
                    -9999.0 if r["_mean_alignment"] is None else r["_mean_alignment"],
                    -9999.0 if r["_mean_reward"] is None else -r["_mean_reward"],
                ),
            )
            if best["_mean_pregrasp_distance"] is not None:
                reason = "lowest mean_pregrasp_distance because success_rate and alignment are below thresholds"
            else:
                reason = "lowest mean_distance because success_rate and alignment are below thresholds"
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
print("pregrasp_succ =", best.get("pregrasp_success_rate"))
print("stage2_ready  =", best.get("stage2_alignment_ready_rate"))
print("stage3_ready  =", best.get("stage3_insertion_ready_rate"))
print("stage3_touch  =", best.get("stage3_touch_ready_rate"))
print("pregrasp_dist =", best.get("mean_pregrasp_distance"))
print("touch_error   =", best.get("mean_touch_error"))
print("mean_distance =", best.get("mean_distance"))
print("mean_alignment=", best.get("mean_alignment"))
print("pregrasp_align=", best.get("mean_pregrasp_alignment"))
print("insert_align  =", best.get("mean_insertion_alignment"))
print("contact_penalty=", best.get("mean_target_contact_penalty"))
print("min_distance  =", best.get("min_distance"))
print("mean_reward   =", best.get("mean_reward"))
print("path          =", best.get("path"))

OUT_PATH.write_text(best.get("path", "") + "\n", encoding="utf-8")
print()
print("[OK] wrote", OUT_PATH)
