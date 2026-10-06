"""
test_coach_engine.py - Unit test suite for coach_engine.py
"""

import os
import unittest
from shot_lab_db import ShotLabDB
from baseline_engine import BaselineEngine
from coach_engine import CoachEngine

class TestCoachEngine(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_coach.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = ShotLabDB(self.test_db)
        self.coach = CoachEngine(self.db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except Exception:
                pass

    def test_tier_prioritization_hierarchy(self):
        """Verify Tier 1 (Sequencing) takes precedence over Tier 2 and 3 when both are present."""
        baseline_data = {
            "player_id": "test_player",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            # Tier 1 flaw present:
            "mean_sequence_lag_all": 120.0,
            "mean_sequence_lag_make": 50.0,
            "mean_sequence_lag_miss": 130.0,
            # Tier 2 flaw also present:
            "mean_elbow_release_all": 138.0,
            "mean_elbow_release_make": 155.0,
            "mean_elbow_release_miss": 130.0,
            # Tier 3 flaw also present:
            "mean_torso_sway_all": 15.0
        }

        cue = self.coach.generate_primary_cue(baseline_data)
        self.assertEqual(cue["priority_tier"], 1)
        self.assertEqual(cue["targeted_flaw"], "Kinetic Sequencing Delay")
        self.assertIn("One-Motion", cue["recommended_drill"])

    def test_tier2_when_tier1_clean(self):
        """Verify Tier 2 is selected when Tier 1 is clean."""
        baseline_data = {
            "player_id": "test_player",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            # Tier 1 clean:
            "mean_sequence_lag_all": 60.0,
            "mean_sequence_lag_make": 55.0,
            "mean_sequence_lag_miss": 65.0,
            # Tier 2 flaw present:
            "mean_elbow_release_all": 142.0,
            "mean_elbow_release_make": 156.0,
            "mean_elbow_release_miss": 138.0,
            # Tier 3 clean:
            "mean_torso_sway_all": 5.0
        }

        cue = self.coach.generate_primary_cue(baseline_data)
        self.assertEqual(cue["priority_tier"], 2)
        self.assertEqual(cue["targeted_flaw"], "Incomplete Release Extension")
        self.assertIn("High-Release Form Shooting", cue["recommended_drill"])

    def test_follow_up_set_evaluation(self):
        """Verify follow-up practice set calculates delta and marks remediation complete."""
        baseline_data = {
            "player_id": "test_player",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            "mean_sequence_lag_all": 125.0,
            "mean_sequence_lag_make": 60.0,
            "mean_sequence_lag_miss": 135.0
        }
        cue = self.coach.generate_primary_cue(baseline_data)
        rem_id = cue["remediation_id"]

        # Simulate 4 follow up shots with improved sequence lag (avg 55ms)
        follow_up_shots = [
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 50.0},
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 55.0},
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 60.0},
            {"tracking_confidence": "SUFFICIENT", "sequence_lag_ms": 55.0}
        ]

        eval_result = self.coach.evaluate_follow_up_set(
            player_id="test_player",
            remediation_id=rem_id,
            follow_up_shots=follow_up_shots,
            feedback_notes="Felt much more connected from floor to fingertips."
        )

        self.assertEqual(eval_result["status"], "EVALUATION_COMPLETE")
        self.assertEqual(eval_result["trend"], "IMPROVED")
        self.assertLess(eval_result["delta"], -50.0)

if __name__ == "__main__":
    unittest.main()
