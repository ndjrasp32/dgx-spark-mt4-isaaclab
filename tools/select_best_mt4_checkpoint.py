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

        try:
            row["_iteration"] = int(row.get("iteration") or 0)
        except Exception:
            row["_iteration"] = 0
        row["_success_rate"] = to_float(row.get("success_rate"))
        row["_stage1_alignment_ready_rate"] = to_float(row.get("stage1_alignment_ready_rate"))
        row["_stage1_latched_rate"] = to_float(row.get("stage1_latched_rate"))
        row["_pregrasp_entry_success_rate"] = to_float(row.get("pregrasp_entry_success_rate"))
        row["_pregrasp_entry_ready_rate"] = to_float(row.get("pregrasp_entry_ready_rate"))
        row["_pregrasp_entry_reached_rate"] = to_float(row.get("pregrasp_entry_reached_rate"))
        row["_pregrasp_success_rate"] = to_float(row.get("pregrasp_success_rate"))
        row["_pregrasp_hold_ready_rate"] = to_float(row.get("pregrasp_hold_ready_rate"))
        row["_pregrasp_held_rate"] = to_float(row.get("pregrasp_held_rate"))
        row["_stage2_pregrasp_ready_rate"] = to_float(row.get("stage2_pregrasp_ready_rate"))
        row["_stage2_latched_rate"] = to_float(row.get("stage2_latched_rate"))
        row["_stage2_alignment_ready_rate"] = to_float(row.get("stage2_alignment_ready_rate"))
        row["_stage3_insertion_ready_rate"] = to_float(row.get("stage3_insertion_ready_rate"))
        row["_stage3_latched_rate"] = to_float(row.get("stage3_latched_rate"))
        row["_stage3_touch_ready_rate"] = to_float(row.get("stage3_touch_ready_rate"))
        row["_stage4_center_ready_rate"] = to_float(row.get("stage4_center_ready_rate"))
        row["_blue_final_center_ready_rate"] = to_float(row.get("blue_final_center_ready_rate"))
        row["_stage4_push_ready_rate"] = to_float(row.get("stage4_push_ready_rate"))
        row["_mean_pregrasp_entry_distance"] = to_float(row.get("mean_pregrasp_entry_distance"))
        row["_mean_pregrasp_distance"] = to_float(row.get("mean_pregrasp_distance"))
        row["_mean_touch_error"] = to_float(row.get("mean_touch_error"))
        row["_mean_distance"] = to_float(row.get("mean_distance"))
        row["_mean_alignment"] = to_float(row.get("mean_alignment"))
        row["_mean_pregrasp_alignment"] = to_float(row.get("mean_pregrasp_alignment"))
        row["_mean_insertion_alignment"] = to_float(row.get("mean_insertion_alignment"))
        row["_mean_target_contact_penalty"] = to_float(row.get("mean_target_contact_penalty"))
        row["_mean_early_target_contact_penalty"] = to_float(row.get("mean_early_target_contact_penalty"))
        row["_mean_pregrasp_center_progress"] = to_float(row.get("mean_pregrasp_center_progress"))
        row["_mean_insertion_progress"] = to_float(row.get("mean_insertion_progress"))
        row["_mean_center_push_progress"] = to_float(row.get("mean_center_push_progress"))
        row["_mean_center_push_overshoot"] = to_float(row.get("mean_center_push_overshoot"))
        row["_mean_best_center_push_progress"] = to_float(row.get("mean_best_center_push_progress"))
        row["_mean_center_push_improvement"] = to_float(row.get("mean_center_push_improvement"))
        row["_mean_best_target_center_distance"] = to_float(row.get("mean_best_target_center_distance"))
        row["_mean_target_center_improvement"] = to_float(row.get("mean_target_center_improvement"))
        row["_mean_target_center_shell_improvement"] = to_float(row.get("mean_target_center_shell_improvement"))
        row["_mean_center_shortest_path_score"] = to_float(row.get("mean_center_shortest_path_score"))
        row["_mean_stage4_time_pressure"] = to_float(row.get("mean_stage4_time_pressure"))
        row["_mean_stage3_time_preserve"] = to_float(row.get("mean_stage3_time_preserve"))
        row["_mean_terminal_success_quality"] = to_float(row.get("mean_terminal_success_quality"))
        row["_mean_near_terminal_reward"] = to_float(row.get("mean_near_terminal_reward"))
        row["_mean_stage_latch_reward"] = to_float(row.get("mean_stage_latch_reward"))
        row["_mean_progressive_stage_weight"] = to_float(row.get("mean_progressive_stage_weight"))
        row["_mean_moving_pregrasp_fraction"] = to_float(row.get("mean_moving_pregrasp_fraction"))
        row["_moving_pregrasp_final_rate"] = to_float(row.get("moving_pregrasp_final_rate"))
        row["_moving_pregrasp_step_ready_rate"] = to_float(row.get("moving_pregrasp_step_ready_rate"))
        row["_mean_moving_pregrasp_hold_progress"] = to_float(row.get("mean_moving_pregrasp_hold_progress"))
        row["_mean_moving_pregrasp_reward"] = to_float(row.get("mean_moving_pregrasp_reward"))
        row["_mean_moving_pregrasp_funnel_reward"] = to_float(row.get("mean_moving_pregrasp_funnel_reward"))
        row["_mean_moving_pregrasp_exp_reward"] = to_float(row.get("mean_moving_pregrasp_exp_reward"))
        row["_mean_moving_pregrasp_shell_improvement"] = to_float(
            row.get("mean_moving_pregrasp_shell_improvement")
        )
        row["_mean_best_moving_pregrasp_distance"] = to_float(row.get("mean_best_moving_pregrasp_distance"))
        row["_mean_final_insertion_reward"] = to_float(row.get("mean_final_insertion_reward"))
        row["_mean_pregrasp_line_error"] = to_float(row.get("mean_pregrasp_line_error"))
        row["_mean_gripper_roll_alignment"] = to_float(row.get("mean_gripper_roll_alignment"))
        row["_mean_reward"] = to_float(row.get("mean_reward"))
        row["_primary_distance"] = row["_mean_pregrasp_distance"]
        if row["_primary_distance"] is None:
            row["_primary_distance"] = row["_mean_distance"]
        rows.append(row)

if not rows:
    raise SystemExit("[ERROR] no rows in checkpoint summary")

# 학습 초반에는 reset 직후 자세/타겟 배치 우연성 때문에 success_rate가 크게 튈 수 있다.
# 충분히 진행된 checkpoint만 best 후보로 삼아 model_0/model_50 같은 초기 착시를 피한다.
max_iteration = max(r["_iteration"] for r in rows)
min_candidate_iteration = 0
if max_iteration >= 100:
    min_candidate_iteration = max(1, int(max_iteration * 0.50))
elif max_iteration > 0:
    min_candidate_iteration = 1

candidate_rows = [r for r in rows if r["_iteration"] >= min_candidate_iteration]
if not candidate_rows:
    candidate_rows = rows
    min_candidate_iteration = 0

rows_with_success = [r for r in candidate_rows if r["_success_rate"] is not None]
max_success_rate = max((r["_success_rate"] for r in rows_with_success), default=None)

if rows_with_success and max_success_rate is not None and max_success_rate >= 0.01:
    best = max(
        rows_with_success,
        key=lambda r: (
            r["_success_rate"],
            -9999.0 if r["_primary_distance"] is None else -r["_primary_distance"],
            -9999.0 if r["_blue_final_center_ready_rate"] is None else r["_blue_final_center_ready_rate"],
            -9999.0 if r["_mean_alignment"] is None else r["_mean_alignment"],
            -9999.0 if r["_mean_gripper_roll_alignment"] is None else r["_mean_gripper_roll_alignment"],
            -9999.0 if r["_mean_reward"] is None else r["_mean_reward"],
            r["_iteration"],
        ),
    )
    reason = f"highest meaningful success_rate after iteration {min_candidate_iteration}"
else:
    rows_with_distance = [r for r in candidate_rows if r["_primary_distance"] is not None]
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
                stage1_ready = r["_stage1_alignment_ready_rate"] or r["_stage2_alignment_ready_rate"] or 0.0
                stage1_latched = r["_stage1_latched_rate"] or 0.0
                entry_success = r["_pregrasp_entry_success_rate"] or 0.0
                entry_ready = r["_pregrasp_entry_ready_rate"] or 0.0
                entry_reached = r["_pregrasp_entry_reached_rate"] or 0.0
                pregrasp_success = r["_pregrasp_success_rate"] or 0.0
                pregrasp_hold = r["_pregrasp_hold_ready_rate"] or 0.0
                pregrasp_held = r["_pregrasp_held_rate"] or 0.0
                stage2_ready = r["_stage2_pregrasp_ready_rate"] or 0.0
                stage2_latched = r["_stage2_latched_rate"] or 0.0
                stage3_ready = r["_stage3_insertion_ready_rate"] or 0.0
                stage3_latched = r["_stage3_latched_rate"] or 0.0
                stage3_touch_ready = r["_stage3_touch_ready_rate"] or 0.0
                stage4_center_ready = r["_stage4_center_ready_rate"] or 0.0
                stage4_push_ready = r["_stage4_push_ready_rate"] or 0.0
                alignment = r["_mean_alignment"] or 0.0
                pregrasp_alignment = r["_mean_pregrasp_alignment"] or alignment
                insertion_alignment = r["_mean_insertion_alignment"] or alignment
                contact_penalty = r["_mean_target_contact_penalty"] or 0.0
                early_contact_penalty = r["_mean_early_target_contact_penalty"] or 0.0
                center_progress = r["_mean_pregrasp_center_progress"] or 0.0
                insertion_progress = r["_mean_insertion_progress"] or 0.0
                center_push_progress = r["_mean_center_push_progress"] or 0.0
                center_push_overshoot = r["_mean_center_push_overshoot"] or 0.0
                best_center_push_progress = r["_mean_best_center_push_progress"] or center_push_progress
                center_push_improvement = r["_mean_center_push_improvement"] or 0.0
                best_center_distance = r["_mean_best_target_center_distance"]
                target_center_improvement = r["_mean_target_center_improvement"] or 0.0
                target_center_shell_improvement = r["_mean_target_center_shell_improvement"] or 0.0
                center_shortest_path_score = r["_mean_center_shortest_path_score"] or 0.0
                stage4_time_pressure = r["_mean_stage4_time_pressure"] or 0.0
                stage3_time_preserve = r["_mean_stage3_time_preserve"] or 0.0
                terminal_success_quality = r["_mean_terminal_success_quality"] or 0.0
                near_terminal_reward = r["_mean_near_terminal_reward"] or 0.0
                stage_latch_reward = r["_mean_stage_latch_reward"] or 0.0
                progressive_stage_weight = r["_mean_progressive_stage_weight"] or 0.0
                moving_pregrasp_fraction = r["_mean_moving_pregrasp_fraction"] or 0.0
                moving_pregrasp_final = r["_moving_pregrasp_final_rate"] or 0.0
                moving_pregrasp_reward = r["_mean_moving_pregrasp_reward"] or 0.0
                final_insertion_reward = r["_mean_final_insertion_reward"] or 0.0
                line_error = r["_mean_pregrasp_line_error"] or 0.0
                blue_final_center = r["_blue_final_center_ready_rate"] or 0.0
                gripper_roll_alignment = r["_mean_gripper_roll_alignment"]
                gripper_roll_score = 0.0
                if gripper_roll_alignment is not None:
                    gripper_roll_score = max(0.0, min(1.0, 0.5 * (gripper_roll_alignment + 1.0)))
                reward = r["_mean_reward"] or 0.0
                return (
                    -distance
                    -0.25 * target_standoff_error
                    -0.40 * touch_error
                    +0.05 * pregrasp_alignment
                    +0.08 * insertion_alignment
                    +0.25 * stage1_ready
                    +0.10 * stage1_latched
                    +0.25 * entry_success
                    +0.20 * entry_ready
                    +0.20 * entry_reached
                    +0.50 * pregrasp_success
                    +0.35 * pregrasp_hold
                    +0.45 * pregrasp_held
                    +0.55 * stage2_ready
                    +0.15 * stage2_latched
                    +1.50 * stage3_ready
                    +0.20 * stage3_latched
                    +2.50 * stage3_touch_ready
                    +5.00 * stage4_center_ready
                    +1.40 * stage4_push_ready
                    +0.20 * center_progress
                    +0.10 * insertion_progress
                    +0.35 * center_push_progress
                    +0.45 * best_center_push_progress
                    +0.30 * center_push_improvement
                    +0.40 * target_center_improvement
                    +0.25 * target_center_shell_improvement
                    +0.35 * center_shortest_path_score
                    +0.20 * stage3_time_preserve
                    +0.50 * terminal_success_quality
                    +0.40 * near_terminal_reward
                    +0.20 * stage_latch_reward
                    +0.05 * progressive_stage_weight
                    +0.20 * moving_pregrasp_fraction
                    +0.60 * moving_pregrasp_final
                    +0.20 * moving_pregrasp_reward
                    +0.60 * blue_final_center
                    +0.10 * gripper_roll_score
                    +0.80 * final_insertion_reward
                    -0.05 * stage4_time_pressure
                    -0.50 * (best_center_distance if best_center_distance is not None else distance)
                    +10.0 * success
                    -5.0 * contact_penalty
                    -6.0 * early_contact_penalty
                    -3.0 * center_push_overshoot
                    -2.0 * line_error
                    +0.000001 * reward
                )

            best = max(rows_with_alignment, key=balanced_score)
            reason = (
                "best balanced pregrasp/stage progress after iteration "
                f"{min_candidate_iteration} because mature success_rate is below 0.01"
            )
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
                reason = (
                    "lowest mean_pregrasp_distance after iteration "
                    f"{min_candidate_iteration} because success_rate and alignment are below thresholds"
                )
            else:
                reason = (
                    "lowest mean_distance after iteration "
                    f"{min_candidate_iteration} because success_rate and alignment are below thresholds"
                )
    else:
        rows_with_reward = [r for r in candidate_rows if r["_mean_reward"] is not None]
        if rows_with_reward:
            best = max(rows_with_reward, key=lambda r: r["_mean_reward"])
            reason = f"highest mean_reward after iteration {min_candidate_iteration}"
        else:
            # fallback: latest iteration
            best = max(candidate_rows, key=lambda r: r["_iteration"])
            reason = "latest checkpoint fallback"

print("========== BEST MT4 CHECKPOINT ==========")
print("reason        =", reason)
print("checkpoint    =", best.get("checkpoint"))
print("iteration     =", best.get("iteration"))
print("success_rate  =", best.get("success_rate"))
print("stage1_ready  =", best.get("stage1_alignment_ready_rate"))
print("stage1_latch  =", best.get("stage1_latched_rate"))
print("entry_succ    =", best.get("pregrasp_entry_success_rate"))
print("entry_ready   =", best.get("pregrasp_entry_ready_rate"))
print("entry_reached =", best.get("pregrasp_entry_reached_rate"))
print("pregrasp_succ =", best.get("pregrasp_success_rate"))
print("pregrasp_hold =", best.get("pregrasp_hold_ready_rate"))
print("pregrasp_held =", best.get("pregrasp_held_rate"))
print("stage2_pregrasp=", best.get("stage2_pregrasp_ready_rate"))
print("stage2_latch  =", best.get("stage2_latched_rate"))
print("stage2_ready  =", best.get("stage2_alignment_ready_rate"))
print("stage3_ready  =", best.get("stage3_insertion_ready_rate"))
print("stage3_latch  =", best.get("stage3_latched_rate"))
print("stage3_touch  =", best.get("stage3_touch_ready_rate"))
print("stage4_center =", best.get("stage4_center_ready_rate"))
print("blue_final    =", best.get("blue_final_center_ready_rate"))
print("stage4_push   =", best.get("stage4_push_ready_rate"))
print("entry_dist    =", best.get("mean_pregrasp_entry_distance"))
print("pregrasp_dist =", best.get("mean_pregrasp_distance"))
print("touch_error   =", best.get("mean_touch_error"))
print("mean_distance =", best.get("mean_distance"))
print("mean_alignment=", best.get("mean_alignment"))
print("pregrasp_align=", best.get("mean_pregrasp_alignment"))
print("insert_align  =", best.get("mean_insertion_alignment"))
print("contact_penalty=", best.get("mean_target_contact_penalty"))
print("early_contact =", best.get("mean_early_target_contact_penalty"))
print("center_prog  =", best.get("mean_pregrasp_center_progress"))
print("push_prog    =", best.get("mean_center_push_progress"))
print("push_overshot=", best.get("mean_center_push_overshoot"))
print("best_push    =", best.get("mean_best_center_push_progress"))
print("push_impr    =", best.get("mean_center_push_improvement"))
print("best_center  =", best.get("mean_best_target_center_distance"))
print("center_impr  =", best.get("mean_target_center_improvement"))
print("shell_impr   =", best.get("mean_target_center_shell_improvement"))
print("shortest_path=", best.get("mean_center_shortest_path_score"))
print("stage4_time  =", best.get("mean_stage4_time_pressure"))
print("stage3_time  =", best.get("mean_stage3_time_preserve"))
print("term_quality =", best.get("mean_terminal_success_quality"))
print("near_terminal=", best.get("mean_near_terminal_reward"))
print("stage_latch =", best.get("mean_stage_latch_reward"))
print("progressive =", best.get("mean_progressive_stage_weight"))
print("moving_frac =", best.get("mean_moving_pregrasp_fraction"))
print("moving_final=", best.get("moving_pregrasp_final_rate"))
print("moving_step =", best.get("moving_pregrasp_step_ready_rate"))
print("moving_hold =", best.get("mean_moving_pregrasp_hold_progress"))
print("moving_reward=", best.get("mean_moving_pregrasp_reward"))
print("moving_funnel=", best.get("mean_moving_pregrasp_funnel_reward"))
print("moving_exp   =", best.get("mean_moving_pregrasp_exp_reward"))
print("moving_shell =", best.get("mean_moving_pregrasp_shell_improvement"))
print("moving_best_d=", best.get("mean_best_moving_pregrasp_distance"))
print("final_insert=", best.get("mean_final_insertion_reward"))
print("line_error   =", best.get("mean_pregrasp_line_error"))
print("gripper_roll =", best.get("mean_gripper_roll_alignment"))
print("min_distance  =", best.get("min_distance"))
print("mean_reward   =", best.get("mean_reward"))
print("path          =", best.get("path"))

OUT_PATH.write_text(best.get("path", "") + "\n", encoding="utf-8")
print()
print("[OK] wrote", OUT_PATH)
