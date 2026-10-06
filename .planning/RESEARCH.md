# Project Positioning and Technical Notes

## Current assessment

The project has a promising review-worthy prototype: pose tracking, shot-state/kinematic analysis, illustrative comparisons, confidence checks, and a five-scenario synthetic regression harness are present. It is not yet an evidence-backed coaching system. A “65% complete” figure is not currently derived from weighted acceptance criteria, so avoid presenting it as an objective measure; report phase gates and evidence instead.

The strongest differentiator to pursue is an honest, player-specific practice loop: let the player review/correct shots, compare their own valid makes and misses, offer one evidence-linked cue, then measure the next practice set. Keep sample counts, uncertainty, and “not enough evidence” visible. That is a better project story than claiming a universal best shooting form or lab-grade biomechanics.

## Claims and evidence boundaries

- MediaPipe world landmarks from a single RGB camera are model-inferred estimates, not sensor-measured depth or multi-camera triangulation. Keep image-plane and world-estimate outputs distinct.
- A discrepancy between the two coordinate pipelines is not an accuracy error unless compared with a valid reference measurement. The `scratch_analyze_klay.py` output is exploratory; reported ±22.9° is unverified in a persisted report and must not be described as ground-truth error or measured foreshortening.
- `EVAL_REPORT.json` records 5/5 synthetic scenarios passing. Precision/recall/F1 of 1.0 describe the fixture set only; they are not expected real-world performance.
- Visibility/presence thresholds indicate landmark tracking quality, not calibrated angle accuracy. Calibrate confidence against annotated error before interpreting it probabilistically.
- Make/miss mechanics are observational associations. Do not claim a cue caused improved shooting without a suitable study.
- Hand-authored Curry/Klay/Ray Allen profiles are illustrative references unless their provenance and measurement protocol are documented.

## Product landscape

Earlier project discussion named HomeCourt, SWISH FORCE, LearnHoops, AKI Sports Tech, and Blast Basketball as adjacent products. Treat those descriptions as preliminary market notes, not verified competitive research. Before including a comparison table in a defense or public README, check current vendor feature pages and distinguish vendor claims from independent evidence. Useful comparison dimensions: capture hardware, supported camera views, output metrics, transparency, personalized longitudinal analysis, confidence/abstention, export, and price/accessibility.

## Recommended differentiation and next work

1. Repair coordinate-basis and confidence-display inconsistencies; align production and evaluator interpolation limits.
2. Preserve the Klay clip as a reproducible exploratory example, with source/version, frame timestamps, valid sample counts, and clear estimate-to-estimate labeling.
3. Create a small consented, human-annotated pilot set with player-separated evaluation where feasible. Report timing error, coverage/abstention, and failures by view; report angle error only against a defined reference.
4. Build Shot Lab review and corrections, then a descriptive personal baseline with minimum sample sizes and matched context.
5. Make cues actionable but traceable: one cue, supporting frames/metrics, confidence, a drill, and a follow-up comparison.
6. Add advanced multi-view or learned models only when they beat a clear baseline on held-out data.

## Reference reading

- MediaPipe Pose Landmarker guide: https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
- MediaPipe Pose paper (BlazePose): https://arxiv.org/abs/2006.10204
- OpenCap (markerless biomechanics using video): https://www.opencap.ai/

These references explain the technology context; they do not validate this project's outputs.
