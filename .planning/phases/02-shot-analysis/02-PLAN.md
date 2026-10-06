# Phase 2 — Shot Analysis Foundations

**Status:** Implemented prototype; outputs are not yet validated broadly.

## Objective

Turn pose/video frames into shot events, joint observations, optional hand/ball signals, and a reviewable session record.

## Delivered scope

- Angle calculations and shooting-side heuristic.
- Shot-phase finite state machine and session summaries.
- Optional hand landmark metrics and YOLO ball/trajectory pipeline.
- DTW comparison against illustrative hand-authored reference curves.
- On-frame feedback and CSV export.

## Closeout evidence to preserve

- Define every output and its coordinate basis, unit, and validity rule.
- Keep synthetic transition fixtures separate from real clip results.
- Label pro curves illustrative; do not report similarity as validated shot quality.
- Document stock COCO versus custom rim weights and make/miss uncertainty.

## Deferred

Generalized accuracy, normative pro biomechanics, causal diagnosis, and predictive shot-quality models are outside this phase.
