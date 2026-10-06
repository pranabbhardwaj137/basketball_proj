import math
from collections import deque
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Hand landmark indices (MediaPipe 21 Hand Landmarks)
WRIST = 0
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12
RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16
PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]


class HandEngine:
    """MediaPipe hand tracking engine for wrist flick dynamics, snap velocity & finger spread analysis."""

    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"

    def __init__(
        self,
        model_path="hand_landmarker.task",
        num_hands=1,
        detection_confidence=0.5,
        tracking_confidence=0.5,
    ):
        self.model_path = Path(model_path).resolve()
        self._ensure_model()

        base_options = python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=detection_confidence,
            min_hand_tracking_confidence=tracking_confidence,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

        # Flick tracking & velocity history
        self.history = deque(maxlen=15)
        self.prev_time = None
        self.flick_event_cooldown = 0
        self.last_flick_detected = False

    def _ensure_model(self):
        """Auto-download hand_landmarker.task if missing."""
        if not self.model_path.exists():
            print(f"Downloading hand landmarker model to {self.model_path.name}...")
            try:
                import urllib.request
                urllib.request.urlretrieve(self.MODEL_URL, str(self.model_path))
                print("Hand landmarker model downloaded successfully.")
            except Exception as exc:
                raise FileNotFoundError(
                    f"Could not download hand landmarker model: {exc}. "
                    f"Please download manually from {self.MODEL_URL} and save as {self.model_path.name}"
                ) from exc

    def process(self, frame, timestamp_ms, pose_wrist=None, pose_elbow=None):
        """
        Process BGR frame and return dict of hand keypoints, wrist snap velocity,
        flexion angle, and flick event flags.
        """
        if timestamp_ms < 0:
            timestamp_ms = 0

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.detector.detect_for_video(mp_image, int(timestamp_ms))

        if not result.hand_landmarks:
            if self.flick_event_cooldown > 0:
                self.flick_event_cooldown -= 1
            return None

        height, width = frame.shape[:2]
        hand_lm = result.hand_landmarks[0]
        handedness = "Right"
        if result.handedness and len(result.handedness) > 0:
            handedness = result.handedness[0][0].category_name

        landmarks = {}
        for idx, lm in enumerate(hand_lm):
            landmarks[idx] = {
                "norm_x": float(lm.x),
                "norm_y": float(lm.y),
                "norm_z": float(lm.z),
                "x": float(lm.x * width),
                "y": float(lm.y * height),
            }

        # True Biomechanical Wrist Flexion
        # Forearm line (Elbow -> Wrist or Palm base -> Middle MCP) to Hand line (Middle MCP -> Middle TIP)
        wrist_flexion = self.compute_wrist_flexion(landmarks, pose_wrist, pose_elbow)
        finger_spread = self.compute_finger_spread(landmarks)

        # Compute wrist snap angular velocity & flick detection
        now_sec = timestamp_ms / 1000.0 if timestamp_ms is not None else 0.0
        snap_velocity = 0.0
        is_flick = False

        if len(self.history) > 0 and wrist_flexion is not None:
            prev_entry = self.history[-1]
            dt = max(0.008, now_sec - prev_entry["time"])
            if prev_entry["wrist_flexion"] is not None:
                # Snap velocity in deg/sec (positive when flexing forward rapidly)
                snap_velocity = (prev_entry["wrist_flexion"] - wrist_flexion) / dt

        # Store in rolling history
        self.history.append({
            "time": now_sec,
            "wrist_flexion": wrist_flexion,
            "snap_velocity": snap_velocity,
        })

        # Flick detection criteria:
        # 1. High forward angular snap speed (e.g. > 150 deg/sec) or flexion angle dropped below 110 deg
        # 2. Previous frames had wrist cocked back (> 130 deg)
        if self.flick_event_cooldown > 0:
            self.flick_event_cooldown -= 1
        elif len(self.history) >= 4 and wrist_flexion is not None:
            past_flexions = [h["wrist_flexion"] for h in list(self.history)[-5:-1] if h["wrist_flexion"] is not None]
            if past_flexions:
                max_past = max(past_flexions)
                # True flick signature: was cocked (> 130 deg) and snapped down by at least 25 deg
                if max_past >= 130.0 and wrist_flexion <= 115.0 and (max_past - wrist_flexion) >= 20.0:
                    is_flick = True
                    self.flick_event_cooldown = 12  # Cooldown frames (~0.4s)

        self.last_flick_detected = is_flick

        return {
            "landmarks": landmarks,
            "handedness": handedness,
            "wrist_flexion_angle": wrist_flexion,
            "wrist_snap_velocity": round(snap_velocity, 1),
            "finger_spread_ratio": finger_spread,
            "is_flick": is_flick,
            "frame_width": width,
            "frame_height": height,
        }

    @staticmethod
    def compute_wrist_flexion(landmarks, pose_wrist=None, pose_elbow=None):
        """
        Calculate true biomechanical wrist flexion angle.
        If pose keypoints (elbow, wrist) are available, uses Forearm (Elbow->Wrist) vs Hand (Wrist->MiddleMCP).
        Otherwise uses Palm Plane (Wrist->MCP) vs Finger Vector (MCP->Tip).
        Angle ranges: ~170°-180° (neutral/cocked) down to ~80°-95° (fully snapped/flexed).
        """
        if not landmarks or WRIST not in landmarks or MIDDLE_MCP not in landmarks:
            return None

        w = landmarks[WRIST]
        m = landmarks[MIDDLE_MCP]
        t = landmarks.get(MIDDLE_TIP, m)

        if pose_elbow is not None and pose_wrist is not None:
            # Vector 1: Forearm (Elbow -> Wrist)
            vec_forearm = (pose_wrist["norm_x"] - pose_elbow["norm_x"], pose_wrist["norm_y"] - pose_elbow["norm_y"])
            # Vector 2: Hand (Wrist -> Middle Tip)
            vec_hand = (t["norm_x"] - w["norm_x"], t["norm_y"] - w["norm_y"])
            vec1, vec2 = vec_forearm, vec_hand
        else:
            # Approximate via Palm Vector (Wrist -> Middle MCP) and Finger Vector (Middle MCP -> Middle Tip)
            vec1 = (m["norm_x"] - w["norm_x"], m["norm_y"] - w["norm_y"])
            vec2 = (t["norm_x"] - m["norm_x"], t["norm_y"] - m["norm_y"])

        mag1 = math.hypot(vec1[0], vec1[1])
        mag2 = math.hypot(vec2[0], vec2[1])

        if mag1 * mag2 == 0:
            return 180.0

        dot = vec1[0] * vec2[0] + vec1[1] * vec2[1]
        cosine = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        angle_rad = math.acos(cosine)
        return round(math.degrees(angle_rad), 1)

    @staticmethod
    def compute_finger_spread(landmarks):
        """Calculate index-tip to pinky-tip distance normalized by palm width."""
        if not landmarks or INDEX_TIP not in landmarks or PINKY_TIP not in landmarks:
            return None
        if INDEX_MCP not in landmarks or PINKY_MCP not in landmarks:
            return None

        it = landmarks[INDEX_TIP]
        pt = landmarks[PINKY_TIP]
        im = landmarks[INDEX_MCP]
        pm = landmarks[PINKY_MCP]

        tip_dist = math.hypot(it["norm_x"] - pt["norm_x"], it["norm_y"] - pt["norm_y"])
        palm_width = math.hypot(im["norm_x"] - pm["norm_x"], im["norm_y"] - pm["norm_y"])

        if palm_width == 0:
            return 1.0

        return round(tip_dist / palm_width, 2)

    def draw(self, frame, hand_info):
        """Draw hand skeleton connections and flick/spread metrics on frame."""
        if not hand_info or "landmarks" not in hand_info:
            return frame

        landmarks = hand_info["landmarks"]
        width = hand_info["frame_width"]
        height = hand_info["frame_height"]

        # Draw connections
        for p1, p2 in HAND_CONNECTIONS:
            if p1 in landmarks and p2 in landmarks:
                pt1 = (int(landmarks[p1]["norm_x"] * width), int(landmarks[p1]["norm_y"] * height))
                pt2 = (int(landmarks[p2]["norm_x"] * width), int(landmarks[p2]["norm_y"] * height))
                cv2.line(frame, pt1, pt2, (0, 255, 255), 2)

        # Draw landmark points
        for idx, lm in landmarks.items():
            center = (int(lm["norm_x"] * width), int(lm["norm_y"] * height))
            color = (255, 0, 0) if idx in (INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP) else (0, 255, 0)
            cv2.circle(frame, center, 3, color, -1)

        # Draw HUD text for hand metrics
        flick = hand_info.get("wrist_flexion_angle")
        spread = hand_info.get("finger_spread_ratio")
        is_snap = hand_info.get("is_flick", False)
        snap_v = hand_info.get("wrist_snap_velocity", 0.0)

        snap_tag = " [FLICK!]" if is_snap else ""
        text_color = (0, 255, 0) if is_snap else (255, 255, 0)

        text = f"Hand ({hand_info['handedness']}): Flex {flick}° | Spread {spread}x | Snap {snap_v}°/s{snap_tag}"
        cv2.putText(frame, text, (30, height - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_color, 2)

        return frame

    def close(self):
        self.detector.close()
