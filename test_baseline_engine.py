"""
test_baseline_engine.py - Unit test suite for baseline_engine.py
"""

import os
import unittest
from shot_lab_db import ShotLabDB
from baseline_engine import BaselineEngine

class TestBaselineEngine(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_baseline.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = ShotLabDB(self.test_db)
        self.engine = BaselineEngine(self.db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except Exception:
                pass

    def test_insufficient_sample_gate(self):
        """Verify baseline calculation abstains when N < 5."""
        sess_id = self.db.create_session(player_id="test_player", camera_view="side_90")
        for i in range(4):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "test_player",
                "camera_view": "side_90",
                "shot_type": "catch_and_shoot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "make",
                "elbow_angle_release_3d": 155.0
            })

        res = self.engine.compute_baseline("test_player", "side_90", "catch_and_shoot")
        self.assertEqual(res["status"], "INSUFFICIENT_SAMPLE")
        self.assertEqual(res["sample_size"], 4)
        self.assertEqual(res["min_required"], 5)

    def test_sufficient_baseline_and_associations(self):
        """Verify N >= 5 produces valid baseline and descriptive associations."""
        sess_id = self.db.create_session(player_id="klay", camera_view="side_90", shot_type="catch_and_shoot")
        
        # 4 Makes with high elbow extension and tight lag
        for i in range(4):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "klay",
                "camera_view": "side_90",
                "shot_type": "catch_and_shoot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "make",
                "elbow_angle_release_3d": 160.0 + i,
                "sequence_lag_ms": 40.0 + (i * 5),
                "knee_angle_dip_3d": 90.0,
                "torso_sway_deg": 4.0
            })

        # 3 Misses with low elbow extension and long lag
        for i in range(3):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "klay",
                "camera_view": "side_90",
                "shot_type": "catch_and_shoot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "miss",
                "elbow_angle_release_3d": 140.0 + i,
                "sequence_lag_ms": 110.0 + (i * 10),
                "knee_angle_dip_3d": 88.0,
                "torso_sway_deg": 12.0
            })

        res = self.engine.compute_baseline("klay", "side_90", "catch_and_shoot")
        self.assertEqual(res["status"], "VALID_BASELINE")
        self.assertEqual(res["sample_size_total"], 7)
        self.assertEqual(res["sample_size_makes"], 4)
        self.assertEqual(res["sample_size_misses"], 3)
        self.assertAlmostEqual(res["mean_elbow_release_make"], 161.5, places=1)
        self.assertAlmostEqual(res["mean_elbow_release_miss"], 141.0, places=1)
        
        # Check descriptive associations
        associations = res["descriptive_associations"]
        self.assertGreaterEqual(len(associations), 2)
        # Verify no causal words
        full_text = " ".join(associations).lower()
        self.assertNotIn("caused", full_text)
        self.assertNotIn("guarantee", full_text)
        self.assertIn("associated with", full_text)
        self.assertIn("+/-", full_text)

if __name__ == "__main__":
    unittest.main()
