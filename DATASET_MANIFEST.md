# Real-World & Public Dataset Manifest for Basketball Shot Analysis

This manifest qualifies external public datasets and project-recorded video clips for validating the basketball biomechanical analysis pipeline.

---

## 1. Candidate Dataset Qualification Matrix

| Dataset | Provider / Source | License | Format & Structure | Intended Role in Pipeline | Inclusions | Exclusions & Caveats |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SPL Open Data (Free Throws)** | MLSE Sport Performance Lab ([GitHub](https://github.com/Sport-Performance-Lab/SPL-Open-Data)) | CC BY-NC-SA 4.0 | 583 trials, 5 participants, 2 sessions. Frame-by-frame 3D markerless mocap JSON trajectories + outcome labels (Made/Missed). | Downstream biomechanics & outcome validation. | Kinematic curves (knee flexion, elbow extension, hip drive), temporal sequencing lags, make/miss labels. | **Cannot test RGB video pose detector:** Provides pre-computed 3D markerless tracking points, not raw synchronized single-camera phone videos. Small cohort ($N=5$). |
| **EPFL SportCenter Dataset** | EPFL CVLab (`clones/sportcenter_camerapose_dataset`) | Academic Research License | 28 smartphone video sequences (Samsung A5 & iPhone 6 at 90°, 50,127 frames), camera intrinsics ($K, distCoeffs$), frame-by-frame ground homography ($Hr$), extrinsic pose ($R, t$), 3D court grid (`ground_grid.json`), and 3D player floor positions (`player_positions.json`, $Z=0$). | **Archived to Phase 6 Backlog:** Camera pose calibration & court geometry reprojection benchmark. | Planar-vs-distorted camera reprojection residuals, FOV court grid coverage, train/test split verification (12 train, 16 test sequences). | **Dropped from Phase 3 active scope:** The dataset contains camera calibration, court homographies, and ground-level player locations ($Z=0$), but **zero human skeletal body-joint annotations**. |
| **SHOT Basketball Dataset** | Muyu et al., ACM MM 2025 ([HuggingFace](https://huggingface.co/datasets/muyu111/basketball)) | Annotations: CC BY-NC 4.0; Broadcast Video: Third-Party Rights Reserved | 1,979 clips, 5 camera views. Player tracks, body poses, tactic labels (Drive, Dunk, Spot-up). | Exploratory action/intention context. | Event timestamps, broad tactical action classifications. | **Excluded from video pipeline:** Raw broadcast footage carries third-party broadcast rights and is not redistributed. Group play does not match solo practice workflow. |
| **Project Single-Player Pilot** | Consented shooting sessions & recorded clips (`klay_vid.mp4`, `mikeddunnstud1.mp4`, `mikeddunnstud2.mp4`) | Project Owned / Consented Reference Clips | 30 FPS RGB video files, full-body side/oblique/frontal framing. | **Primary End-to-End Benchmark:** Pose coverage, shot event detection (dip, release), 2D/3D angle disagreement, outcome review. | Full video stream, MediaPipe BlazePose pipeline, confidence gating, live hotkeys, review queue. | Convenience sample; requires manual multi-angle annotations following `VIDEO_ANNOTATION_PROTOCOL.md`. |

---

## 2. Dataset Schemas & Label Availabilities

### 2.1 EPFL SportCenter Camera-Pose Schema (`clones/sportcenter_camerapose_dataset`)
The cloned dataset provides camera calibration and court geometry records:
- **Intrinsics:** `intrinsics_seq_17xxxx.json` (Samsung A5, 1080p, $K, distCoeffs$) and `intrinsics_seq_98xx.json` (iPhone 6, 1080p, $K, distCoeffs$).
- **Poses & Homographies:** `poses.json` per sequence, providing $Hr$ ($3 \times 3$ ground-to-image homography), $R$ ($3 \times 3$ camera-to-world rotation), and $t$ ($3 \times 1$ camera translation in meters).
- **Court Geometry:** `ground_grid.json` (480 3D court floor coordinates in meters, $Z=0$), `homography_rectified_template.json` ($3 \times 3$ template homography $M$).
- **Player Floor Coordinates:** `player_positions.json` (lists $[X, Y, 0.0]$ ground coordinates of player feet).
- **Body-Joint Availability:** **None.** No skeletal keypoints (head, shoulders, elbows, wrists, hips, knees, ankles) exist in this dataset.

*Rule:* Evaluator computes only mathematically supported camera/court geometry metrics. It does not fabricate body keypoints or report unsupported PCK/MPJPE metrics.

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
