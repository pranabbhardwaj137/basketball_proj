# Graph Report - basketball_proj  (2026-10-04)

## Corpus Check
- 21 files · ~2,466,239 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: .csv 10, (none) 6, .pt 3)

## Summary
- 329 nodes · 499 edges · 14 communities (10 shown, 4 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8b04f1e0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ball_tracker.py
- main.py
- SimpleJointAnalyzer
- JerkProcessor
- SessionRecorder
- run_model.py
- run.py
- run_simon.py
- Basketball Shot Analyzer
- AI Models in Intelligent Basketball Performance Analysis System
- group_work_division.md
- Basketball Shot Analysis
- rules/graphify.md
- workflows/graphify.md

## God Nodes (most connected - your core abstractions)
1. `SimpleJointAnalyzer` - 23 edges
2. `SessionRecorder` - 14 edges
3. `getVideoStreams()` - 14 edges
4. `Project Context: Intelligent Basketball Performance Analysis System` - 14 edges
5. `Basketball Shot Analyzer` - 14 edges
6. `JerkProcessor` - 12 edges
7. `AI Models in Intelligent Basketball Performance Analysis System` - 12 edges
8. `getVideoStreams()` - 11 edges
9. `BallTracker` - 10 edges
10. `PoseEngine` - 10 edges

## Surprising Connections (you probably didn't know these)
- `Component Status Matrix & Progress Gap` --references--> `compute_all_angles()`  [INFERRED]
  README.md → analyzer.py
- `2. Project Origin & Architecture Lineage` --references--> `SessionRecorder`  [INFERRED]
  README.md → analyzer.py
- `Component Status Matrix & Progress Gap` --references--> `release_angle_deg()`  [INFERRED]
  README.md → ball_geometry.py
- `10. Development Roadmap & Updated Task Status` --references--> `fit_parabola()`  [INFERRED]
  README.md → ball_geometry.py
- `Component Status Matrix & Progress Gap` --references--> `fit_parabola()`  [INFERRED]
  README.md → ball_geometry.py

## Import Cycles
- None detected.

## Communities (14 total, 4 thin omitted)

### Community 0 - "ball_tracker.py"
Cohesion: 0.11
Nodes (15): arc_peak(), ball_under_rim(), box_center(), box_to_point_distance(), fit_parabola(), last_valid_box(), point_distance(), release_angle_deg() (+7 more)

### Community 1 - "main.py"
Cohesion: 0.11
Nodes (10): compute_all_angles(), angle(), pt(), detect_shot_phase(), get_angle(), shooting_side(), draw_pose(), maybe_ball_tracker() (+2 more)

### Community 4 - "SessionRecorder"
Cohesion: 0.06
Nodes (30): SessionRecorder, 10. Development Roadmap & Updated Task Status, 11. Common Errors & Troubleshooting, 12. Guidelines for AI Assistants Working on This Project, 1. Offline Voice Feedback Module (`feedback_voice.py`), 1. What This Project Is, 2. PDF Session Report Generator (`report_generator.py`), 2. Project Origin & Architecture Lineage (+22 more)

### Community 5 - "run_model.py"
Cohesion: 0.06
Nodes (10): main(), midpoint(), main(), SimpleJointAnalyzer, crop_images_in_folder(), calculate_angle(), delete_folder_contents(), generate_video() (+2 more)

### Community 6 - "run.py"
Cohesion: 0.13
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

### Community 10 - "group_work_division.md"
Cohesion: 0.18
Nodes (10): Demo Division — 3 Sections, 4 Members, Everyone understands this — run to demo, Owner: Pranab Bhardwaj, Owner: Puneetgouda Patil, Owners: Pavan R Bhat + Pracheth Kashyap, Section 1 — Core Vision Layer, Section 2 — Analysis Engine, Section 3 — Feedback & Output Layer (+2 more)

### Community 11 - "Basketball Shot Analysis"
Cohesion: 0.20
Nodes (9): Basketball Shot Analysis, Contributors, Dataset / training notes, Features, If `pip install -r requirements.txt` fails, Important: missing model weights, Installation, Prerequisites (+1 more)

## Knowledge Gaps
- **83 isolated node(s):** `graphify`, `Workflow: graphify`, `A Deep Technical Reference for Academic Viva`, `Overview: The Full AI Stack`, `How It Works` (+78 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 161 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SimpleJointAnalyzer` connect `SimpleJointAnalyzer` to `run_model.py`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `SessionRecorder` connect `SessionRecorder` to `main.py`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `SessionRecorder` (e.g. with `10. Development Roadmap & Updated Task Status` and `2. Project Origin & Architecture Lineage`) actually correct?**
  _`SessionRecorder` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify`, `Workflow: graphify`, `A Deep Technical Reference for Academic Viva` to the rest of the system?**
  _83 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ball_tracker.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11428571428571428 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Should `SimpleJointAnalyzer` be split into smaller, more focused modules?**
  _Cohesion score 0.13230769230769232 - nodes in this community are weakly interconnected._