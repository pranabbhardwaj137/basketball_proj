# Requirements — Basketball Coach

## Status vocabulary

- **Implemented:** code exists; does not imply validated accuracy.
- **Validated:** acceptance method has been run on documented real data and results recorded.
- **Planned:** not yet implemented.

## Product requirements

### PR-1 — Capture and setup

- Accept webcam and prerecorded video input.
- Document supported Python/dependency setup and distinguish required pose model from optional hand/YOLO assets.
- Give actionable framing guidance: whole body visible, stable camera, supported view, adequate lighting, and player centered.

### PR-2 — Pose and measurement integrity

- Preserve source coordinates, visibility/presence, timestamps, and missing-data markers.
- Keep image-plane angles distinct from MediaPipe world-landmark angle estimates; never mix coordinate bases in one angle calculation.
- Mark every per-shot metric with validity and confidence metadata.
- Interpolate only short gaps under a documented rule. Long gaps invalidate affected measurements and may invalidate the shot summary.
- Show “can't assess” when confidence or view quality falls below a validated gate.

### PR-3 — Shot events and biomechanics

- Detect preparation, set point, release, and follow-through as temporal events with timestamps.
- Reject common non-shot gestures without counting them as shots.
- Report event timing and angular observations with their uncertainty and valid-frame count.
- Label kinetic-chain sequencing as an experimental observation until validated against annotated shots.

### PR-4 — Ball and outcome analysis

- Distinguish stock COCO ball detection from custom ball-and-rim detection.
- Account for actual frame timestamps when detections are skipped.
- Provide `unknown` when detections or trajectory fit are insufficient; do not force make/miss classification.
- Save outcome source (detector or human label) and confidence.

### PR-5 — Coaching and personalization

- Each cue must identify supporting metric(s), event/frame, confidence, and suggested next action.
- Give at most one primary cue per shot or drill interval; include cooldown and user dismissal.
- Compare with the player's own baseline before optional illustrative references.
- State that makes/misses associations are observational, not causal.

### PR-6 — Session and Shot Lab

- Store sessions in a versioned schema with player/session IDs, shot-level observations, timestamps, outcomes, model/config versions, and validity metadata.
- Allow correction of shot boundaries and outcomes, preserving original machine output and edit history.
- Provide a review flow for made/missed shots, one hypothesis, one drill, and a follow-up comparison.
- Export session data in a documented, portable format.

### PR-7 — Evaluation

- Keep synthetic tests for deterministic logic regressions.
- Evaluate separately on annotated real clips with a documented protocol, participant/view breakdown, and held-out clips or players.
- Report shot precision/recall/F1, release-time error, angle error where ground truth exists, coverage/abstention rate, and ball/outcome performance when applicable.
- Publish failures and confidence intervals or other uncertainty summaries when sample size permits.
- Do not claim general accuracy based on synthetic fixtures or a tiny convenience sample.

## Non-functional requirements

- **NFR-1 Reproducibility:** document exact commands, dependency versions, model assets, and evaluation data manifest.
- **NFR-2 Privacy:** local processing by default; no upload without an explicit future product decision.
- **NFR-3 Performance:** measure end-to-end FPS and latency on named hardware/resolution; avoid unsupported universal FPS guarantees.
- **NFR-4 Robustness:** handle missing models, unsupported video, bad framing, occlusion, and optional dependency failures with useful messages.
- **NFR-5 Maintainability:** keep vision, analysis, persistence, coaching, and UI boundaries separate.
- **NFR-6 Honest reporting:** every metric has a definition, unit, source, validity rule, and status (prototype or validated).

## Validation gates

- **Gate A — Unit/regression:** synthetic and targeted fixtures cover expected transitions, invalid data, and edge cases.
- **Gate B — Real-video technical validation:** annotation set, repeatable protocol, and measured errors exist.
- **Gate C — Coaching pilot:** players/coaches can understand and act on cues; usability and outcome association are recorded without causal claims.
- **Gate D — Review release:** fresh-environment install, demo, limitations, evaluation report, and project docs agree.
