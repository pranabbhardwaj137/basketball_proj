# Phase 3 — Ball Tracking Integration & Validation Plan

**Document:** `03-BALL-TRACKING-PLAN.md`  
**Status:** Approved Architectural Plan  
**Context:** Coordinated with [03-CONTEXT.md](03-CONTEXT.md) and [03-PLAN.md](03-PLAN.md)  

---

## 1. Executive Summary & Current State Audit

Ball tracking is currently an **optional prototype** that operates on an independent state machine from human pose analysis.

### Current Reality Check
1. **Ball Detection (Stock COCO):** Running `main.py --ball` without custom weights falls back to stock YOLOv8n (COCO class 32: `sports ball`). It can detect a ball in clear frames and compute approximate flight parabolas, but suffers from detection dropouts during high-velocity release blur.
2. **Rim Detection & Outcome Classification:** Rim detection and automated make/miss determination require custom trained weights (`weights/basket_rim.pt`). **This file is currently absent from the project**, and no validation report exists. Stock COCO cannot detect a basketball rim. Automated make/miss claims are impossible and must remain disabled.
3. **Decoupled State Machines:** `ball_tracker.py` maintains its own `release_started` / `tracking_flight` state machine based purely on hand-box pixel distance (`leave_hand_px`). If a ball is dribbled, tossed during warm-ups, or faked, `ball_tracker` registers a flight event that can erroneously bind to an unrelated pose shot minutes later.
4. **Integrity Rule:** Ball-derived metrics must remain strictly **optional and supplementary**. Missing ball/rim evidence must be explicitly tagged `UNKNOWN` / `N/A`. The primary source of truth for shot outcomes remains human review labels (`M`/`X`/`U`).

---

## 2. Core Architecture: "Hand-in-Hand" Timeline Synchronization

### 2.1 Master Authority: Pose Owns the Shot Lifecycle
Instead of two competing state machines, **`ShotPhaseDetector` (Pose) owns the master timeline and shot boundaries**:

```
[Pose Shot Lifecycle: Master]
Frame:   t_dip --------> t_set --------> t_release --------> t_follow_through ------> t_end
Phase:   PREPARING       SET_POINT       RELEASING           FOLLOW_THROUGH           IDLE
Shot ID: ----------------------- SHOT #N --------------------------------------------->

[Ball Tracker: Frame Observer & Feature Attacher]
Window:  |<- Gathers ball in hand ->|    |<- Tracks flight trajectory ->|    |<- Evaluates rim ->|
Status:  ball_hand_proximity (boost)     parabola_fit(t_rel -> t_end)        rim_status: UNAVAILABLE
```

- When the pose detector initiates a shot (`start_shot(shot_id, frame, timestamp)`), the ball tracker is notified of the active `shot_id`.
- During `PREPARING` and `SET_POINT`, the ball tracker measures **ball-hand proximity** to provide an optional confidence boost to the pose detector.
- At `RELEASING`, the ball tracker logs the exact frame and pixel position where the ball detaches from the hand.
- Between `RELEASING` and `IDLE`, the ball tracker accumulates flight centers specifically associated with this `shot_id`.
- At `end_shot()`, the ball tracker packages its observations directly into that specific shot's summary. If no ball was seen during the shot window, the shot records `ball_status="NOT_DETECTED"`—it never steals flight data from an earlier or later event.

### 2.2 Explicit Status & Missing-Data Schema
Every shot record in `ShotLabDB` and CSV export will feature explicit, mutually exclusive statuses:

| Field | Possible Values | Meaning / Guardrail |
| :--- | :--- | :--- |
| `ball_detection_status` | `HIGH_COVERAGE` ($\ge 70\%$ frames),<br>`LOW_COVERAGE` ($< 70\%$),<br>`NOT_DETECTED` | Explicitly distinguishes lost ball tracking from zero ball presence. |
| `rim_detection_status` | `UNAVAILABLE_NO_WEIGHTS`,<br>`NOT_DETECTED`,<br>`CONFIRMED_RIM` | Honestly declares when custom rim weights are absent. |
| `ball_release_angle` | Float degrees or `None` | Calculated only if $\ge 4$ post-release centers fit a valid upward parabola ($R^2 \ge 0.85$). |
| `ball_release_alignment_ms` | Signed Float (ms) or `None` | $t_{\text{ball\_detach}} - t_{\text{pose\_release}}$. Measures synchronization agreement between kinematic flick and ball flight. |
| `outcome` | `make`, `miss`, `unknown` | Governed by human `M`/`X`/`U` label. Automated outcome is locked to `unknown` until rim model is validated. |
| `outcome_source` | `live_hotkey`, `manual_review`, `unlabeled` | Proves outcome provenance; automated source disallowed during prototype phase. |

---

## 3. Implementation Plan: Phased Execution

### Phase 3A — Unified Timeline & State Machine Refactoring (Immediate)
- **Task 3A.1 — Refactor `BallTracker` Interface:**
  - Deprecate autonomous `BallTracker.update(...)` flight triggers.
  - Implement lifecycle methods:
    - `on_shot_started(shot_id, frame_idx, timestamp_ms)`
    - `on_shot_release(shot_id, frame_idx, timestamp_ms, hand_coords)`
    - `on_shot_ended(shot_id, frame_idx, timestamp_ms)` $\to$ returns `BallShotSummary`
  - Ensure flight centers and timestamp lists reset cleanly per shot and cannot leak across shot boundaries.
- **Task 3A.2 — Honest Rim & Outcome Degradation:**
  - Update `load_yolo()`: if custom weights are missing, set `self.rim_supported = False` and permanently emit `rim_status="UNAVAILABLE_NO_WEIGHTS"`.
  - Disable heuristic make/miss guesses when `rim_supported is False`. Return `outcome="unknown"` and `outcome_reason="NO_RIM_WEIGHTS"`.
- **Task 3A.3 — Wire Synchronization into `main.py`:**
  - Update `main.py` main loop: bind `ball_tracker` lifecycle directly to `phase_detector` transitions.
  - Record `ball_release_alignment_ms` and store `ball_detection_status` in `ShotLabDB`.

### Phase 3B — Real-Video Ball Coverage & Alignment Evaluation (Phase 3 Gate)
- **Task 3B.1 — Extend `evaluate_dataset.py` with Ball Evaluation Mode:**
  - Add `--eval-ball` flag to `evaluate_dataset.py`.
  - For clips with visible ball, evaluate:
    1. **Ball Detection Coverage Rate:** Fraction of active shot frames where ball detection confidence $\ge 0.35$.
    2. **Parabolic Fit Quality:** Distribution of $R^2$ fitting scores and trajectory rejection rate.
    3. **Release Alignment Delta:** Mean Absolute Error ($|\Delta t|$) between kinematic wrist release and ball departure.
- **Task 3B.2 — Report Findings in `DATASET_EVAL_REPORT.json`:**
  - Include ball metrics in the official evaluation report, separated from pose metrics.
  - Clearly disclose camera view limitations (e.g., ball occluded by shooter's torso in certain oblique angles).

### Phase 3C — Custom Rim Model & Automated Outcome Qualification (Phase 6 Backlog)
- **Prerequisite:** Train or obtain `weights/basket_rim.pt` on a basketball dataset (e.g. Roboflow basketball hoop dataset).
- **Validation Requirement:**
  - Measure Rim mAP@0.5 on held-out court footage.
  - Annotate 50+ real makes and misses on full-court clips.
  - Measure automated make/miss precision, recall, and false positive rate against human labels before permitting automated outcome entry into baselines.

---

## 4. Acceptance Criteria

1. **Zero Timeline Desynchronization:** Ball flight observations cannot be attributed to a shot that ended before the flight occurred, or started after it.
2. **Honest Missing Data:** Running with stock COCO weights prints a clear console disclosure and sets `rim_status="UNAVAILABLE_NO_WEIGHTS"`. No shot is automatically tagged "made" or "missed".
3. **Pose Independence Maintained:** A dropped ball detection during high-speed motion never interrupts or invalidates an otherwise valid pose shot detection.
4. **Reproducible Evaluation:** `evaluate_dataset.py --eval-ball` executes without crash on real development clips and logs empirical ball detection coverage.
