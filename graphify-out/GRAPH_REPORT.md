# Graph Report - basketball_proj  (2026-10-08)

## Corpus Check
- 57 files · ~54,398 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: .csv 6, (none) 1, .task 1)

## Summary
- 662 nodes · 970 edges · 67 communities (32 shown, 35 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 42 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a6b6298c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ball_tracker.py
- Project Context: Intelligent Basketball Performance Analysis System
- Real-Video Dataset Collection & Annotation Protocol
- Phase 3 Work Plan — EPFL SportCenter Camera Pose & Court Geometry Evaluation
- AI Models in Intelligent Basketball Performance Analysis System
- Work Division & Project Execution Plan
- shot_lab_db.py
- rules/graphify.md
- workflows/graphify.md
- HandEngine
- ProComparator
- Project Roadmap — Basketball Coach
- Basketball Coach — Project Definition
- Product requirements
- Milestone Summary — v1.0: Reliable, Evidence-Backed Personal Shot Analysis
- TestShotLabFlow
- TestBaselineEngine
- TestCoachEngine
- Key Deliverables & Architecture Implemented
- run_all_public_dataset_evaluations
- Basketball Biomechanics Metric Dictionary
- 2. Work Breakdown & Task Sequence
- Project Positioning and Technical Notes
- Phase 1 — Core Capture and Vision
- Phase 2 — Shot Analysis Foundations
- Phase 5 — Session History, Reports, and Coach Experience
- Phase 6 — Advanced Research and Review Release
- SessionRecorder
- ShotLabDB
- PoseEngine
- .compute_baseline
- KineticChainAnalyzer
- Phase 3 Mid-Phase Plan — Dataset-Based Testing
- CoachEngine
- 2. Locked Architecture & Implementation Decisions
- review_shots.py
- TestShotLabDB
- Real-World & Public Dataset Manifest for Basketball Shot Analysis
- download_models.py
- 2. Locked Architecture & Implementation Decisions
- ShotPhaseDetector
- Phase 3 — Ball Tracking Integration & Validation Plan
- Agent Rules
- 03-PLAN.md
- Work order
- .end_shot
- Phase 3 — Measurement Integrity & Real-Video Validation: Context & Locked Decisions

## God Nodes (most connected - your core abstractions)
1. `ShotLabDB` - 43 edges
2. `ShotPhaseDetector` - 27 edges
3. `SessionRecorder` - 23 edges
4. `PoseEngine` - 22 edges
5. `compute_all_angles()` - 19 edges
6. `BallTracker` - 18 edges
7. `BaselineEngine` - 16 edges
8. `CoachEngine` - 16 edges
9. `ProComparator` - 16 edges
10. `Project Context: Intelligent Basketball Performance Analysis System` - 13 edges

## Surprising Connections (you probably didn't know these)
- `2.1 Configurable Wrist-Height & Vertical Velocity Gates` --references--> `ShotPhaseDetector`  [INFERRED]
  .planning/phases/03-measurement-validation/03-CONTEXT.md → analyzer.py
- `3. Scope Fences & Execution Order` --references--> `ShotPhaseDetector`  [INFERRED]
  .planning/phases/03-measurement-validation/03-CONTEXT.md → analyzer.py
- `Task 4 — Real-video annotation coverage and configurable shot-event gating` --references--> `ShotPhaseDetector`  [INFERRED]
  .planning/phases/03-measurement-validation/03-PLAN.md → analyzer.py
- `Task 6 — Ball trajectory synchronization & honest degradation` --references--> `ShotPhaseDetector`  [INFERRED]
  .planning/phases/03-measurement-validation/03-PLAN.md → analyzer.py
- `1. Coordinate and metric audit` --references--> `PoseEngine`  [INFERRED]
  .planning/PLAN.md → pose_engine.py

## Import Cycles
- None detected.

## Communities (67 total, 35 thin omitted)

### Community 0 - "ball_tracker.py"
Cohesion: 0.06
Nodes (24): arc_peak(), ball_under_rim(), box_center(), box_to_point_distance(), calculate_entry_angle(), fit_parabola(), last_valid_box(), point_distance() (+16 more)

### Community 4 - "Project Context: Intelligent Basketball Performance Analysis System"
Cohesion: 0.07
Nodes (28): Completed Audit Fixes in Phase 3, Completed Work in Phase 4 (Personal Shot Lab), Current validation priorities, Project State, 10. Common Errors & Troubleshooting, 11. Codebase Knowledge Graph & Maintenance (Graphify), 1. What This Project Is, 2. Project Origin & Architecture Lineage (+20 more)

### Community 5 - "Real-Video Dataset Collection & Annotation Protocol"
Cohesion: 0.40
Nodes (4): 1. Video Recording Setup Guidelines, 2. Ground-Truth Annotation Schema (`annotations.json`), 3. Evaluation Metrics & Error Quantification, Real-Video Dataset Collection & Annotation Protocol

### Community 8 - "Phase 3 Work Plan — EPFL SportCenter Camera Pose & Court Geometry Evaluation"
Cohesion: 0.20
Nodes (9): 1. Context & Dataset Qualification Audit, 2.1 Court Grid Projection & FOV Coverage, 2.2 Planar Homography vs. Distorted Camera Projection Reprojection Check, 2. Mathematical Definition of Supported Checks, 3. Implementation Tasks, 4. Acceptance Criteria, Phase 3 Work Plan — EPFL SportCenter Camera Pose & Court Geometry Evaluation, Task 1: Real Dataset Loader & Evaluator (`evaluate_public_datasets.py`) (+1 more)

### Community 9 - "AI Models in Intelligent Basketball Performance Analysis System"
Cohesion: 0.07
Nodes (28): 1. YOLOv8-Pose (Best Alternative for Pose), 2. ViTPose (Most Accurate Pose Model Available), 3. Ball Detection: YOLOv8 Object Detection, 4. Action Recognition: SlowFast / VideoSwin Transformer, 5. Shooting Feedback with LSTM (Custom Temporal Model), 6. MediaPipe Hands (Wrist/Finger Tracking), 7. Pose3D: Lifting 2D to 3D (VideoPose3D), A Deep Technical Reference for Academic Viva (+20 more)

### Community 10 - "Work Division & Project Execution Plan"
Cohesion: 0.11
Nodes (17): 1. `analyzer.py` (Kinematics & State Machine), 1. `pose_engine.py` & `ball_tracker.py` (Refactoring & Decoupling), 1. `report_generator.py` (Automated PDF Report Exporter), 1. Team Allocation & Stream Overview, 2. `dashboard/app.py` (Streamlit Web Dashboard), 2. `feedback_voice.py` (Offline Voice Feedback Engine), 2. `hand_engine.py` (MediaPipe Hands Integration), 2. Technical Specifications by Stream (+9 more)

### Community 15 - "ProComparator"
Cohesion: 0.14
Nodes (3): compute_dtw_distance(), ProComparator, analyze_video()

### Community 16 - "Project Roadmap — Basketball Coach"
Cohesion: 0.18
Nodes (10): Milestone, Ordering and scope guardrails, Phase 1 — Capture and core vision, Phase 2 — Shot analysis foundations, Phase 4 — Personal Shot Lab and evidence-gated coaching, Phase 5 — Durable sessions, reports, and coach experience (deferred), Phase 6 — Advanced research and review release, Phase sequence (+2 more)

### Community 17 - "Basketball Coach — Project Definition"
Cohesion: 0.18
Nodes (10): Basketball Coach — Project Definition, Current product, Current / prototype, Differentiation, Non-goals, Planned, Product principles, Product vision (+2 more)

### Community 18 - "Product requirements"
Cohesion: 0.15
Nodes (12): Non-functional requirements, PR-1 — Capture and setup, PR-2 — Pose and measurement integrity, PR-3 — Shot events and biomechanics, PR-4 — Ball and outcome analysis, PR-5 — Coaching and personalization, PR-6 — Session and Shot Lab, PR-7 — Evaluation (+4 more)

### Community 19 - "Milestone Summary — v1.0: Reliable, Evidence-Backed Personal Shot Analysis"
Cohesion: 0.06
Nodes (36): pt_3d(), Deliverables, Goal, Out of scope, Phase 3 — Measurement Integrity and Real-Video Validation, Plan, Risks and mitigations, Task 1 — Trace coordinate systems and define metrics (+28 more)

### Community 24 - "Key Deliverables & Architecture Implemented"
Cohesion: 0.18
Nodes (10): 1. SQLite Persistence & Versioned Schema (`shot_lab_db.py`), 2. Live Outcome Tagging & Boundary Ingestion (`main.py`), 3. Post-Session Review Queue & Quarantine Protection (`review_shots.py`), 4. Personal Baseline Engine (`baseline_engine.py`), 5. Hierarchical One-Cue Remediation Engine (`coach_engine.py`), Key Deliverables & Architecture Implemented, Milestone Status: COMPLETE, Operational CLI Commands (+2 more)

### Community 26 - "run_all_public_dataset_evaluations"
Cohesion: 0.25
Nodes (5): evaluate_epfl_camerapose_dataset(), evaluate_shot_dataset_qualification(), evaluate_spl_biomechanics_compatibility(), load_json_permissive(), run_all_public_dataset_evaluations()

### Community 27 - "Basketball Biomechanics Metric Dictionary"
Cohesion: 0.15
Nodes (12): 1. Landmark Index Reference (MediaPipe BlazePose 33 Keypoints), 2. Joint Angle Definitions & Formulas, 3. Kinetic Chain Sequencing & Angular Velocities, 4. Missing Data & Temporal Interpolation, 5. Personal Shot Lab Statistical Semantics & Notation, Basketball Biomechanics Metric Dictionary, Continuous Metric Distribution ($\bar{x} \pm s$), Direction-Aware Velocity Definitions ($d\theta/dt$) (+4 more)

### Community 28 - "2. Work Breakdown & Task Sequence"
Cohesion: 0.18
Nodes (10): 1. Executive Summary & Architecture Principles, 2. Work Breakdown & Task Sequence, 3. Acceptance Criteria, Phase 4 — Personal Shot Lab & Evidence-Gated Coaching, Task 1: SQLite Persistence & Provenance Schema (`shot_lab_db.py`), Task 2: Live In-Session Outcome Hotkeys & HUD Overlay (`main.py`), Task 3: Post-Session Shot Review & Explicit Per-Shot Admission Tool (`review_shots.py`), Task 4: Personal Baseline & Descriptive Association Engine (`baseline_engine.py`) (+2 more)

### Community 29 - "Project Positioning and Technical Notes"
Cohesion: 0.29
Nodes (6): Claims and evidence boundaries, Current assessment, Product landscape, Project Positioning and Technical Notes, Recommended differentiation and next work, Reference reading

### Community 30 - "Phase 1 — Core Capture and Vision"
Cohesion: 0.33
Nodes (5): Closeout evidence to preserve, Deferred, Delivered scope, Objective, Phase 1 — Core Capture and Vision

### Community 31 - "Phase 2 — Shot Analysis Foundations"
Cohesion: 0.33
Nodes (5): Closeout evidence to preserve, Deferred, Delivered scope, Objective, Phase 2 — Shot Analysis Foundations

### Community 32 - "Phase 5 — Session History, Reports, and Coach Experience"
Cohesion: 0.33
Nodes (5): Acceptance, Goal, Out of scope, Phase 5 — Session History, Reports, and Coach Experience, Tasks

### Community 33 - "Phase 6 — Advanced Research and Review Release"
Cohesion: 0.33
Nodes (5): Acceptance, Candidate experiments (select by available evidence), Goal, Phase 6 — Advanced Research and Review Release, Release tasks

### Community 36 - "PoseEngine"
Cohesion: 0.12
Nodes (4): PoseEngine, classify_clip_metadata(), run_raw_clips_suite(), test_single_clip()

### Community 39 - "KineticChainAnalyzer"
Cohesion: 0.13
Nodes (3): interpolate_kinematic_series(), KineticChainAnalyzer, BenchmarkEvaluator

### Community 40 - "Phase 3 Mid-Phase Plan — Dataset-Based Testing"
Cohesion: 0.20
Nodes (10): Dataset roles, Goal, Phase 3 Mid-Phase Plan — Dataset-Based Testing, Recommended execution order, References checked, Task 1 — Inspect and qualify candidate data, Task 2 — Public camera-pose & kinematics checks, Task 3 — Target-workflow shooting pilot (+2 more)

### Community 42 - "2. Locked Architecture & Implementation Decisions"
Cohesion: 0.17
Nodes (11): 1. Phase Objective, 2.1 Shot Outcome Labeling, Quarantine & Review Queue (Explicit Per-Shot Review), 2.2 Cue Prioritization & Remediation Engine (Mechanics-Based Gating), 2.3 Shot-Style Differentiation (`jump_shot` vs `set_shot`), 2.4 Follow-Up Comparison Architecture (Observational, No Combined Score), 2.5 Persistence & Storage Engine (`shot_lab.db`), 2.6 Evidence Framing & Ground Truth Boundaries, 2. Locked Architecture & Implementation Decisions (+3 more)

### Community 43 - "review_shots.py"
Cohesion: 0.33
Nodes (4): interactive_review_loop(), main(), print_shot_detail(), print_shot_table()

### Community 46 - "Real-World & Public Dataset Manifest for Basketball Shot Analysis"
Cohesion: 0.29
Nodes (6): 1. Candidate Dataset Qualification Matrix, 2.1 EPFL SportCenter Camera-Pose Schema (`clones/sportcenter_camerapose_dataset`), 2. Dataset Schemas & Label Availabilities, 3. Project Single-Player Pilot Clips Manifest, 4. Evaluation Separation Guarantees, Real-World & Public Dataset Manifest for Basketball Shot Analysis

### Community 48 - "2. Locked Architecture & Implementation Decisions"
Cohesion: 0.33
Nodes (6): 2.1 Configurable Wrist-Height & Vertical Velocity Gates, 2.2 Kinetic Dip-to-Rise Ordering & Plausible Phase Durations, 2.3 Ball Tracking Coordination, Synchronization & Honest Degradation, 2.4 Strict Human-Gated Baseline Inclusion, 2.5 Full-Length Video Evaluation & Subgroup Metrics, 2. Locked Architecture & Implementation Decisions

### Community 49 - "ShotPhaseDetector"
Cohesion: 0.16
Nodes (14): compute_all_angles(), calc_2d(), calc_3d(), pt_2d(), get_angle_3d(), shooting_side(), ShotPhaseDetector, evaluate_video_file() (+6 more)

### Community 50 - "Phase 3 — Ball Tracking Integration & Validation Plan"
Cohesion: 0.33
Nodes (6): 1. Executive Summary & Current State Audit, 2.2 Explicit Status & Missing-Data Schema, 2. Core Architecture: "Hand-in-Hand" Timeline Synchronization, 4. Acceptance Criteria, Current Reality Check, Phase 3 — Ball Tracking Integration & Validation Plan

### Community 63 - "03-PLAN.md"
Cohesion: 0.33
Nodes (3): Active Execution Plan — Phase 3, Follow-on, Verification policy

### Community 64 - "Work order"
Cohesion: 0.33
Nodes (6): 1. Coordinate and metric audit, 2. Confidence and missing-data behavior, 3. Benchmark correctness, 4. Ball and trajectory reliability, 5. Review release, Work order

### Community 66 - "Phase 3 — Measurement Integrity & Real-Video Validation: Context & Locked Decisions"
Cohesion: 0.40
Nodes (3): 1. Phase Objective, 3. Scope Fences & Execution Order, Phase 3 — Measurement Integrity & Real-Video Validation: Context & Locked Decisions

## Knowledge Gaps
- **193 isolated node(s):** `graphify`, `Workflow: graphify`, `2. Confidence and missing-data behavior`, `3. Benchmark correctness`, `4. Ball and trajectory reliability` (+188 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 381 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ShotLabDB` connect `ShotLabDB` to `ball_tracker.py`, `._get_connection`, `CoachEngine`, `shot_lab_db.py`, `review_shots.py`, `TestShotLabDB`, `ShotPhaseDetector`, `Phase 3 — Ball Tracking Integration & Validation Plan`, `TestShotLabFlow`, `TestBaselineEngine`, `TestCoachEngine`?**
  _High betweenness centrality (0.177) - this node is a cross-community bridge._
- **Why does `ShotPhaseDetector` connect `ShotPhaseDetector` to `ball_tracker.py`, `analyzer.py`, `.end_shot`, `Phase 3 — Measurement Integrity & Real-Video Validation: Context & Locked Decisions`, `PoseEngine`, `KineticChainAnalyzer`, `._is_wrist_elevated`, `ProComparator`, `2. Locked Architecture & Implementation Decisions`, `Milestone Summary — v1.0: Reliable, Evidence-Backed Personal Shot Analysis`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `SessionRecorder` connect `SessionRecorder` to `ball_tracker.py`, `.end_shot`, `analyzer.py`, `Project Context: Intelligent Basketball Performance Analysis System`, `PoseEngine`, `KineticChainAnalyzer`, `ProComparator`, `ShotPhaseDetector`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `ShotLabDB` (e.g. with `BaselineEngine` and `CoachEngine`) actually correct?**
  _`ShotLabDB` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `ShotPhaseDetector` (e.g. with `BenchmarkEvaluator` and `2.1 Master Authority: Pose Owns the Shot Lifecycle`) actually correct?**
  _`ShotPhaseDetector` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `SessionRecorder` (e.g. with `BenchmarkEvaluator` and `2. Project Origin & Architecture Lineage`) actually correct?**
  _`SessionRecorder` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify`, `Workflow: graphify`, `2. Confidence and missing-data behavior` to the rest of the system?**
  _193 weakly-connected nodes found - possible documentation gaps or missing edges._