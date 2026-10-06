# Phase 1 — Core Capture and Vision

**Status:** Implemented prototype; clean-install verification outstanding.

## Objective

Accept webcam/video and return visible, temporally smoothed body landmarks for the active player.

## Delivered scope

- OpenCV frame capture and display.
- MediaPipe Tasks PoseLandmarker integration.
- Landmark smoothing and skeleton rendering.
- Pose model asset and basic setup instructions.

## Closeout evidence to preserve

- Record Python/dependency versions and model file identity/checksum.
- Verify required pose model setup from a clean environment.
- Demonstrate one supported webcam and one video-file path.
- Record limitations: one tracked pose, view/occlusion sensitivity, estimated landmarks.

## Deferred

Multi-person selection, calibrated 3D capture, and platform packaging are not Phase 1 deliverables.
