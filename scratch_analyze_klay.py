"""
Run Basketball Analysis Pipeline on klay_vid.mp4
===============================================
Extracts frame-by-frame pose detections, 2D vs 3D world angles,
shot phase transitions, tracking confidence, and kinetic chain metrics.
"""

import os
import cv2
import numpy as np

from pose_engine import PoseEngine
from analyzer import (
    compute_all_angles,
    shooting_side,
    ShotPhaseDetector,
    SessionRecorder,
    KineticChainAnalyzer
)
from pro_comparator import ProComparator


def analyze_video(video_path):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_s = total_frames / fps

    print("\n" + "=" * 65)
    print(f"  ANALYZING VIDEO: {os.path.basename(video_path)}")
    print(f"  FPS: {fps:.1f} | Frames: {total_frames} | Duration: {duration_s:.2f}s")
    print("=" * 65)

    engine = PoseEngine(smoothing_alpha=0.35)
    detector = ShotPhaseDetector()
    recorder = SessionRecorder()
    comparator = ProComparator(target_pro="klay")

    frame_idx = 0
    poses_detected = 0
    conf_counts = {"HIGH": 0, "MODERATE": 0, "INSUFFICIENT": 0}
    phase_timeline = []
    angle_samples = []

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

            # Tracking confidence
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

            # Update State Machine
            state, wrist_v, elbow_v = detector.update(landmarks, angles, timestamp_ms)
            phase_timeline.append((frame_idx, timestamp_ms, state, angles))
            recorder.push_frame(angles, phase=state, timestamp_ms=timestamp_ms)

            if state in ('preparing', 'set_point'):
                recorder.start_shot()
            elif state == 'follow_through':
                recorder.end_shot()

            if angles and angles.get("elbow_shooting_2d") is not None and angles.get("elbow_shooting_3d") is not None:
                angle_samples.append({
                    "frame": frame_idx,
                    "phase": state,
                    "elbow_2d": angles["elbow_shooting_2d"],
                    "elbow_3d": angles["elbow_shooting_3d"],
                    "knee_2d": angles["knee_shooting_2d"],
                    "knee_3d": angles["knee_shooting_3d"],
                    "delta_elbow": angles.get("foreshortening_delta_elbow"),
                })
        else:
            conf_counts["INSUFFICIENT"] += 1
            phase_timeline.append((frame_idx, timestamp_ms, "no_pose", None))

        frame_idx += 1

    cap.release()
    engine.close()

    # Results Breakdown
    print(f"\nPose Detection Rate: {poses_detected}/{total_frames} frames ({poses_detected/total_frames*100:.1f}%)")
    print(f"Tracking Confidence Breakdown:")
    for k, v in conf_counts.items():
        print(f"  - {k:<12}: {v} frames ({v/total_frames*100:.1f}%)")

    print(f"\nTotal Shots Detected: {recorder.shot_count}")
    if recorder.shots:
        print("\nRecorded Shot Summaries:")
        for idx, shot in enumerate(recorder.shots, 1):
            print(f"\n--- SHOT #{idx} ---")
            print(f"  • Frames: {shot.get('frames_recorded')}")
            print(f"  • Knee at Dip: {shot.get('knee_at_dip')}°")
            print(f"  • Elbow at Release: {shot.get('elbow_at_release')}°")
            print(f"  • Repeatability Index: {shot.get('repeatability_index')}")
            print(f"  • Kinetic Efficiency: {shot.get('energy_efficiency')}%")
            print(f"  • Proximal-to-Distal Flow: {shot.get('is_proximal_to_distal')}")
            print(f"  • Diagnostics: {shot.get('kinetic_diagnostics')}")

    if angle_samples:
        deltas = [s["delta_elbow"] for s in angle_samples if s["delta_elbow"] is not None]
        avg_delta = np.mean(deltas) if deltas else 0.0
        max_delta = np.max(deltas) if deltas else 0.0
        print(f"\n2D Image vs 3D World Angle Comparison (Elbow):")
        print(f"  • Mean 2D vs 3D Discrepancy (Foreshortening): ±{avg_delta:.1f}°")
        print(f"  • Max 2D vs 3D Discrepancy: {max_delta:.1f}°")
        print(f"  • Sample frame (Dip/Set): 2D Elbow = {angle_samples[len(angle_samples)//4]['elbow_2d']}° vs 3D = {angle_samples[len(angle_samples)//4]['elbow_3d']}°")
        print(f"  • Sample frame (Release): 2D Elbow = {angle_samples[len(angle_samples)*3//4]['elbow_2d']}° vs 3D = {angle_samples[len(angle_samples)*3//4]['elbow_3d']}°")

    print("=" * 65 + "\n")


if __name__ == "__main__":
    vid = "klay_vid.mp4"
    analyze_video(vid)
