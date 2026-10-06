# Basketball Coach — Project Definition

## Product vision

Build an accessible, local-first basketball shooting practice tool that helps a player understand their own repeatable mechanics and review how those mechanics relate to shot outcomes. It should show the evidence behind each observation, disclose uncertainty, and abstain when video quality is insufficient.

This is a coaching and learning prototype. It is not laboratory motion capture, a medical assessment, or proof that one canonical shooting form is correct.

## Current product

Python desktop application processes a webcam or video file. Current modules provide MediaPipe pose tracking, angle and shot-phase analysis, CSV session recording, optional YOLO ball tracking, optional MediaPipe hand metrics, and illustrative pro-profile/DTW comparisons. A synthetic evaluation harness exercises selected logic.

The implementation is ahead of older README status tables in some areas and behind the planning status claims in others. In particular, the project has not yet established real-video accuracy, calibrated confidence, validated biomechanical angles, or a tested makes-versus-misses coaching effect. Treat current measurements and scores as experimental until Phase 3 exits.

## Differentiation

The project competes in a crowded category of camera-based shot analysis. Feature checklists alone are not a defensible contribution. The intended distinction is a transparent **Shot Lab**:

1. Detect and show representative shots with source frames.
2. Separate made and missed attempts when outcome evidence is available.
3. Compare a player's mechanics with their own baseline before showing optional illustrative references.
4. Offer one evidence-linked adjustment or drill at a time.
5. Compare a controlled follow-up set and report what changed, uncertainty, and sample size.

The tool must describe associations as associations. It must not claim that a measured movement caused a make or miss without a suitable study.

## Product principles

- **Evidence before advice:** every cue points to a measured event, frame, and confidence state.
- **Abstain safely:** missing, occluded, or out-of-view landmarks produce “can't assess,” not fabricated values.
- **Separate coordinate systems:** image-plane measurements and model-inferred 3D estimates are separately named and validated.
- **Personal baseline first:** pro profiles are optional illustrations, never normative ground truth.
- **Offline by default:** process videos locally; make persistence and export explicit.
- **Measure product quality:** report real annotated-video results and failure cases. Synthetic fixtures are regression checks only.
- **Build vertical slices:** complete one player workflow end-to-end before adding broad UI or model complexity.

## Technical scope

### Current / prototype

- Webcam and prerecorded video input through OpenCV.
- MediaPipe Tasks pose inference and 2D landmark display.
- Angle, phase, kinetic-sequence, hand, and ball analysis modules.
- Session CSV output and OpenCV HUD.
- Optional YOLO and hand modules.

### Planned

- Real-video evaluation set with annotation protocol and reproducible metrics.
- Explicit confidence and camera-quality gate.
- Reliable session schema and player-specific longitudinal summaries.
- Shot Lab review flow with outcome labels and evidence-linked cues.
- Reports and optional dashboard after the data contract stabilizes.
- Optional multi-view capture experiment if resources permit; single-view 3D remains an estimate.
- Learned sequence models only if labeled data exists and they beat simpler baselines on held-out players.

## Non-goals

- Claiming sub-millimeter or lab-grade accuracy from a single phone camera.
- Presenting hand-authored pro curves as measured NBA motion-capture data.
- Publishing a similarity percentage as a validated measure of shot quality.
- Training an LSTM/Transformer without an adequately labeled dataset and baseline comparison.
- Building a large web platform before core measurements and session data are dependable.

## Success definition

The project is review-ready when another person can install it, run the core workflow, understand required/optional model assets, inspect a session, reproduce evaluation results, and see honest limits. Scientific claims must be supported by a documented dataset, methods, metrics, and failure analysis.
