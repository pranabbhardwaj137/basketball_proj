# Phase 3 — Measurement Integrity & Real-Video Validation: Context & Locked Decisions

**Status:** Decisions Locked via Phase Discussion  
**Scope:** Shot-Event Detection Reliability, Configurable Kinetic Gates, Real-Video Full-Length Evaluation, and Human-Gated Baseline Integrity  

---

## 1. Phase Objective

Establish honest, reproducible detection accuracy and error bounds for shot events (dip, set, release, follow-through) on real multi-clip video footage without artificial video truncations. Implement configurable kinetic and geometric gates to eliminate false positives during pre-shot gathers and non-shooting movements. Enforce strict human confirmation before admitting shots into personal baselines during the prototype phase.

---

## 2. Locked Architecture & Implementation Decisions

### 2.1 Configurable Wrist-Height & Vertical Velocity Gates
- **Wrist Height Elevation (Hypothesis-Driven & Configurable):**
  - **Jump Shots:** Release requires wrist at or above **nose/forehead level** ($y_{\text{wrist}} \le y_{\text{nose}} + 0.02$ in normalized image coordinates).
  - **Set Shots:** Release allows a lower, shoulder-relative threshold ($y_{\text{wrist}} \le y_{\text{shoulder}} - 0.05$).
  - **Configuration:** Thresholds must be exposed as configurable parameters in `ShotPhaseDetector` (e.g. `shot_style="jump_shot" | "set_shot"`, `wrist_elevation_threshold`).
  - **Confidence Gate:** Requires tracking confidence on shooting wrist, elbow, shoulder, and nose landmarks (`visibility >= 0.5`).
  - **Scientific Guardrail:** Treated as an empirical hypothesis tested against annotated development clips, **not** asserted as a universal biomechanical rule.

- **Vertical Upward Velocity ($v_y$):**
  - Transition into `RELEASING` requires upward vertical velocity ($v_{y, \text{wrist}} < -0.06$ in screen space, equivalent to $\ge 2.0\text{ m/s}$ upward velocity).
  - Downward or lateral arm swings are strictly rejected.

### 2.2 Kinetic Dip-to-Rise Ordering & Plausible Phase Durations
- **Kinetic Ordering Requirement:**
  - A valid shot attempt must exhibit an uncoiling sequence: lower body dip minimum ($\min \theta_{\text{knee}}$) must precede or occur synchronously with upward arm elevation ($t_{\text{knee\_min}} \le t_{\text{set\_point}} < t_{\text{release}}$).
  - Upper-body arm extensions initiated without a preceding or concurrent lower-body drive are rejected or flagged as non-shooting gestures.

- **Plausible Temporal Duration Windows:**
  - **Preparation Phase (Dip $\to$ Set):** $150\text{ms} - 1,200\text{ms}$ (approx 5 to 36 frames at 30 FPS).
  - **Release Drive Phase (Set $\to$ Release):** $100\text{ms} - 450\text{ms}$ (approx 3 to 14 frames at 30 FPS).
  - **Follow-Through Hold:** $100\text{ms} - 800\text{ms}$ (approx 3 to 24 frames).
  - **Total Shot Lifecycle:** $400\text{ms} - 2,000\text{ms}$ (approx 12 to 60 frames).
  - Fast transients ($< 3$ frames) are rejected as sensor jitter; static holds ($> 2.5\text{s}$) abort to `IDLE`.

### 2.3 Ball Tracking Coordination, Synchronization & Honest Degradation
- **Master Authority (Single Shot Timeline):**
  - Pose analysis (`ShotPhaseDetector`) is the master timeline authority for shot lifecycle boundaries (`shot_id`, `start_frame`, `dip_frame`, `set_frame`, `release_frame`, `end_frame`).
  - `BallTracker` acts as a frame observer and feature attacher within the pose-governed shot window, eliminating independent flight triggers and cross-shot data contamination.
- **Ball-Hand Proximity Policy:**
  - Proximity between detected ball and shooting wrist is an **optional confidence booster** during preparation, not a hard gating veto.
  - Because stock YOLO models suffer frame dropouts during high-velocity release motion, absence of ball detection will **not** cause an otherwise valid kinematic shot to be rejected.
  - If ball detection coverage is measured and valid ($\ge 70\%$ of shot duration), ball proximity upgrades shot validity to `HIGH`.
- **Honest Model Degradation & Rim Status:**
  - Without custom trained weights (`weights/basket_rim.pt`), stock YOLOv8n COCO detects class 32 (`sports ball`) only and cannot detect a rim.
  - Rim status must be explicitly recorded as `rim_status="UNAVAILABLE_NO_WEIGHTS"`.
  - Automated rim make/miss classification is strictly prohibited with the stock COCO model. Automated outcomes are locked to `outcome="unknown"`; human `M`/`X`/`U` labels remain the sole outcome source.
  - Ball tracking is supplementary until real annotated clip evaluations verify ball detection coverage, release alignment ($\Delta t$), and rim model accuracy.

### 2.4 Strict Human-Gated Baseline Inclusion
- **Prototype Rule:** **Every shot admitted into personal baseline statistics must be human-confirmed.**
- A live `M`/`X` hotkey press counts as confirmation only if the shooter explicitly confirms the shot event; otherwise, the shot requires manual review in `review_shots.py`.
- Automated inclusion into baselines is quarantined until held-out multi-clip evaluation meets an agreed benchmark reliability gate (e.g. $F_1 \ge 0.85$ on held-out players).
- Unconfirmed automated detections remain stored in `shot_lab.db` with `status: "PENDING_REVIEW"`, but are excluded from `baseline_engine.py` calculations.

### 2.5 Full-Length Video Evaluation & Subgroup Metrics
- **Zero Video Truncation:** Remove all artificial frame caps (`limit_frames = 300`) from evaluation harnesses. Evaluator must process 100% of video frames for every clip in `ground_truth_annotations.json`.
- **Development vs. Held-Out Split Discipline:**
  - Algorithm thresholds are tuned exclusively against the **Development Split** (`klay_vid.mp4`).
  - **Never tune thresholds against the Held-Out Split** (`mikeddunnstud1.mp4`, `mikeddunnstud2.mp4`).
- **Reporting Metrics:**
  - Precision, Recall, F1 score.
  - Release Timing Absolute Error (MAE in frames and ms) with inter-shot spread (std, min, max).
  - Per-Player Subgroup Breakdown (`klay_thompson` vs. `mike_dunn`).
  - Per-Viewpoint Subgroup Breakdown ($90^\circ$ Side vs. $45^\circ$ Oblique).
  - Human Correction Metrics (Boundary timing delta $|\Delta t|$, review override rate).

---

## 3. Scope Fences & Execution Order

Following GSD order:
1. **Lock Context:** Persist decisions in `03-CONTEXT.md`.
2. **Phase Plan:** Create detailed execution tasks in `03-PLAN.md`.
3. **Implementation:** Update `ShotPhaseDetector` in `analyzer.py` with configurable gates.
4. **Verification:** Audit annotation coverage, rerun `evaluate_dataset.py` across full video durations, and emit `DATASET_EVAL_REPORT.json`.
