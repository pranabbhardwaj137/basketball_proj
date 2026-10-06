# Phase 3 Mid-Phase Plan — Dataset-Based Testing

**Status:** Executed & Verified. Reports generated: `DATASET_MANIFEST.md`, `PUBLIC_DATASETS_REPORT.json`, `DATASET_EVAL_REPORT.json`.
Public datasets and user-recorded clips serve distinct test purposes; their scores remain strictly separated.

## Goal

Extend validation beyond synthetic fixtures by testing against real basketball data with known labels, while documenting where public data does not match the product's single-player shooting workflow.

## Dataset roles

| Data source | Use in this project | What it cannot establish | Access / rights notes |
|---|---|---|---|
| [SPL Open Data — basketball free throws](https://github.com/Sport-Performance-Lab/SPL-Open-Data) | Explore downstream kinematic/outcome analysis using released biomechanics trials; compare computed summaries where the trial schema supports it. | Does not test this app's video pose detector if only trial/keypoint data is available; five participants are not broad validation. | Repository reports 583 trials, five participants, CC BY-NC-SA 4.0. Preserve attribution and license constraints. |
| [EPFL SportCenter dataset](https://www.epfl.ch/labs/cvlab/data/sportcenter-dataset/) | Use its multi-view basketball pose subset to check pose/keypoint behavior against manually annotated 2D/triangulated 3D pose references, after confirming exact files/labels and mapping joints. | General game poses do not validate shot phase detection, release events, or coaching cues. Sparse annotated frames cannot support every temporal metric. | Free for research according to dataset page; follow its citation and usage terms. |
| [SHOT basketball dataset](https://huggingface.co/datasets/muyu111/basketball) | Optional exploratory test for player pose and event/context handling across five game camera views, after confirming label alignment and target-player identity. | Group-play keyframes/poses do not establish shooting biomechanics, release-frame accuracy, or shot outcome performance for a solo phone-camera setup. | Dataset annotations list CC BY-NC 4.0; original footage/frames are excluded and have separate rights. Do not use video until rights permit it. |
| Project-recorded, consented single-player clips | Primary end-to-end pilot for target workflow: pose coverage, shot lifecycle/release timing, make/miss/unknown review, camera views, and failure/abstention behavior. | Small convenience samples do not establish population-wide or laboratory-grade accuracy. | Record consent and access restrictions. Do not publish identifiable videos without permission. |

## Work plan

### Task 1 — Inspect and qualify candidate data

- Obtain dataset cards, README/license, sample files, annotation schemas, frame rate, coordinate convention, and participant/split metadata before downloading large corpora.
- Verify that each source contains fields needed for its assigned evaluation task. Record exclusions rather than silently substituting generated labels.
- Create a manifest with source URL/version, license, file IDs, participant IDs where available, labels present, and intended evaluation role.
- Keep each dataset's results in a separate report section. Never aggregate pose, action, and biomechanics labels as if they were interchangeable.

**Acceptance:** manifest and data-use notes identify what can and cannot be scored for each source; no footage is used without a permitted basis.

### Task 2 — Public pose / kinematics checks

- For EPFL annotated pose frames, map available labels to this project's landmark convention; report only joints with valid corresponding ground truth.
- If compatible, calculate keypoint error in pixels/normalized coordinates and PCK at explicitly stated thresholds. For triangulated 3D labels, compare only after aligning coordinate frames and units.
- For SPL trials, first document file schema and coordinate definitions; evaluate downstream kinematic calculations only if raw point trajectories and comparable definitions are provided.
- Use SHOT only for supported pose or event-context experiments; annotate footage license status and do not treat provided pose estimates as ground truth.

**Acceptance:** scripts emit counts, thresholds/units, split IDs, and per-source results; estimates are never relabeled as ground truth.

### Task 3 — Target-workflow shooting pilot

- Record a pilot across multiple people, camera views (side/oblique/front), lighting and framing conditions, and made and missed attempts where practical.
- Have a reviewer label shot start, dip, set point, release, follow-through, outcome, visible/occluded joints, and unusable clips. Double-label a subset and record reviewer agreement.
- Keep all clips from a participant together in either development or held-out evaluation to reduce identity leakage.
- Start with a manageable pilot (for example, 3–5 participants and 10–20 attempts each); label it exploratory, then expand based on uncertainty and failure coverage rather than treating this count as a statistical guarantee.

**Acceptance:** consented clip manifest, annotation instructions, disagreement resolution, and participant-separated split exist.

### Task 4 — Metrics and reporting

- Synthetic regression: pass/fail invariants only; do not call these field accuracy.
- Shot/event detection: precision, recall, F1, per-shot false-positive/false-negative counts, release-frame absolute error in frames and milliseconds, and valid/abstained coverage.
- Pose/keypoint: per-joint pixel or normalized error and PCK only where human labels exist. Report occluded/out-of-frame joints separately.
- Joint angles: report error only against a defined reference angle with documented camera/calibration and annotation uncertainty. 2D-vs-MediaPipe-world disagreement remains a separate descriptive statistic.
- Personal outcome analysis: show sample counts by outcome and view; use descriptive associations, not causal claims.
- Include per-source and per-view failures, sample sizes, and limitations. Keep player-level held-out performance separate from within-player development results.

**Acceptance:** reproducible reports distinguish synthetic, public-data, and project-recorded results and list exact labels supporting each metric.

## Recommended execution order

1. Inspect candidate datasets and licenses; produce the manifest.
2. Prototype EPFL pose mapping first because its manually annotated pose subset directly supports pose checks.
3. Inspect SPL trial schema for downstream kinematics compatibility; use only fields that match documented units/definitions.
4. Exclude SHOT video until third-party footage rights are confirmed; optional annotation-only exploration may proceed if terms allow.
5. Record the consented target-workflow pilot and evaluate with participant-separated splits.
6. Reconcile all results with `EVAL_REPORT.json`, `KLAY_EVAL_REPORT.json`, `ROADMAP.md`, and `STATE.md` without merging incompatible metrics.

## References checked

- SPL Open Data repository: https://github.com/Sport-Performance-Lab/SPL-Open-Data
- EPFL SportCenter dataset page: https://www.epfl.ch/labs/cvlab/data/sportcenter-dataset/
- SHOT dataset card and license notes: https://huggingface.co/datasets/muyu111/basketball

