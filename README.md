# Project Context: Intelligent Basketball Performance Analysis System

## Feed this document to any AI model to get context-aware help on this project.

---

## 1. What This Project Is

An intelligent, real-time computer vision and biomechanical coaching tool built in Python. It analyzes a player's basketball shooting form and shot physics from video (live webcam or pre-recorded video files).

The system performs real-time body pose estimation, computes 3D and 2D biomechanical joint angles (elbow, knee, hip), tracks shot execution phases, measures shot consistency, and provides an individualized **Personal Shot Lab** with evidence-gated baselines, quarantine review workflows, and one-cue-at-a-time remediation practice drills. It also optionally tracks basketball trajectory and rim using YOLO object detection to compute release angles, arc peak height, and make/miss outcomes.

---

## 2. Project Origin & Architecture Lineage

This project (`basketball_proj`) is a unified synthesis of two parent codebases:

1. **`Basketball-Shot-Analyzer`**
   - **Contributed:** Biomechanical joint analysis concepts, joint kinematics, shot phase detection logic, multi-shot session recording (`SessionRecorder`), consistency scoring based on standard deviation, and CSV session data export.

2. **`clones/basketball-shot-analysis`**
   - **Contributed:** YOLO-based ball and rim tracking concepts, spatial release detection (ball position relative to hand/elbow), parabolic trajectory fitting (`y = ax^2 + bx + c`), release angle calculation, arc peak detection, and rim proximity heuristics for make/miss classification.

`basketball_proj` refactors, modernizes, and integrates these techniques into a single, clean Python application built on **Python 3.12+** using **MediaPipe's modern Tasks API**, **Ultralytics YOLOv8**, and **SQLite3** for immutable provenance.

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
| **Hand Tracking** | MediaPipe Tasks API (`>=0.10.13`) | `hand_landmarker.task` model |
| **Shot Lab DB** | SQLite3 | Versioned schema (v2) with machine vs. human review provenance |
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
├── .planning/                  # GSD Project Roadmap, State, Plans, and Milestone Reports
├── graphify-out/               # Graphify Knowledge Graph (graph.json, GRAPH_REPORT.md, graph.html)
├── requirements.txt            # Dependency definitions (mediapipe, opencv-python, numpy, matplotlib)
├── download_models.py          # Automated model asset downloader (pose_landmarker.task, hand_landmarker.task)
├── seed_shot_lab.py            # Local starter database seeder with sample players and baselines
├── main.py                     # Main CLI entry point & real-time pipeline orchestrator
├── pose_engine.py              # PoseEngine: MediaPipe inference, landmark extraction & smoothing
├── hand_engine.py              # HandEngine: Wrist flick and finger spread tracking
├── analyzer.py                 # Biomechanical angle math, shot phase detection & SessionRecorder
├── baseline_engine.py          # Personal baseline computation with sample gating (N>=5) & isolation
├── coach_engine.py             # Hierarchical One-Cue Remediation and observational follow-up evaluation
├── review_shots.py             # CLI & interactive shot review queue and boundary correction tool
├── shot_lab_db.py              # Versioned SQLite persistence engine with dual-provenance tracking
├── ball_tracker.py             # BallTracker: In-memory YOLO ball/rim detection & state machine
├── ball_geometry.py            # Mathematical primitives for trajectory, release angle & parabola
├── pro_comparator.py           # Illustrative pro kinematic curve comparisons (Curry, Klay, Ray Allen)
├── evaluate_dataset.py         # Full-length video evaluation benchmark tool
├── test_shot_lab_flow.py       # Comprehensive end-to-end integration test suite
├── test_baseline_engine.py     # Unit tests for baseline computation and sample gating
├── test_coach_engine.py        # Unit tests for hierarchical one-cue coaching engine
├── test_shot_lab_db.py         # Unit tests for database schema, provenance, and migrations
├── group_work_division.md      # Team workload division & academic demo guide
├── AI_Models_Deep_Dive.md      # Technical deep-dive reference for academic viva
└── METRIC_DICTIONARY.md        # Mathematical definitions, coordinate bases, and limitations
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

### Step 2: Download Model Assets

Run the automated asset downloader to fetch the required MediaPipe pose and hand models:

```bash
python download_models.py
```

### Step 3: (Optional) Seed Starter Database for Development

If you want to immediately test the Personal Shot Lab and coaching engines without recording footage first:

```bash
python seed_shot_lab.py
```

### Step 4: Running the Application

```
usage: main.py [-h] [--video VIDEO] [--ball] [--yolo YOLO] [--detect-every DETECT_EVERY] [--hands] [--pro [{curry,klay,ray_allen}]] [--shot-style {jump_shot,set_shot}] [--player PLAYER]
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

3. **Run with Set-Shot Mechanics Tuning (e.g. Free Throws):**
   ```bash
   python main.py --video sample_shot.mp4 --shot-style set_shot
   ```

4. **Run Pose Analysis WITH Ball & Rim Tracking (Stock YOLO COCO model):**
   ```bash
   python main.py --video sample_shot.mp4 --ball
   ```

5. **Run with Hand Tracking (Wrist Flick & Finger Spread Analysis):**
   ```bash
   python main.py --video sample_shot.mp4 --hands
   ```

6. **Run with Pro Player Benchmark Comparison (Curry, Klay, Ray Allen):**
   ```bash
   python main.py --video sample_shot.mp4 --pro curry
   ```

7. **Run Full Pipeline (Pose + Ball + Hands + Pro Comparator):**
   ```bash
   python main.py --video sample_shot.mp4 --ball --hands --pro curry
   ```

### Step 5: Interactive Runtime Controls & Live Tagging

- Press **`M`** – Tag detected shot as **Make** (approves shot for baseline admission).
- Press **`X`** – Tag detected shot as **Miss** (approves shot for baseline admission).
- Press **`U`** – Tag detected shot as **Unknown** (leaves shot quarantined for later review).
- Press **`SPACE`** – Pause / resume video playback.
- Press **`S`** – Instantly export current session metrics to a timestamped CSV file.
- Press **`Q`** – Quit the program.

### Step 6: Post-Session Shot Review & Baseline Inspection

1. **Review Quarantined Shots Interactively:**
   ```bash
   python review_shots.py --quarantined --interactive
   ```
2. **Inspect Shot Detail and Provenance:**
   ```bash
   python review_shots.py --inspect <SHOT_ID>
   ```
3. **Approve a Shot for Baseline Admission:**
   ```bash
   python review_shots.py --approve <SHOT_ID> --notes "Confirmed release keyframe"
   ```
4. **Discard an Outlier or Occluded Shot:**
   ```bash
   python review_shots.py --discard <SHOT_ID> --notes "Occlusion during jump"
   ```

---

## 7. Biomechanical & Ball Metrics Tracked

| Metric | Calculation Method / Indices | Target Range / Meaning |
| --- | --- | --- |
| **Elbow Angle (Shooting Arm)** | Landmarks 12 → 14 → 16 (Right) or 11 → 13 → 15 (Left) | **160°–175° at release** (Full arm extension) |
| **Knee Bend Angle** | Landmarks 24 → 26 → 28 (Right) or 23 → 25 → 27 (Left) | **100°–130° at lowest dip** (Power generation) |
| **Hip Posture Angle** | Landmarks 12 → 24 → 26 (Right) or 11 → 23 → 25 (Left) | **150°–170°** (Forward lean check) |
| **Kinetic Sequence Lag** | Temporal offset between knee max extension and wrist max velocity | **< 80 ms** for jump shots, **< 70 ms** for set shots |
| **Torso Sway** | Angular deviation of mid-hip to mid-shoulder vector from vertical | **< 8°** (Lateral stability) |
| **Shooting Side** | Auto-detected (Hand/wrist with smaller `norm_y`) | Identifies left vs right handed shooter |
| **Shot Phase** | Wrist height relative to shoulder/nose & vertical velocity | `preparing`, `releasing`, `follow_through`, `idle` |
| **Form Consistency Score** | `max(0, 100 - (elbow_std + knee_std))` | Higher score (0-100) indicates repeatable mechanics |
| **Release Launch Angle** | Vector angle of ball center between release frames | **45°–55°** optimal trajectory launch angle |
| **Arc Peak Height** | Minimum pixel `y` of ball during flight trajectory | Peak height of parabolic flight path |
| **Make / Miss Result** | Spatial alignment of ball center entering rim box | Evaluates shot success heuristic |

---

## 8. Milestone Status & Scientific Integrity (GSD v1.0)

Milestone: **Reliable, Evidence-Backed Personal Shot Analysis**. Detailed GSD record: [`.planning/STATE.md`](.planning/STATE.md).

| Phase | Focus | Current status | Evidence / remaining gate |
| --- | --- | --- | --- |
| 1 | Capture and core vision | **Completed** | MediaPipe Tasks pose pipeline and capture code exist. Clean-install and cross-platform setup documented. |
| 2 | Shot events and kinematics | **Completed** | Shot-state, angle, sequencing, and illustrative DTW comparisons exist. Pro profiles are examples, not measured pro ground truth. |
| 3 | Measurement integrity and evaluation | **Completed & Verified** | Full-length benchmark (2,667 frames) evaluated in `DATASET_EVAL_REPORT.json` (80.0% recall, MAE 227.8 ms, zero baseline contamination via human-gated quarantine). |
| 4 | Personal Shot Lab and evidence-gated coaching | **Completed & Verified** | SQLite dual-provenance, M/X/U live hotkeys, post-session review queue, shot-style isolation, $N \ge 5$ baseline gating, mechanics-threshold cues, and observational follow-up evaluation. All 18 unit/integration tests pass. |
| 5 | Session reports and coach experience | Active (Human-confirmed sessions ready) | Prioritize detector/review reliability. Build reports only from human-confirmed shots until an evidence-backed event threshold is met. |
| 6 | Research and review release | Planned | Compare optional methods against baselines; complete reproducible packaging and academic review materials. |

### Evaluation Status & Limits

- `EVAL_REPORT.json` is a **synthetic regression report**. Its scores measure generated test cases, not real-world basketball accuracy.
- `evaluate_public_datasets.py` loads and evaluates actual dataset files (`PUBLIC_DATASETS_REPORT.json`). EPFL SportCenter camera-pose calibration evaluated on 28 real sequences (50,127 frames) with mean planar-vs-distorted reprojection residual of 5.17 px (train) and 4.06 px (test). Because it contains zero skeletal body-joint annotations, EPFL is archived to the Phase 6 backlog as a court-geometry/calibration experiment; SPL kinematic bounds verified.
- `DATASET_EVAL_REPORT.json` evaluates 100% of video frames across all clips (2,667 total frames) without artificial truncation:
  - **Overall Recall:** 80.0% (4/5 total annotated shots detected).
  - **Overall Precision:** 22.2% (4 TP, 14 FP across continuous unedited practice drills).
  - **Development Split (`klay_vid.mp4`):** 100.0% Precision, 100.0% Recall (F1: 1.000), Timing MAE: 133.5 ms.
  - **Held-Out Split (`mike_dunn`):** 75.0% Recall (3/4 shots detected, 14 FP across unedited drills), Timing MAE: 275.0 ms.
    - `mikeddunnstud1.mp4` (Oblique 45°): 2/2 TP (100.0% Recall), Timing MAE: 83.3 ms (spread 66.7–100.0 ms), F1: 0.571.
    - `mikeddunnstud2.mp4` (Side 90°): 1/2 TP (50.0% Recall, 11 FP during continuous dribbling/gathers), Timing MAE: 466.7 ms, F1: 0.143.
  - **Baseline Integrity:** All 14 unconfirmed false machine detections quarantined with `status: PENDING_REVIEW`, protecting baselines from contamination.
- The 2D-versus-MediaPipe-world angle difference (mean 19.7°) is **estimate disagreement**, representing perspective foreshortening and monocular depth inference divergence, not ground-truth sensor error.

---

## 9. Running the Test Suite

Run the full test suite across database provenance, baseline sample gating, hierarchical coaching, and end-to-end integration:

```bash
python -m unittest discover
```

Expected output:
```
----------------------------------------------------------------------
Ran 18 tests in 0.600s

OK
```

---

## 10. Common Errors & Troubleshooting

| Error | Cause | Solution |
| --- | --- | --- |
| `AttributeError: module 'mediapipe' has no attribute 'solutions'` | Legacy API invoked on Python 3.12 | Use `mediapipe.tasks.python.vision.PoseLandmarker` as shown in `pose_engine.py` |
| `FileNotFoundError: pose_landmarker.task` | Model file missing in project root | Run `python download_models.py` |
| `ModuleNotFoundError: No module named 'ultralytics'` | Running `--ball` without YOLO installed | Run `pip install ultralytics` inside `.venv` |
| Low FPS / Video lag | Heavy model running on slow CPU | Pass `--detect-every 2` or switch model path to `pose_landmarker_full.task` |
| No landmarks detected | Poor lighting or subject out of frame | Ensure subject is fully visible from side/front profile with clear lighting |

---

## 11. Codebase Knowledge Graph & Maintenance (Graphify)

This project uses **Graphify** (`graphifyy` package) to maintain an AST-indexed Knowledge Graph of code dependencies, function call flow, and architectural hubs in `graphify-out/`.

### Knowledge Graph Artifacts
- **`graphify-out/graph.json`**: Graph data model.
- **`graphify-out/GRAPH_REPORT.md`**: Architectural breakdown detailing God Nodes, Community Hubs, and modularity suggestions.
- **`graphify-out/graph.html`**: Interactive D3/Vis network graph visualization.

### Usage & Maintenance Commands

1. **Incremental Update (After code edits - Fast & free):**
   ```powershell
   python -m graphify update .
   ```
2. **Full AST Extraction (Code-only, no API key needed):**
   ```powershell
   python -m graphify extract . --code-only
   ```
3. **Export Interactive Visualizations:**
   ```powershell
   python -m graphify export html
   ```

---

_Project: Intelligent Basketball Performance Analysis System | BMSIT&M BCS506 | 2025–26_  
_Developer: Pranab Bhardwaj | GitHub: pranabbhardwaj137_
