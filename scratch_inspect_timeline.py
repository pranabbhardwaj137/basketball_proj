"""
Diagnostic tool to inspect state machine and kinematics across klay_vid.mp4
"""
import os
import cv2
import numpy as np

from pose_engine import PoseEngine
from analyzer import compute_all_angles, shooting_side, ShotPhaseDetector

def inspect_timeline(video_path="klay_vid.mp4"):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    engine = PoseEngine(smoothing_alpha=0.35)
    detector = ShotPhaseDetector()

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        ts_ms = int(frame_idx * (1000.0 / fps))
        out = engine.process(frame, ts_ms)
        if out:
            landmarks = out["smoothed_landmarks"]
            valid = out["valid"]
            world_lms = out.get("world_landmarks")
            angles = compute_all_angles(landmarks, valid, world_landmarks=world_lms)
            state, vy, ve = detector.update(landmarks, angles, ts_ms)
            
            # Print frames with activity
            side = angles.get("shooting_side", "right") if angles else "right"
            w_idx = 15 if side == 'left' else 16
            s_idx = 11 if side == 'left' else 12
            w_y = landmarks[w_idx]["norm_y"] if w_idx in landmarks else None
            s_y = landmarks[s_idx]["norm_y"] if s_idx in landmarks else None
            el = angles.get("elbow_shooting") if angles else None
            kn = angles.get("knee_shooting") if angles else None

            if frame_idx % 10 == 0 or state != 'idle':
                print(f"F#{frame_idx:03d} | State: {state:<14} | Side: {side} | WristY: {w_y:.2f} (ShY: {s_y:.2f}) | Elbow: {el} | Knee: {kn} | v_y: {vy:+.3f}")
        else:
            if frame_idx % 20 == 0:
                print(f"F#{frame_idx:03d} | No pose detected")
        frame_idx += 1

    cap.release()
    engine.close()

if __name__ == "__main__":
    inspect_timeline()
