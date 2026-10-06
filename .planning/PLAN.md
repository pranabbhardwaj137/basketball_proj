# Active Execution Plan — Phase 3

**Goal:** produce honest, repeatable evidence about what the current single-camera system can and cannot measure. Core safeguards exist, but coordinate/confidence mismatches and missing annotated real-video evaluation keep Phase 3 active.

**Phase plan:** [03-PLAN.md](phases/03-measurement-validation/03-PLAN.md)

## Work order

### 1. Coordinate and metric audit

- Trace landmark values from `PoseEngine` through angle, temporal, HUD, and CSV code.
- Keep image-plane and world-landmark calculations separate; annotate coordinate basis/units in outputs.
- Fix world-landmark fallback mixing, mismatched confidence badge/gate, and evaluator-versus-production interpolation limits.
- Produce a metric dictionary defining each angle, event, validity rule, and known limitation.

**Done when:** no angle function silently combines incompatible coordinate systems; outputs identify their basis.

### 2. Confidence and missing-data behavior

- Carry visibility/presence and missing-frame information through shot analysis.
- Define short-gap interpolation; invalid longer gaps and low confidence suppress dependent metrics/cues.
- Add camera/framing guidance tied to the reason for insufficient confidence.

**Done when:** unit/regression cases cover occlusion, missing joints, frame gaps, and recovery without false shots or fake values.

### 3. Benchmark correctness

- Keep the five passing synthetic scenarios as regression checks; label their output synthetic and do not infer real-world accuracy.
- Define annotation schema for shot boundary, release frame, visible joints, outcome, view, and optional reference angles.
- Record annotated clips with player-separated holdout where feasible.
- Add real-video evaluation report with metric definitions, sample counts, error breakdowns, and failure examples.

**Done when:** another developer can reproduce the report from documented data and commands; synthetic and real results are distinct.

### 4. Ball and trajectory reliability

- Preserve actual timestamps for detections, especially when `detect_every > 1`.
- Gate trajectory/outcome on enough high-confidence detections and fit quality.
- Return unknown when rim/outcome evidence is unavailable.

**Done when:** tests cover dropped detections, vertical/near-vertical motion, missing rim, and insufficient fit evidence.

### 5. Review release

- Reconcile `.planning`, README, CLI help, and implemented behavior.
- Document required/optional model assets, offline behavior, machine profile, and known limits.
- Capture a short demo plus one failure case and include current evaluation summary.

**Done when:** fresh setup and review checklist pass; no synthetic metric is described as real-world accuracy.

## Verification policy

Run targeted automated checks for behavior changes and the evaluation harness only after the fixture/report defects are corrected. Do not use passing tests alone as scientific validation; Phase 3 also requires annotated real clips and a written protocol.

## Follow-on

Phase 4 review-queue and schema scaffolding may begin while Phase 3 continues. Personalized cues must remain experimental until measurement validity/abstention behavior is stable. Phase 5 reports/dashboard depend on a versioned session schema.
