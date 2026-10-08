# Project State

## Current milestone

**Reliable, evidence-backed personal shot analysis**

- **Active phase:** Phase 4 — Personal Shot Lab & Evidence-Gated Coaching (Complete — exit gate satisfied with versioned SQLite provenance, per-shot quarantine review, shot-style isolation, mechanics threshold cue gating, observational follow-up reporting, and 18/18 passing tests).
- **Phase 1:** Capture/pose/rendering implemented as a prototype; clean-install and cross-platform evidence documented.
- **Phase 2:** Shot state, kinematics, DTW/comparison and related components implemented as prototypes; not broadly validated. Pro profiles are illustrative.
- **Phase 3 (Measurement Integrity & Full-Length Video Benchmark):** Completed and verified.
  - **Full-Duration Benchmark (`DATASET_EVAL_REPORT.json` — 2,667 total frames evaluated across all clips with zero truncation):**
    - Overall: 80.0% Recall (4/5 total annotated shots detected), Precision 22.2% (4 TP, 14 FP across continuous practice drills), F1 Score 0.348, Release Timing MAE: 227.8 $\pm$ 170.1 ms.
    - Development Split (`klay_vid.mp4`, 211 frames): 100.0% Precision, 100.0% Recall (F1: 1.000), Release Timing MAE: 133.5 ms.
    - Held-Out Split (`mike_dunn`, 2,392 frames): 75.0% Recall (3/4 shots detected, 14 FP across unedited practice drills), F1: 0.286.
      - `mikeddunnstud1.mp4` (Oblique 45°): 2/2 TP (100.0% Recall), Timing MAE: 83.3 ms (spread 66.7–100.0 ms), F1: 0.571.
      - `mikeddunnstud2.mp4` (Side 90°): 1/2 TP (50.0% Recall, 11 FP during continuous dribbling/gathers), Timing MAE: 466.7 ms, F1: 0.143.
    - Coordinate Basis Disagreement: Mean 2D vs. 3D angle divergence is $\pm 19.7^\circ$ ($\pm 22.9^\circ$ Dev, $\pm 18.1^\circ$ Held-Out).
  - **Kinematic & Gate Protections (`analyzer.py`):** Configurable `shot_style` (`jump_shot` with nose/forehead elevation vs. `set_shot` with shoulder elevation), upward vertical velocity gate ($v_{y, \text{wrist}} \le -0.06$), dip-to-rise ordering, and duration guards ($150-1200$ms prep, $100-450$ms release).
  - **Baseline Protection Engine (`baseline_engine.py`):** Strict prototype gate (`require_human_confirmed=True`) quarantines all unconfirmed automated detections, preventing baseline contamination without human verification.
  - **Ball Tracking Lifecycle & Honest Degradation (`ball_tracker.py`):** Pose master-timeline synchronization (`on_shot_started`, `on_shot_release`, `on_shot_ended`); missing `weights/basket_rim.pt` triggers clean `rim_status="UNAVAILABLE_NO_WEIGHTS"` and locks automated outcomes to `"unknown"`.
- **Phase 4 (Personal Shot Lab & Evidence-Gated Coaching):** Completed and verified.
- **Phase 5 (Coach UX & Dashboard):** Unlocked for human-confirmed session workflows.
- **Next:** Proceed to Phase 5 (Durable sessions, reports, and coach experience).

## Completed Work in Phase 4 (Personal Shot Lab)

- [x] **SQLite & Provenance Engine (`shot_lab_db.py`):** Schema version 2 with `players`, `sessions`, `shots`, `baselines`, and `remediations`. Preserves immutable machine boundaries (`machine_*_frame`) alongside editable human review boundaries (`annotated_*_frame`). Added `shot_style` and `review_status` columns with automatic migration.
- [x] **Live Outcome Hotkeys & HUD Overlay (`main.py`):** Interactive non-blocking 2.5s prompt `[M] Make | [X] Miss | [U] Unknown` stamping `outcome_source: live_hotkey` and approving reviewed shots while leaving unlabeled/unknown attempts quarantined. Passed `shot_style` context through pipeline.
- [x] **Post-Session Review Queue (`review_shots.py`):** CLI and interactive keyframe scrubber allowing boundary and label overrides without data loss. Explicit per-shot approval (`--approve`) and discarding (`--discard`). Blind batch-approval (`--batch-approve`) explicitly rejected with exit code 1 to safeguard baseline integrity.
- [x] **Personal Baseline Engine (`baseline_engine.py`):** Strict shot-style isolation (`jump_shot` vs `set_shot`). Enforces $N \ge 5$ approved shots for baseline computation. Gated make-versus-miss contrast until $N_{\text{makes}} \ge 5 \land N_{\text{misses}} \ge 5$ to prevent small-sample noise distortion. Reports $\bar{x} \pm s$ sample standard deviations and temporal quantization error ($\pm 33.3\text{ms}$ at 30 FPS).
- [x] **Hierarchical One-Cue Remediation (`coach_engine.py`):** Triggers cues based on repeating mechanics thresholds against baselines (Tier 1 Sequencing $\to$ Tier 2 Release Extension $\to$ Tier 3 Frontal Stability). Separated thresholds and drills for `jump_shot` and `set_shot`. Follow-up set evaluation produces purely observational reporting ($N_{\text{pre}}$, $N_{\text{post}}$, $\bar{x} \pm s$, $M/N$ make percentages, `drill_completed`) with zero causal claims.
- [x] **Comprehensive Test Suite:** 18/18 tests passing across `test_shot_lab_db.py`, `test_baseline_engine.py`, `test_coach_engine.py`, and `test_shot_lab_flow.py`.

**Evidence limit:** Passing integration tests confirm application flow, not field accuracy. The N≥5 gate is not protection against false detections unless the underlying shots are reviewed/confirmed.


## Completed Audit Fixes in Phase 3

- [x] **Coordinate-Basis Purity:** `pt_3d` in `analyzer.py` strictly requires all joints from `world_landmarks` in meters; zero fallback to normalized image coordinates within 3D angle calculations.
- [x] **Interpolation Limit Alignment:** Production `interpolate_kinematic_series` default and synthetic evaluator aligned to identical $\le 2$ frames rule ($\le 66\text{ms}$ at 30 FPS).
- [x] **Exploratory Real-Video Benchmark:** `evaluate_video.py` generates `KLAY_EVAL_REPORT.json` with frame-by-frame breakdown, detection rate (65.1%), and explicit labeling of 2D vs. 3D estimate-to-estimate disagreement ($\pm 22.9^\circ$).
- [x] **Metric Dictionary:** Created `METRIC_DICTIONARY.md` defining all formulas, joint triplets, coordinate bases, units, and limitations.
- [x] **Separation of Evidence:** Synthetic regression results (`EVAL_REPORT.json`) strictly distinguished from real video evaluation (`KLAY_EVAL_REPORT.json`).

## Current validation priorities

- The 283.4 ms pilot release-timing MAE is much larger than one-frame quantization at 30 FPS (about 33.3 ms); investigate state-machine timing and false transitions first.
- Evaluate configurable combinations of wrist height/velocity, dip-to-rise ordering, and plausible duration. Treat ball-hand proximity as optional only when YOLO coverage/confidence is measured; unavailable detections mean unknown contact.
- Expand annotations across players and camera views. Report per-player/per-view F1 and timing-error distributions, sample counts, and uncertainty when the sample supports it.
- Record machine-to-human boundary correction rate, boundary shift, and outcome relabel rate while retaining original machine detections.
- The reported 19.7° 2D/world difference is estimate disagreement. Without independent ground truth, neither estimate is known to be more accurate.

