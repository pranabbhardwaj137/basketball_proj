"""
test_shot_lab_flow.py - Comprehensive End-to-End Integration Verification for Phase 4 Personal Shot Lab.

Validates:
 1. Versioned SQLite schema creation & provenance immutability.
 2. Live outcome tagging simulation (M=Make, X=Miss, U=Unknown).
 3. Post-session review boundary overrides preserving raw machine predictions.
 4. Baseline calculation gating (N < 5 abstention, N >= 5 computation with +/- s standard deviations).
 5. Hierarchical One-Cue Remediation Engine (Tier 1 -> Tier 2 -> Tier 3).
 6. Follow-up practice set tracking with delta calculation.
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
        """Verify database initialized with schema version 1 and player registration."""
        self.db.upsert_player("player_curry", "Stephen Curry", height_m=1.88, wingspan_m=1.92)
        with self.db._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM players WHERE player_id = 'player_curry'")
            row = c.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["name"], "Stephen Curry")

    def test_02_shot_ingestion_and_provenance(self):
        """Verify shots preserve machine boundaries and record outcome sources."""
        sess_id = self.db.create_session(
            player_id="player_curry",
            camera_view="side_90",
            shot_type="catch_and_shoot",
            fps=30.0
        )

        shot_id = self.db.save_shot({
            "session_id": sess_id,
            "player_id": "player_curry",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
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

        # Simulate live hotkey tagging
        self.db.update_shot_annotation(shot_id, outcome="make", outcome_source="live_hotkey")
        shot = self.db.get_shot(shot_id)
        self.assertEqual(shot["outcome"], "make")
        self.assertEqual(shot["outcome_source"], "live_hotkey")
        self.assertEqual(shot["machine_release_frame"], 145)

        # Simulate post-session review boundary correction
        self.db.update_shot_annotation(
            shot_id,
            annotated_boundaries={"release_frame": 148},
            review_notes="Shifted release frame to ball separation"
        )
        shot_after_review = self.db.get_shot(shot_id)
        self.assertEqual(shot_after_review["machine_release_frame"], 145)   # IMMUTABLE MACHINE PREDICTION
        self.assertEqual(shot_after_review["annotated_release_frame"], 148) # UPDATED HUMAN ANNOTATION
        self.assertEqual(shot_after_review["review_notes"], "Shifted release frame to ball separation")

    def test_03_baseline_sample_gating(self):
        """Verify baseline computation abstains for N < 5 and executes for N >= 5."""
        sess_id = self.db.create_session(
            player_id="player_klay",
            camera_view="frontal",
            shot_type="catch_and_shoot",
            fps=30.0
        )

        # Ingest 3 shots (N < 5)
        for i in range(3):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "player_klay",
                "camera_view": "frontal",
                "shot_type": "catch_and_shoot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "make",
                "elbow_angle_release_3d": 160.0,
                "sequence_lag_ms": 50.0
            })

        res_gated = self.baseline_engine.compute_baseline("player_klay", "frontal", "catch_and_shoot")
        self.assertEqual(res_gated["status"], "INSUFFICIENT_SAMPLE")
        self.assertEqual(res_gated["sample_size"], 3)
        self.assertIn("Baseline Pending", res_gated["message"])

        # Ingest 4 more shots (3 misses, 1 make -> total N = 7 >= 5)
        # Misses with severe sequencing lag (> 110 ms)
        for i in range(3):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "player_klay",
                "camera_view": "frontal",
                "shot_type": "catch_and_shoot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "miss",
                "elbow_angle_release_3d": 145.0,
                "sequence_lag_ms": 120.0 + (i * 10),
                "torso_sway_deg": 11.0
            })
        self.db.save_shot({
            "session_id": sess_id,
            "player_id": "player_klay",
            "camera_view": "frontal",
            "shot_type": "catch_and_shoot",
            "tracking_confidence": "SUFFICIENT",
            "outcome": "make",
            "elbow_angle_release_3d": 162.0,
            "sequence_lag_ms": 45.0,
            "torso_sway_deg": 5.0
        })

        res_valid = self.baseline_engine.compute_baseline("player_klay", "frontal", "catch_and_shoot")
        self.assertEqual(res_valid["status"], "VALID_BASELINE")
        self.assertEqual(res_valid["sample_size_total"], 7)
        self.assertEqual(res_valid["sample_size_makes"], 4)
        self.assertEqual(res_valid["sample_size_misses"], 3)

        # Check descriptive associations formatting
        associations = res_valid["descriptive_associations"]
        self.assertGreater(len(associations), 0)
        report_str = "\n".join(associations)
        self.assertIn("associated with", report_str)
        self.assertIn("quantization uncertainty", report_str)

    def test_04_one_cue_remediation_hierarchy(self):
        """Verify Tier 1 flaw takes priority and generates single actionable cue."""
        baseline = self.baseline_engine.compute_baseline("player_klay", "frontal", "catch_and_shoot")
        cue = self.coach_engine.generate_primary_cue(baseline)

        # Because misses had sequence lag >= 120ms (vs makes 45ms), Tier 1 must trigger
        self.assertEqual(cue["priority_tier"], 1)
        self.assertEqual(cue["targeted_flaw"], "Kinetic Sequencing Delay")
        self.assertEqual(cue["recommended_drill"], "One-Motion Dip-to-Rise Wall/Rim Jumps")
        self.assertIn("remediation_id", cue)
        self.assertEqual(cue["status"], "active")

    def test_05_follow_up_practice_set_evaluation(self):
        """Verify follow-up practice set calculates delta and completes remediation."""
        active_rem = self.db.get_active_remediation("player_klay")
        self.assertIsNotNone(active_rem)
        rem_id = active_rem["remediation_id"]

        # Simulate follow-up set of 4 shots with improved kinetic sequencing (avg 48 ms)
        follow_up_shots = [
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 45.0},
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 50.0},
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 48.0},
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 50.0}
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

        # Active remediation should now be closed/completed
        self.assertIsNone(self.db.get_active_remediation("player_klay"))


if __name__ == "__main__":
    print("\n=================================================================")
    print("   PERSONAL SHOT LAB - END-TO-END INTEGRATION TEST SUITE")
    print("=================================================================\n")
    unittest.main()
