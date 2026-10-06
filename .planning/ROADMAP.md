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
| 3 | Measurement integrity and real-video validation | **Active — implementation mostly present; validation open** | Fix coordinate/confidence inconsistencies; persist a reproducible, annotated real-video evaluation. |
| 4 | Personal Shot Lab and evidence-gated coaching | **Implemented & Verified** | Player baseline, outcome review, one-cue loop, and follow-up comparison work end-to-end, with experimental status labels. |
| 5 | Durable sessions, reports, coach UX | **Active / Next** | Versioned data and reports are usable; dashboard is built only on validated fields. |
| 6 | Advanced research, release, and defense | Planned | Optional advanced model/multi-view work beats a baseline or is explicitly reported as exploratory; clean release and defense package ready. |

## Phase 1 — Capture and core vision

**Scope:** webcam/video capture, MediaPipe Tasks pose, frame rendering, setup and model asset handling.

**Review note:** pose capture/rendering exists. Cross-platform and clean-environment readiness still need a fresh setup walkthrough; implementation is not the same as packaging validation.

**Exit evidence:** install/run instructions verified on a clean environment; sample clip processed; dependency and model download behavior documented.

## Phase 2 — Shot analysis foundations

**Scope:** shot-phase state machine, joint-angle calculations, session summaries, optional hands and ball tracking, DTW/pro reference display.

**Review note:** shot-state, kinematic, comparator, and 2D/world-estimate code exists. Pro curves are illustrative, not NBA ground truth. MediaPipe world landmarks are monocular estimates, not measured 3D capture. “Calibrated DTW” is not calibration against a labeled benchmark.

**Exit evidence:** targeted regression coverage for shot lifecycle and missing data; every metric named and unit-labeled; ball/rim availability shown honestly.

## Phase 3 — Measurement integrity and validation (active)

**Goal:** know when outputs can be trusted, quantify error on real video, and abstain when they cannot. Current code has meaningful safeguards, but this phase is not complete.

**Work packages:**

1. Audit coordinate use. Keep pixel/image-plane and world-landmark estimates distinct; compare both where useful.
2. Propagate per-joint confidence and temporal validity through angle, event, kinetic-chain, and shot-summary code.
3. Gate camera framing and cues; show a reason when the system abstains.
4. Keep the five passing synthetic scenarios as regression tests; they do not establish field accuracy.
5. Create a small annotated clip set across players and camera views. Define event labels, angle references, splits, and annotation agreement.
6. Report precision/recall/F1, release timing error, angle error where reference exists, coverage/abstention, and subgroup/failure breakdown.
7. Treat ball outcome as unknown when detection/trajectory evidence is insufficient; preserve timestamps across skipped frames.

**Current evidence:** `EVAL_REPORT.json` reports five synthetic scenarios passing (shot lifecycle, two gesture rejections, imputation, severe occlusion). `scratch_analyze_klay.py` can compare image-plane and MediaPipe world-estimate elbow angles on `klay_vid.mp4`; its printed difference is not error against ground truth. The reported ±22.9° and frame-by-frame notes are not currently persisted as a reproducible evidence report, so treat them as an unverified exploratory observation.

**Exit criteria:**

- No coordinate-basis mixing in angle calculations.
- Confidence gates tested for occlusion, out-of-frame joints, and long gaps.
- Real-video evaluation is reproducible from documented instructions and has per-view/per-player results.
- Synthetic benchmark is explicitly labeled synthetic; missing labels cannot produce a perfect timing score.
- README, requirements, roadmap, and HUD claims agree with current code and results.

## Phase 4 — Personal Shot Lab and evidence-gated coaching

**Goal:** turn available measurements into an individualized practice experiment. Phase 4 can start with review/storage scaffolding while Phase 3 closes; personalized coaching cues must remain experimental until their inputs pass validation.

**Work packages:**

1. Build a shot review queue with detected boundaries, keyframes, make/miss/unknown labels, and user corrections.
2. Preserve original machine output, corrected labels, and provenance.
3. Form a player baseline only after sufficient valid shots; compare matched contexts when possible (view, distance, drill, shot type).
4. Show made-versus-missed differences as descriptive associations, with sample sizes and uncertainty.
5. Generate one cue at a time. Each cue links to frames and metrics, carries a confidence state, and offers a drill or “dismiss.”
6. Run a follow-up set and show whether the chosen measurement changed; do not claim the cue caused a make-rate change without a suitable study.

**Exit criteria:** one complete local workflow from clip/session → review/correct → baseline comparison → cue/drill → follow-up; insufficient data produces a clear “not enough evidence.”

## Phase 5 — Durable sessions, reports, and coach experience

**Goal:** make reliable analysis easy to use across sessions and by a coach.

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
- Compare simple event/feature baselines with DTW or a learned temporal model using player-separated held-out evaluation.
- Add confidence calibration and personalized cue ranking if enough reviewed examples exist.
- Explore a coach-in-the-loop annotation set that captures corrections and cue usefulness.

**Release work:** fresh install, model licensing/attribution check, latency/FPS benchmark on named hardware, demo script, mathematical definitions, failure examples, limitations, and final graph/document sync.

**Exit criteria:** advanced method demonstrably improves a predefined metric over baseline or is excluded from product claims; review package is reproducible and candid.

## Ordering and scope guardrails

- Phase 3 blocks claims and features that depend on accurate measurements.
- Phase 4 is the product differentiator: player-specific Shot Lab, not a generic pro-match score.
- Phase 5 follows a stable data schema; avoid dashboard-first work.
- Phase 6 models are optional experiments, never assumed deliverables.
- Do not use universal “optimal” angles without context and evidence.
