from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


REQUIRED_LANDMARKS = (11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)


class PoseEngine:
    """MediaPipe pose inference and smoothed landmark feature extraction."""

    def __init__(
        self,
        model_path="pose_landmarker.task",
        detection_confidence=0.5,
        tracking_confidence=0.7,
        smoothing_alpha=0.35,
    ):
        if not 0 < smoothing_alpha <= 1:
            raise ValueError("smoothing_alpha must be between 0 and 1")

        base_options = python.BaseOptions(
            model_asset_path=str(Path(model_path).resolve())
        )
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)
        self.smoothing_alpha = smoothing_alpha
        self._smoothed = {}

    def process(self, frame, timestamp_ms):
        """Return features for one BGR frame, or None when no pose is found."""
        if timestamp_ms < 0:
            raise ValueError("timestamp_ms must be non-negative")

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.detector.detect_for_video(mp_image, int(timestamp_ms))
        if not result.pose_landmarks:
            self._smoothed.clear()
            return None

        height, width = frame.shape[:2]
        landmarks = self._landmarks_to_dict(result.pose_landmarks[0], width, height)
        smoothed = self._smooth(landmarks)
        valid = self._valid_landmarks(landmarks)

        return {
            "landmarks": landmarks,
            "smoothed_landmarks": smoothed,
            "valid": valid,
            "frame_width": width,
            "frame_height": height,
            "timestamp_ms": int(timestamp_ms),
        }

    def _landmarks_to_dict(self, landmarks, width, height):
        return {
            index: {
                "norm_x": float(landmark.x),
                "norm_y": float(landmark.y),
                "norm_z": float(landmark.z),
                "x": float(landmark.x * width),
                "y": float(landmark.y * height),
                "visibility": float(getattr(landmark, "visibility", 0.0)),
                "presence": float(getattr(landmark, "presence", 0.0)),
            }
            for index, landmark in enumerate(landmarks)
        }

    def _smooth(self, landmarks):
        smoothed = {}
        alpha = self.smoothing_alpha
        for index, landmark in landmarks.items():
            previous = self._smoothed.get(index)
            if previous is None:
                current_x = landmark["norm_x"]
                current_y = landmark["norm_y"]
            else:
                current_x = alpha * landmark["norm_x"] + (1 - alpha) * previous["norm_x"]
                current_y = alpha * landmark["norm_y"] + (1 - alpha) * previous["norm_y"]

            smoothed[index] = {
                **landmark,
                "norm_x": current_x,
                "norm_y": current_y,
                "x": current_x * landmark["x"] / landmark["norm_x"] if landmark["norm_x"] else 0.0,
                "y": current_y * landmark["y"] / landmark["norm_y"] if landmark["norm_y"] else 0.0,
            }
        self._smoothed = smoothed
        return smoothed

    @staticmethod
    def _valid_landmarks(landmarks, threshold=0.5):
        return {
            index: (
                landmarks[index]["visibility"] >= threshold
                and landmarks[index]["presence"] >= threshold
            )
            for index in REQUIRED_LANDMARKS
        }

    def close(self):
        self.detector.close()
