# Phase 6 — Advanced Research and Review Release

**Status:** Planned; proceed only when Phase 3–5 evidence and data are available.

## Goal

Test advanced ideas against simpler baselines, then ship a reproducible and candid academic release.

## Candidate experiments (select by available evidence)

1. **Two-view capture:** synchronize/calibrate two phones; quantify whether reconstructed joint/ball estimates improve over single-view relative to a defined reference. Record setup friction and failure rate.
2. **Temporal models:** compare rule/state-machine and DTW baselines with an LSTM/Transformer using player-separated holdouts. Keep the learned model only if it improves predefined metrics without harming calibration or robustness.
3. **Personal cue ranking:** learn from coach/player corrections only after sufficient labeled feedback; preserve an interpretable reason for every cue.
4. **Practice design:** test whether a specific cue/drill changes a targeted measure in a controlled pilot; report as exploratory unless adequately powered.

## Release tasks

- Reproducible clean install and run on named hardware.
- Model/dependency/license/attribution inventory.
- Performance and latency measurements by resolution/model option.
- Final evaluation report, data/annotation protocol, known failure cases, and limitations.
- Demo script showing normal use, an abstention case, and a longitudinal Shot Lab example.
- Viva/defense materials with equations, coordinate assumptions, baselines, and negative results.
- Final README, planning state, and Graphify synchronization.

## Acceptance

- Each advanced feature has a preregistered comparison metric and baseline; no feature ships on novelty alone.
- Model outputs and datasets are versioned and reproducible.
- Final claims match the evidence and state clearly what single-view video cannot establish.
- Fresh reviewer can install, reproduce the demo/evaluation, and understand limitations without project authors present.
