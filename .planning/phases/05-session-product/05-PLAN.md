# Phase 5 — Session History, Reports, and Coach Experience

**Status:** Planned; depends on Phase 4 data contract and Phase 3 validated fields.

## Goal

Make verified session insights durable, shareable with consent, and easy to inspect.

## Tasks

1. Finalize versioned SQLite schema and migration/export strategy; keep source video optional and local by default.
2. Store metric validity, confidence, event timestamps, input metadata, model/config versions, outcome provenance, and annotation edits.
3. Add a report generator with shot count, valid-data coverage, selected examples, personal trends, and explicit limits.
4. Build review timeline/video scrubber around shot phases, ball path, confidence, and coach notes.
5. Add coach/player workflow: review queue, corrections, assigned drill, and follow-up state.
6. Add backup/delete/export controls and consent-aware sharing if sharing is implemented.
7. Build dashboard only after report/session contract is stable; support reduced-motion/readable contrast and useful empty states.

## Acceptance

- Restarting app preserves sessions and migrations preserve old data.
- Any chart or claim links back to its shots and denominator.
- Invalid/unknown data remains visible as such.
- A coach can review and correct without losing original automated output.
- Local-first behavior and any sharing boundary are documented.

## Out of scope

Cloud accounts, team SaaS, or dashboards that imply reliability beyond Phase 3 evidence.
