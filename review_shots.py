"""
review_shots.py - Personal Shot Lab Post-Session Shot Review and Correction Tool.

Allows players and coaches to inspect detected shots, scrub keyframe boundaries,
correct make/miss/unknown outcome labels, and add review notes.
Strictly preserves machine-detected predictions alongside human annotations.
"""

from __future__ import annotations
import argparse
import sys
from typing import Optional, List, Dict, Any
from shot_lab_db import ShotLabDB

def print_shot_table(shots: List[Dict[str, Any]]) -> None:
    """Print tabular overview of shots with style and quarantine review status."""
    if not shots:
        print("\n[INFO] No shots found matching criteria.")
        return

    print("\n" + "=" * 115)
    print(f"{'Shot ID':<12} | {'Style':<10} | {'View':<10} | {'Dip->Rel':<14} | {'3D Elbow':<10} | {'Seq Lag':<10} | {'Conf':<11} | {'Outcome':<8} | {'Status':<12}")
    print("-" * 115)
    for s in shots:
        dip = s.get("annotated_dip_frame") or s.get("machine_dip_frame") or "-"
        rel = s.get("annotated_release_frame") or s.get("machine_release_frame") or "-"
        span = f"F{dip}->F{rel}"
        elbow = f"{s.get('elbow_angle_release_3d', 0):.1f} deg" if s.get('elbow_angle_release_3d') is not None else "N/A"
        lag = f"{s.get('sequence_lag_ms', 0):.1f} ms" if s.get('sequence_lag_ms') is not None else "N/A"
        conf = s.get("tracking_confidence", "UNKNOWN")
        outcome = (s.get("outcome") or "unknown").upper()
        status = (s.get("review_status") or "quarantined").upper()
        style = s.get("shot_style", "jump_shot")
        print(f"{s['shot_id']:<12} | {style:<10} | {s.get('camera_view', '-'):<10} | {span:<14} | {elbow:<10} | {lag:<10} | {conf:<11} | {outcome:<8} | {status:<12}")
    print("=" * 115 + "\n")

def print_shot_detail(s: Dict[str, Any]) -> None:
    """Print full provenance and biomechanics detail for a shot."""
    print("\n" + "=" * 65)
    print(f" SHOT DETAIL: {s['shot_id']} (Player: {s.get('player_id')})")
    print("=" * 65)
    print(f" Session ID:          {s.get('session_id')}")
    print(f" Camera View:         {s.get('camera_view')} | Shot Type: {s.get('shot_type')} | Style: {s.get('shot_style', 'jump_shot')}")
    print(f" Review Status:       {(s.get('review_status') or 'quarantined').upper()}")
    print(f" Tracking Validity:   {s.get('tracking_confidence')} (Valid frames: {s.get('valid_frame_ratio', 1.0)*100:.1f}%)")
    print(f" Outcome Status:      {s.get('outcome', 'unknown').upper()} (Source: {s.get('outcome_source')})")
    if s.get("review_notes"):
        print(f" Review Notes:        {s.get('review_notes')}")
    print("-" * 65)
    print(" EVENT BOUNDARIES (Machine vs. Annotated Human Review):")
    print(f"   Start Frame:       Machine={s.get('machine_start_frame')} | Annotated={s.get('annotated_start_frame')}")
    print(f"   Dip Frame:         Machine={s.get('machine_dip_frame')} | Annotated={s.get('annotated_dip_frame')}")
    print(f"   Set Frame:         Machine={s.get('machine_set_frame')} | Annotated={s.get('annotated_set_frame')}")
    print(f"   Release Frame:     Machine={s.get('machine_release_frame')} | Annotated={s.get('annotated_release_frame')}")
    print(f"   End Frame:         Machine={s.get('machine_end_frame')} | Annotated={s.get('annotated_end_frame')}")
    print("-" * 65)
    print(" BIOMECHANICAL MEASUREMENTS:")
    print(f"   3D Elbow Extension (World): {s.get('elbow_angle_release_3d')} deg")
    print(f"   2D Elbow Extension (Image): {s.get('elbow_angle_release_2d')} deg")
    print(f"   2D/3D Foreshortening Discrepancy: {s.get('foreshortening_discrepancy_deg')} deg")
    print(f"   Knee Angle at Dip (3D):     {s.get('knee_angle_dip_3d')} deg")
    print(f"   Kinetic Sequence Lag:       {s.get('sequence_lag_ms')} ms (+/- 33.3 ms quantization)")
    print(f"   Torso Sway / Tilt:          {s.get('torso_sway_deg')} deg")
    print("=" * 65 + "\n")

def interactive_review_loop(
    db: ShotLabDB,
    player_id: Optional[str] = None,
    session_id: Optional[str] = None,
    review_status_filter: Optional[str] = None,
    shot_style_filter: Optional[str] = None
):
    """Interactive CLI menu for explicit per-shot review and correction."""
    current_status_filter = review_status_filter
    while True:
        shots = db.get_shots(
            player_id=player_id,
            session_id=session_id,
            shot_style=shot_style_filter,
            review_status=current_status_filter,
            min_confidence=None
        )
        print_shot_table(shots)
        print("OPTIONS:")
        print("  [1-N] Select Shot ID to inspect/review")
        print("  [T] Toggle Quarantine Filter (All vs Quarantined-Only)")
        print("  [B] Compute & Display Matched Baseline")
        print("  [Q] Quit Review Tool")
        choice = input("\nEnter selection: ").strip().lower()

        if choice in ("q", "quit", "exit"):
            print("Exiting review tool.")
            break
        elif choice == "t":
            current_status_filter = None if current_status_filter == "quarantined" else "quarantined"
            filter_label = "QUARANTINED ONLY" if current_status_filter else "ALL SHOTS"
            print(f"[FILTER] View toggled to: {filter_label}")
        elif choice == "b":
            from baseline_engine import BaselineEngine
            from coach_engine import CoachEngine
            b_engine = BaselineEngine(db)
            c_engine = CoachEngine(db)
            pid = player_id or "default_player"
            style = shot_style_filter or "jump_shot"
            res = b_engine.compute_baseline(pid, shot_style=style)
            if res["status"] == "INSUFFICIENT_SAMPLE":
                print(f"\n[BASELINE STATUS] {res['message']}\n")
            else:
                print("\n" + "=" * 60)
                print(f" PERSONAL BASELINE: {pid} (Style: {style})")
                print("=" * 60)
                for stmt in res.get("descriptive_associations", []):
                    print(f" - {stmt}")
                cue = c_engine.generate_primary_cue(res, save_to_db=False)
                print("\n PRIMARY COACHING CUE:")
                print(f"  Title: {cue['cue_title']}")
                print(f"  Evidence: {cue['biomechanical_evidence']}")
                print(f"  Recommended Drill: {cue['recommended_drill']} ({cue.get('drill_reps')} reps)")
                print("=" * 60 + "\n")
        else:
            target_shot = None
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(shots):
                    target_shot = shots[idx]
            else:
                target_shot = db.get_shot(choice)

            if not target_shot:
                print(f"[ERROR] Invalid selection '{choice}'.")
                continue

            # Shot sub-menu
            print_shot_detail(target_shot)
            print("ACTION FOR THIS SHOT (Explicit Per-Shot Review):")
            print("  [A] APPROVE shot for baseline admission (Confirms keyframes & boundaries)")
            print("  [M] Mark as MAKE (manual review)")
            print("  [X] Mark as MISS (manual review)")
            print("  [U] Mark as UNKNOWN (manual review)")
            print("  [D] DISCARD / Flag shot (Exclude from baseline)")
            print("  [E] Edit Release Frame Boundary")
            print("  [F] Edit Dip Frame Boundary")
            print("  [C] Cancel / Return to list")
            act = input("Action: ").strip().lower()

            if act == "a":
                db.update_shot_annotation(
                    target_shot["shot_id"],
                    review_status="approved",
                    outcome_source="manual_review",
                    review_notes="Approved via explicit per-shot review"
                )
                print(f"[SUCCESS] Shot {target_shot['shot_id']} APPROVED for baseline inclusion.")
            elif act == "m":
                db.update_shot_annotation(target_shot["shot_id"], outcome="make", outcome_source="manual_review")
                print("[SUCCESS] Shot marked as MAKE.")
            elif act == "x":
                db.update_shot_annotation(target_shot["shot_id"], outcome="miss", outcome_source="manual_review")
                print("[SUCCESS] Shot marked as MISS.")
            elif act == "u":
                db.update_shot_annotation(target_shot["shot_id"], outcome="unknown", outcome_source="manual_review")
                print("[SUCCESS] Shot marked as UNKNOWN.")
            elif act == "d":
                db.update_shot_annotation(
                    target_shot["shot_id"],
                    review_status="discarded",
                    review_notes="Discarded during explicit review"
                )
                print(f"[SUCCESS] Shot {target_shot['shot_id']} DISCARDED.")
            elif act == "e":
                new_f = input("Enter corrected release frame number: ").strip()
                if new_f.isdigit():
                    db.update_shot_annotation(target_shot["shot_id"], annotated_boundaries={"release_frame": int(new_f)})
                    print(f"[SUCCESS] Release frame updated to {new_f}.")
            elif act == "f":
                new_f = input("Enter corrected dip frame number: ").strip()
                if new_f.isdigit():
                    db.update_shot_annotation(target_shot["shot_id"], annotated_boundaries={"dip_frame": int(new_f)})
                    print(f"[SUCCESS] Dip frame updated to {new_f}.")

def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Personal Shot Lab Review & Boundary Correction Tool")
    parser.add_argument("--db", default="shot_lab.db", help="Path to SQLite database")
    parser.add_argument("--session", default=None, help="Filter by session ID")
    parser.add_argument("--player", default=None, help="Filter by player ID")
    parser.add_argument("--shot-style", choices=["jump_shot", "set_shot"], default=None, help="Filter by shot style")
    parser.add_argument("--quarantined", action="store_true", help="Filter to only quarantined shots needing review")
    parser.add_argument("--approved", action="store_true", help="Filter to only approved shots")
    parser.add_argument("--latest", action="store_true", help="Filter by most recent session")
    parser.add_argument("--list", action="store_true", help="List all shots in tabular view")
    parser.add_argument("--inspect", default=None, help="Inspect specific shot ID")
    parser.add_argument("--approve", default=None, metavar="SHOT_ID", help="Explicitly approve a single shot for baseline admission")
    parser.add_argument("--discard", default=None, metavar="SHOT_ID", help="Explicitly discard a single shot")
    parser.add_argument("--set-outcome", nargs=2, metavar=("SHOT_ID", "OUTCOME"), help="Set outcome (make/miss/unknown)")
    parser.add_argument("--set-release-frame", nargs=2, metavar=("SHOT_ID", "FRAME"), help="Set corrected release frame")
    parser.add_argument("--set-dip-frame", nargs=2, metavar=("SHOT_ID", "FRAME"), help="Set corrected dip frame")
    parser.add_argument("--batch-approve", action="store_true", help="Batch approve shots (REJECTED)")
    parser.add_argument("--notes", default=None, help="Review notes for annotation")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive review menu")

    args = parser.parse_args(argv)

    # Reject blind batch-approval to protect baseline integrity (Decision 1)
    if args.batch_approve:
        print("[ERROR] Batch approval is rejected to maintain baseline integrity. Please review each shot individually before approving.", file=sys.stderr)
        sys.exit(1)

    db = ShotLabDB(args.db)

    session_id = args.session
    if args.latest:
        with db._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT session_id FROM sessions ORDER BY created_at DESC LIMIT 1")
            row = c.fetchone()
            if row:
                session_id = row[0]
                print(f"[INFO] Using latest session: {session_id}")

    if args.inspect:
        shot = db.get_shot(args.inspect)
        if shot:
            print_shot_detail(shot)
        else:
            print(f"[ERROR] Shot '{args.inspect}' not found.")
        return

    if args.approve:
        shot = db.get_shot(args.approve)
        if not shot:
            print(f"[ERROR] Shot '{args.approve}' not found.")
            return
        db.update_shot_annotation(
            args.approve,
            review_status="approved",
            outcome_source="manual_review",
            review_notes=args.notes or "Explicitly approved via review_shots CLI"
        )
        print(f"[SUCCESS] Shot {args.approve} explicitly APPROVED for baseline admission.")
        return

    if args.discard:
        shot = db.get_shot(args.discard)
        if not shot:
            print(f"[ERROR] Shot '{args.discard}' not found.")
            return
        db.update_shot_annotation(
            args.discard,
            review_status="discarded",
            review_notes=args.notes or "Explicitly discarded via review_shots CLI"
        )
        print(f"[SUCCESS] Shot {args.discard} explicitly DISCARDED.")
        return

    if args.set_outcome:
        s_id, outcome = args.set_outcome
        if outcome.lower() in ("make", "miss", "unknown"):
            db.update_shot_annotation(s_id, outcome=outcome, outcome_source="manual_review", review_notes=args.notes)
            print(f"[SUCCESS] Shot {s_id} outcome updated to {outcome.upper()}.")
        else:
            print("[ERROR] Outcome must be one of: make, miss, unknown")
        return

    if args.set_release_frame:
        s_id, frame_str = args.set_release_frame
        if frame_str.isdigit():
            db.update_shot_annotation(s_id, annotated_boundaries={"release_frame": int(frame_str)}, review_notes=args.notes)
            print(f"[SUCCESS] Shot {s_id} annotated release frame set to {frame_str}.")
        else:
            print("[ERROR] Frame must be an integer.")
        return

    if args.set_dip_frame:
        s_id, frame_str = args.set_dip_frame
        if frame_str.isdigit():
            db.update_shot_annotation(s_id, annotated_boundaries={"dip_frame": int(frame_str)}, review_notes=args.notes)
            print(f"[SUCCESS] Shot {s_id} annotated dip frame set to {frame_str}.")
        else:
            print("[ERROR] Frame must be an integer.")
        return

    status_filter = None
    if args.quarantined:
        status_filter = "quarantined"
    elif args.approved:
        status_filter = "approved"

    if args.list:
        shots = db.get_shots(
            player_id=args.player,
            session_id=session_id,
            shot_style=args.shot_style,
            review_status=status_filter,
            min_confidence=None
        )
        print_shot_table(shots)
        return

    # Default to interactive if no specific action specified
    interactive_review_loop(
        db,
        player_id=args.player,
        session_id=session_id,
        review_status_filter=status_filter,
        shot_style_filter=args.shot_style
    )

if __name__ == "__main__":
    main()

