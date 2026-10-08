# Phase 3 — Measurement Integrity and Real-Video Validation

**Status:** Complete & Verified. Configurable kinematic gates, master-timeline ball tracking with honest degradation, and human-gated baseline quarantine are fully implemented and verified against the full-duration (2,667 frames) multi-clip benchmark (`DATASET_EVAL_REPORT.json`).

**Dataset follow-on:** See [03-DATASET-PLAN.md](03-DATASET-PLAN.md) and [03-EPFL-CAMERA-POSE-PLAN.md](03-EPFL-CAMERA-POSE-PLAN.md) for public dataset qualification (EPFL camera-pose calibration, SPL trial kinematics), and single-player/multi-player video pilots. Results remain strictly separated by data source and label type. Body-joint PCK/MPJPE are not claimed from EPFL camera-pose files.

## Goal

Establish reproducible limits and error rates for current measurements. Suppress analysis when the video cannot support it.

## Deliverables

1. Metric/coordinate audit and definitions.
2. Confidence and missing-data propagation with a tested abstention state.
3. Correctly scoped five-scenario synthetic regression suite.
4. Human-annotated real-video evaluation set and protocol.
5. Real-video report with breakdowns, uncertainty, and representative failures.
6. Reconciled user/setup documentation.

## Plan

### Task 1 — Trace coordinate systems and define metrics

- Trace image-normalized, pixel, and world landmarks from `pose_engine.py` through `analyzer.py`, `main.py`, hand/ball modules, and CSV export.
- Ensure a 2D angle uses a consistent image-plane basis and a 3D estimate uses one consistent world basis; never mix the two silently.
- Resolve `pt_3d` fallback behavior: if world landmarks are unavailable for any required joint, either mark the world estimate unavailable or identify a separately computed image-space fallback; never label a mixed result `3D_WORLD_METRIC`.
- Correct/define image-plane geometry when video aspect ratio differs from square pixels in normalized coordinate calculations.
- Add a metric dictionary: formula/landmarks, coordinate basis, units, valid view assumptions, confidence source, missing-data behavior.
- Preserve raw and smoothed coordinates separately so smoothing cannot hide source uncertainty.

**Acceptance:** metric definitions match implementation; coordinate basis is explicit in code/output; sample calculations can be independently reproduced.

### Task 2 — Confidence and temporal integrity

- Build joint confidence from available visibility/presence and validity signals; do not treat confidence as angle accuracy until calibrated.
- Propagate validity masks into angle, phase, kinetic-chain, and shot summary logic.
- Interpolate only documented short gaps; preserve long gaps as invalid and avoid fixed-value substitution.
- Add a whole-shot coverage rule and states `HIGH`, `MODERATE`, `INSUFFICIENT` with reasons (joint occluded, framing, too few frames, etc.).
- Align HUD tracking confidence with the joints and threshold actually required by each displayed metric; a global badge must not imply an angle is valid when its gate rejects the landmarks.
- Align the production interpolation default with the documented rule and evaluator (currently evaluator uses max gap 2; production helper default is 3).
- Suppress metric-specific cues if any required input is invalid; let unrelated valid metrics remain available.
- Verify phase-machine recovery after occlusion and prevent a dropout from ending/counting a shot incorrectly.

**Acceptance:** targeted cases cover each confidence state, each important joint missing, short/long gaps, false gestures, and recovery. Invalid metrics never become plausible numeric values.

### Task 3 — Repair synthetic evaluator semantics

- Keep synthetic generated streams as deterministic regression fixtures and label their report accordingly.
- Count actual release detections separately from recorder shot count.
- Remove timing fallback that substitutes the ground-truth frame when no release was detected; missing event becomes a miss/unscored timing value, never zero error.
- Include true negatives/negative scenarios and define metric denominators; report undefined metrics as `N/A`, not 100% by convention.
- Make scenario inventory in code, report, and docs match; test all documented scenarios.
- Separate detector/phase unit fixtures from end-to-end video evaluation; avoid describing synthetic results as pipeline accuracy.

**Acceptance:** a deliberately broken detector cannot yield perfect timing; scenario count and metrics are internally consistent; output banner says synthetic regression.

### Task 4 — Real-video annotation coverage and configurable shot-event gating

- **Annotation audit and coverage:**
  - Audit `ground_truth_annotations.json` against actual video lengths in `raw_clips/`.
  - Ensure development split (`klay_vid.mp4`) and held-out split (`mikeddunnstud1.mp4`, `mikeddunnstud2.mp4`) are strictly separated.
  - Zero tuning against held-out clips.
- **Configurable shot-event gates in `analyzer.py` (`ShotPhaseDetector`):**
  - **Wrist-height elevation gate:** Configurable threshold (`shot_style="jump_shot"` requiring wrist $\ge$ nose/forehead level, vs. `"set_shot"` requiring shoulder-relative elevation). Enforce landmark confidence/visibility $\ge 0.5$.
  - **Vertical velocity gate:** Require upward vertical velocity ($v_{y, \text{wrist}} < -0.06$) to enter `releasing`; suppress downward/lateral arm movements.
  - **Dip-to-rise kinetic ordering:** Verify lower-body dip/flexion precedes or syncs with upper-body drive.
  - **Phase duration sanity windows:** Require plausible timing windows ($150-1200$ms prep, $100-450$ms release drive, $400-2000$ms total); suppress jitter transients and timeout static holds.
  - **Ball proximity policy:** Treat ball proximity as an optional confidence booster, not an exclusionary gate.
- **Human-gated baseline inclusion in `baseline_engine.py`:**
  - Prototype gate: require human confirmation for every shot admitted to personal baselines.
  - Live `M`/`X` hotkey counts only if shot event is explicitly confirmed; otherwise route to CLI review (`review_shots.py`).
  - Quarantine automated admission until held-out benchmark reliability gate is met.

**Acceptance:** Gated detector suppresses false gathers; unit tests verify gate parameters; baseline engine rejects unconfirmed shots.

### Task 5 — Full-length real-video evaluation and stratified reporting

- **Remove video frame caps:**
  - Remove all artificial truncation (`limit_frames = 300`) in `evaluate_dataset.py` to evaluate 100% of video frames across all clips.
- **Evaluate and report stratified metrics:**
  - Compute overall Precision, Recall, and F1 score.
  - Release timing error: Mean Absolute Error (MAE in frames and ms) with inter-shot spread (std, min, max).
  - Subgroup breakdown by player: Development (`klay_thompson`) vs. Held-Out (`mike_dunn`).
  - Subgroup breakdown by viewpoint: $90^\circ$ Side vs. $45^\circ$ Oblique.
  - Human correction metrics: review override rate and boundary delta $|\Delta t|$.
  - Output to `DATASET_EVAL_REPORT.json` and update `.planning/STATE.md`.

**Acceptance:** Evaluation runs over complete video durations with zero truncation; outputs per-player and per-view metric spread; never tunes on held-out clips.

### Task 6 — Ball trajectory synchronization & honest degradation

- **Detailed Plan:** See [03-BALL-TRACKING-PLAN.md](03-BALL-TRACKING-PLAN.md).
- **Master timeline synchronization:**
  - Deprecate independent state machine in `ball_tracker.py`. Bind ball flight lifecycle directly to pose `ShotPhaseDetector` shot ID and frame windows ($t_{\text{start}} \to t_{\text{release}} \to t_{\text{end}}$).
  - Use ball-hand proximity as an optional confidence boost during prep, not a gating veto.
  - Reset flight observations per shot; eliminate cross-shot data leakage.
- **Honest rim & outcome degradation:**
  - Explicitly declare rim status: when custom weights (`weights/basket_rim.pt`) are absent, permanently emit `rim_status="UNAVAILABLE_NO_WEIGHTS"`.
  - Prohibit heuristic make/miss classification on stock COCO `sports ball` detections; set `outcome="unknown"`. Human `M`/`X`/`U` labels remain the sole outcome source for baselines.
- **Real-video ball evaluation:**
  - Extend `evaluate_dataset.py` with `--eval-ball` to measure real-world ball detection coverage (% of flight frames detected) and release alignment delta ($|\Delta t| = |t_{\text{ball\_detach}} - t_{\text{pose\_release}}|$) on annotated clips.
  - Gate parabola/entry-angle metrics on count ($\ge 4$ points), confidence, and fit quality ($R^2 \ge 0.85$).

**Acceptance:** Ball flight attributes are bound to pose shot IDs; missing rim weights trigger clean `UNAVAILABLE_NO_WEIGHTS` degradation; zero automated outcomes enter baselines without custom weights.

### Task 7 — Documentation and phase closeout

- Update README, CLI help, `.planning/PROJECT.md`, roadmap, and state to reflect verified implementation only.
- Explain model setup: pose model required today; hand and stock YOLO assets optional and fetched only through their paths.
- Add one successful capture example and one failure/abstention example.
- Publish known limitations and the evaluation report.

**Acceptance:** clean setup and demo instructions agree with code; phase exit gate in ROADMAP.md is backed by linked evidence.

## Risks and mitigations

- **Small dataset:** report it as a pilot, avoid population/generalization language, and recruit more participants before strong claims.
- **Reference-angle ambiguity:** define camera and annotation protocol; compare against a suitable reference and report annotator variation.
- **Camera/view confounding:** hold out participants and stratify by view; do not tune and evaluate on the same clips.
- **Confidence overclaim:** visibility is an input signal, not a calibrated probability of measurement correctness; calibrate against annotated error.

## Out of scope

Voice coaching, dashboard, LSTM/Transformer, pro digital twins, causal miss diagnosis, and broad product claims. These depend on Phase 3 evidence.
