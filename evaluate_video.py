"""
Real-Video Evaluation & Disagreement Benchmark Harness
======================================================
Processes recorded video clips (e.g. klay_vid.mp4) to measure:
1. Frame-by-frame pose tracking and confidence breakdown (HIGH / MODERATE / INSUFFICIENT).
2. Detected shot lifecycle events (dip, release, follow-through).
3. 2D image-space vs. 3D model-inferred world-space angle disagreement.
   (Explicitly documented as estimate-to-estimate disagreement, not ground-truth error).
4. Emits a versioned, reproducible JSON report.

Usage:
    python evaluate_video.py [--video klay_vid.mp4] [--output KLAY_EVAL_REPORT.json]
"""

import os
import sys
import json
import argparse
import numpy as np
import cv2

from pose_engine import PoseEngine
from analyzer import (
    compute_all_angles,
    shooting_side,
    ShotPhaseDetector,
    SessionRecorder,
    KineticChainAnalyzer,
    interpolate_kinematic_series
)
from pro_comparator import ProComparator


def evaluate_video_file(video_path, output_report_path="KLAY_EVAL_REPORT.json"):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Target video file does not exist: {video_path}")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps

    engine = PoseEngine(smoothing_alpha=0.35)
    detector = ShotPhaseDetector()
    recorder = SessionRecorder()
    comparator = ProComparator(target_pro="klay")

    frame_idx = 0
    poses_detected = 0
    conf_counts = {"HIGH": 0, "MODERATE": 0, "INSUFFICIENT": 0}
    angle_comparisons = []
    frame_samples = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        timestamp_ms = int(frame_idx * (1000.0 / fps))
        out = engine.process(frame, timestamp_ms)

        if out is not None:
            poses_detected += 1
            landmarks = out["smoothed_landmarks"]
            valid = out["valid"]
            world_landmarks = out.get("world_landmarks")

            key_joint_indices = (11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)
            valid_count = sum(1 for idx in key_joint_indices if valid.get(idx, False))
            conf_ratio = valid_count / len(key_joint_indices)

            if conf_ratio >= 0.85:
                conf = "HIGH"
            elif conf_ratio >= 0.60:
                conf = "MODERATE"
            else:
                conf = "INSUFFICIENT"
            conf_counts[conf] += 1

            angles = compute_all_angles(landmarks, valid, world_landmarks=world_landmarks, min_visibility=0.45)
            state, vy, ve = detector.update(landmarks, angles, timestamp_ms)
            recorder.push_frame(angles, phase=state, timestamp_ms=timestamp_ms)

            if state in ('preparing', 'set_point'):
                recorder.start_shot()
            elif state == 'follow_through':
                recorder.end_shot()

            if angles and angles.get("elbow_shooting_2d") is not None and angles.get("elbow_shooting_3d") is not None:
                el_2d = angles["elbow_shooting_2d"]
                el_3d = angles["elbow_shooting_3d"]
                diff = abs(el_3d - el_2d)
                angle_comparisons.append(diff)
                if frame_idx % 25 == 0:
                    frame_samples.append({
                        "frame": frame_idx,
                        "timestamp_ms": timestamp_ms,
                        "phase": state,
                        "elbow_2d_deg": el_2d,
                        "elbow_3d_world_deg": el_3d,
                        "estimate_disagreement_deg": round(diff, 1),
                        "coordinate_frame": angles.get("coordinate_frame")
                    })
        else:
            conf_counts["INSUFFICIENT"] += 1

        frame_idx += 1

    cap.release()
    engine.close()

    # Aggregate Statistics
    mean_disagreement = float(np.mean(angle_comparisons)) if angle_comparisons else None
    max_disagreement = float(np.max(angle_comparisons)) if angle_comparisons else None
    median_disagreement = float(np.median(angle_comparisons)) if angle_comparisons else None

    report = {
        "evaluation_type": "Exploratory Single-Video Benchmark",
        "video_metadata": {
            "file": os.path.basename(video_path),
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "duration_seconds": round(duration_sec, 2),
        },
        "pose_tracking": {
            "frames_detected": poses_detected,
            "detection_rate_pct": round(poses_detected / max(1, total_frames) * 100, 1),
            "confidence_breakdown": {
                "HIGH": conf_counts["HIGH"],
                "MODERATE": conf_counts["MODERATE"],
                "INSUFFICIENT": conf_counts["INSUFFICIENT"],
            }
        },
        "shot_detection": {
            "total_valid_shots_recorded": recorder.shot_count,
            "shots": recorder.shots,
        },
        "coordinate_estimate_disagreement": {
            "metric": "Elbow Extension (2D Image Projection vs. MediaPipe 3D World Estimate)",
            "interpretation_note": "Represents geometric and neural estimate disagreement (including perspective foreshortening); NOT calibrated laboratory ground-truth error.",
            "mean_disagreement_deg": round(mean_disagreement, 1) if mean_disagreement else None,
            "median_disagreement_deg": round(median_disagreement, 1) if median_disagreement else None,
            "max_disagreement_deg": round(max_disagreement, 1) if max_disagreement else None,
            "sample_frames": frame_samples,
        },
        "limitations": [
            "Single-camera monocular view without multi-view triangulation.",
            "MediaPipe world landmarks are model priors, not physical motion-capture measurements.",
            "Lower-body framing truncation occurs in clips where shooter jumps or is partially out of frame.",
            "Real-world accuracy claims require multi-angle human-annotated reference benchmarks."
        ]
    }

    with open(output_report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 65)
    print("      REAL-VIDEO EVALUATION REPORT (EXPLORATORY)")
    print("=" * 65)
    print(f" Video:                        {report['video_metadata']['file']}")
    print(f" Duration:                     {report['video_metadata']['duration_seconds']}s ({report['video_metadata']['total_frames']} frames)")
    print(f" Pose Detection Rate:          {report['pose_tracking']['detection_rate_pct']}%")
    print(f" Valid Shots Recorded:         {report['shot_detection']['total_valid_shots_recorded']}")
    if mean_disagreement is not None:
        print(f" 2D vs. 3D Disagreement:      Mean: ±{mean_disagreement:.1f}° | Max: {max_disagreement:.1f}°")
    print("-" * 65)
    print(f"[INFO] Report saved to: {output_report_path}\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate video with basketball analysis pipeline")
    parser.add_argument("--video", default="klay_vid.mp4", help="Path to video file")
    parser.add_argument("--output", default="KLAY_EVAL_REPORT.json", help="Path to output JSON report")
    args = parser.parse_args()

    evaluate_video_file(args.video, args.output)
