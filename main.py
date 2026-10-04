import argparse
import time

import cv2

from analyzer import SessionRecorder, ShotPhaseDetector, compute_all_angles
from pose_engine import PoseEngine


CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (24, 26), (26, 28),
]


def draw_pose(frame, landmarks, valid):
    height, width = frame.shape[:2]
    for first, second in CONNECTIONS:
        if not (valid.get(first, True) and valid.get(second, True)):
            continue
        point_a = (int(landmarks[first]["norm_x"] * width), int(landmarks[first]["norm_y"] * height))
        point_b = (int(landmarks[second]["norm_x"] * width), int(landmarks[second]["norm_y"] * height))
        cv2.line(frame, point_a, point_b, (0, 255, 0), 2)

    for index, landmark in landmarks.items():
        center = (int(landmark["norm_x"] * width), int(landmark["norm_y"] * height))
        color = (0, 0, 255) if valid.get(index, True) else (0, 165, 255)
        cv2.circle(frame, center, 4, color, -1)


def maybe_ball_tracker(enabled, weights, detect_every):
    if not enabled:
        return None
    try:
        from ball_tracker import BallTracker
        return BallTracker(weights_path=weights, detect_every=detect_every)
    except Exception as exc:
        print(f"Ball tracking disabled: {exc}")
        return None


def maybe_hand_engine(enabled):
    if not enabled:
        return None
    try:
        from hand_engine import HandEngine
        return HandEngine()
    except Exception as exc:
        print(f"Hand tracking disabled: {exc}")
        return None


def maybe_pro_comparator(pro_target):
    if not pro_target:
        return None
    try:
        from pro_comparator import ProComparator
        return ProComparator(target_pro=pro_target)
    except Exception as exc:
        print(f"Pro comparator disabled: {exc}")
        return None


def run(source, use_ball=False, yolo_weights=None, detect_every=1, use_hands=False, pro_target=None):
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_interval_ms = 1000.0 / fps if fps and fps > 1 else 33.33
    frame_number = 0
    engine = PoseEngine()
    recorder = SessionRecorder()
    phase_detector = ShotPhaseDetector()
    ball_tracker = maybe_ball_tracker(use_ball, yolo_weights, detect_every)
    hand_engine = maybe_hand_engine(use_hands)
    pro_comparator = maybe_pro_comparator(pro_target)

    prev_phase = "idle"
    prev_time = time.time()
    paused = False
    last_ball_info = None
    last_pro_result = None

    print("Q quit | SPACE pause | S save session CSV")
    if ball_tracker:
        print(f"Ball tracker on ({ball_tracker.mode} weights)")
    if hand_engine:
        print("Hand tracking on (21 keypoints & wrist flick)")
    if pro_comparator:
        print(f"Pro Comparator on (Target: {pro_comparator.profile['name']})")

    try:
        while capture.isOpened():
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord(" "):
                paused = not paused
            if key == ord("s"):
                recorder.export_csv()
                stats = recorder.get_session_stats()
                if stats:
                    print(stats)

            if paused:
                continue

            success, frame = capture.read()
            if not success:
                break

            timestamp_ms = round(frame_number * frame_interval_ms)
            output = engine.process(frame, timestamp_ms)
            frame_number += 1

            now = time.time()
            live_fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now
            cv2.putText(
                frame, f"FPS: {live_fps:.1f}", (frame.shape[1] - 130, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2,
            )

            # Process hand tracking if enabled
            hand_info = None
            if hand_engine:
                hand_info = hand_engine.process(frame, timestamp_ms)
                if hand_info:
                    hand_engine.draw(frame, hand_info)

            ball_info = None
            if ball_tracker:
                detections = ball_tracker.detect(frame)
                if output is not None:
                    ball_info = ball_tracker.update(
                        detections, output["smoothed_landmarks"], output["valid"]
                    )
                else:
                    ball_info = {
                        "status": "no_pose",
                        "ball": detections.get("ball"),
                        "rim": detections.get("rim"),
                        "release_angle": None,
                        "flight_centers": [],
                    }
                last_ball_info = ball_info
                ball_tracker.draw(frame, ball_info)

            if output is None:
                cv2.putText(frame, "No pose detected", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                landmarks = output["smoothed_landmarks"]
                valid = output["valid"]
                draw_pose(frame, landmarks, valid)
                angles = compute_all_angles(landmarks, valid)

                phase, v_y, v_ang = phase_detector.update(landmarks, angles, timestamp_ms)
                recorder.push_frame(angles, phase)

                if prev_phase != "releasing" and phase == "releasing":
                    recorder.start_shot()

                if prev_phase == "releasing" and phase != "releasing":
                    extra = {}
                    if last_ball_info and last_ball_info.get("last_shot"):
                        shot = last_ball_info["last_shot"]
                        extra["ball_result"] = shot.get("result")
                        extra["ball_release_angle"] = shot.get("release_angle")
                        extra["ball_release_frames"] = shot.get("release_frames")

                    if hand_info:
                        extra["wrist_flexion_angle"] = hand_info.get("wrist_flexion_angle")
                        extra["finger_spread_ratio"] = hand_info.get("finger_spread_ratio")

                    summary = recorder.end_shot(extra)
                    if summary:
                        print(
                            f"Shot {summary['shot_number']} | "
                            f"Elbow: {summary.get('elbow_at_release')}° | "
                            f"Knee dip: {summary.get('knee_at_dip')}° | "
                            f"Ball: {summary.get('ball_result', '-')}"
                        )

                prev_phase = phase

                elbow = angles.get("elbow_shooting")
                knee = angles.get("knee_shooting")
                hip = angles.get("hip_shooting")
                elbow_text = f"Elbow: {elbow:.1f}" if elbow is not None else "Elbow: unavailable"
                knee_text = f"Knee:  {knee:.1f}" if knee is not None else "Knee:  unavailable"
                cv2.putText(frame, elbow_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(frame, knee_text, (30, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.putText(
                    frame, f"Phase: {phase}  Shots: {recorder.shot_count}",
                    (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2,
                )

                # Update Pro Comparator matching if enabled
                if pro_comparator:
                    user_metrics = {
                        "elbow_release": elbow if phase == "releasing" else None,
                        "knee_dip": knee if phase in ("preparing", "releasing") else None,
                        "hip_posture": hip,
                        "launch_angle": last_ball_info.get("release_angle") if last_ball_info else None,
                        "wrist_flick": hand_info.get("wrist_flexion_angle") if hand_info else None,
                    }
                    comp_res = pro_comparator.compare(user_metrics)
                    if comp_res:
                        last_pro_result = comp_res
                    if last_pro_result:
                        pro_comparator.draw(frame, last_pro_result)

                if elbow is None or knee is None:
                    feedback = "Tracking unclear - improve framing or lighting"
                elif elbow > 150:
                    feedback = "Good form"
                else:
                    feedback = "Extend your shooting arm more"
                cv2.putText(frame, feedback, (30, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            cv2.imshow("Basketball Coach", frame)
    finally:
        capture.release()
        cv2.destroyAllWindows()
        engine.close()
        if hand_engine:
            hand_engine.close()
        if recorder.shots:
            recorder.export_csv()
            print(recorder.get_session_stats())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run basketball pose analysis")
    parser.add_argument("--video", help="Path to a video file; defaults to webcam 0")
    parser.add_argument("--ball", action="store_true", help="Enable YOLO ball/rim tracking")
    parser.add_argument("--yolo", help="Optional custom weights (basket_rim.pt)")
    parser.add_argument("--detect-every", type=int, default=1, help="Run YOLO every N frames")
    parser.add_argument("--hands", action="store_true", help="Enable MediaPipe hand tracking & wrist flick analysis")
    parser.add_argument("--pro", choices=["curry", "klay", "ray_allen"], nargs="?", const="curry", help="Enable Pro Player Benchmark comparison")
    args = parser.parse_args()
    run(
        args.video if args.video else 0,
        use_ball=args.ball,
        yolo_weights=args.yolo,
        detect_every=args.detect_every,
        use_hands=args.hands,
        pro_target=args.pro,
    )

