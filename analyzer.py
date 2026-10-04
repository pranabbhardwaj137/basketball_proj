# analyzer.py

import numpy as np
import csv
import time
from datetime import datetime

# ── PAVAN'S PART ──────────────────────────────────────────────

def get_angle(a, b, c):
    """Angle at joint b given three (x,y) coordinate pairs"""
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    denominator = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denominator < 1e-6:
        return None
    cosine = np.dot(ba, bc) / denominator
    return round(float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))), 1)

def compute_all_angles(landmarks, valid=None):
    """
    Returns dict of all relevant basketball angles.
    landmarks: output of extract_landmarks() from pose_engine.py
    """
    if not landmarks:
        return None

    def pt(idx):
        if valid is not None and not valid.get(idx, False):
            return None
        return [landmarks[idx]['norm_x'], landmarks[idx]['norm_y']]

    def angle(a, b, c):
        points = (pt(a), pt(b), pt(c))
        if any(point is None for point in points):
            return None
        return get_angle(*points)

    angles = {
        'elbow_right':    angle(12, 14, 16),
        'elbow_left':     angle(11, 13, 15),
        'knee_right':     angle(24, 26, 28),
        'knee_left':      angle(23, 25, 27),
        'hip_right':      angle(12, 24, 26),
        'hip_left':       angle(11, 23, 25),
        'shoulder_right': angle(14, 12, 24),
    }
    side = shooting_side(landmarks, valid)
    angles['shooting_side'] = side
    if side == 'left':
        angles['elbow_shooting'] = angles['elbow_left']
        angles['knee_shooting'] = angles['knee_left']
        angles['hip_shooting'] = angles['hip_left']
    else:
        angles['elbow_shooting'] = angles['elbow_right']
        angles['knee_shooting'] = angles['knee_right']
        angles['hip_shooting'] = angles['hip_right']
    return angles


def shooting_side(landmarks, valid=None):
    """Higher wrist (smaller y) is treated as the shooting hand."""
    if not landmarks:
        return 'right'
    left_ok = valid is None or valid.get(15, True)
    right_ok = valid is None or valid.get(16, True)
    if left_ok and right_ok:
        return 'left' if landmarks[15]['norm_y'] < landmarks[16]['norm_y'] else 'right'
    if left_ok:
        return 'left'
    return 'right'

def detect_shot_phase(landmarks, prev_wrist_y, threshold=0.05):
    """
    Detects if player is in shot motion.
    Returns: 'preparing', 'releasing', 'follow_through', 'idle'
    Wrist rising above shoulder = shot initiated.
    """
    if not landmarks:
        return 'idle', prev_wrist_y

    side = shooting_side(landmarks)
    if side == 'left':
        wrist_y = landmarks[15]['norm_y']
        shoulder_y = landmarks[11]['norm_y']
        elbow_y = landmarks[13]['norm_y']
    else:
        wrist_y = landmarks[16]['norm_y']
        shoulder_y = landmarks[12]['norm_y']
        elbow_y = landmarks[14]['norm_y']

    wrist_rising = (prev_wrist_y - wrist_y) > threshold  # wrist moving up

    if wrist_y < shoulder_y and elbow_y < shoulder_y:
        phase = 'releasing'
    elif wrist_rising and wrist_y > shoulder_y:
        phase = 'preparing'
    elif wrist_y < prev_wrist_y - 0.02:
        phase = 'follow_through'
    else:
        phase = 'idle'

    return phase, wrist_y

# ── PRACHETH'S PART ───────────────────────────────────────────

class SessionRecorder:
    """Records per-shot data across the session"""

    def __init__(self):
        self.shots = []           # list of shot dicts
        self.current_shot = []    # angle frames for current shot
        self.recording = False
        self.shot_count = 0
        self.session_start = datetime.now().strftime("%Y%m%d_%H%M%S")

    def start_shot(self):
        if not self.recording:
            self.recording = True
            self.current_shot = []

    def add_frame(self, angles):
        if self.recording and angles:
            numeric = {k: v for k, v in angles.items() if isinstance(v, (int, float))}
            self.current_shot.append(numeric)

    def end_shot(self, extra=None):
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
        return None

    def _summarize_shot(self, frames):
        """Event-aware angles: max elbow (release), min knee (dip), plus averages."""
        keys = [k for k in frames[0].keys() if k != 'shooting_side']
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

        elbow_std = summary.get('std_elbow_shooting') or summary.get('std_elbow_right') or 20
        knee_std = summary.get('std_knee_shooting') or summary.get('std_knee_right') or 20
        summary['consistency_score'] = max(0, round(100 - (elbow_std + knee_std), 1))
        return summary

    def export_csv(self):
        if not self.shots:
            print("No shots recorded yet.")
            return
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
        if not self.shots:
            return None
        elbow_avgs = [
            s.get('elbow_at_release') or s.get('avg_elbow_shooting') or s.get('avg_elbow_right')
            for s in self.shots
        ]
        elbow_avgs = [v for v in elbow_avgs if v is not None]
        if not elbow_avgs:
            return {'total_shots': self.shot_count}
        return {
            'total_shots': self.shot_count,
            'avg_elbow_angle': round(float(np.mean(elbow_avgs)), 1),
            'best_elbow_angle': round(float(max(elbow_avgs)), 1),
            'consistency_trend': 'Improving' if elbow_avgs[-1] > elbow_avgs[0] else 'Needs work'
        }
