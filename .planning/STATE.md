# Project State

## Current milestone

**Reliable, evidence-backed personal shot analysis**

- **Active phase:** Phase 3 — Measurement integrity and real-video validation.
- **Phase 1:** Capture/pose/rendering implemented as a prototype; clean-install and cross-platform evidence still required.
- **Phase 2:** Shot state, kinematics, DTW/comparison and related components implemented as prototypes; not broadly validated. Pro profiles are illustrative.
- **Phase 3:** Completed measurement integrity audit fixes and baseline exploratory video benchmark on `klay_vid.mp4` (`KLAY_EVAL_REPORT.json`).
- **Phase 3 Dataset Plan Execution ([03-DATASET-PLAN.md](phases/03-measurement-validation/03-DATASET-PLAN.md)):** Executed end-to-end.
  - Manifest created in `DATASET_MANIFEST.md` and `DATASET_MANIFEST.json` qualifying SPL Open Data, EPFL SportCenter, SHOT dataset, and project single-player pilot clips.
  - Public dataset checks in `evaluate_public_datasets.py` (`PUBLIC_DATASETS_REPORT.json`): EPFL PCK@20% = 100.0%, PCK@5% = 77.8%; SPL kinematic formulas verified against published 3D bounds; SHOT broadcast rights exclusions documented.
  - Multi-clip shooting pilot in `evaluate_dataset.py` (`DATASET_EVAL_REPORT.json`): Evaluated against human reference annotations (`ground_truth_annotations.json`) across development (Klay) and held-out (Mike Dunn) splits. Overall: Precision 25.0%, Recall 40.0% (F1: 0.308), Timing MAE 283.4 ms, Mean 2D vs 3D Disagreement $\pm 19.7^\circ$.
- **Phase 4 (Personal Shot Lab):** Execution complete. Delivered `shot_lab_db.py` (versioned SQLite provenance schema preserving machine vs annotated boundaries), `main.py` live outcome hotkeys (`M`/`X`/`U`) with HUD overlay, `review_shots.py` post-session CLI review queue, `baseline_engine.py` ($N \ge 5$ sample gate, $\bar{x} \pm s$ distributions, temporal quantization disclaimer, descriptive make/miss associations), `coach_engine.py` (3-tier hierarchical One-Cue engine and follow-up delta tracking), and `test_shot_lab_flow.py` (100% test pass).
- **Next:** Phase 5 — Durable sessions, reports, coach UX & dashboard.

## Completed Work in Phase 4 (Personal Shot Lab)

- [x] **SQLite & Provenance Engine (`shot_lab_db.py`):** Schema version 1 with `players`, `sessions`, `shots`, `baselines`, and `remediations`. Preserves immutable machine boundaries (`machine_*_frame`) alongside editable human review boundaries (`annotated_*_frame`).
- [x] **Live Outcome Hotkeys & HUD Overlay (`main.py`):** Interactive non-blocking 2.5s prompt `[M] Make | [X] Miss | [U] Unknown` stamping `outcome_source: live_hotkey` to DB.
- [x] **Post-Session Review Queue (`review_shots.py`):** CLI and interactive keyframe scrubber allowing boundary and label overrides without data loss.
- [x] **Personal Baseline Engine (`baseline_engine.py`):** Enforces $N \ge 5$ valid shots, matches camera view and shot type, reports $\bar{x} \pm s$ sample standard deviations and temporal quantization error ($\pm 33.3\text{ms}$ at 30 FPS).
- [x] **Hierarchical One-Cue Remediation (`coach_engine.py`):** Evaluates Tier 1 (Sequencing lag) $\to$ Tier 2 (Release extension) $\to$ Tier 3 (Torso sway), outputs at most 1 cue + drill, and tracks follow-up sets.
- [x] **End-to-End Test Suite (`test_shot_lab_flow.py`):** 5/5 integration tests passing.


## Completed Audit Fixes in Phase 3

- [x] **Coordinate-Basis Purity:** `pt_3d` in `analyzer.py` strictly requires all joints from `world_landmarks` in meters; zero fallback to normalized image coordinates within 3D angle calculations.
- [x] **Interpolation Limit Alignment:** Production `interpolate_kinematic_series` default and synthetic evaluator aligned to identical $\le 2$ frames rule ($\le 66\text{ms}$ at 30 FPS).
- [x] **Exploratory Real-Video Benchmark:** `evaluate_video.py` generates `KLAY_EVAL_REPORT.json` with frame-by-frame breakdown, detection rate (65.1%), and explicit labeling of 2D vs. 3D estimate-to-estimate disagreement ($\pm 22.9^\circ$).
- [x] **Metric Dictionary:** Created `METRIC_DICTIONARY.md` defining all formulas, joint triplets, coordinate bases, units, and limitations.
- [x] **Separation of Evidence:** Synthetic regression results (`EVAL_REPORT.json`) strictly distinguished from real video evaluation (`KLAY_EVAL_REPORT.json`).

