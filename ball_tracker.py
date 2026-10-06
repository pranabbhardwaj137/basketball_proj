"""In-memory ball and rim tracker with explicit confidence gating and model limitations.

Model Limitations:
  - Stock YOLOv8n COCO model detects class 32 ('sports ball') only. Rim tracking,
    rim entry angle, and automated make/miss classification are UNAVAILABLE without
    custom trained weights (weights/basket_rim.pt).
  - Custom basket_rim.pt weights (class 0=ball, class 2=rim) enable rim proximity
    and make/miss heuristics.
  - Confidence gating: detections with confidence < 0.35 or flights with < 4 verified
    centers are marked as 'Inconclusive / Insufficient Evidence'.
"""

from pathlib import Path
import cv2
import numpy as np

from ball_geometry import (
    arc_peak,
    ball_under_rim,
    box_center,
    box_to_point_distance,
    calculate_entry_angle,
    fit_parabola,
    last_valid_box,
    point_distance,
    release_angle_deg,
    sample_parabola,
)

COCO_SPORTS_BALL = 32
CUSTOM_BALL = 0
CUSTOM_RIM = 2


def load_yolo(weights_path=None):
    """Return (model, mode) where mode is 'custom' or 'coco'."""
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Ball tracking needs ultralytics. Run: pip install ultralytics"
        ) from exc

    custom = Path(weights_path) if weights_path else Path("weights/basket_rim.pt")
    if custom.exists():
        print(f"Loading custom basketball & rim weights: {custom}")
        return YOLO(str(custom)), "custom"
    
    print("Using stock YOLOv8n COCO model. Note: Rim detection & Make/Miss heuristics require custom weights.")
    return YOLO("yolov8n.pt"), "coco"


class BallTracker:
    """Tracks basketball trajectory, launch angle, and optional rim entry geometry."""

    def __init__(
        self,
        weights_path=None,
        conf=0.25,
        near_hand_px=130,
        leave_hand_px=150,
        detect_every=1,
    ):
        self.model, self.mode = load_yolo(weights_path)
        self.conf = conf
        self.near_hand_px = near_hand_px
        self.leave_hand_px = leave_hand_px
        self.detect_every = max(1, detect_every)
        self._frame_i = 0
        self._last = {"ball": None, "rim": None, "ball_conf": 0.0, "rim_conf": 0.0}

        self.release_started = False
        self.release_ended = False
        self.tracking_flight = False
        self.ball_history = []
        self.rim_history = []
        self.flight_centers = []
        self.flight_timestamps = []
        self.release_frames = 0
        self.last_shot = None

    def detect(self, frame):
        """Run YOLO inference every `detect_every` frames to optimize throughput."""
        self._frame_i += 1
        if (self._frame_i - 1) % self.detect_every != 0:
            return dict(self._last)

        if self.mode == "custom":
            results = self.model.predict(
                frame, verbose=False, conf=self.conf, classes=[CUSTOM_BALL, CUSTOM_RIM]
            )
        else:
            results = self.model.predict(
                frame, verbose=False, conf=self.conf, classes=[COCO_SPORTS_BALL]
            )

        ball, rim, ball_conf, rim_conf = None, None, 0.0, 0.0
        if results:
            boxes = results[0].boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = [float(v) for v in box.xyxy[0].tolist()]
                if self.mode == "custom":
                    if cls == CUSTOM_BALL and conf >= ball_conf:
                        ball, ball_conf = xyxy, conf
                    elif cls == CUSTOM_RIM and conf >= rim_conf:
                        rim, rim_conf = xyxy, conf
                elif cls == COCO_SPORTS_BALL and conf >= ball_conf:
                    ball, ball_conf = xyxy, conf

        self._last = {
            "ball": ball,
            "rim": rim,
            "ball_conf": round(ball_conf, 2),
            "rim_conf": round(rim_conf, 2),
        }
        return dict(self._last)

    def update(self, detections, landmarks, valid=None, timestamp_ms=0):
        """Advance trajectory state machine with confidence gating and frame-gap awareness."""
        wrists = _wrist_pixels(landmarks, valid)
        elbow_y = _shooting_elbow_y(landmarks, valid)
        ball = detections.get("ball")
        rim = detections.get("rim")
        ball_conf = detections.get("ball_conf", 0.0)

        self.ball_history.append(ball)
        self.rim_history.append(rim)

        status = "idle"
        release_angle = None
        outcome = None

        near = _ball_near_any_wrist(ball, wrists, self.near_hand_px)
        above_elbow = _ball_above_elbow(ball, elbow_y)

        # 1. Start Release: Ball near shooting hand and elevated above elbow
        if not self.release_started:
            if above_elbow and near and ball_conf >= 0.30:
                self.release_started = True
                self.release_ended = False
                self.tracking_flight = False
                self.release_frames = 0
                self.flight_centers = []
                self.flight_timestamps = []
                status = "release_started"
            else:
                status = "idle"

        # 2. In Hand Rising: Ball rising toward release apex
        elif self.release_started and not self.release_ended:
            self.release_frames += 1
            center = box_center(ball)
            if center is not None:
                self.flight_centers.append(center)
                self.flight_timestamps.append(timestamp_ms)

            left_hand = not _ball_near_any_wrist(ball, wrists, self.leave_hand_px)
            if ball is not None and left_hand:
                self.release_ended = True
                self.tracking_flight = True
                prev = last_valid_box(self.ball_history)
                release_angle = release_angle_deg(ball, prev)
                status = "released"
            else:
                status = "releasing"

        # 3. Ball in Flight: Tracking parabolic arc toward rim
        elif self.release_started and self.release_ended and self.tracking_flight:
            self.release_frames += 1
            center = box_center(ball)
            if center is not None:
                self.flight_centers.append(center)
                self.flight_timestamps.append(timestamp_ms)

            # Evaluate make/miss if rim is available
            outcome = self._judge_make_miss(ball, rim)
            if outcome is not None:
                self.last_shot = self._close_shot(outcome, release_angle)
                status = outcome.lower()
                self.tracking_flight = False
            elif self.release_frames > 75:  # Flight timeout (~2.5s)
                # Close flight with honest status
                default_outcome = "In Flight (Timeout)" if self.mode == "coco" else "Unknown Outcome"
                self.last_shot = self._close_shot(default_outcome, release_angle)
                status = "completed"
                self.tracking_flight = False
            else:
                status = "in_flight"

        # Reset trigger: Ball caught or returned to player hands
        if (
            self.release_started
            and self.release_ended
            and _ball_near_any_wrist(ball, wrists, 60)
        ):
            if self.tracking_flight:
                self.last_shot = self._close_shot("Player Rebound / Caught", release_angle)
            self.reset()
            status = "reset"

        return {
            "status": status,
            "mode": self.mode,
            "ball_conf": ball_conf,
            "release_angle": release_angle,
            "outcome": outcome,
            "release_frames": self.release_frames,
            "ball": ball,
            "rim": rim,
            "flight_centers": list(self.flight_centers),
            "last_shot": self.last_shot,
        }

    def _judge_make_miss(self, ball, rim):
        """Evaluate shot outcome with explicit model limitations."""
        if self.mode == "coco":
            # Stock COCO model does not detect basketball rims
            return None

        if ball is None or rim is None:
            return None

        if ball_under_rim(ball, rim, x_threshold=85):
            return "Make"

        if len(self.ball_history) < 3 or len(self.rim_history) < 3:
            return None

        prev_ball = last_valid_box(self.ball_history)
        prev_rim = last_valid_box(self.rim_history)
        now_d = point_distance(box_center(ball), box_center(rim))
        prev_d = point_distance(box_center(prev_ball), box_center(prev_rim))

        if now_d is None or prev_d is None:
            return None

        # Ball moving away from rim level
        if now_d > prev_d + 15:
            return "Make" if ball_under_rim(ball, rim, x_threshold=70) else "Miss"

        return None

    def _close_shot(self, outcome, release_angle):
        """Summarize trajectory curve, apex height, and goodness-of-fit."""
        pts = [c for c in self.flight_centers if c is not None]
        if len(pts) < 4:
            return {
                "result": outcome,
                "release_angle": release_angle,
                "release_frames": self.release_frames,
                "arc_peak": None,
                "entry_angle": None,
                "trajectory_fit_r2": None,
                "trajectory": [],
                "confidence_note": "Insufficient tracked flight points (<4)",
            }

        peak = arc_peak(self.flight_centers)
        fit_res = fit_parabola(self.flight_centers)
        xs = [c[0] for c in pts]
        curve = []
        r2 = None
        entry_angle = None

        if fit_res is not None:
            coeffs = fit_res[:3]
            r2 = fit_res[3]
            curve = sample_parabola(coeffs, min(xs), max(xs))

            # If custom rim was tracked, calculate entry angle into hoop
            valid_rim = last_valid_box(self.rim_history)
            if valid_rim:
                entry_angle = calculate_entry_angle(coeffs, box_center(valid_rim))

        angle = release_angle
        if angle is None and len(self.ball_history) >= 2:
            angle = release_angle_deg(self.ball_history[-1], last_valid_box(self.ball_history))

        return {
            "result": outcome,
            "release_angle": angle,
            "entry_angle": entry_angle,
            "release_frames": self.release_frames,
            "arc_peak": peak,
            "trajectory_fit_r2": r2,
            "trajectory": curve,
            "flight_centers": list(self.flight_centers),
            "confidence_note": "Verified Parabolic Flight" if (r2 and r2 >= 0.75) else "Estimated Flight Path",
        }

    def reset(self):
        self.release_started = False
        self.release_ended = False
        self.tracking_flight = False
        self.ball_history = []
        self.rim_history = []
        self.flight_centers = []
        self.flight_timestamps = []
        self.release_frames = 0

    def draw(self, frame, info):
        """Render ball trajectory, bounding box, and model transparency banner."""
        if not info:
            return frame

        ball = info.get("ball")
        rim = info.get("rim")
        ball_conf = info.get("ball_conf", 0.0)
        mode = info.get("mode", "coco")

        # 1. Draw Ball Bounding Box & Center
        if ball is not None and ball_conf >= 0.30:
            cx, cy = [int(v) for v in box_center(ball)]
            x1, y1, x2, y2 = [int(v) for v in ball]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 140, 255), -1)
            cv2.putText(
                frame, f"Ball: {ball_conf:.2f}", (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1, cv2.LINE_AA,
            )

        # 2. Draw Rim Bounding Box (if custom weights active)
        if rim is not None:
            rx1, ry1, rx2, ry2 = [int(v) for v in rim]
            cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (0, 255, 0), 2)
            cv2.putText(
                frame, "Basket Rim", (rx1, max(20, ry1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA,
            )

        # 3. Draw Parabolic Flight Path Trail
        centers = info.get("flight_centers", [])
        for i in range(1, len(centers)):
            pt1 = (int(centers[i - 1][0]), int(centers[i - 1][1]))
            pt2 = (int(centers[i][0]), int(centers[i][1]))
            cv2.line(frame, pt1, pt2, (0, 215, 255), 2, cv2.LINE_AA)

        # 4. Ball HUD status badge (Bottom Left)
        height = frame.shape[0]
        mode_text = "YOLO: Stock COCO (Ball Only)" if mode == "coco" else "YOLO: Custom (Ball + Rim)"
        status_text = info.get("status", "idle").upper()
        hud_str = f"{mode_text} | Status: {status_text}"
        cv2.putText(frame, hud_str, (30, height - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1, cv2.LINE_AA)

        return frame


def _wrist_pixels(landmarks, valid=None):
    if not landmarks:
        return []
    pts = []
    for idx in (15, 16):
        if idx in landmarks and (valid is None or valid.get(idx, True)):
            pts.append((landmarks[idx]["x"], landmarks[idx]["y"]))
    return pts


def _shooting_elbow_y(landmarks, valid=None):
    if not landmarks:
        return None
    for idx in (14, 13):
        if idx in landmarks and (valid is None or valid.get(idx, True)):
            return landmarks[idx]["y"]
    return None


def _ball_near_any_wrist(ball, wrists, threshold_px):
    if ball is None or not wrists:
        return False
    center = box_center(ball)
    return any(point_distance(center, w) < threshold_px for w in wrists)


def _ball_above_elbow(ball, elbow_y):
    if ball is None or elbow_y is None:
        return False
    center = box_center(ball)
    return center[1] < elbow_y
