# Project Context: Intelligent Basketball Performance Analysis System

## Feed this document to any AI model to get context-aware help on this project.

---

## What This Project Is

A real-time computer vision basketball coaching tool built in Python. It analyzes a player's shooting form from video (webcam or file), detects body pose using AI, computes biomechanical angles, and gives instant feedback on shooting technique.

**Short version:** Point a camera at someone shooting a basketball. The system draws a skeleton on them, measures their elbow and knee angles, and tells them if their form is good or needs fixing.

---

## Developer Profile

- **Name:** Pranab Bhardwaj (goes by Prab)
- **Background:** Final year Information Science & Engineering, BMSIT&M Bengaluru
- **Skill level:** Intermediate Python, strong React/JS frontend, comfortable with OpenCV and NumPy basics, learning MediaPipe and computer vision from scratch on this project
- **Style preference:** Prefers concise explanations with working code examples. Learns better from concrete examples than theory alone.
- **Existing tech stack:** Python, JavaScript, React, Node.js, OpenCV, NumPy, Pandas, Matplotlib, n8n, Gemini API

---

## Academic Context

- **Course:** BCS506 Major Project, Bachelor of Engineering in Information Science & Engineering
- **University:** Visvesvaraya Technological University (VTU), Belagavi
- **Institution:** BMS Institute of Technology & Management (BMSIT&M), Bengaluru
- **Year:** 2025-26
- **Guide:** Asst. Prof. Amulya P, Department of ISE
- **Team Members:** Pranab Bhardwaj (1BY23IS154), Pavan R Bhat (1BY23IS145), Pracheth Kashyap (1BY23IS152), Puneetgouda Patil (1BY23IS165)

---

## Current Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12.6 |
| Pose Detection | MediaPipe 0.10.x (new Tasks API — NOT mp.solutions) |
| Pose Model | `pose_landmarker_heavy.task` (BlazePose GHUM, 29MB) |
| Video Processing | OpenCV (cv2) |
| Math/Angles | NumPy |
| Environment | Windows 11, VS Code, .venv |
| IDE | VS Code with Python extension |

### CRITICAL: MediaPipe Version Note

This project uses **Python 3.12.6** which is NOT compatible with `mediapipe==0.10.9` (the old `mp.solutions.pose` API). We are using the **new Tasks API**:

```python
# OLD API (does NOT work on Python 3.12):
mp_pose = mp.solutions.pose  # ← BREAKS

# NEW API (what we use):
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
detector = vision.PoseLandmarker.create_from_options(options)
result = detector.detect(mp_image)
landmarks = result.pose_landmarks[0]  # list of 33 NormalizedLandmark objects
# Each landmark has: .x, .y, .z (normalized 0-1), .visibility (0-1)
```

---

## Current Working Code (main.py)

```python
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

base_options = python.BaseOptions(model_asset_path='pose_landmarker.task')
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    num_poses=1,
    min_pose_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.PoseLandmarker.create_from_options(options)

CONNECTIONS = [
    (11,12),(11,13),(13,15),(12,14),(14,16),
    (11,23),(12,24),(23,24),
    (23,25),(25,27),(24,26),(26,28)
]

def get_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = detector.detect(mp_image)

    if result.pose_landmarks:
        lm = result.pose_landmarks[0]

        for a, b in CONNECTIONS:
            x1, y1 = int(lm[a].x * w), int(lm[a].y * h)
            x2, y2 = int(lm[b].x * w), int(lm[b].y * h)
            cv2.line(frame, (x1,y1), (x2,y2), (0,255,0), 2)

        for landmark in lm:
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (cx, cy), 4, (0,0,255), -1)

        shoulder = [lm[12].x, lm[12].y]
        elbow    = [lm[14].x, lm[14].y]
        wrist    = [lm[16].x, lm[16].y]
        elbow_angle = get_angle(shoulder, elbow, wrist)

        hip   = [lm[24].x, lm[24].y]
        knee  = [lm[26].x, lm[26].y]
        ankle = [lm[28].x, lm[28].y]
        knee_angle = get_angle(hip, knee, ankle)

        cv2.putText(frame, f"Elbow: {elbow_angle:.1f}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)
        cv2.putText(frame, f"Knee:  {knee_angle:.1f}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)

        feedback = "Good form!" if elbow_angle > 150 else "Extend your arm more"
        cv2.putText(frame, feedback, (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

    cv2.imshow("Basketball Coach", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()
```

---

## MediaPipe Landmark Index Reference

```
# Face
0  = Nose
1  = Left Eye Inner
2  = Left Eye
3  = Left Eye Outer
4  = Right Eye Inner
5  = Right Eye
6  = Right Eye Outer
7  = Left Ear
8  = Right Ear
9  = Mouth Left
10 = Mouth Right

# Upper Body
11 = Left Shoulder
12 = Right Shoulder
13 = Left Elbow
14 = Right Elbow
15 = Left Wrist
16 = Right Wrist
17 = Left Pinky
18 = Right Pinky
19 = Left Index
20 = Right Index
21 = Left Thumb
22 = Right Thumb

# Lower Body
23 = Left Hip
24 = Right Hip
25 = Left Knee
26 = Right Knee
27 = Left Ankle
28 = Right Ankle
29 = Left Heel
30 = Right Heel
31 = Left Foot Index
32 = Right Foot Index
```

---

## Basketball-Specific Angles We Track

| Angle | Landmark Indices | Good Range | Meaning |
|---|---|---|---|
| Elbow (shooting arm - right) | 12 → 14 → 16 | 160–175° at release | Arm fully extended |
| Knee bend | 24 → 26 → 28 | 100–130° before jump | Power generation |
| Hip angle | 12 → 24 → 26 | 150–170° | Forward lean |
| Shoulder elevation | 0 → 12 → 14 | Symmetrical | Balance |

---

## Project Folder Structure

```
basketball_proj/
├── .venv/                      # Python virtual environment
├── main.py                     # Main script (currently working)
├── pose_landmarker.task        # AI model file (29MB, do not delete)
├── requirements.txt            # mediapipe, opencv-python, numpy
└── videos/                     # (planned) test video files
```

---

## What Is Working

- Live webcam feed with skeleton overlay (green lines, red dots)
- Real-time elbow angle measurement displayed on screen
- Real-time knee angle measurement displayed on screen
- Basic text feedback based on elbow angle threshold

---

## What Needs To Be Built Next (Roadmap)

### Phase 2 — Core Analysis (Immediate)
- [ ] Detect shot moment automatically (wrist rises above shoulder = shot initiated)
- [ ] Record angle sequence per shot (not just per frame)
- [ ] Per-shot summary: avg elbow angle, knee bend, consistency score
- [ ] Add hip angle tracking
- [ ] Add shoulder symmetry check
- [ ] Save session data to JSON or CSV

### Phase 3 — Ball Tracking
- [ ] Add YOLOv8 for basketball detection (pip install ultralytics)
- [ ] Track ball trajectory across frames
- [ ] Compute release angle (angle of ball path at the moment of release)
- [ ] Compute arc height (peak y coordinate of ball path)
- [ ] Determine release point height (wrist height at release)

### Phase 4 — Intelligent Feedback
- [ ] Build shot classifier (good form vs bad form) using rule-based scoring
- [ ] Compare player angles against professional benchmarks
- [ ] Generate text report per session (PDF export)
- [ ] Add voice feedback using pyttsx3 or gTTS

### Phase 5 — Dashboard (Optional/Future)
- [ ] React web frontend for uploading and viewing analysis
- [ ] Session history and progress tracking
- [ ] Side-by-side comparison of multiple shots
- [ ] Overlay comparison with pro player reference pose

---

## Key Decisions & Constraints

- **No GPU available** — all models must run on CPU. BlazePose Heavy runs at ~20 FPS on Intel i5/i7 laptop. This is acceptable.
- **Python 3.12.6** — cannot use mediapipe < 0.10.13. Always use new Tasks API.
- **Windows environment** — paths use backslash, PowerShell commands used for downloads.
- **Single player focus for now** — `num_poses=1` in options. Multi-player analysis is a future enhancement.
- **Offline system** — no internet dependency during analysis. Model file is local.

---

## Common Errors and Fixes

| Error | Cause | Fix |
|---|---|---|
| `AttributeError: module 'mediapipe' has no attribute 'solutions'` | Old API on Python 3.12 | Use new Tasks API (shown above) |
| `Could not find version mediapipe==0.10.9` | Python 3.12 incompatibility | Use latest mediapipe (0.10.13+) |
| `FileNotFoundError: pose_landmarker.task` | Model file missing | Re-download with PowerShell command |
| Low FPS / lag | Heavy model on slow CPU | Switch to `pose_landmarker_full.task` |
| Jittery skeleton | Fast movement + low tracking confidence | Set `min_tracking_confidence=0.7` |
| No landmarks detected | Poor lighting or player too far | Improve lighting, move closer |

---

## Packages Required

```
pip install mediapipe opencv-python numpy
```

For future phases:
```
pip install ultralytics    # YOLOv8 for ball detection
pip install matplotlib     # Graphs and trajectory plots
pip install pyttsx3        # Voice feedback (offline TTS)
pip install fpdf2          # PDF report generation
```

---

## How to Download the Model File

```powershell
# PowerShell (Windows):
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task" -OutFile "pose_landmarker.task"
```

```bash
# Linux/Mac:
wget -O pose_landmarker.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task
```

---

## If You Are An AI Model Reading This

When helping with this project:

1. **Always use the new MediaPipe Tasks API** — never suggest `mp.solutions.pose`
2. **Python 3.12.6 is fixed** — don't suggest downgrading Python
3. Access landmarks as `result.pose_landmarks[0][index].x` — it's a list, not a named dict
4. Coordinates are **normalized (0.0 to 1.0)** — multiply by `w` and `h` to get pixels
5. OpenCV uses **BGR** color format — MediaPipe needs **RGB** — always convert with `cv2.cvtColor`
6. The model file is at `pose_landmarker.task` in the project root
7. Prab prefers **concise code** with comments, not verbose explanations inline
8. Basketball-specific angles: elbow (12→14→16), knee (24→26→28), hip (12→24→26)
9. A "good" shooting elbow angle at release is **160–175 degrees**
10. A "good" knee bend before a jump shot is **100–130 degrees**

---

*Project: Intelligent Basketball Performance Analysis System | BMSIT&M BCS506 | 2025-26*
*Developer: Pranab Bhardwaj | GitHub: pranabbhardwaj137*
