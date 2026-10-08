import argparse
import time

import cv2

from analyzer import SessionRecorder, ShotPhaseDetector, compute_all_angles, shooting_side
from pose_engine import PoseEngine
from shot_lab_db import ShotLabDB


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


def run(
    source,
    use_ball=False,
    yolo_weights=None,
    detect_every=1,
    use_hands=False,
    pro_target=None,
    fullscreen=True,
    player_id="default_player",
    camera_view="frontal",
    shot_type="catch_and_shoot",
    shot_style="jump_shot",
    db_path="shot_lab.db"
):
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    frame_interval_ms = 1000.0 / fps if fps and fps > 1 else 33.33
    frame_number = 0
    engine = PoseEngine()
    recorder = SessionRecorder()
    phase_detector = ShotPhaseDetector(shot_style=shot_style)
    ball_tracker = maybe_ball_tracker(use_ball, yolo_weights, detect_every)
    hand_engine = maybe_hand_engine(use_hands)
    pro_comparator = maybe_pro_comparator(pro_target)

    # Initialize Shot Lab Database & Session
    db = ShotLabDB(db_path)
    session_id = db.create_session(
        player_id=player_id,
        camera_view=camera_view,
        shot_type=shot_type,
        shot_style=shot_style,
        fps=fps or 30.0,
        model_version="1.0.0"
    )

    prev_phase = "idle"
    prev_time = time.time()
    paused = False
    is_fullscreen = fullscreen
    show_ghost = True
    last_ball_info = None
    last_pro_result = None
    last_dtw_result = None
    last_shot_summary = None

    # Live Outcome Tagging State
    active_shot_id = None
    toast_start_time = 0.0
    toast_text = ""
    toast_color = (0, 255, 255)

    window_title = "Intelligent Basketball Biomechanics Coach"
    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
    if is_fullscreen:
        cv2.setWindowProperty(window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("\n" + "="*60)
    print("  INTELLIGENT BASKETBALL BIOMECHANICS COACH")
    print("="*60)
    print(f"Player ID:    {player_id}")
    print(f"Session ID:   {session_id}")
    print(f"Camera View:  {camera_view} | Shot Type: {shot_type}")
    print("Controls:")
    print("  Q         - Quit application")
    print("  SPACE     - Pause / Resume playback")
    print("  M / X / U - Tag last shot: [M]ake / Miss [X] / [U]nknown")
    print("  F         - Toggle Fullscreen / Windowed mode")
    print("  G         - Toggle Full-Body Pro Ghost Skeleton")
    print("  S         - Save and export session analytics CSV")
    if ball_tracker:
        print(f"  * Ball Tracking: ON ({ball_tracker.mode})")
    if hand_engine:
        print("  * Hand & Wrist Snap Tracking: ON")
    if pro_comparator:
        print(f"  * Pro Benchmark: ON (Target: {pro_comparator.profile['name']})")
        print("    -> Full-body ghost skeleton active (Knees to Elbows to Head)")
    print("="*60 + "\n")


    try:
        while capture.isOpened():
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord(" "):
                paused = not paused
            if key == ord("f"):
                is_fullscreen = not is_fullscreen
                prop = cv2.WINDOW_FULLSCREEN if is_fullscreen else cv2.WINDOW_NORMAL
                cv2.setWindowProperty(window_title, cv2.WND_PROP_FULLSCREEN, prop)
            if key == ord("g"):
                show_ghost = not show_ghost
            if key == ord("s"):
                recorder.export_csv()
                stats = recorder.get_session_stats()
                if stats:
                    print(stats)

            # Live Outcome Tagging Hotkeys
            if key in (ord("m"), ord("M")) and active_shot_id:
                db.update_shot_annotation(active_shot_id, outcome="make", outcome_source="live_hotkey", review_status="approved")
                toast_text = f"Recorded: MAKE (Shot #{last_shot_summary.get('shot_number', '')})"
                toast_color = (0, 255, 0)
                toast_start_time = time.time()
                print(f"[SHOT LAB] Shot {active_shot_id} tagged as MAKE (approved for baseline).")

            elif key in (ord("x"), ord("X")) and active_shot_id:
                db.update_shot_annotation(active_shot_id, outcome="miss", outcome_source="live_hotkey", review_status="approved")
                toast_text = f"Recorded: MISS (Shot #{last_shot_summary.get('shot_number', '')})"
                toast_color = (0, 0, 255)
                toast_start_time = time.time()
                print(f"[SHOT LAB] Shot {active_shot_id} tagged as MISS (approved for baseline).")

            elif key in (ord("u"), ord("U")) and active_shot_id:
                db.update_shot_annotation(active_shot_id, outcome="unknown", outcome_source="live_hotkey", review_status="quarantined")
                toast_text = f"Recorded: UNKNOWN (Shot #{last_shot_summary.get('shot_number', '')})"
                toast_color = (200, 200, 200)
                toast_start_time = time.time()
                print(f"[SHOT LAB] Shot {active_shot_id} tagged as UNKNOWN (quarantined).")


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
                pose_wrist = None
                pose_elbow = None
                if output is not None:
                    lms = output["smoothed_landmarks"]
                    side = shooting_side(lms, output["valid"])
                    w_idx = 15 if side == 'left' else 16
                    e_idx = 13 if side == 'left' else 14
                    pose_wrist = lms.get(w_idx)
                    pose_elbow = lms.get(e_idx)

                hand_info = hand_engine.process(frame, timestamp_ms, pose_wrist, pose_elbow)
                if hand_info:
                    hand_engine.draw(frame, hand_info)

            ball_info = None
            if ball_tracker:
                detections = ball_tracker.detect(frame)
                if output is not None:
                    ball_info = ball_tracker.update(
                        detections, output["smoothed_landmarks"], output["valid"], timestamp_ms
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
                cv2.putText(frame, "No pose detected - step into camera frame", (30, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            else:
                landmarks = output["smoothed_landmarks"]
                valid = output["valid"]
                world_landmarks = output.get("world_landmarks")
                draw_pose(frame, landmarks, valid)
                angles = compute_all_angles(landmarks, valid, world_landmarks=world_landmarks, min_visibility=0.45)


                # Calculate Tracking Confidence based on visibility of key biomechanical landmarks
                key_joint_indices = (11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)
                valid_count = sum(1 for idx in key_joint_indices if valid.get(idx, False))
                conf_ratio = valid_count / len(key_joint_indices)

                if conf_ratio >= 0.85:
                    conf_level = "HIGH"
                    conf_color = (0, 255, 0)
                elif conf_ratio >= 0.60:
                    conf_level = "MODERATE"
                    conf_color = (0, 255, 255)
                else:
                    conf_level = "INSUFFICIENT"
                    conf_color = (0, 0, 255)

                # Update state machine with hand metrics
                phase, v_y, v_ang = phase_detector.update(landmarks, angles, timestamp_ms, hand_info)
                recorder.push_frame(angles, phase, timestamp_ms, hand_info)

                # Trigger shot recording lifecycle
                if prev_phase in ("idle", "preparing") and phase in ("preparing", "set_point", "releasing"):
                    if not recorder.recording:
                        recorder.start_shot()
                        shot_seq_id = f"shot_{session_id}_{recorder.shot_count}"
                        if ball_tracker:
                            ball_tracker.on_shot_started(shot_seq_id, frame_number, timestamp_ms)

                if prev_phase in ("preparing", "set_point") and phase == "releasing":
                    shot_seq_id = f"shot_{session_id}_{recorder.shot_count}"
                    if ball_tracker:
                        ball_tracker.on_shot_release(shot_seq_id, frame_number, timestamp_ms)

                if prev_phase in ("releasing", "follow_through") and phase == "idle":
                    extra = {}
                    ball_summary = None
                    shot_seq_id = f"shot_{session_id}_{recorder.shot_count}"
                    if ball_tracker:
                        ball_summary = ball_tracker.on_shot_ended(shot_seq_id, frame_number, timestamp_ms)
                        if ball_summary:
                            extra["ball_detection_status"] = ball_summary.get("ball_detection_status")
                            extra["rim_detection_status"] = ball_summary.get("rim_detection_status")
                            extra["ball_release_angle"] = ball_summary.get("ball_release_angle")
                            extra["ball_coverage_ratio"] = ball_summary.get("ball_coverage_ratio")

                    if hand_info:
                        extra["wrist_flexion_angle"] = hand_info.get("wrist_flexion_angle")
                        extra["finger_spread_ratio"] = hand_info.get("finger_spread_ratio")
                        extra["wrist_snap_velocity"] = hand_info.get("wrist_snap_velocity")

                    # Run DTW sequence match on completed shot
                    if pro_comparator and recorder.current_shot:
                        dtw_res = pro_comparator.compare_sequence(recorder.current_shot)
                        if dtw_res:
                            last_dtw_result = dtw_res
                            extra["dtw_similarity_score"] = dtw_res["dtw_similarity_score"]
                            extra["dtw_deviation_deg"] = dtw_res["avg_angular_deviation_deg"]

                    summary = recorder.end_shot(extra)
                    if summary:
                        last_shot_summary = summary
                        dtw_tag = f" | DTW Match: {summary.get('dtw_similarity_score', '-')}% (+/-{summary.get('dtw_deviation_deg', 0)} deg)" if pro_comparator else ""
                        rep_score = summary.get('repeatability_index', '-')
                        print(
                            f"Shot #{summary['shot_number']} | "
                            f"Elbow: {summary.get('elbow_at_release')} deg | "
                            f"Knee Dip: {summary.get('knee_at_dip')} deg | "
                            f"Repeatability Index: {rep_score}% | "
                            f"Kinetic Seq: {summary.get('kinetic_sequencing_score', '-')}%"
                            f"{dtw_tag}"
                        )

                        # Persist to ShotLabDB
                        shot_rec = {
                            "session_id": session_id,
                            "player_id": player_id,
                            "camera_view": camera_view,
                            "shot_type": shot_type,
                            "shot_style": shot_style,
                            "machine_start_frame": max(0, frame_number - summary.get("frames_recorded", 30)),
                            "machine_dip_frame": max(0, frame_number - summary.get("frames_recorded", 30) + 10),
                            "machine_set_frame": max(0, frame_number - summary.get("frames_recorded", 30) + 20),
                            "machine_release_frame": max(0, frame_number - 5),
                            "machine_end_frame": frame_number,
                            "outcome": "unknown",
                            "outcome_source": "unlabeled",
                            "review_status": "quarantined",
                            "tracking_confidence": summary.get("tracking_confidence", "SUFFICIENT"),
                            "knee_angle_dip_3d": summary.get("knee_angle_dip_3d"),
                            "elbow_angle_release_3d": summary.get("elbow_angle_release_3d"),
                            "elbow_angle_release_2d": summary.get("elbow_angle_release_2d"),
                            "foreshortening_discrepancy_deg": summary.get("foreshortening_discrepancy_deg"),
                            "sequence_lag_ms": summary.get("sequence_lag_ms"),
                            "torso_sway_deg": summary.get("torso_sway_deg")
                        }
                        active_shot_id = db.save_shot(shot_rec)
                        toast_start_time = time.time()
                        toast_text = f"[M] Make  |  [X] Miss  |  [U] Unknown  (Shot #{summary['shot_number']})"
                        toast_color = (0, 255, 255)

                prev_phase = phase

                elbow = angles.get("elbow_shooting")
                elbow_2d = angles.get("elbow_shooting_2d")
                elbow_3d = angles.get("elbow_shooting_3d")
                knee = angles.get("knee_shooting")

                if elbow_3d is not None and elbow_2d is not None:
                    delta = angles.get("foreshortening_delta_elbow", 0.0)
                    elbow_text = f"Elbow: {elbow_3d:.1f} deg (2D: {elbow_2d:.1f} deg | Diff: {delta:.1f} deg)"
                elif elbow is not None:
                    elbow_text = f"Elbow: {elbow:.1f} deg ({angles.get('coordinate_frame', '2D')})"
                else:
                    elbow_text = "Elbow: UNAVAILABLE (Occluded)"

                knee_text = f"Knee:  {knee:.1f} deg" if knee is not None else "Knee:  UNAVAILABLE (Occluded)"
                cv2.putText(frame, elbow_text, (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 0), 2)
                cv2.putText(frame, knee_text, (30, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 0), 2)

                # Tracking Confidence Badge
                cv2.putText(frame, f"Tracking: {conf_level} ({conf_ratio*100:.0f}%)", (30, 105),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, conf_color, 2)

                # Phase & Shot Count HUD
                phase_color = (0, 255, 0) if phase in ("releasing", "follow_through") else (0, 255, 255)
                cv2.putText(
                    frame, f"Phase: {phase.upper()}  |  Valid Shots (N): {recorder.shot_count}",
                    (30, 132), cv2.FONT_HERSHEY_SIMPLEX, 0.65, phase_color, 2,
                )

                # Render Live Outcome Tagging Toast Overlay
                if (time.time() - toast_start_time) < 3.0 and toast_text:
                    box_w, box_h = 560, 36
                    bx = max(10, (frame.shape[1] - box_w) // 2)
                    by = 20
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (bx, by), (bx + box_w, by + box_h), (30, 30, 30), -1)
                    cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)
                    cv2.rectangle(frame, (bx, by), (bx + box_w, by + box_h), toast_color, 2)
                    cv2.putText(frame, toast_text, (bx + 15, by + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)

                # Render Full-Body Pro Comparator Ghost Skeleton & Match Widget
                if pro_comparator:
                    hip = angles.get("hip_shooting")
                    user_metrics = {
                        "elbow_release": elbow if phase in ("releasing", "follow_through") else None,
                        "knee_dip": knee if phase in ("preparing", "set_point") else None,
                        "hip_posture": hip,
                        "launch_angle": last_ball_info.get("release_angle") if last_ball_info else None,
                        "wrist_flick": hand_info.get("wrist_flexion_angle") if hand_info else None,
                    }
                    comp_res = pro_comparator.compare(user_metrics)
                    if comp_res:
                        last_pro_result = comp_res
                    if last_pro_result:
                        pro_comparator.draw(frame, last_pro_result, last_dtw_result)

                    # Draw FULL-BODY Ghost Skeleton overlay
                    if show_ghost:
                        pro_comparator.draw_full_body_ghost_skeleton(frame, landmarks, angles, phase)

                # Feedback & Kinetic diagnostic overlay
                if conf_level == "INSUFFICIENT":
                    # Framing guidance when camera cannot see player properly
                    cv2.putText(frame, "Camera Guidance: Step back 3-4m to capture full body from feet to overhead",
                                (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 165, 255), 2)
                elif last_shot_summary:
                    diag = last_shot_summary.get("kinetic_diagnostics", "")
                    eff = last_shot_summary.get("energy_efficiency")
                    eff_str = f"Eff {eff}%" if eff is not None else "Eff: N/A"
                    diag_color = (0, 255, 0) if (eff is not None and eff >= 75) else (0, 255, 255)
                    cv2.putText(frame, f"Last Shot: {eff_str} | {diag}", (30, 160),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.50, diag_color, 2)
                elif elbow is None or knee is None:
                    feedback = "Tracking joints... hold steady in frame"
                    cv2.putText(frame, feedback, (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
                elif elbow > 150:
                    feedback = "Good extension - hold follow through"
                    cv2.putText(frame, feedback, (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
                else:
                    feedback = "Extend shooting arm up & through"
                    cv2.putText(frame, feedback, (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

            cv2.imshow(window_title, frame)
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
    parser.add_argument("input_video", nargs="?", default=None, help="Optional positional path to a video file")
    parser.add_argument("--video", "--source", dest="video", help="Path to a video file; defaults to webcam 0")
    parser.add_argument("--player", default="default_player", help="Player identifier for Shot Lab")
    parser.add_argument("--camera-view", choices=["frontal", "side_90", "oblique_45"], default="frontal", help="Camera viewpoint")
    parser.add_argument("--shot-type", choices=["catch_and_shoot", "off_dribble", "free_throw"], default="catch_and_shoot", help="Shot type context")
    parser.add_argument("--shot-style", choices=["jump_shot", "set_shot"], default="jump_shot", help="Shot mechanic style (jump_shot: forehead level, set_shot: shoulder level)")
    parser.add_argument("--db", default="shot_lab.db", help="Path to Shot Lab SQLite database")
    parser.add_argument("--ball", action="store_true", help="Enable YOLO ball/rim tracking")
    parser.add_argument("--yolo", help="Optional custom weights (basket_rim.pt)")
    parser.add_argument("--detect-every", type=int, default=1, help="Run YOLO every N frames")
    parser.add_argument("--hands", action="store_true", help="Enable MediaPipe hand tracking & wrist flick analysis")
    parser.add_argument("--pro", choices=["curry", "klay", "ray_allen"], nargs="?", const="curry", help="Enable Pro Player Benchmark comparison")
    parser.add_argument("--windowed", action="store_true", help="Start in normal windowed mode instead of fullscreen")
    args = parser.parse_args()

    video_src = args.video if args.video else (args.input_video if args.input_video else 0)
    run(
        video_src,
        use_ball=args.ball,
        yolo_weights=args.yolo,
        detect_every=args.detect_every,
        use_hands=args.hands,
        pro_target=args.pro,
        fullscreen=not args.windowed,
        player_id=args.player,
        camera_view=args.camera_view,
        shot_type=args.shot_type,
        shot_style=args.shot_style,
        db_path=args.db
    )


