# Project Context: Intelligent Basketball Performance Analysis System

## Feed this document to any AI model to get context-aware help on this project.

---

## 1. What This Project Is

An intelligent, real-time computer vision and biomechanical coaching tool built in Python. It analyzes a player's basketball shooting form and shot physics from video (live webcam or pre-recorded video files).

The system performs real-time body pose estimation, computes biomechanical joint angles (elbow, knee, hip), tracks shot execution phases, measures shot consistency, and optionally tracks the basketball trajectory and rim using YOLO object detection to compute release angles, arc peak height, and make/miss outcomes.

---

## 2. Project Origin & Architecture Lineage

This project (`basketball_proj`) is a unified synthesis of two parent codebases:

1. **`Basketball-Shot-Analyzer`**
   - **Contributed:** Biomechanical joint analysis concepts, joint kinematics, shot phase detection logic, multi-shot session recording (`SessionRecorder`), consistency scoring based on standard deviation, and CSV session data export.

2. **`clones/basketball-shot-analysis`**
   - **Contributed:** YOLO-based ball and rim tracking concepts, spatial release detection (ball position relative to hand/elbow), parabolic trajectory fitting (`y = ax^2 + bx + c`), release angle calculation, arc peak detection, and rim proximity heuristics for make/miss classification.

`basketball_proj` refactors, modernizes, and integrates these techniques into a single, clean Python application built on **Python 3.12+** using **MediaPipe's modern Tasks API** and **Ultralytics YOLOv8**.

---

## 3. Developer & Academic Profile

- **Developer:** Pranab Bhardwaj (GitHub: `pranabbhardwaj137`)
- **Background:** Final year Information Science & Engineering, BMSIT&M Bengaluru
- **Course:** BCS506 Major Project, Bachelor of Engineering in ISE
- **University:** Visvesvaraya Technological University (VTU), Belagavi
- **Institution:** BMS Institute of Technology & Management (BMSIT&M), Bengaluru (Academic Year 2025–26)
- **Guide:** Asst. Prof. Amulya P, Department of ISE
- **Team Members:**
  - Pranab Bhardwaj (1BY23IS154) – Core Vision Layer (`pose_engine.py`)
  - Pavan R Bhat (1BY23IS145) – Kinematics & Shot Phase Detection (`analyzer.py`)
  - Pracheth Kashyap (1BY23IS152) – Session Recorder & Data Export (`analyzer.py`)
  - Puneetgouda Patil (1BY23IS165) – Feedback & Output Interface (`feedback.py`)

---

## 4. Current Tech Stack & Dependencies

| Component | Technology / Library | Details |
| --- | --- | --- |
| **Language** | Python 3.12.6 | Virtual environment located at `.venv` |
| **Pose Engine** | MediaPipe Tasks API (`>=0.10.13`) | `pose_landmarker.task` model (BlazePose Heavy) |
| **Object Detection** | Ultralytics YOLOv8 (Optional) | COCO `yolov8n.pt` or custom `weights/basket_rim.pt` |
| **Video Processing** | OpenCV (`opencv-python`) | Frame capture, skeleton drawing, HUD text overlay |
| **Mathematics & Stats** | NumPy | Vector dot products, arccos angles, curve fitting, std dev |
| **Environment** | Windows 11 / PowerShell / VS Code | Virtual environment (`.venv`) |

### CRITICAL: MediaPipe Tasks API Requirement

This project uses **Python 3.12**, which is incompatible with legacy `mp.solutions.pose` (`mediapipe==0.10.9`). It **MUST** use the MediaPipe Tasks API:

```python
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base_options = python.BaseOptions(model_asset_path='pose_landmarker.task')
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_poses=1,
    min_pose_detection_confidence=0.5,
    min_tracking_confidence=0.7
)
detector = vision.PoseLandmarker.create_from_options(options)
```

---

## 5. Repository File Structure & Module Breakdown

```
basketball_proj/
├── .venv/                      # Isolated Python 3.12 virtual environment
├── graphify-out/               # Graphify Knowledge Graph (graph.json, GRAPH_REPORT.md, graph.html)
├── pose_landmarker.task        # MediaPipe BlazePose Heavy model (29MB)
├── requirements.txt            # Dependency definitions (mediapipe, opencv-python, numpy)
├── main.py                     # Main CLI entry point & real-time pipeline orchestrator
├── pose_engine.py              # PoseEngine: MediaPipe inference, landmark extraction & smoothing
├── analyzer.py                 # Biomechanical angle math, shot phase detection & SessionRecorder
├── ball_tracker.py             # BallTracker: In-memory YOLO ball/rim detection & state machine
├── ball_geometry.py            # Mathematical primitives for trajectory, release angle & parabola
├── group_work_division.md      # Team workload division & academic demo guide
├── AI_Models_Deep_Dive.md      # Technical deep-dive reference for academic viva
└── Project_Context_For_AI.md   # System context, execution guide & technical reference
```

---

## 6. How to Set Up & Run the Project

### Step 1: Environment Setup

Navigate to the project root and activate the virtual environment:

```powershell
# Windows PowerShell
cd c:\Users\bhard\Downloads\major_pro\major_pro\basketball_proj
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
cd basketball_proj
source .venv/bin/activate
```

If dependencies are missing, install them:

```bash
pip install -r requirements.txt
```

*(Optional for ball tracking):*
```bash
pip install ultralytics
```

### Step 2: Ensure Model Asset is Present

Ensure `pose_landmarker.task` exists in the project root. If missing, download it:

```powershell
# Windows PowerShell
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task" -OutFile "pose_landmarker.task"
```

### Step 3: Running the Application

```
usage: main.py [-h] [--video VIDEO] [--ball] [--yolo YOLO] [--detect-every DETECT_EVERY]
```

#### Examples

1. **Run Live Pose Analysis on Webcam (Default):**
   ```bash
   python main.py
   ```

2. **Run Pose Analysis on a Pre-Recorded Video File:**
   ```bash
   python main.py --video sample_shot.mp4
   ```

3. **Run Pose Analysis WITH Ball & Rim Tracking (Stock YOLO COCO model):**
   ```bash
   python main.py --video sample_shot.mp4 --ball
   ```

4. **Run with Custom Ball/Rim Weights (`basket_rim.pt`):**
   ```bash
   python main.py --video sample_shot.mp4 --ball --yolo weights/basket_rim.pt
   ```

5. **Run with Frame Skipping for Low-Spec CPUs (runs YOLO every 2 frames):**
   ```bash
   python main.py --video sample_shot.mp4 --ball --detect-every 2
   ```

### Step 4: Interactive Runtime Controls

- Press **`Q`** – Quit the program.
- Press **`SPACE`** – Pause / resume video playback.
- Press **`S`** – Instantly export current session metrics to a timestamped CSV file (e.g. `session_20261004_101500.csv`) and print summary stats in the terminal.

---

## 7. Biomechanical & Ball Metrics Tracked

| Metric | Calculation Method / Indices | Target Range / Meaning |
| --- | --- | --- |
| **Elbow Angle (Shooting Arm)** | Landmarks 12 → 14 → 16 (Right) or 11 → 13 → 15 (Left) | **160°–175° at release** (Full arm extension) |
| **Knee Bend Angle** | Landmarks 24 → 26 → 28 (Right) or 23 → 25 → 27 (Left) | **100°–130° at lowest dip** (Power generation) |
| **Hip Posture Angle** | Landmarks 12 → 24 → 26 (Right) or 11 → 23 → 25 (Left) | **150°–170°** (Forward lean check) |
| **Shooting Side** | Auto-detected (Hand/wrist with smaller `norm_y`) | Identifies left vs right handed shooter |
| **Shot Phase** | Wrist height relative to shoulder & vertical delta | `preparing`, `releasing`, `follow_through`, `idle` |
| **Form Consistency Score** | `max(0, 100 - (elbow_std + knee_std))` | Higher score (0-100) indicates repeatable mechanics |
| **Release Launch Angle** | Vector angle of ball center between release frames | **45°–55°** optimal trajectory launch angle |
| **Arc Peak Height** | Minimum pixel `y` of ball during flight trajectory | Peak height of parabolic flight path |
| **Make / Miss Result** | Spatial alignment of ball center entering rim box | Evaluates shot success heuristic |

---

## 8. Target Architecture Alignment & Progress Gap Analysis

### Reference Architecture: `AI_Models_Deep_Dive.md` (Lines 396–425)

The target full-system flow consists of 14 components across 5 layers:

```
Input Layer
├── Webcam / Smartphone Video
└── Pre-recorded Game Footage
        ↓
Detection Layer
├── BlazePose (pose landmarks)        ← CURRENT
├── YOLOv8 (basketball detection)     ← CURRENT
└── MediaPipe Hands (wrist snap)      ← FUTURE / TO ADD
        ↓
Analysis Layer
├── Angle Computation (numpy)         ← CURRENT
├── Trajectory Tracking (OpenCV)      ← CURRENT
├── Ball Arc Analysis                 ← CURRENT
└── Temporal Consistency (LSTM)       ← FUTURE / TO ADD
        ↓
Feedback Layer
├── Rule-Based Feedback               ← CURRENT
├── AI-Generated Feedback (LSTM)      ← FUTURE / TO ADD
└── Voice Feedback (TTS)              ← FUTURE / TO ADD
        ↓
Output Layer
├── Annotated Video                   ← CURRENT
├── Session Report (PDF)              ← FUTURE / TO ADD
├── Progress Dashboard (web app)      ← FUTURE / TO ADD
└── Comparison vs Pro Players         ← FUTURE / TO ADD
```

### Component Status Matrix & Progress Gap

| Layer | Architecture Component | Implementation Status | Existing File / Code | What Needs to be Added |
| --- | --- | --- | --- | --- |
| **Input** | Webcam / Smartphone Video | **DONE (100%)** | `main.py` (`cv2.VideoCapture(0)`) | None |
| **Input** | Pre-recorded Game Footage | **DONE (100%)** | `main.py` (`--video path`) | None |
| **Detection** | BlazePose Keypoints | **DONE (100%)** | `pose_engine.py` (MediaPipe Tasks API) | None |
| **Detection** | YOLOv8 Ball & Rim Detection | **DONE (100%)** | `ball_tracker.py` (Ultralytics YOLO) | None |
| **Detection** | MediaPipe Hands (Wrist Snap) | **MISSING (0%)** | None | Add `HandLandmarker` Tasks API for 21 hand points & release wrist flick |
| **Analysis** | Biomechanical Angle Math | **DONE (100%)** | `analyzer.py` (`compute_all_angles`) | Add wrist-elbow alignment deviation |
| **Analysis** | Trajectory Tracking | **DONE (100%)** | `ball_tracker.py` & `ball_geometry.py` | None |
| **Analysis** | Ball Arc & Launch Angle | **DONE (100%)** | `ball_geometry.py` (`fit_parabola`, `release_angle_deg`) | None |
| **Analysis** | Temporal Consistency (LSTM) | **PARTIAL (30%)** | `SessionRecorder` (Statistical `100 - std_dev`) | Train/integrate sequence LSTM model for multi-frame shot form classification |
| **Feedback** | Rule-Based Feedback Engine | **DONE (100%)** | `main.py` & `group_work_division.md` (`feedback.py`) | Wire `feedback.py` panel overlay into `main.py` pipeline |
| **Feedback** | AI-Generated Sequence Feedback | **MISSING (0%)** | Static text strings | Feed LSTM sequence prediction into automated feedback string generator |
| **Feedback** | Voice Feedback (TTS) | **MISSING (0%)** | None | Add `pyttsx3` background thread for real-time verbal cues ("Extend shooting arm!") |
| **Output** | Live Annotated Video HUD | **DONE (100%)** | `main.py` (Skeleton, joint angles, trajectory line) | None |
| **Output** | Session PDF Report | **MISSING (0%)** | CSV export only (`SessionRecorder.export_csv`) | Build PDF exporter (`fpdf2`) with embedded matplotlib chart PNGs |
| **Output** | Progress Dashboard Web App | **MISSING (0%)** | Terminal CLI output | Build Web Dashboard (Streamlit / React) for session history & video player |
| **Output** | Comparison vs Pro Players | **MISSING (0%)** | None | Build pro benchmark pose overlay & angle curve comparison tool |

---

### Progress Scorecard

- **Components Completed:** 8 / 14 (**~57% Complete**)
- **Components Remaining:** 6 / 14 (**~43% to Build**)

---

## 9. Concrete Implementation Plan to Complete the Flow

To achieve 100% completion of the proposed flow, the following 6 modules must be created and integrated into `basketball_proj`:

### 1. Offline Voice Feedback Module (`feedback_voice.py`)
- **Library:** `pyttsx3` (runs offline without internet or API keys).
- **Functionality:** Launches a non-blocking background thread that speaks live coaching cues when shot release or follow-through is detected:
  - *"Extend your shooting arm more"* (if release elbow < 155°)
  - *"Great release!"* (if elbow > 160° and release angle 45-55°)
  - *"Bend knees more for power"* (if dip knee > 135°)

### 2. PDF Session Report Generator (`report_generator.py`)
- **Library:** `fpdf2` + `matplotlib`.
- **Functionality:** Replaces raw CSV export with a professional PDF report containing:
  - Session header (Player Name, Date, Total Shots).
  - Summary table (Shot #, Elbow Angle at Release, Knee Dip, Launch Angle, Outcome).
  - Embedded Matplotlib trend charts (Elbow Angle Trend, Knee Bend Trend, Form Consistency Score).

### 3. MediaPipe Hands Integration (`hand_engine.py`)
- **Library:** `mediapipe.tasks.python.vision.HandLandmarker`.
- **Functionality:** Tracks 21 hand landmarks on the shooting hand during release:
  - Measures wrist snap/flexion angle at release frame.
  - Measures finger spread (index to pinky distance) at release.

### 4. Pro Player Benchmark Comparison Tool (`pro_comparator.py`)
- **Functionality:**
  - Stores reference joint angle curves of elite shooters (e.g. Stephen Curry release curve).
  - Plots player's shot angle curve vs pro benchmark curve.
  - Calculates a **Pro Similarity Percentage Score (0–100%)**.

### 5. LSTM Temporal Shot Quality Classifier (`shot_classifier.py`)
- **Framework:** PyTorch / TensorFlow.
- **Functionality:** Accepts an $(N, 4)$ sequence tensor of joint angles across 30 frames of shot execution to output shot quality probability ($0.0 - 1.0$).

### 6. Web Progress Dashboard (`dashboard/app.py`)
- **Framework:** Streamlit or Next.js / FastAPI.
- **Functionality:**
  - Drag-and-drop video file upload.
  - Interactive playback with pose skeleton & ball trajectory overlays.
  - Historical progress dashboard showing consistency scores over time.

---

## 10. Development Roadmap & Updated Task Status

- [x] **Phase 1: Core Vision & Modularization**
  - MediaPipe Tasks API integration with BlazePose Heavy model (`pose_engine.py`).
  - Landmark extraction and exponential smoothing.
  - Skeleton drawing with landmark visibility confidence flags.
- [x] **Phase 2: Kinematics & Session Analytics**
  - Real-time angle computation for elbow, knee, hip, shoulder (`analyzer.py`).
  - Automated shot phase detection based on wrist movement.
  - Multi-shot `SessionRecorder` with CSV export and session statistics.
- [x] **Phase 3: Ball & Rim Tracking Integration**
  - Ultralytics YOLO ball & rim detection module (`ball_tracker.py`).
  - Flight path trajectory curve fitting (`fit_parabola`).
  - Release launch angle and make/miss judgment heuristics (`ball_geometry.py`).
- [ ] **Phase 4: Feedback & Output Enhancement (Next Priority)**
  - Integrate `feedback.py` panel overlay & matplotlib trend charts into `main.py`.
  - Add offline Voice Feedback using `pyttsx3`.
  - Add PDF Session Report generation using `fpdf2`.
- [ ] **Phase 5: Hands, Pro Benchmarking & Web Dashboard**
  - Integrate MediaPipe Hands Tasks API for wrist snap & finger spread.
  - Build Pro Player benchmark comparison overlay.
  - Launch Streamlit / Web UI Progress Dashboard.

---

## 11. Common Errors & Troubleshooting

| Error | Cause | Solution |
| --- | --- | --- |
| `AttributeError: module 'mediapipe' has no attribute 'solutions'` | Legacy API invoked on Python 3.12 | Use `mediapipe.tasks.python.vision.PoseLandmarker` as shown in `pose_engine.py` |
| `FileNotFoundError: pose_landmarker.task` | Model file missing in project root | Re-download using the PowerShell / curl command in Step 2 |
| `ModuleNotFoundError: No module named 'ultralytics'` | Running `--ball` without YOLO installed | Run `pip install ultralytics` inside `.venv` |
| Low FPS / Video lag | Heavy model running on slow CPU | Pass `--detect-every 2` or switch model path to `pose_landmarker_full.task` |
| No landmarks detected | Poor lighting or subject out of frame | Ensure subject is fully visible from side/front profile with clear lighting |

---

## 12. Guidelines for AI Assistants Working on This Project

1. **Always use MediaPipe Tasks API** (`mediapipe.tasks.python.vision`) – NEVER write `mp.solutions.pose`.
2. **Do NOT downgrade Python 3.12** – Keep code compatible with Python 3.12.6.
3. Access landmarks via index in `result.pose_landmarks[0][idx]` – coordinate attributes are `.x`, `.y`, `.z` (normalized 0.0–1.0).
4. Frame dimensions: multiply `.x` by frame width (`w`) and `.y` by frame height (`h`) for pixel coordinates.
5. Color formats: OpenCV handles **BGR**, MediaPipe requires **RGB** (`cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)`).
6. Keep modules decoupled: `pose_engine.py` handles vision/pose, `analyzer.py` handles biomechanical math/session stats, `ball_tracker.py` & `ball_geometry.py` handle YOLO ball physics, and `main.py` handles CLI orchestration.

---

## 13. Codebase Knowledge Graph & Maintenance (Graphify)

This project uses **Graphify** (`graphifyy` package) to maintain an AST-indexed Knowledge Graph of code dependencies, function call flow, and architectural hubs in `graphify-out/`.

### Knowledge Graph Artifacts
- **`graphify-out/graph.json`**: Graph data model (207 nodes, 378 edges, 10 communities).
- **`graphify-out/GRAPH_REPORT.md`**: Architectural breakdown detailing God Nodes, Community Hubs, and modularity suggestions.
- **`graphify-out/graph.html`**: Interactive D3/Vis network graph visualization.

### Usage & Maintenance Commands

1. **Incremental Update (After code edits - Fast & free):**
   ```powershell
   .\.venv\Scripts\graphify.exe update .
   ```
   *Run this command whenever python source files are modified to keep `graphify-out/graph.json` in sync.*

2. **Full AST Extraction (Code-only, no API key needed):**
   ```powershell
   .\.venv\Scripts\graphify.exe extract . --code-only
   ```

3. **Re-clustering & Report Regeneration:**
   ```powershell
   .\.venv\Scripts\graphify.exe cluster-only .
   ```

4. **Export Interactive Visualizations:**
   ```powershell
   .\.venv\Scripts\graphify.exe export html
   ```

5. **Antigravity AI Agent Rule Setup:**
   ```powershell
   .\.venv\Scripts\graphify.exe antigravity install
   ```

### AI Agent Rules for Graphify
- Before making structural changes, consult `graphify-out/GRAPH_REPORT.md` or query `graphify-out/graph.json` for component relationships.
- Always run `.\.venv\Scripts\graphify.exe update .` after code edits.

---

_Project: Intelligent Basketball Performance Analysis System | BMSIT&M BCS506 | 2025–26_  
_Developer: Pranab Bhardwaj | GitHub: pranabbhardwaj137_

