Let me read the project context first to align the division properly.Got the context. You have 4 members and 3 sections, so Section 2 gets 2 people since it's the heaviest. Here's the full breakdown:

---

## Demo Division — 3 Sections, 4 Members

```
Section 1: Core Vision Layer       → Pranab (you)
Section 2: Analysis Engine         → Pavan + Pracheth
Section 3: Feedback & Output       → Puneetgouda
```

Each section is a **separate Python file** that plugs into the others. Nobody steps on each other's code.

---

## Section 1 — Core Vision Layer

### Owner: Pranab Bhardwaj

**File: `pose_engine.py`**

This is the foundation everything runs on. You already have it mostly built — polish and modularize it.

**Deliverables:**

- Clean webcam + video file input (toggle with a flag)
- Skeleton drawing with color-coded confidence (green = high, yellow = medium, red = low visibility)
- Landmark extraction as a clean dictionary other modules can consume
- FPS counter on screen
- Ability to pause/resume with spacebar

```python
# pose_engine.py

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time

# Landmark name map for clean output
LANDMARK_NAMES = {
    11: "LEFT_SHOULDER",  12: "RIGHT_SHOULDER",
    13: "LEFT_ELBOW",     14: "RIGHT_ELBOW",
    15: "LEFT_WRIST",     16: "RIGHT_WRIST",
    23: "LEFT_HIP",       24: "RIGHT_HIP",
    25: "LEFT_KNEE",      26: "RIGHT_KNEE",
    27: "LEFT_ANKLE",     28: "RIGHT_ANKLE"
}

CONNECTIONS = [
    (11,12),(11,13),(13,15),(12,14),(14,16),
    (11,23),(12,24),(23,24),
    (23,25),(25,27),(24,26),(26,28)
]

def load_detector(model_path='pose_landmarker.task'):
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        num_poses=1,
        min_pose_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )
    return vision.PoseLandmarker.create_from_options(options)

def extract_landmarks(result, frame_w, frame_h):
    """Returns a clean dict: {index: {'x': px, 'y': px, 'norm_x': 0-1, 'norm_y': 0-1, 'visibility': 0-1}}"""
    if not result.pose_landmarks:
        return None
    lm = result.pose_landmarks[0]
    landmarks = {}
    for idx in LANDMARK_NAMES:
        landmarks[idx] = {
            'x': int(lm[idx].x * frame_w),
            'y': int(lm[idx].y * frame_h),
            'norm_x': lm[idx].x,
            'norm_y': lm[idx].y,
            'visibility': lm[idx].visibility
        }
    return landmarks

def draw_skeleton(frame, landmarks):
    """Draws skeleton with color based on visibility confidence"""
    if not landmarks:
        return frame
    h, w = frame.shape[:2]

    for a, b in CONNECTIONS:
        if a not in landmarks or b not in landmarks:
            continue
        vis = min(landmarks[a]['visibility'], landmarks[b]['visibility'])
        # Green = confident, Yellow = medium, Red = low
        if vis > 0.7:
            color = (0, 255, 0)
        elif vis > 0.4:
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)
        cv2.line(frame, (landmarks[a]['x'], landmarks[a]['y']),
                         (landmarks[b]['x'], landmarks[b]['y']), color, 2)

    for idx, data in landmarks.items():
        cv2.circle(frame, (data['x'], data['y']), 5, (255, 255, 255), -1)

    return frame

def run_camera(source=0):
    """Main loop — yields (frame, landmarks) each iteration"""
    detector = load_detector()
    cap = cv2.VideoCapture(source)
    prev_time = time.time()
    paused = False

    while cap.isOpened():
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = detector.detect(mp_image)

            landmarks = extract_landmarks(result, w, h)
            frame = draw_skeleton(frame, landmarks)

            # FPS counter
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time
            cv2.putText(frame, f"FPS: {fps:.1f}", (w-120, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)

            yield frame, landmarks

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = not paused

    cap.release()
    detector.close()
```

**Demo talking point:** "This module is the eyes of the system. It processes every frame, detects the player's skeleton with confidence-based coloring, and outputs structured landmark data that the analysis engine consumes."

---

## Section 2 — Analysis Engine

### Owners: Pavan R Bhat + Pracheth Kashyap

**File: `analyzer.py`**

This is the brain. Takes landmarks from Section 1, computes all angles, detects the shot moment, and records session data.

**Pavan handles:** Angle calculations + shot detection logic
**Pracheth handles:** Session recording + CSV export + consistency scoring

```python
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
```

**Demo talking point — Pavan:** "I built the angle computation engine and the shot phase detector. The system identifies exactly when a player enters the release phase by tracking the wrist trajectory relative to the shoulder in real time."

**Demo talking point — Pracheth:** "I built the session recorder that collects angle data across every shot, computes consistency scores using standard deviation, and exports the full session to CSV for post-analysis."

---

## Section 3 — Feedback & Output Layer

### Owner: Puneetgouda Patil

**File: `feedback.py`**

This is the face of the system. Takes the analyzed data and produces feedback text on screen, angle-over-time graphs, and a session summary panel.

```python
# feedback.py

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # non-interactive backend for saving plots

# ── RULE-BASED FEEDBACK ENGINE ─────────────────────────────────

THRESHOLDS = {
    'elbow_right':    {'good': (155, 180), 'warn': (130, 155), 'label': 'Arm Extension'},
    'knee_right':     {'good': (100, 135), 'warn': (135, 160), 'label': 'Knee Bend'},
    'hip_right':      {'good': (145, 175), 'warn': (120, 145), 'label': 'Hip Posture'},
    'shoulder_right': {'good': (70, 110),  'warn': (50, 70),   'label': 'Shoulder Angle'},
}

COACHING_TIPS = {
    'elbow_right': {
        'low':  "Extend your arm fully at release",
        'high': "Arm extension looks good!",
        'warn': "Almost there — push through more"
    },
    'knee_right': {
        'low':  "Bend knees more for jump power",
        'high': "Good knee bend!",
        'warn': "Slight knee bend — push lower"
    },
    'hip_right': {
        'low':  "Stand straighter — avoid forward lean",
        'high': "Body posture is solid",
        'warn': "Slight lean — try to balance"
    }
}

def evaluate_angles(angles):
    """Returns list of feedback items per angle"""
    if not angles:
        return []

    feedback = []
    for key, cfg in THRESHOLDS.items():
        if key not in angles:
            continue
        val = angles[key]
        lo, hi = cfg['good']
        wlo, whi = cfg['warn']

        if lo <= val <= hi:
            status = 'GOOD'
            color = (0, 200, 0)
        elif wlo <= val < lo or hi < val <= whi:
            status = 'OKAY'
            color = (0, 200, 255)
        else:
            status = 'FIX'
            color = (0, 0, 255)

        tip = ''
        if key in COACHING_TIPS:
            tip = COACHING_TIPS[key]['high'] if status == 'GOOD' else \
                  COACHING_TIPS[key]['warn'] if status == 'OKAY' else \
                  COACHING_TIPS[key]['low']

        feedback.append({
            'label': cfg['label'],
            'value': val,
            'status': status,
            'color': color,
            'tip': tip
        })
    return feedback

def draw_feedback_panel(frame, feedback_items, shot_phase, shot_count):
    """Draws a dark semi-transparent feedback sidebar on the right side"""
    h, w = frame.shape[:2]
    panel_w = 280
    overlay = frame.copy()

    # Dark background panel
    cv2.rectangle(overlay, (w - panel_w, 0), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    x = w - panel_w + 10
    y = 30

    # Header
    cv2.putText(frame, "COACH PANEL", (x, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 165, 0), 2)
    y += 25
    cv2.line(frame, (x, y), (w-10, y), (80, 80, 80), 1)
    y += 20

    # Shot phase indicator
    phase_color = {'releasing': (0,255,0), 'preparing': (0,255,255),
                   'follow_through': (255,165,0), 'idle': (150,150,150)}
    pcolor = phase_color.get(shot_phase, (150,150,150))
    cv2.putText(frame, f"Phase: {shot_phase.upper()}", (x, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, pcolor, 1)
    y += 20
    cv2.putText(frame, f"Shots recorded: {shot_count}", (x, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
    y += 30
    cv2.line(frame, (x, y), (w-10, y), (80, 80, 80), 1)
    y += 20

    # Per-angle feedback rows
    for item in feedback_items:
        status_icons = {'GOOD': '[+]', 'OKAY': '[~]', 'FIX': '[!]'}
        icon = status_icons.get(item['status'], '[ ]')
        text = f"{icon} {item['label']}: {item['value']}"
        cv2.putText(frame, text, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, item['color'], 1)
        y += 18
        cv2.putText(frame, f"    {item['tip']}", (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180,180,180), 1)
        y += 22

    return frame

def generate_shot_graph(shots, filename='shot_analysis.png'):
    """Generates a multi-angle trend graph across all shots in session"""
    if not shots:
        return

    shot_nums = [s['shot_number'] for s in shots]
    elbow_angles = [s['avg_elbow_right'] for s in shots]
    knee_angles  = [s['avg_knee_right']  for s in shots]
    consistency  = [s['consistency_score'] for s in shots]

    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    fig.patch.set_facecolor('#1a1a2e')

    for ax in axes:
        ax.set_facecolor('#16213e')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('#444')
        ax.spines['left'].set_color('#444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    # Plot 1: Elbow angle with good zone shaded
    axes[0].plot(shot_nums, elbow_angles, 'o-', color='#00d4ff', linewidth=2, markersize=6)
    axes[0].axhspan(155, 180, alpha=0.15, color='green', label='Good zone (155-180)')
    axes[0].set_ylabel('Degrees', color='white')
    axes[0].set_title('Elbow Angle at Release', color='white', fontsize=11)
    axes[0].legend(facecolor='#1a1a2e', labelcolor='white', fontsize=8)
    axes[0].set_ylim(60, 190)

    # Plot 2: Knee angle with good zone
    axes[1].plot(shot_nums, knee_angles, 's-', color='#ff6b6b', linewidth=2, markersize=6)
    axes[1].axhspan(100, 135, alpha=0.15, color='green', label='Good zone (100-135)')
    axes[1].set_ylabel('Degrees', color='white')
    axes[1].set_title('Knee Bend Angle', color='white', fontsize=11)
    axes[1].legend(facecolor='#1a1a2e', labelcolor='white', fontsize=8)

    # Plot 3: Consistency score bar chart
    colors = ['#00b894' if c >= 70 else '#fdcb6e' if c >= 50 else '#e17055'
              for c in consistency]
    axes[2].bar(shot_nums, consistency, color=colors)
    axes[2].set_ylabel('Score', color='white')
    axes[2].set_xlabel('Shot Number', color='white')
    axes[2].set_title('Form Consistency Score', color='white', fontsize=11)
    axes[2].set_ylim(0, 100)
    axes[2].axhline(70, color='#00b894', linestyle='--', alpha=0.5, label='Target (70+)')
    axes[2].legend(facecolor='#1a1a2e', labelcolor='white', fontsize=8)

    plt.tight_layout(pad=2.0)
    plt.savefig(filename, dpi=120, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"Graph saved: {filename}")
    return filename

def print_session_summary(stats):
    """Console summary printed at end of session"""
    if not stats:
        print("No shots recorded this session.")
        return
    print("\n" + "="*40)
    print("   SESSION SUMMARY")
    print("="*40)
    print(f"  Total Shots    : {stats['total_shots']}")
    print(f"  Avg Elbow Angle: {stats['avg_elbow_angle']}°")
    print(f"  Best Shot      : {stats['best_elbow_angle']}°")
    print(f"  Trend          : {stats['consistency_trend']}")
    print("="*40 + "\n")
```

**Demo talking point:** "I built the entire output layer. The feedback panel uses a color-coded coaching system — green means good form, yellow means nearly there, red means needs fixing. At the end of each session, the system generates a multi-chart performance report showing angle trends and consistency scores across every shot."

---

## The Integration File (Main Entry Point)

### Everyone understands this — run to demo

```python
# main.py — integrates all 3 sections

from pose_engine import run_camera       # Section 1 - Pranab
from analyzer import (                   # Section 2 - Pavan + Pracheth
    compute_all_angles,
    detect_shot_phase,
    SessionRecorder
)
from feedback import (                   # Section 3 - Puneetgouda
    evaluate_angles,
    draw_feedback_panel,
    generate_shot_graph,
    print_session_summary
)
import cv2

recorder = SessionRecorder()
prev_wrist_y = 1.0
prev_phase = 'idle'

print("Press Q to quit | SPACE to pause | S to save session")

for frame, landmarks in run_camera(source=0):  # swap 0 for "video.mp4"

    angles = compute_all_angles(landmarks)
    phase, prev_wrist_y = detect_shot_phase(landmarks, prev_wrist_y)

    # Auto-record shots based on phase transitions
    if prev_phase != 'releasing' and phase == 'releasing':
        recorder.start_shot()
    if prev_phase == 'releasing' and phase != 'releasing':
        shot_summary = recorder.end_shot()
        if shot_summary:
            print(f"Shot {shot_summary['shot_number']} | "
                  f"Elbow: {shot_summary['avg_elbow_right']}° | "
                  f"Consistency: {shot_summary['consistency_score']}")
    prev_phase = phase

    if recorder.recording:
        recorder.add_frame(angles)

    feedback_items = evaluate_angles(angles)
    frame = draw_feedback_panel(frame, feedback_items, phase, recorder.shot_count)

    cv2.imshow("Basketball Coach", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        recorder.export_csv()
        generate_shot_graph(recorder.shots)
        print_session_summary(recorder.get_session_stats())

cv2.destroyAllWindows()
```

---

## What This Covers (Objectives Check)

| Project Objective       | Covered By              | Status |
| ----------------------- | ----------------------- | ------ |
| Pose Estimation         | Section 1               | Done   |
| Real-time tracking      | Section 1               | Done   |
| Joint angle computation | Section 2 (Pavan)       | Done   |
| Shot detection          | Section 2 (Pavan)       | Done   |
| Session data recording  | Section 2 (Pracheth)    | Done   |
| Consistency scoring     | Section 2 (Pracheth)    | Done   |
| Visual feedback         | Section 3 (Puneetgouda) | Done   |
| Performance graphs      | Section 3 (Puneetgouda) | Done   |
| CSV export              | Section 2 (Pracheth)    | Done   |

That's roughly **55-60% of total objectives** — enough for a solid first demo without ball tracking or the LSTM model, which can be Phase 2.

**Install one extra package** before the demo:

```bash
pip install matplotlib
```

Want me to clean this up into a proper demo script or add voice feedback too?
