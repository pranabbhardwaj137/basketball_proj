# Graph Report - basketball_proj  (2026-10-05)

## Corpus Check
- 44 files · ~2,481,749 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: .csv 9, (none) 6, .pt 3)

## Summary
- 548 nodes · 808 edges · 32 communities (24 shown, 8 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 19 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f05bfaea`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ball_tracker.py
- SessionRecorder
- SimpleJointAnalyzer
- JerkProcessor
- Project Context: Intelligent Basketball Performance Analysis System
- Real-Video Dataset Collection & Annotation Protocol
- run.py
- run_simon.py
- Basketball Shot Analyzer
- AI Models in Intelligent Basketball Performance Analysis System
- Work Division & Project Execution Plan
- Basketball Shot Analysis
- rules/graphify.md
- workflows/graphify.md
- HandEngine
- main.py
- Project Roadmap — Basketball Coach
- Basketball Coach — Project Definition
- Product requirements
- Plan
- SimpleJointAnalyzer
- image_cropper.py
- run_model.py
- Basketball Biomechanics Metric Dictionary
- Phase 4 — Personal Shot Lab
- Project Positioning and Technical Notes
- Phase 1 — Core Capture and Vision
- Phase 2 — Shot Analysis Foundations
- Phase 5 — Session History, Reports, and Coach Experience
- Phase 6 — Advanced Research and Review Release

## God Nodes (most connected - your core abstractions)
1. `SimpleJointAnalyzer` - 23 edges
2. `SessionRecorder` - 21 edges
3. `PoseEngine` - 18 edges
4. `compute_all_angles()` - 16 edges
5. `ProComparator` - 16 edges
6. `ShotPhaseDetector` - 15 edges
7. `Project Context: Intelligent Basketball Performance Analysis System` - 15 edges
8. `getVideoStreams()` - 14 edges
9. `Basketball Shot Analyzer` - 14 edges
10. `box_center()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `1. Coordinate and metric audit` --references--> `PoseEngine`  [INFERRED]
  .planning/PLAN.md → pose_engine.py
- `Completed Audit Fixes in Phase 3` --references--> `interpolate_kinematic_series()`  [INFERRED]
  .planning/STATE.md → analyzer.py
- `Task 1 — Trace coordinate systems and define metrics` --references--> `pt_3d()`  [INFERRED]
  .planning/phases/03-measurement-validation/03-PLAN.md → analyzer.py
- `Completed Audit Fixes in Phase 3` --references--> `pt_3d()`  [INFERRED]
  .planning/STATE.md → analyzer.py
- `4. Missing Data & Temporal Interpolation` --references--> `KineticChainAnalyzer`  [INFERRED]
  METRIC_DICTIONARY.md → analyzer.py

## Import Cycles
- None detected.

## Communities (32 total, 8 thin omitted)

### Community 0 - "ball_tracker.py"
Cohesion: 0.08
Nodes (17): arc_peak(), ball_under_rim(), box_center(), box_to_point_distance(), calculate_entry_angle(), fit_parabola(), last_valid_box(), point_distance() (+9 more)

### Community 1 - "SessionRecorder"
Cohesion: 0.06
Nodes (7): interpolate_kinematic_series(), KineticChainAnalyzer, SessionRecorder, ShotPhaseDetector, BenchmarkEvaluator, evaluate_video_file(), 2. Project Origin & Architecture Lineage

### Community 2 - "SimpleJointAnalyzer"
Cohesion: 0.11
Nodes (3): main(), midpoint(), SimpleJointAnalyzer

### Community 4 - "Project Context: Intelligent Basketball Performance Analysis System"
Cohesion: 0.06
Nodes (31): 10. Development Roadmap & Updated Task Status, 11. Common Errors & Troubleshooting, 12. Guidelines for AI Assistants Working on This Project, 13. Codebase Knowledge Graph & Maintenance (Graphify), 1. Offline Voice Feedback Module (`feedback_voice.py`), 1. What This Project Is, 2. PDF Session Report Generator (`report_generator.py`), 3. Developer & Academic Profile (+23 more)

### Community 5 - "Real-Video Dataset Collection & Annotation Protocol"
Cohesion: 0.40
Nodes (4): 1. Video Recording Setup Guidelines, 2. Ground-Truth Annotation Schema (`annotations.json`), 3. Evaluation Metrics & Error Quantification, Real-Video Dataset Collection & Annotation Protocol

### Community 6 - "run.py"
Cohesion: 0.11
Nodes (18): ball_near_body(), ball_under_basket(), calculate_angle(), delete_folder_contents(), detect_API(), distance(), find_suitable_ball(), get_angles_postions() (+10 more)

### Community 7 - "run_simon.py"
Cohesion: 0.24
Nodes (12): ball_near_body(), ball_under_basket(), calculate_angle(), delete_folder_contents(), detect_API(), distance(), find_suitable_ball(), get_angles_postions() (+4 more)

### Community 8 - "Basketball Shot Analyzer"
Cohesion: 0.06
Nodes (35): 1. Basic Biomechanical Analysis, 2. Pose Detection and Joint Marking, 3. Post-processing Analysis, Analysis Metrics, Analysis Parameters, Analysis Results, Applications, Basketball Shot Analyzer (+27 more)

### Community 9 - "AI Models in Intelligent Basketball Performance Analysis System"
Cohesion: 0.07
Nodes (28): 1. YOLOv8-Pose (Best Alternative for Pose), 2. ViTPose (Most Accurate Pose Model Available), 3. Ball Detection: YOLOv8 Object Detection, 4. Action Recognition: SlowFast / VideoSwin Transformer, 5. Shooting Feedback with LSTM (Custom Temporal Model), 6. MediaPipe Hands (Wrist/Finger Tracking), 7. Pose3D: Lifting 2D to 3D (VideoPose3D), A Deep Technical Reference for Academic Viva (+20 more)

### Community 10 - "Work Division & Project Execution Plan"
Cohesion: 0.11
Nodes (17): 1. `analyzer.py` (Kinematics & State Machine), 1. `pose_engine.py` & `ball_tracker.py` (Refactoring & Decoupling), 1. `report_generator.py` (Automated PDF Report Exporter), 1. Team Allocation & Stream Overview, 2. `dashboard/app.py` (Streamlit Web Dashboard), 2. `feedback_voice.py` (Offline Voice Feedback Engine), 2. `hand_engine.py` (MediaPipe Hands Integration), 2. Technical Specifications by Stream (+9 more)

### Community 11 - "Basketball Shot Analysis"
Cohesion: 0.20
Nodes (9): Basketball Shot Analysis, Contributors, Dataset / training notes, Features, If `pip install -r requirements.txt` fails, Important: missing model weights, Installation, Prerequisites (+1 more)

### Community 15 - "main.py"
Cohesion: 0.06
Nodes (16): compute_all_angles(), calc_2d(), calc_3d(), pt_2d(), get_angle_3d(), shooting_side(), draw_pose(), maybe_ball_tracker() (+8 more)

### Community 16 - "Project Roadmap — Basketball Coach"
Cohesion: 0.17
Nodes (11): Milestone, Ordering and scope guardrails, Phase 1 — Capture and core vision, Phase 2 — Shot analysis foundations, Phase 3 — Measurement integrity and validation (active), Phase 4 — Personal Shot Lab and evidence-gated coaching, Phase 5 — Durable sessions, reports, and coach experience, Phase 6 — Advanced research and review release (+3 more)

### Community 17 - "Basketball Coach — Project Definition"
Cohesion: 0.18
Nodes (10): Basketball Coach — Project Definition, Current product, Current / prototype, Differentiation, Non-goals, Planned, Product principles, Product vision (+2 more)

### Community 18 - "Product requirements"
Cohesion: 0.15
Nodes (12): Non-functional requirements, PR-1 — Capture and setup, PR-2 — Pose and measurement integrity, PR-3 — Shot events and biomechanics, PR-4 — Ball and outcome analysis, PR-5 — Coaching and personalization, PR-6 — Session and Shot Lab, PR-7 — Evaluation (+4 more)

### Community 19 - "Plan"
Cohesion: 0.07
Nodes (26): pt_3d(), Deliverables, Goal, Out of scope, Phase 3 — Measurement Integrity and Real-Video Validation, Plan, Risks and mitigations, Task 1 — Trace coordinate systems and define metrics (+18 more)

### Community 25 - "run_model.py"
Cohesion: 0.22
Nodes (5): calculate_angle(), delete_folder_contents(), generate_video(), get_files(), process_frame_media_pipe()

### Community 27 - "Basketball Biomechanics Metric Dictionary"
Cohesion: 0.22
Nodes (8): 1. Landmark Index Reference (MediaPipe BlazePose 33 Keypoints), 2. Joint Angle Definitions & Formulas, 3. Kinetic Chain Sequencing & Angular Velocities, 4. Missing Data & Temporal Interpolation, Basketball Biomechanics Metric Dictionary, Direction-Aware Velocity Definitions ($d\theta/dt$), Metric Specifications Table, Proximal-to-Distal Sequencing Rule

### Community 28 - "Phase 4 — Personal Shot Lab"
Cohesion: 0.29
Nodes (6): Acceptance, Creative hypothesis, Goal, Out of scope, Phase 4 — Personal Shot Lab, Tasks

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

## Knowledge Gaps
- **169 isolated node(s):** `graphify`, `Workflow: graphify`, `2. Confidence and missing-data behavior`, `3. Benchmark correctness`, `4. Ball and trajectory reliability` (+164 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 302 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SessionRecorder` connect `SessionRecorder` to `ball_tracker.py`, `Project Context: Intelligent Basketball Performance Analysis System`, `main.py`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `Project Context: Intelligent Basketball Performance Analysis System` connect `Project Context: Intelligent Basketball Performance Analysis System` to `SessionRecorder`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `SimpleJointAnalyzer` connect `SimpleJointAnalyzer` to `SessionRecorder`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `SessionRecorder` (e.g. with `BenchmarkEvaluator` and `10. Development Roadmap & Updated Task Status`) actually correct?**
  _`SessionRecorder` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify`, `Workflow: graphify`, `2. Confidence and missing-data behavior` to the rest of the system?**
  _169 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ball_tracker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08048103607770583 - nodes in this community are weakly interconnected._
- **Should `SessionRecorder` be split into smaller, more focused modules?**
  _Cohesion score 0.05583972719522592 - nodes in this community are weakly interconnected._