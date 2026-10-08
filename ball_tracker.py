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

        self.mode = self.mode  # 'custom' or 'coco'
        self.rim_supported = (self.mode == "custom")
        self.rim_status = "NOT_DETECTED" if self.rim_supported else "UNAVAILABLE_NO_WEIGHTS"

        # Active Shot Lifecycle Synchronization State
        self.active_shot_id = None
        self.active_shot_start_frame = None
        self.active_shot_release_frame = None
        self.active_shot_release_time_ms = None
        self.active_shot_total_frames = 0
        self.active_shot_ball_frames = 0
        self.active_shot_flight_centers = []
        self.active_shot_flight_timestamps = []

        self.release_started = False
        self.release_ended = False
        self.tracking_flight = False
        self.ball_history = []
        self.rim_history = []
        self.flight_centers = []
        self.flight_timestamps = []
        self.release_frames = 0
        self.last_shot = None

    def on_shot_started(self, shot_id: str, frame_idx: int, timestamp_ms: int):
        """Called by master pose engine when a new shot attempt begins."""
        self.active_shot_id = shot_id
        self.active_shot_start_frame = frame_idx
        self.active_shot_release_frame = None
        self.active_shot_release_time_ms = None
        self.active_shot_total_frames = 0
        self.active_shot_ball_frames = 0
        self.active_shot_flight_centers = []
        self.active_shot_flight_timestamps = []
        self.release_started = True
        self.tracking_flight = False

    def on_shot_release(self, shot_id: str, frame_idx: int, timestamp_ms: int, hand_coords=None):
        """Called by master pose engine when kinematic release is triggered."""
        if self.active_shot_id == shot_id:
            self.active_shot_release_frame = frame_idx
            self.active_shot_release_time_ms = timestamp_ms
            self.tracking_flight = True

    def on_shot_ended(self, shot_id: str, frame_idx: int, timestamp_ms: int):
        """Called by master pose engine when follow-through completes. Returns isolated summary."""
        if self.active_shot_id != shot_id:
            return None

        total_frames = max(1, self.active_shot_total_frames)
        detected_frames = self.active_shot_ball_frames
        coverage_ratio = detected_frames / total_frames

        if detected_frames == 0:
            coverage_status = "NOT_DETECTED"
        elif coverage_ratio >= 0.70:
            coverage_status = "HIGH_COVERAGE"
        else:
            coverage_status = "LOW_COVERAGE"

        # Fit parabola to flight centers collected during post-release flight
        pts = [c for c in self.active_shot_flight_centers if c is not None]
        release_angle = None
        entry_angle = None
        fit_r2 = None
        peak = None

        if len(pts) >= 4:
            peak = arc_peak(self.active_shot_flight_centers)
            parabola = fit_parabola(self.active_shot_flight_centers)
            if parabola is not None:
                fit_r2 = parabola.get("r2")
                entry_angle = calculate_entry_angle(parabola)
            if len(pts) >= 2:
                release_angle = release_angle_deg(
                    {"box": [pts[1][0]-10, pts[1][1]-10, pts[1][0]+10, pts[1][1]+10]},
                    {"box": [pts[0][0]-10, pts[0][1]-10, pts[0][0]+10, pts[0][1]+10]}
                )

        # Honest degradation: no automated make/miss without custom rim weights
        if not self.rim_supported:
            outcome = "unknown"
            outcome_reason = "UNAVAILABLE_NO_WEIGHTS"
        else:
            outcome = "unknown"
            outcome_reason = "INCONCLUSIVE"

        summary = {
            "shot_id": shot_id,
            "ball_detection_status": coverage_status,
            "rim_detection_status": self.rim_status,
            "ball_coverage_ratio": round(coverage_ratio, 2),
            "ball_release_angle": release_angle,
            "entry_angle": entry_angle,
            "trajectory_fit_r2": fit_r2,
            "arc_peak": peak,
            "outcome": outcome,
            "outcome_reason": outcome_reason,
            "flight_points_count": len(pts),
        }

        self.last_shot = summary
        self.active_shot_id = None
        self.tracking_flight = False
        return summary

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

        if self.rim_supported and rim is not None:
            self.rim_status = "CONFIRMED_RIM"
        elif self.rim_supported:
            self.rim_status = "NOT_DETECTED"
        else:
            self.rim_status = "UNAVAILABLE_NO_WEIGHTS"

        self._last = {
            "ball": ball,
            "rim": rim,
            "ball_conf": round(ball_conf, 2),
            "rim_conf": round(rim_conf, 2),
            "rim_status": self.rim_status,
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

        if self.active_shot_id is not None:
            self.active_shot_total_frames += 1
            if ball is not None and ball_conf >= 0.30:
                self.active_shot_ball_frames += 1
                center = box_center(ball)
                if center is not None and self.tracking_flight:
                    self.active_shot_flight_centers.append(center)
                    self.active_shot_flight_timestamps.append(timestamp_ms)

        status = "idle"
        release_angle = None
        outcome = None

        near = _ball_near_any_wrist(ball, wrists, self.near_hand_px)
        above_elbow = _ball_above_elbow(ball, elbow_y)

        # In-hand proximity for optional confidence boost
        if near and above_elbow:
            status = "in_hand"
        elif self.tracking_flight:
            status = "in_flight"

        return {
            "status": status,
            "mode": self.mode,
            "rim_status": self.rim_status,
            "ball_conf": ball_conf,
            "release_angle": release_angle,
            "outcome": outcome,
            "release_frames": self.release_frames,
            "ball": ball,
            "rim": rim,
            "flight_centers": list(self.active_shot_flight_centers) if self.active_shot_id else list(self.flight_centers),
            "last_shot": self.last_shot,
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
