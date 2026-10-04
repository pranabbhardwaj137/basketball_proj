# Work Division & Project Execution Plan

This document defines the 3-member team work division, technical specifications, and execution roadmap for the **Intelligent Basketball Performance Analysis System**.

---

## 1. Team Allocation & Stream Overview

```
                      ┌────────────────────────────────────────┐
                      │    Basketball Analysis System (100%)   │
                      └───────────────────┬────────────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
        ▼                                 ▼                                 ▼
┌───────────────────────┐     ┌───────────────────────┐     ┌───────────────────────┐
│       STREAM 1        │     │       STREAM 2        │     │       STREAM 3        │
│ Vision & Kinematics   │     │ Sequence & Voice AI   │     │ Reports & Web UI      │
│   (Pranab Bhardwaj)   │     │    (Pavan R Bhat)     │     │   (Pracheth Kashyap)  │
└───────────────────────┘     └───────────────────────┘     └───────────────────────┘
```

| Member | Primary Focus | Key Responsibilities & Deliverables | Target Files / Modules |
| --- | --- | --- | --- |
| **Pranab Bhardwaj** | **Core Vision, Hand Tracking & Pro Comparator** | • Pose landmark extraction (`pose_engine.py`) & YOLO tracking (`ball_tracker.py`) decoupling<br>• MediaPipe 21-point Hand Landmarker (`hand_engine.py`) for wrist flick & finger spread<br>• Pro Shooter Benchmark Comparison (`pro_comparator.py`) with similarity scoring & ghost overlays | `pose_engine.py`<br>`ball_tracker.py`<br>`hand_engine.py` [NEW]<br>`pro_comparator.py` [NEW] |
| **Pavan R Bhat** | **Kinematics Engine, Sequence Classifier & Voice AI** | • Real-time biomechanical angle math & shot phase state machine (`analyzer.py`)<br>• Threaded, non-blocking offline voice feedback (`feedback_voice.py`) using `pyttsx3`<br>• Temporal sequence classifier (`shot_classifier.py`) for continuous shot quality scoring | `analyzer.py`<br>`feedback_voice.py` [NEW]<br>`shot_classifier.py` [NEW] |
| **Pracheth Kashyap** | **Data Persistence, PDF Reports & Web Dashboard** | • Session statistics recorder & CSV data exporter (`analyzer.py`)<br>• Multi-page PDF session report exporter (`report_generator.py`) with `matplotlib` charts<br>• Interactive Web Progress Dashboard (`dashboard/app.py` via Streamlit)<br>• Pipeline orchestrator refactoring (`main.py`) | `report_generator.py` [NEW]<br>`dashboard/app.py` [NEW]<br>`main.py` |

---

## 2. Technical Specifications by Stream

### Stream 1: Core Vision, Hand Tracking & Pro Benchmark
**Owner:** Pranab Bhardwaj

#### 1. `pose_engine.py` & `ball_tracker.py` (Refactoring & Decoupling)
- Maintain MediaPipe Tasks API (`PoseLandmarker`) for 33 body keypoints with exponential smoothing.
- Decouple `ball_tracker.py` state machine to resolve low cohesion flagged in `GRAPH_REPORT.md`.
- Unify frame pre-processing so RGB conversion occurs once per frame.

#### 2. `hand_engine.py` (MediaPipe Hands Integration)
- **API:** `mediapipe.tasks.python.vision.HandLandmarker`.
- **Metrics Tracked:**
  - Wrist Flexion Angle: Angle formed by forearm vector vs hand vector ($160^\circ \to 90^\circ$ at release flick).
  - Finger Spread Index: Distance between Index tip (8) and Pinky tip (20) normalized by palm width.

#### 3. `pro_comparator.py` (Pro Benchmark Engine)
- **Data:** Stores baseline joint angle curves of elite shooters (e.g., Stephen Curry release curve).
- **Algorithms:** Dynamic Time Warping (DTW) / Cosine similarity to compute **Pro Similarity Percentage (0–100%)**.
- **Visuals:** Renders side-by-side pose overlay or ghost benchmark skeleton on screen.

---

### Stream 2: Kinematics Engine, Sequence AI & Voice Feedback
**Owner:** Pavan R Bhat

#### 1. `analyzer.py` (Kinematics & State Machine)
- Compute 7 biomechanical joint angles (`elbow_right`, `knee_right`, `hip_right`, `shoulder_right`, etc.).
- Refactor `detect_shot_phase` into an explicit Finite State Machine (`IDLE` $\to$ `PREPARING` $\to$ `RELEASING` $\to$ `FOLLOW_THROUGH`).

#### 2. `feedback_voice.py` (Offline Voice Feedback Engine)
- **Library:** `pyttsx3` (runs 100% offline without API keys).
- **Execution:** Uses a background `queue.Queue` thread to ensure zero frame rate lag.
- **Triggers:** Speaks instant verbal coaching cues upon phase transition:
  - *"Extend your shooting arm!"* (if release elbow < $155^\circ$)
  - *"Bend knees deeper for power!"* (if dip knee > $135^\circ$)
  - *"Great follow through!"*

#### 3. `shot_classifier.py` (Temporal Sequence Classifier)
- **Input:** Sliding window of 30 frames containing $(N, 4)$ joint angle feature vector.
- **Output:** Continuous Shot Quality Index ($0.0 - 1.0$) and primary flaw diagnosis.

---

### Stream 3: Data Persistence, PDF Reports & Web Dashboard
**Owner:** Pracheth Kashyap

#### 1. `report_generator.py` (Automated PDF Report Exporter)
- **Library:** `fpdf2` + `matplotlib`.
- **Features:**
  - Executive session summary table (Shot count, Avg Elbow Extension, Knee Dip, Form Consistency Score).
  - Embedded Matplotlib trend plots (Elbow Angle Trend, Knee Bend Trend, Consistency Histogram).
  - Automatically triggered via `S` key or web interface.

#### 2. `dashboard/app.py` (Streamlit Web Dashboard)
- **Framework:** Streamlit (`streamlit run dashboard/app.py`).
- **Features:**
  - Video upload interface (supports `.mp4`, `.avi`, `.mov`).
  - Interactive frame-by-frame skeleton playback.
  - Session history viewer and PDF report download link.

#### 3. `main.py` (Pipeline Orchestrator & CLI)
- Modular CLI orchestrator connecting `pose_engine`, `analyzer`, `ball_tracker`, `feedback_voice`, and `report_generator`.
- Decouples UI overlay rendering from video loop.

---

## 3. Knowledge Graph Maintenance (Graphify Workflow)

After creating or modifying files in any stream, team members must run:

```powershell
.\.venv\Scripts\graphify.exe update .
```

This keeps the codebase Knowledge Graph (`graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md`) fully in sync without consuming LLM tokens.

---

## 4. Academic Viva & Demo Responsibilities

- **Pranab Bhardwaj:** Demonstrates the core vision pipeline, MediaPipe BlazePose Heavy model setup, 21-point hand flick analysis, and Pro Player similarity overlay.
- **Pavan R Bhat:** Demonstrates the biomechanical angle math, finite-state shot phase detection, sequence classifier, and live offline voice feedback system.
- **Pracheth Kashyap:** Demonstrates multi-shot session recording, standard deviation consistency scoring, PDF report export, and the Streamlit Web Progress Dashboard.

---

_Project: Intelligent Basketball Performance Analysis System | BMSIT&M BCS506_  
_Plan Updated: October 2026_
