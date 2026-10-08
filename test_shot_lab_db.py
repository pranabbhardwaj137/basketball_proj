"""
test_shot_lab_db.py - Unit test suite for shot_lab_db.py
"""

import os
import unittest
from shot_lab_db import ShotLabDB

class TestShotLabDB(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_shot_lab.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = ShotLabDB(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except Exception:
                pass

    def test_schema_init(self):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM schema_meta WHERE key = 'version'")
            version = cursor.fetchone()[0]
            self.assertEqual(version, "2")

    def test_provenance_immutability(self):
        """Verify machine boundaries are preserved when human annotations are updated."""
        sess_id = self.db.create_session(player_id="steph", camera_view="side_90", shot_type="catch_and_shoot")
        shot_id = self.db.save_shot({
            "session_id": sess_id,
            "player_id": "steph",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            "machine_start_frame": 10,
            "machine_dip_frame": 25,
            "machine_set_frame": 40,
            "machine_release_frame": 55,
            "machine_end_frame": 75,
            "outcome": "unknown",
            "tracking_confidence": "SUFFICIENT",
            "elbow_angle_release_3d": 156.4
        })

        # Check initial values
        shot = self.db.get_shot(shot_id)
        self.assertEqual(shot["machine_release_frame"], 55)
        self.assertEqual(shot["annotated_release_frame"], 55)
        self.assertEqual(shot["outcome"], "unknown")

        # Apply human review edit
        success = self.db.update_shot_annotation(
            shot_id=shot_id,
            annotated_boundaries={"release_frame": 58, "dip_frame": 24},
            outcome="make",
            outcome_source="manual_review",
            review_notes="Shifted release 3 frames later to true hand separation"
        )
        self.assertTrue(success)

        # Confirm machine boundaries remain untouched while annotated boundaries are updated
        updated_shot = self.db.get_shot(shot_id)
        self.assertEqual(updated_shot["machine_release_frame"], 55)  # UNCHANGED!
        self.assertEqual(updated_shot["annotated_release_frame"], 58) # UPDATED!
        self.assertEqual(updated_shot["outcome"], "make")
        self.assertEqual(updated_shot["outcome_source"], "manual_review")
        self.assertEqual(updated_shot["review_notes"], "Shifted release 3 frames later to true hand separation")

    def test_baseline_and_remediation(self):
        """Verify baseline storage and remediation life-cycle."""
        base_id = self.db.save_baseline({
            "player_id": "steph",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            "sample_size_makes": 6,
            "sample_size_misses": 4,
            "mean_elbow_release_make": 158.5,
            "std_elbow_release_make": 3.2,
            "mean_elbow_release_miss": 142.1,
            "std_elbow_release_miss": 6.8,
            "mean_sequence_lag_make": 45.0,
            "std_sequence_lag_make": 12.0,
            "mean_sequence_lag_miss": 115.0,
            "std_sequence_lag_miss": 25.0
        })

        latest_base = self.db.get_latest_baseline("steph", "side_90", "catch_and_shoot")
        self.assertIsNotNone(latest_base)
        self.assertEqual(latest_base["baseline_id"], base_id)
        self.assertEqual(latest_base["sample_size_makes"], 6)

        rem_id = self.db.save_remediation({
            "player_id": "steph",
            "baseline_id": base_id,
            "targeted_flaw": "Kinetic Sequencing Lag > 100ms",
            "priority_tier": 1,
            "recommended_drill": "One-Motion Dip-to-Rise Wall/Rim Jumps",
            "drill_reps": 10,
            "pre_drill_metric_mean": 115.0
        })

        active_rem = self.db.get_active_remediation("steph")
        self.assertIsNotNone(active_rem)
        self.assertEqual(active_rem["remediation_id"], rem_id)

        # Complete drill
        self.db.update_remediation_status(
            rem_id,
            status="completed",
            drill_completed=True,
            post_drill_metric_mean=55.0,
            post_drill_metric_std=14.0,
            post_make_count=5,
            post_total_count=6,
            feedback_notes="Rhythm felt significantly more unified"
        )
        self.assertIsNone(self.db.get_active_remediation("steph"))

    def test_shot_style_and_quarantine(self):
        """Verify shot_style recording and quarantine default vs approved status."""
        sess_id = self.db.create_session(
            player_id="steph",
            camera_view="frontal",
            shot_type="catch_and_shoot",
            shot_style="set_shot"
        )
        
        # Unlabeled shot should default to quarantined
        shot_id1 = self.db.save_shot({
            "session_id": sess_id,
            "player_id": "steph",
            "camera_view": "frontal",
            "shot_type": "catch_and_shoot",
            "shot_style": "set_shot",
            "machine_start_frame": 10,
            "machine_dip_frame": 20,
            "machine_release_frame": 40,
            "outcome": "unknown",
            "outcome_source": "unlabeled",
            "tracking_confidence": "SUFFICIENT"
        })
        shot1 = self.db.get_shot(shot_id1)
        self.assertEqual(shot1["shot_style"], "set_shot")
        self.assertEqual(shot1["review_status"], "quarantined")

        # Live hotkey labeled make should default to approved
        shot_id2 = self.db.save_shot({
            "session_id": sess_id,
            "player_id": "steph",
            "camera_view": "frontal",
            "shot_type": "catch_and_shoot",
            "shot_style": "set_shot",
            "machine_start_frame": 50,
            "machine_dip_frame": 60,
            "machine_release_frame": 80,
            "outcome": "make",
            "outcome_source": "live_hotkey",
            "tracking_confidence": "SUFFICIENT"
        })
        shot2 = self.db.get_shot(shot_id2)
        self.assertEqual(shot2["review_status"], "approved")

        # Explicit update review_status to approved
        self.db.update_shot_annotation(shot_id1, review_status="approved", review_notes="Reviewed keyframes")
        shot1_upd = self.db.get_shot(shot_id1)
        self.assertEqual(shot1_upd["review_status"], "approved")
        self.assertEqual(shot1_upd["review_notes"], "Reviewed keyframes")

        # Query filtering by review_status and shot_style
        approved_shots = self.db.get_shots(player_id="steph", shot_style="set_shot", review_status="approved")
        self.assertEqual(len(approved_shots), 2)

if __name__ == "__main__":
    unittest.main()

