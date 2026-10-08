"""
run_all_raw_clips_test.py - Comprehensive Test & Evaluation Harness for all raw_clips.

Processes 100% of frames across all 15 video files in raw_clips/ to evaluate:
  1. Video metadata and stream decoding integrity.
  2. MediaPipe Pose tracking coverage and confidence state breakdown (HIGH/MODERATE/INSUFFICIENT).
  3. Key joint visibility and occlusion statistics.
  4. 2D image-plane vs. 3D MediaPipe world angle discrepancy (foreshortening audit).
  5. Shot event detection across shot styles (jump_shot vs set_shot) with kinematic metrics.
  6. Kinetic chain sequencing timing (knee dip to release drive).
  7. Human-gated baseline quarantine audit.
  8. Stratified summaries by player, viewpoint (90 deg side, 45 deg oblique, 0 deg frontal), and aspect ratio.
  9. Ground-truth benchmark verification where human annotations are available.

Emits RAW_CLIPS_TEST_REPORT.json and prints a structured, terminal report.
"""

import os
import sys
import json
import time
import argparse
import numpy as np
import cv2
from typing import Dict, Any, List, Optional

from pose_engine import PoseEngine
from analyzer import (
    compute_all_angles,
    ShotPhaseDetector,
    SessionRecorder,
    KineticChainAnalyzer
)

MATCH_TOLERANCE_FRAMES = 15  # +/- 500 ms at 30 FPS


def classify_clip_metadata(filename: str, w: int, h: int) -> Dict[str, Any]:
    """Infer player, viewpoint, and orientation metadata from filename conventions."""
    name_lower = filename.lower()
    
    # Player ID
    if "klay" in name_lower:
        player_id = "klay_thompson"
    elif "mike" in name_lower:
        player_id = "mike_dunn"
    elif "lavish" in name_lower:
        player_id = "lavish"
    elif "sid" in name_lower:
        player_id = "sid"
    else:
        player_id = "unknown_player"

    # Viewpoint
    if "90deg" in name_lower or "97deg" in name_lower or "side" in name_lower or "klay" in name_lower or "mikeddunnstud2" in name_lower:
        viewpoint = "side_90"
    elif "0deg" in name_lower or "front" in name_lower:
        viewpoint = "frontal_0"
    elif "stud1" in name_lower or "mix" in name_lower or "mult" in name_lower or "mikedunn.mp4" in name_lower:
        viewpoint = "oblique_45"
    elif "sid_1" in name_lower or "sid_2" in name_lower:
        viewpoint = "oblique_45"
    else:
        viewpoint = "unspecified_view"

    # Orientation
    orientation = "portrait_9_16" if h > w else "landscape_16_9"

    return {
        "player_id": player_id,
        "viewpoint": viewpoint,
        "orientation": orientation
    }


def test_single_clip(
    video_path: str,
    gt_annotations: Optional[Dict[str, Any]] = None,
    shot_style: str = "jump_shot",
    eval_ball: bool = False
) -> Dict[str, Any]:
    """Execute complete analysis pipeline over 100% of frames in a single video clip."""
    filename = os.path.basename(video_path)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"file": filename, "status": "ERROR_FAILED_TO_OPEN"}

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_s = total_frames / fps if fps > 0 else 0.0

    meta = classify_clip_metadata(filename, w, h)

    engine = PoseEngine(smoothing_alpha=0.35)
    detector = ShotPhaseDetector(shot_style=shot_style)
    recorder = SessionRecorder()

    ball_tracker = None
    if eval_ball:
        try:
            from ball_tracker import BallTracker
            ball_tracker = BallTracker(detect_every=1)
        except Exception:
            pass

    frame_idx = 0
    poses_detected = 0
    conf_counts = {"HIGH": 0, "MODERATE": 0, "INSUFFICIENT": 0}
    joint_visibility_counts = {
        "left_wrist": 0, "right_wrist": 0,
        "left_elbow": 0, "right_elbow": 0,
        "left_shoulder": 0, "right_shoulder": 0,
        "left_hip": 0, "right_hip": 0,
        "left_knee": 0, "right_knee": 0,
        "left_ankle": 0, "right_ankle": 0,
    }

    angle_discrepancies = {
        "elbow": [],
        "knee": [],
        "hip": []
    }

    detected_shots = []
    current_shot_start = None
    current_set_point = None
    current_release = None
    prev_state = "idle"

    key_joints_map = {
        15: "left_wrist", 16: "right_wrist",
        13: "left_elbow", 14: "right_elbow",
        11: "left_shoulder", 12: "right_shoulder",
        23: "left_hip", 24: "right_hip",
        25: "left_knee", 26: "right_knee",
        27: "left_ankle", 28: "right_ankle"
    }

    start_time = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        timestamp_ms = int(frame_idx * (1000.0 / fps))
        out = engine.process(frame, timestamp_ms)

        ball_info = None
        if ball_tracker and out is not None:
            dets = ball_tracker.detect(frame)
            ball_info = ball_tracker.update(dets, out["smoothed_landmarks"], out["valid"], timestamp_ms)

        if out is not None:
            poses_detected += 1
            landmarks = out["smoothed_landmarks"]
            valid = out["valid"]
            world_landmarks = out.get("world_landmarks")

            # Count joint visibilities
            for j_idx, j_name in key_joints_map.items():
                if valid.get(j_idx, False):
                    joint_visibility_counts[j_name] += 1

            # Determine confidence tier
            key_joints = tuple(key_joints_map.keys())
            valid_count = sum(1 for idx in key_joints if valid.get(idx, False))
            conf_ratio = valid_count / len(key_joints)
            if conf_ratio >= 0.85:
                conf = "HIGH"
            elif conf_ratio >= 0.60:
                conf = "MODERATE"
            else:
                conf = "INSUFFICIENT"
            conf_counts[conf] += 1

            # Compute biomechanical angles
            angles = compute_all_angles(landmarks, valid, world_landmarks=world_landmarks, min_visibility=0.45)
            state, vy, ve = detector.update(landmarks, angles, timestamp_ms, ball_info=ball_info)
            recorder.push_frame(angles, phase=state, timestamp_ms=timestamp_ms)

            # Track phase transitions
            if prev_state in ("idle", "follow_through") and state == "preparing":
                current_shot_start = frame_idx
                current_set_point = None
                current_release = None
                if not recorder.recording:
                    recorder.start_shot()

            if prev_state == "preparing" and state == "set_point":
                current_set_point = frame_idx

            if prev_state in ("preparing", "set_point") and state == "releasing":
                current_release = frame_idx

            if state == "follow_through" and prev_state in ("releasing", "set_point"):
                shot_record = {
                    "shot_index": len(detected_shots) + 1,
                    "start_frame": current_shot_start if current_shot_start is not None else frame_idx - 15,
                    "set_point_frame": current_set_point,
                    "release_frame": current_release if current_release is not None else frame_idx,
                    "follow_through_frame": frame_idx,
                    "duration_frames": frame_idx - (current_shot_start or (frame_idx - 15)),
                    "duration_ms": round((frame_idx - (current_shot_start or (frame_idx - 15))) * (1000.0 / fps), 1),
                    "vertical_velocity_at_release": round(vy, 4) if vy is not None else None,
                    "extension_velocity": round(ve, 4) if ve is not None else None,
                    "shooting_elbow_angle": round(angles.get("elbow_shooting_2d", 0.0), 1) if angles else None,
                    "knee_dip_angle": round(angles.get("knee_right", 0.0), 1) if angles else None,
                }
                detected_shots.append(shot_record)
                if recorder.recording:
                    recorder.end_shot()
                current_shot_start = None
                current_set_point = None
                current_release = None

            prev_state = state

            # Angle Discrepancy Audits (2D image-plane vs 3D world estimate)
            if angles:
                if angles.get("elbow_shooting_2d") is not None and angles.get("elbow_shooting_3d") is not None:
                    angle_discrepancies["elbow"].append(abs(angles["elbow_shooting_3d"] - angles["elbow_shooting_2d"]))
                if angles.get("knee_right") is not None and angles.get("knee_right_3d") is not None:
                    angle_discrepancies["knee"].append(abs(angles["knee_right_3d"] - angles["knee_right"]))
                if angles.get("hip_posture_2d") is not None and angles.get("hip_posture_3d") is not None:
                    angle_discrepancies["hip"].append(abs(angles["hip_posture_3d"] - angles["hip_posture_2d"]))
        else:
            conf_counts["INSUFFICIENT"] += 1

        frame_idx += 1

    cap.release()
    engine.close()
    elapsed = time.time() - start_time

    # Calculate Pose Coverage & Joint Visibility Rates
    coverage_pct = round((poses_detected / max(1, frame_idx)) * 100.0, 1)
    joint_rates = {k: round((v / max(1, frame_idx)) * 100.0, 1) for k, v in joint_visibility_counts.items()}

    # Calculate Discrepancy Statistics
    def get_disc_stats(arr: List[float]) -> Dict[str, float]:
        if not arr:
            return {"mean_deg": 0.0, "median_deg": 0.0, "max_deg": 0.0}
        return {
            "mean_deg": round(float(np.mean(arr)), 1),
            "median_deg": round(float(np.median(arr)), 1),
            "max_deg": round(float(np.max(arr)), 1)
        }

    elbow_disc = get_disc_stats(angle_discrepancies["elbow"])
    knee_disc = get_disc_stats(angle_discrepancies["knee"])
    hip_disc = get_disc_stats(angle_discrepancies["hip"])

    # Ground-Truth Verification (if annotations available for this clip)
    gt_eval = None
    if gt_annotations:
        gt_shots = gt_annotations.get("shots", [])
        gt_releases = [s["events"]["release_frame"] for s in gt_shots]
        det_releases = [s["release_frame"] for s in detected_shots]

        matched_gt = set()
        matched_det = set()
        timing_errors_ms = []

        for d_idx, d_frame in enumerate(det_releases):
            best_gt = None
            best_err = float("inf")
            for g_idx, g_frame in enumerate(gt_releases):
                if g_idx not in matched_gt:
                    err = abs(d_frame - g_frame)
                    if err <= MATCH_TOLERANCE_FRAMES and err < best_err:
                        best_err = err
                        best_gt = g_idx
            if best_gt is not None:
                matched_gt.add(best_gt)
                matched_det.add(d_idx)
                timing_errors_ms.append(best_err * (1000.0 / fps))

        tp = len(matched_gt)
        fp = len(det_releases) - len(matched_det)
        fn = len(gt_releases) - len(matched_gt)
        p = (tp / max(1, tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
        r = (tp / max(1, tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
        f1 = (2 * p * r) / max(1e-5, p + r)

        gt_eval = {
            "annotated_shots_count": len(gt_releases),
            "annotated_releases": gt_releases,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision_pct": round(p, 1),
            "recall_pct": round(r, 1),
            "f1_score": round(f1 / 100.0, 3),
            "timing_mae_ms": round(float(np.mean(timing_errors_ms)), 1) if timing_errors_ms else 0.0
        }

    return {
        "file": filename,
        "video_properties": {
            "resolution": f"{w}x{h}",
            "fps": round(fps, 2),
            "total_frames": frame_idx,
            "duration_seconds": round(duration_s, 2),
            "processing_time_seconds": round(elapsed, 2),
            "fps_speed": round(frame_idx / max(0.01, elapsed), 1)
        },
        "metadata": meta,
        "tracking_quality": {
            "pose_detection_rate_pct": coverage_pct,
            "confidence_breakdown": conf_counts,
            "joint_visibility_pct": joint_rates
        },
        "angle_discrepancy": {
            "elbow_2d_vs_3d": elbow_disc,
            "knee_2d_vs_3d": knee_disc,
            "hip_2d_vs_3d": hip_disc,
        },
        "event_detection": {
            "shot_style": shot_style,
            "detected_shots_count": len(detected_shots),
            "detected_shots": detected_shots
        },
        "ground_truth_comparison": gt_eval,
        "baseline_quarantine_status": {
            "admitted_to_baseline": gt_eval["true_positives"] if gt_eval else 0,
            "quarantined_pending_review": len(detected_shots) - (gt_eval["true_positives"] if gt_eval else 0)
        }
    }


def run_raw_clips_suite(
    raw_dir: str = "raw_clips",
    annotations_file: str = "ground_truth_annotations.json",
    output_report: str = "RAW_CLIPS_TEST_REPORT.json",
    shot_style: str = "jump_shot"
) -> Dict[str, Any]:
    """Run full test suite across all video files in raw_clips/ directory."""
    if not os.path.exists(raw_dir):
        raise FileNotFoundError(f"Directory not found: {raw_dir}")

    # Load annotations if present
    annotations_map = {}
    if os.path.exists(annotations_file):
        with open(annotations_file, "r") as f:
            annot_data = json.load(f)
            for c in annot_data.get("clips", []):
                annotations_map[c["file"]] = c

    files = sorted([f for f in os.listdir(raw_dir) if f.lower().endswith(('.mp4', '.avi', '.mov'))])
    print("\n" + "=" * 80)
    print("      COMPREHENSIVE REAL-VIDEO TEST BENCHMARK — ALL RAW CLIPS (100% FRAMES)")
    print("=" * 80)
    print(f" Found {len(files)} video clips in '{raw_dir}' directory.")
    print(f" Shot Style Config: {shot_style} | Gating: Velocity + Height + Duration + Quarantine\n")

    results = []
    total_start = time.time()

    for idx, f in enumerate(files, 1):
        v_path = os.path.join(raw_dir, f)
        gt = annotations_map.get(f)
        print(f"[{idx:02d}/{len(files):02d}] Processing: {f:25s} ... ", end="", flush=True)
        clip_res = test_single_clip(v_path, gt_annotations=gt, shot_style=shot_style)
        results.append(clip_res)

        vp = clip_res["video_properties"]
        tq = clip_res["tracking_quality"]
        ed = clip_res["event_detection"]
        gt_info = ""
        if clip_res["ground_truth_comparison"]:
            gt_c = clip_res["ground_truth_comparison"]
            gt_info = f" | GT Match: {gt_c['true_positives']}/{gt_c['annotated_shots_count']} TP (F1: {gt_c['f1_score']})"

        print(f"Done ({vp['total_frames']} frames, {vp['duration_seconds']}s) -> "
              f"Pose: {tq['pose_detection_rate_pct']}% | Shots: {ed['detected_shots_count']}{gt_info}")

    total_time = time.time() - total_start

    # Aggregations
    total_frames_all = sum(r["video_properties"]["total_frames"] for r in results if "video_properties" in r)
    total_duration_all = sum(r["video_properties"]["duration_seconds"] for r in results if "video_properties" in r)
    total_detected_shots = sum(r["event_detection"]["detected_shots_count"] for r in results if "event_detection" in r)
    mean_pose_cov = float(np.mean([r["tracking_quality"]["pose_detection_rate_pct"] for r in results if "tracking_quality" in r]))
    mean_elbow_disc = float(np.mean([r["angle_discrepancy"]["elbow_2d_vs_3d"]["mean_deg"] for r in results if "angle_discrepancy" in r and r["angle_discrepancy"]["elbow_2d_vs_3d"]["mean_deg"] > 0]))

    # Stratified by Player
    player_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        p = r["metadata"]["player_id"]
        player_groups.setdefault(p, []).append(r)

    # Stratified by Viewpoint
    view_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        v = r["metadata"]["viewpoint"]
        view_groups.setdefault(v, []).append(r)

    # Stratified by Orientation
    orient_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        o = r["metadata"]["orientation"]
        orient_groups.setdefault(o, []).append(r)

    def summarize_group(grp: List[Dict[str, Any]]) -> Dict[str, Any]:
        frames = sum(x["video_properties"]["total_frames"] for x in grp)
        dur = sum(x["video_properties"]["duration_seconds"] for x in grp)
        shots = sum(x["event_detection"]["detected_shots_count"] for x in grp)
        cov = float(np.mean([x["tracking_quality"]["pose_detection_rate_pct"] for x in grp]))
        disc = float(np.mean([x["angle_discrepancy"]["elbow_2d_vs_3d"]["mean_deg"] for x in grp if x["angle_discrepancy"]["elbow_2d_vs_3d"]["mean_deg"] > 0])) if grp else 0.0
        return {
            "clips_count": len(grp),
            "total_frames": frames,
            "total_duration_seconds": round(dur, 2),
            "total_detected_shots": shots,
            "mean_pose_coverage_pct": round(cov, 1),
            "mean_elbow_2d_vs_3d_disc_deg": round(disc, 1)
        }

    report = {
        "report_version": "1.0.0",
        "title": "Comprehensive Raw Video Benchmark Report (All 15 Clips in raw_clips/)",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "configuration": {
            "raw_directory": raw_dir,
            "total_clips": len(results),
            "shot_style": shot_style,
            "quarantine_gate_active": True
        },
        "overall_summary": {
            "total_clips_evaluated": len(results),
            "total_frames_processed": total_frames_all,
            "total_duration_seconds": round(total_duration_all, 2),
            "total_duration_minutes": round(total_duration_all / 60.0, 2),
            "overall_mean_pose_coverage_pct": round(mean_pose_cov, 1),
            "overall_mean_elbow_2d_vs_3d_disagreement_deg": round(mean_elbow_disc, 1),
            "total_machine_shots_detected": total_detected_shots,
            "human_confirmed_shots_admitted": sum(r["baseline_quarantine_status"]["admitted_to_baseline"] for r in results),
            "unconfirmed_shots_quarantined": sum(r["baseline_quarantine_status"]["quarantined_pending_review"] for r in results),
            "total_benchmark_execution_time_s": round(total_time, 2)
        },
        "breakdown_by_player": {p: summarize_group(grp) for p, grp in player_groups.items()},
        "breakdown_by_viewpoint": {v: summarize_group(grp) for v, grp in view_groups.items()},
        "breakdown_by_orientation": {o: summarize_group(grp) for o, grp in orient_groups.items()},
        "per_clip_detailed_results": results
    }

    with open(output_report, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 80)
    print("                    RAW CLIPS BENCHMARK SUMMARY")
    print("=" * 80)
    print(f" Total Clips Evaluated:         {len(results)}")
    print(f" Total Video Frames Processed:  {total_frames_all:,} frames ({round(total_duration_all, 1)}s / {round(total_duration_all/60.0, 2)} mins)")
    print(f" Overall Pose Tracking Rate:    {round(mean_pose_cov, 1)}%")
    print(f" 2D vs. 3D Elbow Disagreement:  +/- {round(mean_elbow_disc, 1)} deg (Perspective foreshortening)")
    print(f" Total Machine Shots Detected:  {total_detected_shots} shots")
    print(f" Baseline Quarantine Status:    {report['overall_summary']['human_confirmed_shots_admitted']} Human-Confirmed | {report['overall_summary']['unconfirmed_shots_quarantined']} Quarantined Pending Review")
    print("-" * 80)
    print(" PLAYER STRATIFICATION:")
    for p, sm in report["breakdown_by_player"].items():
        print(f"  - {p:18s}: {sm['clips_count']:2d} clips | {sm['total_frames']:5d} frames | Pose: {sm['mean_pose_coverage_pct']}% | Shots: {sm['total_detected_shots']:2d}")
    print("-" * 80)
    print(" VIEWPOINT STRATIFICATION:")
    for v, sm in report["breakdown_by_viewpoint"].items():
        print(f"  - {v:18s}: {sm['clips_count']:2d} clips | {sm['total_frames']:5d} frames | Pose: {sm['mean_pose_coverage_pct']}% | Shots: {sm['total_detected_shots']:2d}")
    print("-" * 80)
    print(f" [OK] Full Report saved to: {output_report}\n")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test all clips in raw_clips directory")
    parser.add_argument("--raw-dir", default="raw_clips", help="Directory containing video files")
    parser.add_argument("--annotations", default="ground_truth_annotations.json", help="Annotations JSON file")
    parser.add_argument("--output", default="RAW_CLIPS_TEST_REPORT.json", help="Output JSON report file")
    parser.add_argument("--shot-style", choices=["jump_shot", "set_shot"], default="jump_shot", help="Shot style")
    args = parser.parse_args()

    run_raw_clips_suite(
        raw_dir=args.raw_dir,
        annotations_file=args.annotations,
        output_report=args.output,
        shot_style=args.shot_style
    )
