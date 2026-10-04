import csv
import math
import os
import time
from collections import deque
from datetime import datetime

import numpy as np


def get_angle_3d(a, b, c):
    """3D or 2D angle at joint b given coordinate dicts or lists."""
    if a is None or b is None or c is None:
        return None

    coords_a = np.array([a[0], a[1], a[2] if len(a) > 2 else 0.0])
    coords_b = np.array([b[0], b[1], b[2] if len(b) > 2 else 0.0])
    coords_c = np.array([c[0], c[1], c[2] if len(c) > 2 else 0.0])

    ba = coords_a - coords_b
    bc = coords_c - coords_b

    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-6:
        return None

    cosine = np.dot(ba, bc) / denom
    cosine = np.clip(cosine, -1.0, 1.0)
    return round(float(np.degrees(np.arccos(cosine))), 1)


def shooting_side(landmarks, valid=None):
    """Determine shooting side based on wrist position and visibility."""
    if not landmarks:
        return 'right'

    left_wrist = landmarks.get(15)
    right_wrist = landmarks.get(16)

    if left_wrist and right_wrist:
        left_y = left_wrist.get('norm_y', 1.0)
        right_y = right_wrist.get('norm_y', 1.0)
        return 'left' if left_y < right_y else 'right'
    if left_wrist:
        return 'left'
    return 'right'


def compute_all_angles(landmarks, valid=None):
    """Compute biomechanical angles across kinetic chain using all 33 pose landmarks."""
    if not landmarks:
        return None

    def pt(idx):
        if idx not in landmarks:
            return None
        lm = landmarks[idx]
        return [lm['norm_x'], lm['norm_y'], lm.get('norm_z', 0.0)]

    def calc_angle(a, b, c):
        pa, pb, pc = pt(a), pt(b), pt(c)
        return get_angle_3d(pa, pb, pc)

    angles = {
        'elbow_right': calc_angle(12, 14, 16),      # shoulder -> elbow -> wrist
        'elbow_left': calc_angle(11, 13, 15),
        'knee_right': calc_angle(24, 26, 28),       # hip -> knee -> ankle
        'knee_left': calc_angle(23, 25, 27),
        'hip_right': calc_angle(12, 24, 26),        # shoulder -> hip -> knee
        'hip_left': calc_angle(11, 23, 25),
        'shoulder_right': calc_angle(14, 12, 24),   # elbow -> shoulder -> hip
        'shoulder_left': calc_angle(13, 11, 23),
    }

    side = shooting_side(landmarks, valid)
    angles['shooting_side'] = side

    if side == 'left':
        angles['elbow_shooting'] = angles['elbow_left']
        angles['knee_shooting'] = angles['knee_left']
        angles['hip_shooting'] = angles['hip_left']
        angles['shoulder_shooting'] = angles['shoulder_left']
    else:
        angles['elbow_shooting'] = angles['elbow_right']
        angles['knee_shooting'] = angles['knee_right']
        angles['hip_shooting'] = angles['hip_right']
        angles['shoulder_shooting'] = angles['shoulder_right']

    return angles


class ShotPhaseDetector:
    """Multi-metric biomechanical shot phase detector with hysteresis & debouncing."""

    def __init__(self, debounce_frames=3):
        self.state = 'idle'
        self.debounce_frames = debounce_frames
        self.candidate_state = 'idle'
        self.candidate_count = 0

        self.prev_wrist_y = None
        self.prev_elbow_angle = None
        self.prev_time = None

    def update(self, landmarks, angles, timestamp_ms=None):
        """Update phase state machine using kinematic velocities and joint positions."""
        if not landmarks or not angles:
            return self.state, 0.0, 0.0

        side = angles.get('shooting_side', 'right')
        wrist_idx = 15 if side == 'left' else 16
        shoulder_idx = 11 if side == 'left' else 12
        nose_idx = 0

        wrist_y = landmarks[wrist_idx]['norm_y'] if wrist_idx in landmarks else 1.0
        shoulder_y = landmarks[shoulder_idx]['norm_y'] if shoulder_idx in landmarks else 1.0
        nose_y = landmarks[nose_idx]['norm_y'] if nose_idx in landmarks else shoulder_y - 0.15

        elbow_angle = angles.get('elbow_shooting') or 120.0
        knee_angle = angles.get('knee_shooting') or 150.0

        now = timestamp_ms / 1000.0 if timestamp_ms is not None else time.time()
        dt = max(0.016, now - self.prev_time) if self.prev_time is not None else 0.033
        self.prev_time = now

        # Compute kinematic velocities
        wrist_v_y = (wrist_y - self.prev_wrist_y) / dt if self.prev_wrist_y is not None else 0.0
        elbow_v_ang = (elbow_angle - self.prev_elbow_angle) / dt if self.prev_elbow_angle is not None else 0.0

        self.prev_wrist_y = wrist_y
        self.prev_elbow_angle = elbow_angle

        # Determine raw candidate phase based on biomechanical metrics
        raw_phase = 'idle'

        # 1. PREPARING (Dip Phase): Knee flexed (<140 deg) or wrist loading below shoulder
        if knee_angle < 140.0 or (wrist_y > shoulder_y and wrist_v_y > 0.05):
            raw_phase = 'preparing'

        # 2. SET_POINT: Wrist at or near head level, elbow bent (65 - 125 deg)
        elif wrist_y <= (shoulder_y + 0.05) and wrist_y >= (nose_y - 0.1) and 60.0 <= elbow_angle <= 125.0:
            raw_phase = 'set_point'

        # 3. RELEASING: Upward wrist velocity (v_y < -0.01), elbow extending (elbow_v_ang > 0), wrist near/above shoulder
        elif wrist_y < (shoulder_y + 0.05) and (wrist_v_y < -0.01 or elbow_v_ang > 10.0) and elbow_angle >= 110.0:
            raw_phase = 'releasing'

        # 4. FOLLOW_THROUGH: Wrist at peak height, elbow fully extended (>=150 deg)
        elif wrist_y < shoulder_y and elbow_angle >= 150.0 and abs(wrist_v_y) < 0.1:
            raw_phase = 'follow_through'

        else:
            raw_phase = 'idle'

        # Debounce state transition to prevent state chatter
        if raw_phase == self.candidate_state:
            self.candidate_count += 1
        else:
            self.candidate_state = raw_phase
            self.candidate_count = 1

        if self.candidate_count >= self.debounce_frames:
            self.state = self.candidate_state

        return self.state, round(wrist_v_y, 4), round(elbow_v_ang, 2)


class SessionRecorder:
    """Records per-shot data using a 45-frame rolling pre-roll buffer."""

    def __init__(self, pre_roll_capacity=45):
        self.shots = []
        self.current_shot = []
        self.frame_history = deque(maxlen=pre_roll_capacity)
        self.recording = False
        self.shot_count = 0
        self.session_start = datetime.now().strftime("%Y%m%d_%H%M%S")

    def push_frame(self, angles, phase="idle"):
        """Continuously push frame angles to the rolling pre-roll buffer."""
        if angles:
            entry = {k: v for k, v in angles.items() if isinstance(v, (int, float))}
            entry['_phase'] = phase
            self.frame_history.append(entry)
            if self.recording:
                self.current_shot.append(entry)

    def start_shot(self):
        """Start recording a shot, pre-populating with 45-frame history for complete knee dip capture."""
        if not self.recording:
            self.recording = True
            # Pre-populate current_shot with full ring buffer history so dip phase is captured
            self.current_shot = list(self.frame_history)

    def add_frame(self, angles):
        """Add current frame to current shot buffer."""
        if self.recording and angles:
            entry = {k: v for k, v in angles.items() if isinstance(v, (int, float))}
            self.current_shot.append(entry)

    def end_shot(self, extra=None):
        """End shot recording and compute shot summary statistics."""
        if self.recording and len(self.current_shot) > 5:
            self.shot_count += 1
            summary = self._summarize_shot(self.current_shot)
            summary['shot_number'] = self.shot_count
            summary['timestamp'] = time.strftime("%H:%M:%S")
            if extra:
                summary.update(extra)
            self.shots.append(summary)
            self.recording = False
            self.current_shot = []
            return summary

        self.recording = False
        self.current_shot = []
        return None

    def _summarize_shot(self, frames):
        """Summarize shot: max elbow (release extension), min knee (dip depth), consistency score."""
        keys = [k for k in frames[0].keys() if not k.startswith('_') and k != 'shooting_side']
        summary = {}

        for key in keys:
            values = [f[key] for f in frames if f.get(key) is not None]
            if not values:
                summary[f'avg_{key}'] = None
                summary[f'std_{key}'] = None
                continue
            summary[f'avg_{key}'] = round(float(np.mean(values)), 1)
            summary[f'std_{key}'] = round(float(np.std(values)), 1)

        elbow_vals = [f['elbow_shooting'] for f in frames if f.get('elbow_shooting') is not None]
        knee_vals = [f['knee_shooting'] for f in frames if f.get('knee_shooting') is not None]

        summary['elbow_at_release'] = round(float(np.max(elbow_vals)), 1) if elbow_vals else None
        summary['knee_at_dip'] = round(float(np.min(knee_vals)), 1) if knee_vals else None

        elbow_std = summary.get('std_elbow_shooting') or summary.get('std_elbow_right') or 15.0
        knee_std = summary.get('std_knee_shooting') or summary.get('std_knee_right') or 15.0
        summary['consistency_score'] = max(0, round(100.0 - (elbow_std + knee_std), 1))

        return summary

    def export_csv(self):
        """Export session data to timestamped CSV file."""
        if not self.shots:
            print("No shots recorded yet.")
            return None
        filename = f"session_{self.session_start}.csv"
        keys = []
        for shot in self.shots:
            for key in shot.keys():
                if key not in keys:
                    keys.append(key)
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.shots)
        print(f"Session saved to {filename}")
        return filename

    def get_session_stats(self):
        """Return session statistics dictionary."""
        if not self.shots:
            return None
        elbow_avgs = [
            s.get('elbow_at_release') or s.get('avg_elbow_shooting')
            for s in self.shots
        ]
        elbow_avgs = [v for v in elbow_avgs if v is not None]
        if not elbow_avgs:
            return {'total_shots': self.shot_count}
        return {
            'total_shots': self.shot_count,
            'avg_elbow_angle': round(float(np.mean(elbow_avgs)), 1),
            'best_elbow_angle': round(float(max(elbow_avgs)), 1),
            'consistency_trend': 'Improving' if elbow_avgs[-1] >= elbow_avgs[0] else 'Needs work'
        }
