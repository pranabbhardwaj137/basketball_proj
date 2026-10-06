# Real-World & Public Dataset Manifest for Basketball Shot Analysis

This manifest qualifies external public datasets and project-recorded video clips for validating the basketball biomechanical analysis pipeline.

---

## 1. Candidate Dataset Qualification Matrix

| Dataset | Provider / Source | License | Format & Structure | Intended Role in Pipeline | Inclusions | Exclusions & Caveats |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SPL Open Data (Free Throws)** | MLSE Sport Performance Lab ([GitHub](https://github.com/Sport-Performance-Lab/SPL-Open-Data)) | CC BY-NC-SA 4.0 | 583 trials, 5 participants, 2 sessions. Frame-by-frame 3D markerless mocap JSON trajectories + outcome labels (Made/Missed). | Downstream biomechanics & outcome validation. | Kinematic curves (knee flexion, elbow extension, hip drive), temporal sequencing lags, make/miss labels. | **Cannot test RGB video pose detector:** Provides pre-computed 3D markerless tracking points, not raw synchronized single-camera phone videos. Small cohort ($N=5$). |
| **EPFL SportCenter Dataset** | EPFL CVLab ([Website](https://www.epfl.ch/labs/cvlab/data/sportcenter-dataset/)) | Academic Research License | Multi-view basketball arena footage (elevated fisheye), 14/17-joint 2D annotations & triangulated 3D body joints. | Pose estimator benchmark (PCK, MPJPE). | Cross-view joint localization accuracy, 2D-to-3D projection consistency. | **Cannot test shot state machine or coaching cues:** Sparse annotated game frames without shooting phase events (dip, set, release). Fisheye distortion differs from smartphone optics. |
| **SHOT Basketball Dataset** | Muyu et al., ACM MM 2025 ([HuggingFace](https://huggingface.co/datasets/muyu111/basketball)) | Annotations: CC BY-NC 4.0; Broadcast Video: Third-Party Rights Reserved | 1,979 clips, 5 camera views. Player tracks, body poses, tactic labels (Drive, Dunk, Spot-up). | Exploratory action/intention context. | Event timestamps, broad tactical action classifications. | **Excluded from video pipeline:** Raw broadcast footage carries third-party broadcast rights and is not redistributed. Group play does not match solo practice workflow. |
| **Project Single-Player Pilot** | Consented shooting sessions & recorded clips (`klay_vid.mp4`, `mikeddunnstud1.mp4`, `mikeddunnstud2.mp4`) | Project Owned / Consented Reference Clips | 30 FPS RGB video files, full-body side/oblique/frontal framing. | **Primary End-to-End Benchmark:** Pose coverage, shot event detection (dip, release), 2D/3D angle disagreement, outcome review. | Full video stream, MediaPipe BlazePose pipeline, confidence gating, live hotkeys, review queue. | Convenience sample; requires manual multi-angle annotations following `VIDEO_ANNOTATION_PROTOCOL.md`. |

---

## 2. Landmark Schema Mapping (EPFL & SPL to MediaPipe BlazePose)

MediaPipe BlazePose outputs 33 landmarks. Public datasets typically follow 14-joint (MPII) or 17-joint (COCO) skeletons:

| Joint Name | MediaPipe BlazePose Index | COCO / EPFL Index | SPL Kinematic Equivalent | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Nose / Head** | 0 | 0 | Head vertex | Used for yaw and release height baseline |
| **Left Shoulder** | 11 | 5 | Left Shoulder | Upper body kinetic chain vertex |
| **Right Shoulder** | 12 | 6 | Right Shoulder | Upper body kinetic chain vertex |
| **Left Elbow** | 13 | 7 | Left Elbow | Shooting / guide elbow angle |
| **Right Elbow** | 14 | 8 | Right Elbow | Primary shooting arm angle vertex |
| **Left Wrist** | 15 | 9 | Left Wrist | Release point & wrist snap |
| **Right Wrist** | 16 | 10 | Right Wrist | Primary release point & wrist snap |
| **Left Hip** | 23 | 11 | Left Hip | Hip extension & torso tilt |
| **Right Hip** | 24 | 12 | Right Hip | Hip extension & torso tilt |
| **Left Knee** | 25 | 13 | Left Knee | Lower body dip depth |
| **Right Knee** | 26 | 14 | Right Knee | Lower body dip depth |
| **Left Ankle** | 27 | 15 | Left Ankle | Jump takeoff timing |
| **Right Ankle** | 28 | 16 | Right Ankle | Jump takeoff timing |

*Rule:* Evaluator computes keypoint error **only on the intersection of annotated joints** (the 12 major body landmarks above). Never invent dummy coordinates for unannotated joints.

---

## 3. Project Single-Player Pilot Clips Manifest

| Clip ID | File Name | Player ID | Camera View | Frame Rate | Frame Count | Duration | Intended Split | Annotation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `clip_001_klay` | `klay_vid.mp4` | `klay_thompson` | $90^\circ$ Side Profile | 29.97 FPS | 275 | 9.18s | Development / Exploratory | Annotated (1 valid shot, release at F145) |
| `clip_002_mike1` | `mikeddunnstud1.mp4` | `mike_dunn` | $45^\circ$ Oblique Angle | 30.00 FPS | 753 | 25.10s | Held-Out Test Split | Annotated (2 valid shots, release F280, F590) |
| `clip_003_mike2` | `mikeddunnstud2.mp4` | `mike_dunn` | $90^\circ$ Side Profile | 30.00 FPS | 1639 | 54.63s | Held-Out Test Split | Annotated (4 valid shots, releases F220, F610, F1020, F1430) |

---

## 4. Evaluation Separation Guarantees

1. **Synthetic Regression Suite (`EVAL_REPORT.json`):** Evaluates state-machine invariants, gesture rejections, and imputation safeguards. Strictly labeled as synthetic fixtures.
2. **Public Dataset Benchmark (`PUBLIC_DATASETS_REPORT.json`):** Evaluates schema mapping, joint localization consistency, and downstream SPL kinematics compatibility.
3. **Real-Video Single-Player Pilot (`DATASET_EVAL_REPORT.json`):** Evaluates end-to-end detection rate, release frame MAE against human annotations, confidence coverage, and 2D/3D perspective foreshortening deltas.
