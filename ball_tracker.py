"""In-memory ball/rim tracker.

Logic comes from clones/basketball-shot-analysis:
  - release starts when the ball is above the shooting elbow and near a wrist
  - release ends when the ball leaves the hand
  - make/miss uses ball-under-rim and growing ball-rim distance
  - reset when the ball returns to the body

Inference is Ultralytics YOLO in memory (no temp.jpg / yolov5.detect disk runs).
Custom `weights/basket_rim.pt` (class 0=ball, class 2=rim) is preferred.
Otherwise YOLOv8n COCO `sports ball` is used and rim/make-miss stay unavailable.
"""

from pathlib import Path

import cv2

from ball_geometry import (
    arc_peak,
    ball_under_rim,
    box_center,
    box_to_point_distance,
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
            "Ball tracking needs ultralytics. pip install ultralytics"
        ) from exc

    custom = Path(weights_path) if weights_path else Path("weights/basket_rim.pt")
    if custom.exists():
        return YOLO(str(custom)), "custom"
    return YOLO("yolov8n.pt"), "coco"


class BallTracker:
    def __init__(
        self,
        weights_path=None,
        conf=0.25,
        near_hand_px=120,
        leave_hand_px=140,
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
        self.release_frames = 0
        self.last_shot = None

    def detect(self, frame):
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
            "ball_conf": ball_conf,
            "rim_conf": rim_conf,
        }
        return dict(self._last)

    def update(self, detections, landmarks, valid=None):
        """Advance the release / make-miss state machine. Returns overlay info."""
        wrists = _wrist_pixels(landmarks, valid)
        elbow_y = _shooting_elbow_y(landmarks, valid)
        ball = detections.get("ball")
        rim = detections.get("rim")

        self.ball_history.append(ball)
        self.rim_history.append(rim)

        status = "idle"
        release_angle = None
        outcome = None

        near = _ball_near_any_wrist(ball, wrists, self.near_hand_px)
        above_elbow = _ball_above_elbow(ball, elbow_y)

        if not self.release_started:
            if above_elbow and near:
                self.release_started = True
                self.release_ended = False
                self.tracking_flight = False
                self.release_frames = 0
                self.flight_centers = []
                status = "release_started"
            else:
                status = "idle"

        elif self.release_started and not self.release_ended:
            self.release_frames += 1
            center = box_center(ball)
            if center is not None:
                self.flight_centers.append(center)
            left_hand = _ball_near_any_wrist(ball, wrists, self.leave_hand_px)
            if ball is not None and not left_hand:
                self.release_ended = True
                self.tracking_flight = True
                prev = last_valid_box(self.ball_history)
                release_angle = release_angle_deg(ball, prev)
                status = "release_ended"
            else:
                status = "releasing"

        elif self.release_started and self.release_ended and self.tracking_flight:
            self.release_frames += 1
            center = box_center(ball)
            if center is not None:
                self.flight_centers.append(center)

            outcome = self._judge_make_miss(ball, rim)
            if outcome is not None:
                self.last_shot = self._close_shot(outcome, release_angle)
                status = outcome.lower()
                self.tracking_flight = False
            else:
                status = "in_flight"

        if (
            self.release_started
            and self.release_ended
            and _ball_near_any_wrist(ball, wrists, 50)
        ):
            if self.tracking_flight:
                self.last_shot = self._close_shot("unknown", release_angle)
            self.reset()
            status = "reset"

        return {
            "status": status,
            "release_angle": release_angle,
            "outcome": outcome,
            "release_frames": self.release_frames,
            "ball": ball,
            "rim": rim,
            "flight_centers": list(self.flight_centers),
            "last_shot": self.last_shot,
        }

    def _judge_make_miss(self, ball, rim):
        if ball is None or rim is None:
            return None
        if ball_under_rim(ball, rim, x_threshold=100):
            return "Make"
        if len(self.ball_history) < 2 or len(self.rim_history) < 2:
            return None
        prev_ball = last_valid_box(self.ball_history)
        prev_rim = last_valid_box(self.rim_history)
        now_d = point_distance(box_center(ball), box_center(rim))
        prev_d = point_distance(box_center(prev_ball), box_center(prev_rim))
        if now_d is None or prev_d is None:
            return None
        if now_d > prev_d:
            return "Make" if ball_under_rim(ball, rim, x_threshold=70) else "Miss"
        return None

    def _close_shot(self, outcome, release_angle):
        peak = arc_peak(self.flight_centers)
        coeffs = fit_parabola(self.flight_centers)
        xs = [c[0] for c in self.flight_centers if c is not None]
        curve = []
        if coeffs is not None and xs:
            curve = sample_parabola(coeffs, min(xs), max(xs))
        angle = release_angle
        if angle is None and len(self.ball_history) >= 2:
            angle = release_angle_deg(self.ball_history[-1], last_valid_box(self.ball_history))
        return {
            "result": outcome,
            "release_angle": angle,
            "release_frames": self.release_frames,
            "arc_peak": peak,
            "trajectory": curve,
            "flight_centers": list(self.flight_centers),
        }

    def reset(self):
        self.release_started = False
        self.release_ended = False
        self.tracking_flight = False
        self.ball_history = []
        self.rim_history = []
        self.flight_centers = []
        self.release_frames = 0

    def draw(self, frame, info):
        ball = info.get("ball")
        rim = info.get("rim")
        if ball is not None:
            cx, cy = [int(v) for v in box_center(ball)]
            cv2.circle(frame, (cx, cy), 18, (255, 0, 0), 2)
            cv2.putText(frame, "BALL", (cx - 20, cy - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        if rim is not None:
            x1, y1, x2, y2 = [int(v) for v in rim]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (48, 124, 255), 2)
            cv2.putText(frame, "RIM", (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (48, 124, 255), 1)

        curve = []
        if self.last_shot and self.last_shot.get("trajectory"):
            curve = self.last_shot["trajectory"]
        elif len(info.get("flight_centers") or []) >= 3:
            coeffs = fit_parabola(info["flight_centers"])
            xs = [c[0] for c in info["flight_centers"]]
            curve = sample_parabola(coeffs, min(xs), max(xs)) if coeffs else []
        for i in range(1, len(curve)):
            p1 = (int(curve[i - 1][0]), int(curve[i - 1][1]))
            p2 = (int(curve[i][0]), int(curve[i][1]))
            cv2.line(frame, p1, p2, (0, 0, 255), 2)

        status = info.get("status", "")
        cv2.putText(frame, f"Ball: {status}", (30, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 140, 255), 2)
        angle = info.get("release_angle")
        if angle is not None:
            cv2.putText(frame, f"Release: {angle:.1f} deg", (30, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        return frame


def _wrist_pixels(landmarks, valid):
    if not landmarks:
        return []
    points = []
    for idx in (15, 16):
        if valid is not None and not valid.get(idx, False):
            continue
        points.append((landmarks[idx]["x"], landmarks[idx]["y"]))
    return points


def _shooting_elbow_y(landmarks, valid):
    """Elbow of the higher wrist (typical shooting arm)."""
    if not landmarks:
        return None
    left_ok = valid is None or valid.get(15, False)
    right_ok = valid is None or valid.get(16, False)
    if left_ok and right_ok:
        shooting_right = landmarks[16]["y"] < landmarks[15]["y"]
    else:
        shooting_right = right_ok
    elbow_idx = 14 if shooting_right else 13
    if valid is not None and not valid.get(elbow_idx, False):
        return None
    return landmarks[elbow_idx]["y"]


def _ball_near_any_wrist(ball, wrists, threshold):
    if ball is None or not wrists:
        return False
    for wrist in wrists:
        dist = box_to_point_distance(ball, wrist)
        if dist is not None and dist < threshold:
            return True
    return False


def _ball_above_elbow(ball, elbow_y):
    if ball is None or elbow_y is None:
        return False
    return ball[3] < elbow_y
