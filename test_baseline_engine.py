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
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 155.0
            })

        res = self.engine.compute_baseline("test_player", "side_90", "catch_and_shoot")
        self.assertEqual(res["status"], "INSUFFICIENT_SAMPLE")
        self.assertEqual(res["sample_size"], 4)
        self.assertEqual(res["min_required"], 5)

    def test_unconfirmed_shots_quarantine(self):
        """Verify automated unconfirmed shots are quarantined from baselines."""
        sess_id = self.db.create_session(player_id="auto_player", camera_view="side_90")
        for i in range(6):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "auto_player",
                "camera_view": "side_90",
                "shot_type": "catch_and_shoot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "unknown",
                "outcome_source": "unlabeled",
                "elbow_angle_release_3d": 155.0
            })

        # By default require_human_confirmed=True -> 0 confirmed shots
        res = self.engine.compute_baseline("auto_player", "side_90", "catch_and_shoot")
        self.assertEqual(res["status"], "INSUFFICIENT_SAMPLE")
        self.assertEqual(res["sample_size"], 0)

        # If override require_human_confirmed=False -> admits all 6
        res_unlocked = self.engine.compute_baseline("auto_player", "side_90", "catch_and_shoot", require_human_confirmed=False)
        self.assertEqual(res_unlocked["status"], "VALID_BASELINE")
        self.assertEqual(res_unlocked["sample_size_total"], 6)

    def test_sufficient_baseline_and_associations(self):
        """Verify N >= 5 produces valid baseline, reports overall metrics, and tests make/miss contrast gating."""
        sess_id = self.db.create_session(
            player_id="klay",
            camera_view="side_90",
            shot_type="catch_and_shoot",
            shot_style="jump_shot"
        )
        
        # 4 Makes with high elbow extension and tight lag
        for i in range(4):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "klay",
                "camera_view": "side_90",
                "shot_type": "catch_and_shoot",
                "shot_style": "jump_shot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "make",
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 160.0 + i,
                "sequence_lag_ms": 40.0 + (i * 5),
                "knee_angle_dip_3d": 90.0,
                "torso_sway_deg": 4.0
            })

        # 3 Misses with low elbow extension and long lag (Total = 7 >= 5, but makes=4 < 5)
        for i in range(3):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "klay",
                "camera_view": "side_90",
                "shot_type": "catch_and_shoot",
                "shot_style": "jump_shot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "miss",
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 140.0 + i,
                "sequence_lag_ms": 110.0 + (i * 10),
                "knee_angle_dip_3d": 88.0,
                "torso_sway_deg": 12.0
            })

        res = self.engine.compute_baseline("klay", "side_90", "catch_and_shoot", shot_style="jump_shot")
        self.assertEqual(res["status"], "VALID_BASELINE")
        self.assertEqual(res["sample_size_total"], 7)
        self.assertEqual(res["sample_size_makes"], 4)
        self.assertEqual(res["sample_size_misses"], 3)
        self.assertAlmostEqual(res["mean_elbow_release_make"], 161.5, places=1)
        self.assertAlmostEqual(res["mean_elbow_release_miss"], 141.0, places=1)
        self.assertIsNotNone(res["mean_elbow_release_all"])
        
        # Check descriptive associations: contrast pending because makes=4 < 5
        associations = res["descriptive_associations"]
        full_text = " ".join(associations).lower()
        self.assertIn("overall baseline across 7 reviewed jump_shot shots", full_text)
        self.assertIn("make-versus-miss contrast pending", full_text)
        self.assertNotIn("caused", full_text)

        # Ingest 1 more make and 2 more misses -> 5 makes, 5 misses (N=10)
        self.db.save_shot({
            "session_id": sess_id,
            "player_id": "klay",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            "shot_style": "jump_shot",
            "tracking_confidence": "SUFFICIENT",
            "outcome": "make",
            "outcome_source": "live_hotkey",
            "elbow_angle_release_3d": 164.0,
            "sequence_lag_ms": 45.0
        })
        for _ in range(2):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "klay",
                "camera_view": "side_90",
                "shot_type": "catch_and_shoot",
                "shot_style": "jump_shot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "miss",
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 142.0,
                "sequence_lag_ms": 125.0
            })

        res10 = self.engine.compute_baseline("klay", "side_90", "catch_and_shoot", shot_style="jump_shot")
        self.assertEqual(res10["sample_size_makes"], 5)
        self.assertEqual(res10["sample_size_misses"], 5)
        assoc10 = res10["descriptive_associations"]
        full_text10 = " ".join(assoc10).lower()
        self.assertIn("associated with", full_text10)
        self.assertIn("quantization uncertainty", full_text10)
        self.assertNotIn("caused", full_text10)

    def test_shot_style_isolation(self):
        """Verify jump_shot and set_shot baselines are strictly isolated."""
        sess_id = self.db.create_session(
            player_id="curry",
            camera_view="frontal",
            shot_type="catch_and_shoot",
            shot_style="jump_shot"
        )
        for _ in range(5):
            self.db.save_shot({
                "session_id": sess_id,
                "player_id": "curry",
                "camera_view": "frontal",
                "shot_type": "catch_and_shoot",
                "shot_style": "jump_shot",
                "tracking_confidence": "SUFFICIENT",
                "outcome": "make",
                "outcome_source": "live_hotkey",
                "elbow_angle_release_3d": 160.0
            })

        # Querying set_shot baseline should find 0 shots and abstain
        res_set = self.engine.compute_baseline("curry", "frontal", "catch_and_shoot", shot_style="set_shot")
        self.assertEqual(res_set["status"], "INSUFFICIENT_SAMPLE")
        self.assertEqual(res_set["sample_size"], 0)

        # Querying jump_shot baseline should find 5 shots and succeed
        res_jump = self.engine.compute_baseline("curry", "frontal", "catch_and_shoot", shot_style="jump_shot")
        self.assertEqual(res_jump["status"], "VALID_BASELINE")
        self.assertEqual(res_jump["sample_size_total"], 5)

if __name__ == "__main__":
    unittest.main()

