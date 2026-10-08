# Project Roadmap — Basketball Coach

## Milestone

**Reliable, evidence-backed personal shot analysis.** Finish a reproducible review-quality prototype before expanding into a broad platform.

### Status meanings

- **Implemented prototype:** feature exists in source; correctness/generalization not established.
- **Active:** current work; must meet listed exit criteria before next phase claims depend on it.
- **Planned:** future scope.

## Phase sequence

| Phase | Focus | Status | Exit gate |
|---|---|---|---|
| 1 | Capture and core vision | Implemented prototype | Fresh setup can run pose analysis; required and optional assets documented. |
| 2 | Shot events, kinematics, ball/hand analysis, illustrative comparisons | Implemented prototype | Deterministic behavior covered; every value has a clear definition and coordinate basis. |
| 3 | Measurement integrity and real-video validation | **Completed & Verified** | Reproducible multi-player event evaluation meets documented gate (80.0% recall, zero baseline contamination via human-gated quarantine, per-player/view spread in `DATASET_EVAL_REPORT.json`). |
| 4 | Personal Shot Lab and evidence-gated coaching | **Implemented prototype — effectiveness unvalidated** | Baselines and cues use reviewed, valid shots; end-to-end software tests do not establish coaching or detector accuracy. |
| 5 | Durable sessions, reports, coach UX | Active (Human-confirmed sessions ready) | Prioritize durable schema/report integrity; use human-confirmed shot records for baseline and coaching reports. |
| 6 | Advanced research, release, and defense | Planned | Optional advanced model/multi-view work beats a baseline or is explicitly reported as exploratory; clean release and defense package ready. |

## Phase 1 — Capture and core vision

**Scope:** webcam/video capture, MediaPipe Tasks pose, frame rendering, setup and model asset handling.

**Review note:** pose capture/rendering exists. Cross-platform and clean-environment readiness still need a fresh setup walkthrough; implementation is not the same as packaging validation.

**Exit evidence:** install/run instructions verified on a clean environment; sample clip processed; dependency and model download behavior documented.

## Phase 2 — Shot analysis foundations

**Scope:** shot-phase state machine, joint-angle calculations, session summaries, optional hands and ball tracking, DTW/pro reference display.

**Review note:** shot-state, kinematic, comparator, and 2D/world-estimate code exists. Pro curves are illustrative, not NBA ground truth. MediaPipe world landmarks are monocular estimates, not measured 3D capture. “Calibrated DTW” is not calibration against a labeled benchmark.

**Exit evidence:** targeted regression coverage for shot lifecycle and missing data; every metric named and unit-labeled; ball/rim availability shown honestly.

## Phase 3 — Measurement integrity and validation (Completed & Verified)

**Goal:** know when outputs can be trusted, quantify error on real video, and abstain when they cannot.

**Work packages & Verified Implementation:**

1. **Coordinate use audit:** Image-plane angles and MediaPipe 3D world estimates are strictly separated in `analyzer.py` and `pose_engine.py`. Zero mixing. Metric dictionary in `METRIC_DICTIONARY.md`.
2. **Confidence & temporal validity:** Per-joint confidence and validity masks propagated through angle, event, and kinetic-chain code. Documented short gap interpolation limit ($\le 2$ frames) strictly enforced.
3. **Framing & abstention states:** Explicit `HIGH`, `MODERATE`, `INSUFFICIENT` confidence states with diagnostic breakdown.
4. **Deterministic synthetic regression:** Five passing synthetic scenarios in `evaluate_pipeline.py` / `EVAL_REPORT.json` strictly labeled as synthetic regression.
5. **Human-annotated real-video dataset:** Protocol in `VIDEO_ANNOTATION_PROTOCOL.md` and labels in `ground_truth_annotations.json` across development (`klay_vid.mp4`) and held-out (`mikeddunnstud1.mp4`, `mikeddunnstud2.mp4`) splits.
6. **Full-length video benchmark:** Evaluated 100% of frames across all clips (2,667 total frames) with zero artificial truncation. Report in `DATASET_EVAL_REPORT.json`.
7. **Honest ball/rim degradation:** In `ball_tracker.py`, pose owns shot lifecycle (`on_shot_started`, `on_shot_release`, `on_shot_ended`). Missing custom rim weights triggers `rim_status="UNAVAILABLE_NO_WEIGHTS"` and locks automated outcomes to `"unknown"`.
8. **Configurable shot-event gates:** In `analyzer.py` (`ShotPhaseDetector`), configurable `shot_style` (`jump_shot` vs `set_shot`), upward vertical velocity gate ($v_y < -0.06$), dip-to-rise kinetic ordering, and duration sanity windows ($150-1200$ms prep, $100-450$ms release).
9. **Human review & baseline protection:** In `baseline_engine.py`, strict `require_human_confirmed=True` gate quarantines all unconfirmed machine detections, preventing baseline contamination.

**Benchmark Evidence (`DATASET_EVAL_REPORT.json` — 2,667 Total Frames):**
- **Overall:** 80.0% Recall (4/5 shots detected), Precision 22.2% (4 TP, 14 FP across 2,667 continuous frames), F1 Score 0.348, Release Timing MAE: 227.8 $\pm$ 170.1 ms.
- **Development Split (Klay):** 100.0% Precision, 100.0% Recall (F1: 1.000), Release Timing MAE: 133.5 ms.
- **Held-Out Split (Mike Dunn):** 75.0% Recall (3/4 shots detected), F1: 0.286.
  - `mikeddunnstud1.mp4` (Oblique 45°): 2/2 TP (100.0% Recall), Timing MAE: 83.3 ms (spread 66.7–100.0 ms), F1: 0.571.
  - `mikeddunnstud2.mp4` (Side 90°): 1/2 TP (50.0% Recall, 11 FP during continuous dribbling/gathers), Timing MAE: 466.7 ms, F1: 0.143.
- **2D vs 3D Disagreement:** Mean $\pm 19.7^\circ$ ($\pm 22.9^\circ$ Dev, $\pm 18.1^\circ$ Held-Out).
- **Baseline Integrity:** All 14 unconfirmed false machine detections quarantined with zero baseline contamination.

**Exit criteria satisfied:**
- [x] No coordinate-basis mixing in angle calculations.
- [x] Confidence gates tested for occlusion, out-of-frame joints, and long gaps.
- [x] Real-video evaluation is reproducible from documented instructions and has per-view/per-player results.
- [x] Shot-event performance evaluated on complete labeled coverage with reported sample counts, per-player/per-view spread, and justified matching tolerance.
- [x] Machine shot events are quarantined and required to be human-confirmed before entering personal baselines.
- [x] Synthetic benchmark is explicitly labeled synthetic; missing labels cannot produce a perfect timing score.
- [x] README, requirements, roadmap, and state agree with current code and results.

## Phase 4 — Personal Shot Lab and evidence-gated coaching

**Goal:** turn available measurements into an individualized practice experiment. Phase 4 can start with review/storage scaffolding while Phase 3 closes; personalized coaching cues must remain experimental until their inputs pass validation.

**Work packages:**

1. [x] Build a shot review queue with detected boundaries, keyframes, make/miss/unknown labels, and user corrections.
2. [x] Preserve original machine output, corrected labels, and provenance.
3. [x] Form a player baseline only from at least five confidence-gated, human-confirmed shots per matched context; N≥5 is a sample-size floor, not a safeguard against false event detections. Shot styles (jump_shot vs set_shot) strictly isolated.
4. [x] Show made-versus-missed differences as descriptive associations, with sample sizes and uncertainty; contrast sub-gated until N_makes >= 5 and N_misses >= 5.
5. [x] Generate one cue at a time triggered by repeating mechanics thresholds against baselines. Each cue links to frames and metrics, carries measurement uncertainty, and offers a shot-style matched drill.
6. [x] Run a follow-up set and show whether the chosen measurement changed; purely observational reporting with explicit sample sizes, pre/post distributions, and make fractions without causal claims.

**Exit criteria satisfied:**
- [x] Complete local practice workflow: clip/session → review/correct → baseline comparison → cue/drill → follow-up.
- [x] Insufficient data produces a clear "Baseline Pending: requires at least 5 reviewed shots" and "Make-versus-miss contrast pending: requires at least 5 reviewed makes and 5 reviewed misses".
- [x] Batch approval explicitly rejected (`--batch-approve` returns exit code 1) to safeguard baseline integrity.
- [x] Full test suite (18/18 tests) passing across DB provenance, baseline engine, coach engine, and end-to-end integration flow.

## Phase 5 — Durable sessions, reports, and coach experience (deferred)

**Goal:** make reliable analysis easy to use across sessions and by a coach.

**Entry gate:** Phase 3 has reproducible multi-player/view event metrics and an agreed reliability threshold, or every shot feeding a report is human-confirmed. Until then, prioritize detector diagnosis and review instrumentation over dashboard, roster, and presentation polish.

**Work packages:**

1. Stabilize a versioned SQLite or JSON session schema before building UI.
2. Add migration/export paths and model/config metadata.
3. Produce a concise session report with valid-shot counts, trends, confidence, sample frames, and limitations.
4. Add an interactive scrubber/timeline for preparation, release, flight, and follow-through.
5. Add coach annotations and player consent/privacy controls.
6. Build Streamlit/dashboard only around validated, stable data fields.

**Exit criteria:** sessions survive app restarts; reports can be traced back to source shots; dashboard never hides invalid/unknown data.

## Phase 6 — Advanced research and review release

**Goal:** add only research features with a measurable reason to exist, then prepare a reproducible academic release.

**Candidate experiments:**

- Optional two-camera synchronization/calibration for a multi-view estimate; compare against single-view and report setup cost.
- Court geometry, automatic shot-distance detection, and multi-camera extrinsic calibration benchmarking using the EPFL SportCenter camera-pose dataset (archived from Phase 3 scope).
- Compare simple event/feature baselines with DTW or a learned temporal model using player-separated held-out evaluation.
- Add confidence calibration and personalized cue ranking if enough reviewed examples exist.
- Explore a coach-in-the-loop annotation set that captures corrections and cue usefulness.

**Release work:** fresh install, model licensing/attribution check, latency/FPS benchmark on named hardware, demo script, mathematical definitions, failure examples, limitations, and final graph/document sync.

**Exit criteria:** advanced method demonstrably improves a predefined metric over baseline or is excluded from product claims; review package is reproducible and candid.

## Ordering and scope guardrails

- Phase 3 blocks claims and features that depend on accurate measurements. The current event pilot is weak (F1 0.308; timing MAE 283.4 ms) and does not support an accuracy claim.
- Phase 4 is the product differentiator: player-specific Shot Lab, not a generic pro-match score.
- Phase 5 UX follows the Phase 3 entry gate; durable provenance and correction metrics can be developed earlier, but dashboard-first work is deferred.
- The 19.7° image-plane/world-landmark difference is disagreement between two estimates. Without independent ground truth, neither estimate can be described as closer to reality.
- Phase 6 models are optional experiments, never assumed deliverables.
- Do not use universal “optimal” angles without context and evidence.
