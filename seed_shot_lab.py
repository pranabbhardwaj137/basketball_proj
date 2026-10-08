"""
seed_shot_lab.py - Local Database Populator & Fixture Seeder.

Creates a starter SQLite database with sample players, sessions, approved & quarantined
shots, and computed baselines so new team members can immediately test baseline and coaching
features without needing to record live video first.

Usage:
    python seed_shot_lab.py [--db shot_lab.db]
"""

import os
import sys
import argparse
from shot_lab_db import ShotLabDB
from baseline_engine import BaselineEngine
from coach_engine import CoachEngine

def seed_database(db_path: str = "shot_lab.db") -> None:
    print(f"\n[SEED] Initializing database at: {db_path}")
    db = ShotLabDB(db_path)
    baseline_engine = BaselineEngine(db)
    coach_engine = CoachEngine(db)

    # 1. Register sample players
    print("[SEED] Registering sample players...")
    db.upsert_player("player_curry", "Stephen Curry", height_m=1.88, wingspan_m=1.92)
    db.upsert_player("player_klay", "Klay Thompson", height_m=1.98, wingspan_m=2.06)

    # 2. Create sample session for Stephen Curry (Jump Shots)
    print("[SEED] Creating sessions and populating shots for Stephen Curry...")
    sess_curry_jump = db.create_session(
        player_id="player_curry",
        camera_view="side_90",
        shot_type="catch_and_shoot",
        shot_style="jump_shot",
        fps=30.0
    )

    # 6 Approved Makes (clean kinetic sequencing ~45ms, release angle ~158 deg)
    for i in range(6):
        db.save_shot({
            "session_id": sess_curry_jump,
            "player_id": "player_curry",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            "shot_style": "jump_shot",
            "machine_start_frame": 100 + (i * 100),
            "machine_dip_frame": 115 + (i * 100),
            "machine_set_frame": 130 + (i * 100),
            "machine_release_frame": 145 + (i * 100),
            "machine_end_frame": 170 + (i * 100),
            "outcome": "make",
            "outcome_source": "live_hotkey",
            "review_status": "approved",
            "tracking_confidence": "SUFFICIENT",
            "elbow_angle_release_3d": 158.0 + (i * 0.5),
            "elbow_angle_release_2d": 142.0,
            "foreshortening_discrepancy_deg": 16.0,
            "knee_angle_dip_3d": 88.0,
            "sequence_lag_ms": 45.0 + (i * 2.0),
            "torso_sway_deg": 4.5
        })

    # 5 Approved Misses (delayed kinetic sequencing ~115ms, release angle ~142 deg)
    for i in range(5):
        db.save_shot({
            "session_id": sess_curry_jump,
            "player_id": "player_curry",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            "shot_style": "jump_shot",
            "machine_start_frame": 700 + (i * 100),
            "machine_dip_frame": 715 + (i * 100),
            "machine_set_frame": 730 + (i * 100),
            "machine_release_frame": 745 + (i * 100),
            "machine_end_frame": 770 + (i * 100),
            "outcome": "miss",
            "outcome_source": "live_hotkey",
            "review_status": "approved",
            "tracking_confidence": "SUFFICIENT",
            "elbow_angle_release_3d": 142.0 + (i * 0.5),
            "elbow_angle_release_2d": 130.0,
            "foreshortening_discrepancy_deg": 12.0,
            "knee_angle_dip_3d": 92.0,
            "sequence_lag_ms": 115.0 + (i * 3.0),
            "torso_sway_deg": 9.0
        })

    # 2 Quarantined Shots (unlabeled attempts awaiting review)
    for i in range(2):
        db.save_shot({
            "session_id": sess_curry_jump,
            "player_id": "player_curry",
            "camera_view": "side_90",
            "shot_type": "catch_and_shoot",
            "shot_style": "jump_shot",
            "machine_start_frame": 1200 + (i * 100),
            "machine_dip_frame": 1215 + (i * 100),
            "machine_set_frame": 1230 + (i * 100),
            "machine_release_frame": 1245 + (i * 100),
            "machine_end_frame": 1270 + (i * 100),
            "outcome": "unknown",
            "outcome_source": "unlabeled",
            "review_status": "quarantined",
            "tracking_confidence": "SUFFICIENT",
            "elbow_angle_release_3d": 150.0,
            "sequence_lag_ms": 70.0
        })

    # 3. Create sample session for Klay Thompson (Set Shots)
    print("[SEED] Populating set shots for Klay Thompson...")
    sess_klay_set = db.create_session(
        player_id="player_klay",
        camera_view="frontal",
        shot_type="free_throw",
        shot_style="set_shot",
        fps=30.0
    )
    for i in range(6):
        db.save_shot({
            "session_id": sess_klay_set,
            "player_id": "player_klay",
            "camera_view": "frontal",
            "shot_type": "free_throw",
            "shot_style": "set_shot",
            "machine_start_frame": 100 + (i * 90),
            "machine_dip_frame": 115 + (i * 90),
            "machine_set_frame": 128 + (i * 90),
            "machine_release_frame": 140 + (i * 90),
            "machine_end_frame": 165 + (i * 90),
            "outcome": "make",
            "outcome_source": "live_hotkey",
            "review_status": "approved",
            "tracking_confidence": "SUFFICIENT",
            "elbow_angle_release_3d": 152.0 + (i * 0.4),
            "sequence_lag_ms": 52.0 + (i * 1.5),
            "torso_sway_deg": 3.8
        })

    # 4. Compute personal baselines
    print("[SEED] Computing initial personal baselines...")
    bl_curry = baseline_engine.compute_baseline("player_curry", "side_90", "catch_and_shoot", shot_style="jump_shot")
    bl_klay = baseline_engine.compute_baseline("player_klay", "frontal", "free_throw", shot_style="set_shot")

    print("\n" + "=" * 60)
    print("      STARTER DATABASE POPULATED SUCCESSFULLY")
    print("=" * 60)
    print(f" Database: {db_path}")
    print(f" Players:  Stephen Curry (11 approved jump shots, 2 quarantined)")
    print(f"           Klay Thompson (6 approved set shots)")
    print("\n Try running review queue:")
    print(f"   python review_shots.py --db {db_path} --quarantined")
    print(" Try inspecting a baseline:")
    print("   python -c \"from baseline_engine import BaselineEngine; import pprint; pprint.pprint(BaselineEngine().compute_baseline('player_curry', 'side_90', 'catch_and_shoot'))\"")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate local SQLite database with sample Shot Lab data.")
    parser.add_argument("--db", default="shot_lab.db", help="Path to SQLite database file")
    args = parser.parse_args()
    seed_database(args.db)
