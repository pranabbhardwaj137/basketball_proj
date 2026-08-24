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
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return round(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))), 1)

def compute_all_angles(landmarks):
    """
    Returns dict of all relevant basketball angles.
    landmarks: output of extract_landmarks() from pose_engine.py
    """
    if not landmarks:
        return None

    def pt(idx):
        return [landmarks[idx]['norm_x'], landmarks[idx]['norm_y']]

    angles = {
        'elbow_right':    get_angle(pt(12), pt(14), pt(16)),  # shoulder→elbow→wrist
        'elbow_left':     get_angle(pt(11), pt(13), pt(15)),
        'knee_right':     get_angle(pt(24), pt(26), pt(28)),  # hip→knee→ankle
        'knee_left':      get_angle(pt(23), pt(25), pt(27)),
        'hip_right':      get_angle(pt(12), pt(24), pt(26)),  # shoulder→hip→knee
        'hip_left':       get_angle(pt(11), pt(23), pt(25)),
        'shoulder_right': get_angle(pt(14), pt(12), pt(24)), # elbow→shoulder→hip
    }
    return angles

def detect_shot_phase(landmarks, prev_wrist_y, threshold=0.05):
    """
    Detects if player is in shot motion.
    Returns: 'preparing', 'releasing', 'follow_through', 'idle'
    Wrist rising above shoulder = shot initiated.
    """
    if not landmarks:
        return 'idle', prev_wrist_y

    wrist_y   = landmarks[16]['norm_y']   # right wrist (lower value = higher on screen)
    shoulder_y = landmarks[12]['norm_y']  # right shoulder
    elbow_y    = landmarks[14]['norm_y']  # right elbow

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
            self.current_shot.append(angles)

    def end_shot(self):
        if self.recording and len(self.current_shot) > 5:
            self.shot_count += 1
            summary = self._summarize_shot(self.current_shot)
            summary['shot_number'] = self.shot_count
            summary['timestamp'] = time.strftime("%H:%M:%S")
            self.shots.append(summary)
            self.recording = False
            self.current_shot = []
            return summary
        self.recording = False
        return None

    def _summarize_shot(self, frames):
        """Average angles + consistency score across all frames of one shot"""
        keys = frames[0].keys()
        summary = {}
        for key in keys:
            values = [f[key] for f in frames]
            summary[f'avg_{key}'] = round(np.mean(values), 1)
            summary[f'std_{key}'] = round(np.std(values), 1)

        # Consistency score: lower std deviation = more consistent
        elbow_std = summary.get('std_elbow_right', 20)
        knee_std  = summary.get('std_knee_right', 20)
        summary['consistency_score'] = max(0, round(100 - (elbow_std + knee_std), 1))

        return summary

    def export_csv(self):
        if not self.shots:
            print("No shots recorded yet.")
            return
        filename = f"session_{self.session_start}.csv"
        keys = self.shots[0].keys()
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.shots)
        print(f"Session saved to {filename}")
        return filename

    def get_session_stats(self):
        if not self.shots:
            return None
        elbow_avgs = [s['avg_elbow_right'] for s in self.shots]
        return {
            'total_shots': self.shot_count,
            'avg_elbow_angle': round(np.mean(elbow_avgs), 1),
            'best_elbow_angle': round(max(elbow_avgs), 1),
            'consistency_trend': 'Improving' if elbow_avgs[-1] > elbow_avgs[0] else 'Needs work'
        }
