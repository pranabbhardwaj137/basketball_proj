# Phase 3 — Measurement Integrity and Real-Video Validation

**Status:** Active. Core safeguards and synthetic regression fixtures exist, but code consistency and real-video validation do not close this phase.

**Dataset follow-on:** See [03-DATASET-PLAN.md](03-DATASET-PLAN.md) for public dataset qualification, pose/kinematics checks, and a consented single-player video pilot. Keep results separated by data source and label type.

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

### Task 4 — Define and collect real-video annotations

- Write a capture protocol covering side, diagonal, and front views; stable camera; full-body framing; resolution/FPS; distance; lighting; and shot types.
- Create annotation schema for player/clip IDs, view, shot start, release frame/time, follow-through, visible/occluded key joints, shot outcome, and optional reference angle.
- State outcome-label source. Use human-reviewed outcome labels when automatic rim detection is absent.
- Collect diverse clips with consent and document exclusion criteria. Keep training/tuning clips separate from held-out evaluation clips, preferably by player.
- Double-annotate a subset and report agreement before treating labels as ground truth.

**Acceptance:** dataset manifest, annotation instructions, split definition, and label-quality summary exist; no identifiable practice clip is published without permission.

### Task 5 — Evaluate and report

- Report shot precision, recall, F1, false positives by gesture, release timing error, valid-shot coverage, abstention rate, and confidence/error calibration where sample size permits.
- Report angle error only for a defined reference and matching joint/view; disclose that coach markup is not laboratory ground truth.
- Break down by camera view, player, lighting/occlusion, and shot type; include failures and uncertainty intervals when appropriate.
- Compare image-plane and model-inferred world-angle estimates without calling either lab-grade by default.
- Persist the `klay_vid.mp4` exploratory output with frame and timestamp samples. Describe the ±22.9° user-reported difference as unverified until reproduced; even when reproduced, call it 2D-vs-model-world estimate disagreement, not measurement error or measured foreshortening.
- Record hardware, software/model versions, commands, and evaluation data IDs for reproducibility.

**Acceptance:** evaluation reruns from documented commands and emits sample counts with every metric; headline claims never omit their data basis.

### Task 6 — Ball trajectory validity

- Preserve per-detection timestamps when `detect_every > 1`; fit using time-aware observations where the model requires time.
- Gate parabola/entry-angle metrics on number, confidence, temporal span, and fit quality.
- Distinguish `ball unavailable`, `rim unavailable`, `trajectory inconclusive`, `made`, and `missed`.
- Test missing detections, vertical/near-vertical trajectories, outliers, and no-rim cases.

**Acceptance:** unsupported result returns `unknown` with reason; no skipped-frame spacing is treated as uniform by accident.

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
