"""
test_shot_lab_flow.py - Comprehensive End-to-End Integration Verification for Phase 4 Personal Shot Lab.

Validates:
 1. Versioned SQLite schema (v2) with shot_style and review_status.
 2. Live outcome tagging simulation (M=Make, X=Miss, U=Unknown) with review status updates.
 3. Post-session review boundary overrides preserving raw machine predictions.
 4. Baseline calculation gating:
    - Shot style strict isolation (jump_shot vs set_shot).
    - Minimum sample gate (N < 5 abstention, N >= 5 computation with +/- s standard deviations).
    - Make-versus-miss contrast sub-gate (requires N >= 5 makes AND N >= 5 misses).
 5. Hierarchical One-Cue Remediation Engine (Tier 1 -> Tier 2 -> Tier 3) triggered by mechanics thresholds.
 6. Observational follow-up practice set evaluation with explicit sample sizes, pre/post means +/- std,
    make fractions (M/N), drill completion status, and no causal language.
 7. Quarantine gating: unreviewed shots quarantined, per-shot explicit approval, and rejection of batch approval.
"""

import os
import unittest
from shot_lab_db import ShotLabDB
from baseline_engine import BaselineEngine
from coach_engine import CoachEngine
import review_shots

class TestShotLabFlow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_shot_lab_integration.db"
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
            except Exception:
                pass
        cls.db = ShotLabDB(cls.db_path)
        cls.baseline_engine = BaselineEngine(cls.db)
        cls.coach_engine = CoachEngine(cls.db)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
            except Exception:
                pass

    def test_01_schema_and_player_registration(self):
        """Verify database initialized with schema version 2 and player registration."""
        self.db.upsert_player("player_curry", "Stephen Curry", height_m=1.88, wingspan_m=1.92)
        with self.db._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM schema_meta WHERE key = 'version'")
            ver_row = c.fetchone()
            self.assertIsNotNone(ver_row)
            self.assertEqual(int(ver_row[0]), 2)

            c.execute("SELECT * FROM players WHERE player_id = 'player_curry'")
            row = c.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["name"], "Stephen Curry")

            # Verify columns shot_style and review_status exist in shots table
            c.execute("PRAGMA table_info(shots)")
            columns = [col["name"] for col in c.fetchall()]
            self.assertIn("shot_style", columns)
            self.assertIn("review_status", columns)

    def test_02_shot_ingestion_and_provenance(self):
        """Verify shots preserve machine boundaries, record styles, and handle review statuses."""
        sess_id = self.db.create_session(
            player_id="player_curry",
            camera_view="side_90",
            shot_type="catch_and_shoot",
            shot_style="jump_shot",
            fps=30.0
        )

        shot_id = self.db.save_shot({
            "session_id": sess_id,
            "player_id": "player_curry",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            "shot_style": "jump_shot",
            "machine_start_frame": 100,
            "machine_dip_frame": 115,
            "machine_set_frame": 130,
            "machine_release_frame": 145,
            "machine_end_frame": 170,
            "outcome": "unknown",
            "outcome_source": "unlabeled",
            "tracking_confidence": "SUFFICIENT",
            "elbow_angle_release_3d": 158.0,
            "elbow_angle_release_2d": 140.0,
            "foreshortening_discrepancy_deg": 18.0,
            "knee_angle_dip_3d": 88.0,
            "sequence_lag_ms": 45.0,
            "torso_sway_deg": 4.5
        })

        # By default unreviewed shots should be quarantined
        shot = self.db.get_shot(shot_id)
        self.assertEqual(shot["review_status"], "quarantined")
        self.assertEqual(shot["shot_style"], "jump_shot")

        # Simulate live hotkey tagging (M=Make -> approved)
        self.db.update_shot_annotation(shot_id, outcome="make", outcome_source="live_hotkey", review_status="approved")
        shot = self.db.get_shot(shot_id)
        self.assertEqual(shot["outcome"], "make")
        self.assertEqual(shot["outcome_source"], "live_hotkey")
        self.assertEqual(shot["review_status"], "approved")
        self.assertEqual(shot["machine_release_frame"], 145)

        # Simulate post-session review boundary correction preserving machine prediction
        self.db.update_shot_annotation(
            shot_id,
            annotated_boundaries={"release_frame": 148},
            review_notes="Shifted release frame to ball separation"
        )
        shot_after_review = self.db.get_shot(shot_id)
        self.assertEqual(shot_after_review["machine_release_frame"], 145)   # IMMUTABLE MACHINE PREDICTION
        self.assertEqual(shot_after_review["annotated_release_frame"], 148) # UPDATED HUMAN ANNOTATION
        self.assertEqual(shot_after_review["review_notes"], "Shifted release frame to ball separation")

    def test_03_baseline_sample_gating_and_isolation(self):
        """Verify shot-style isolation, N < 5 baseline gate, and N >= 5 make/miss sub-gate."""
        sess_id = self.db.create_session(
            player_id="player_klay",
            camera_view="frontal",
            shot_type="catch_and_shoot",
            shot_style="jump_shot",
            fps=30.0
        )

        # Ingest 3 jump shots (N < 5)
        for i in range(3):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "player_klay",
                "camera_view": "frontal",
                "shot_type": "catch_and_shoot",
                "shot_style": "jump_shot",
                "tracking_confidence": "SUFFICIENT",
                "review_status": "approved",
                "outcome": "make",
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 160.0,
                "sequence_lag_ms": 115.0
            })

        # Also ingest 2 set shots to test isolation
        for i in range(2):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "player_klay",
                "camera_view": "frontal",
                "shot_type": "catch_and_shoot",
                "shot_style": "set_shot",
                "tracking_confidence": "SUFFICIENT",
                "review_status": "approved",
                "outcome": "make",
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 150.0,
                "sequence_lag_ms": 50.0
            })

        # Query baseline for jump_shot: only 3 jump shots exist -> INSUFFICIENT_SAMPLE
        res_gated = self.baseline_engine.compute_baseline("player_klay", "frontal", "catch_and_shoot", shot_style="jump_shot")
        self.assertEqual(res_gated["status"], "INSUFFICIENT_SAMPLE")
        self.assertEqual(res_gated["sample_size"], 3)
        self.assertIn("Baseline Pending", res_gated["message"])

        # Ingest 4 more jump shots (3 misses, 1 make -> total jump_shot N = 7 >= 5)
        # Sequence lag is severe (> 110 ms)
        for i in range(3):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "player_klay",
                "camera_view": "frontal",
                "shot_type": "catch_and_shoot",
                "shot_style": "jump_shot",
                "tracking_confidence": "SUFFICIENT",
                "review_status": "approved",
                "outcome": "miss",
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 145.0,
                "sequence_lag_ms": 125.0 + (i * 10),
                "torso_sway_deg": 11.0
            })
        self.db.save_shot({
            "session_id": sess_id,
            "player_id": "player_klay",
            "camera_view": "frontal",
            "shot_type": "catch_and_shoot",
            "shot_style": "jump_shot",
            "tracking_confidence": "SUFFICIENT",
            "review_status": "approved",
            "outcome": "make",
            "outcome_source": "live_hotkey",
            "elbow_angle_release_3d": 162.0,
            "sequence_lag_ms": 110.0,
            "torso_sway_deg": 5.0
        })

        # Now N = 7 jump shots: valid baseline, but 4 makes and 3 misses (make/miss contrast pending!)
        res_valid = self.baseline_engine.compute_baseline("player_klay", "frontal", "catch_and_shoot", shot_style="jump_shot")
        self.assertEqual(res_valid["status"], "VALID_BASELINE")
        self.assertEqual(res_valid["sample_size_total"], 7)
        self.assertEqual(res_valid["sample_size_makes"], 4)
        self.assertEqual(res_valid["sample_size_misses"], 3)
        report_str = "\n".join(res_valid["descriptive_associations"])
        self.assertIn("Make-versus-miss contrast pending", report_str)
        self.assertIn("requires at least 5 reviewed makes and 5 reviewed misses", report_str)

        # Ingest 2 more makes and 2 more misses to reach >= 5 makes and >= 5 misses (total 11 shots)
        for i in range(2):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "player_klay",
                "camera_view": "frontal",
                "shot_type": "catch_and_shoot",
                "shot_style": "jump_shot",
                "tracking_confidence": "SUFFICIENT",
                "review_status": "approved",
                "outcome": "make",
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 160.0,
                "sequence_lag_ms": 105.0,
                "torso_sway_deg": 6.0
            })
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "player_klay",
                "camera_view": "frontal",
                "shot_type": "catch_and_shoot",
                "shot_style": "jump_shot",
                "tracking_confidence": "SUFFICIENT",
                "review_status": "approved",
                "outcome": "miss",
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 142.0,
                "sequence_lag_ms": 135.0,
                "torso_sway_deg": 12.0
            })

        res_contrast = self.baseline_engine.compute_baseline("player_klay", "frontal", "catch_and_shoot", shot_style="jump_shot")
        self.assertEqual(res_contrast["sample_size_total"], 11)
        self.assertEqual(res_contrast["sample_size_makes"], 6)
        self.assertEqual(res_contrast["sample_size_misses"], 5)
        contrast_str = "\n".join(res_contrast["descriptive_associations"])
        self.assertIn("associated with", contrast_str)
        self.assertIn("quantization uncertainty", contrast_str)
        self.assertNotIn("caused by", contrast_str.lower())

    def test_04_one_cue_remediation_hierarchy(self):
        """Verify Tier 1 flaw triggers from repeating mechanics thresholds and matches shot style."""
        baseline = self.baseline_engine.compute_baseline("player_klay", "frontal", "catch_and_shoot", shot_style="jump_shot")
        cue = self.coach_engine.generate_primary_cue(baseline)

        # Baseline sequencing lag exceeds jump_shot 100ms threshold -> Tier 1 triggers
        self.assertEqual(cue["priority_tier"], 1)
        self.assertEqual(cue["targeted_flaw"], "Kinetic Sequencing Delay")
        self.assertEqual(cue["recommended_drill"], "One-Motion Dip-to-Rise Wall/Rim Jumps")
        self.assertIn("remediation_id", cue)
        self.assertEqual(cue["status"], "active")
        self.assertIn("uncertainty: +/- 33.3 ms", cue["biomechanical_evidence"])

    def test_05_follow_up_practice_set_evaluation(self):
        """Verify observational follow-up reporting with sample sizes, +/- s, make counts, and drill status."""
        active_rem = self.db.get_active_remediation("player_klay")
        self.assertIsNotNone(active_rem)
        rem_id = active_rem["remediation_id"]

        # Simulate follow-up set of 4 shots with improved kinetic sequencing (avg 48 ms) and 3 makes
        follow_up_shots = [
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 45.0, "outcome": "make"},
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 50.0, "outcome": "make"},
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 48.0, "outcome": "miss"},
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 49.0, "outcome": "make"}
        ]

        result = self.coach_engine.evaluate_follow_up_set(
            player_id="player_klay",
            remediation_id=rem_id,
            follow_up_shots=follow_up_shots,
            feedback_notes="Energy transfer felt synchronized directly from floor contact."
        )

        self.assertEqual(result["status"], "EVALUATION_COMPLETE")
        self.assertEqual(result["trend"], "IMPROVED")
        self.assertLess(result["delta"], -40.0)
        self.assertTrue(result["drill_completed"])
        self.assertEqual(result["sample_size_pre"], 11)
        self.assertEqual(result["sample_size_post"], 4)
        self.assertIsNotNone(result["post_drill_mean"])
        self.assertIsNotNone(result["post_drill_std"])

        # Check observational report string for fractions and strictly non-causal language
        report = result["observational_report"]
        self.assertIn("Observed post-drill session", report)
        self.assertIn("3/4 (75.0%)", report)
        self.assertNotIn("cause", report.lower())
        self.assertNotIn("fixed", report.lower())

        # Active remediation should now be closed/completed
        self.assertIsNone(self.db.get_active_remediation("player_klay"))

    def test_06_quarantine_admission_and_batch_approve_rejection(self):
        """Verify unreviewed quarantine, per-shot CLI approval, and rejection of batch approve."""
        sess_id = self.db.create_session(
            player_id="player_quarantine",
            camera_view="frontal",
            shot_type="catch_and_shoot",
            shot_style="jump_shot",
            fps=30.0
        )
        shot_id = self.db.save_shot({
            "session_id": sess_id,
            "player_id": "player_quarantine",
            "camera_view": "frontal",
            "shot_type": "catch_and_shoot",
            "tracking_confidence": "SUFFICIENT",
            "elbow_angle_release_3d": 155.0,
            "sequence_lag_ms": 60.0
        })

        # 1. Shot starts as quarantined
        shot = self.db.get_shot(shot_id)
        self.assertEqual(shot["review_status"], "quarantined")

        # 2. Baseline excludes quarantined shots when require_human_confirmed=True
        bl = self.baseline_engine.compute_baseline("player_quarantine", "frontal", "catch_and_shoot", require_human_confirmed=True)
        self.assertEqual(bl["sample_size"], 0)

        # 3. Test that review_shots rejects batch approval with exit code 1
        with self.assertRaises(SystemExit) as cm:
            review_shots.main(["--batch-approve", "--db", self.db_path])
        self.assertEqual(cm.exception.code, 1)

        # 4. Explicit per-shot approval via review_shots CLI
        review_shots.main(["--approve", shot_id, "--db", self.db_path, "--notes", "Verified clean mechanics"])
        shot_approved = self.db.get_shot(shot_id)
        self.assertEqual(shot_approved["review_status"], "approved")
        self.assertEqual(shot_approved["outcome_source"], "manual_review")
        self.assertIn("Verified clean mechanics", shot_approved["review_notes"])

        # 5. Discarding a shot marks it discarded
        review_shots.main(["--discard", shot_id, "--db", self.db_path, "--notes", "Flawed release point"])
        shot_discarded = self.db.get_shot(shot_id)
        self.assertEqual(shot_discarded["review_status"], "discarded")

        # Discarded shot remains excluded from baseline
        bl_after_discard = self.baseline_engine.compute_baseline("player_quarantine", "frontal", "catch_and_shoot", require_human_confirmed=True)
        self.assertEqual(bl_after_discard["sample_size"], 0)


if __name__ == "__main__":
    print("\n=================================================================")
    print("   PERSONAL SHOT LAB - END-TO-END INTEGRATION TEST SUITE")
    print("=================================================================\n")
    unittest.main()
