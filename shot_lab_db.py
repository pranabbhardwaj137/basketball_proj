"""
shot_lab_db.py - Personal Shot Lab SQLite Persistence and Provenance Engine.

Provides versioned schema management, separate tracking for machine predictions
and human-corrected annotations, context grouping, and remediation logs.
"""

from __future__ import annotations
import sqlite3
import datetime
import uuid
import json
from typing import Dict, Any, List, Optional, Tuple

import contextlib

SCHEMA_VERSION = 1

class ShotLabDB:
    def __init__(self, db_path: str = "shot_lab.db"):
        self.db_path = db_path
        self.init_db()

    @contextlib.contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


    def init_db(self) -> None:
        """Initialize SQLite database tables with versioned schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Schema metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            cursor.execute("SELECT value FROM schema_meta WHERE key = 'version'")
            row = cursor.fetchone()
            if not row:
                cursor.execute("INSERT INTO schema_meta (key, value) VALUES ('version', ?)", (str(SCHEMA_VERSION),))
            
            # Players
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    height_m REAL,
                    wingspan_m REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    player_id TEXT NOT NULL,
                    camera_view TEXT NOT NULL, -- 'frontal', 'side_90', 'oblique_45'
                    shot_type TEXT NOT NULL,   -- 'catch_and_shoot', 'off_dribble', 'free_throw'
                    fps REAL DEFAULT 30.0,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (player_id) REFERENCES players (player_id)
                )
            """)

            # Shots (Preserves machine predictions and human annotations separately)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shots (
                    shot_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    player_id TEXT NOT NULL,
                    camera_view TEXT NOT NULL,
                    shot_type TEXT NOT NULL,
                    
                    -- Machine detected event boundaries (Immutable from capture)
                    machine_start_frame INTEGER,
                    machine_dip_frame INTEGER,
                    machine_set_frame INTEGER,
                    machine_release_frame INTEGER,
                    machine_end_frame INTEGER,
                    
                    -- Human annotated/corrected event boundaries
                    annotated_start_frame INTEGER,
                    annotated_dip_frame INTEGER,
                    annotated_set_frame INTEGER,
                    annotated_release_frame INTEGER,
                    annotated_end_frame INTEGER,
                    
                    -- Outcome & Provenance
                    outcome TEXT DEFAULT 'unknown',       -- 'make', 'miss', 'unknown'
                    outcome_source TEXT DEFAULT 'unlabeled', -- 'live_hotkey', 'manual_review', 'unlabeled'
                    review_notes TEXT,
                    
                    -- Tracking Confidence & Quality Gates
                    tracking_confidence TEXT NOT NULL,    -- 'SUFFICIENT', 'INSUFFICIENT'
                    valid_frame_ratio REAL DEFAULT 1.0,
                    
                    -- 3D World Space Biomechanics (Estimates in meters)
                    knee_angle_dip_3d REAL,
                    elbow_angle_release_3d REAL,
                    release_height_rel_m REAL,
                    
                    -- 2D Image Space Biomechanics & Foreshortening
                    elbow_angle_release_2d REAL,
                    foreshortening_discrepancy_deg REAL,
                    
                    -- Kinetic Sequencing
                    sequence_lag_ms REAL,
                    sequence_order_valid INTEGER DEFAULT 1,
                    torso_sway_deg REAL,
                    
                    -- Raw reference
                    raw_landmarks_ref TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                    FOREIGN KEY (player_id) REFERENCES players (player_id)
                )
            """)

            # Baselines (Descriptive associations for matched player/view/type)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS baselines (
                    baseline_id TEXT PRIMARY KEY,
                    player_id TEXT NOT NULL,
                    camera_view TEXT NOT NULL,
                    shot_type TEXT NOT NULL,
                    sample_size_makes INTEGER NOT NULL,
                    sample_size_misses INTEGER NOT NULL,
                    
                    -- Descriptive distributions (mean and sample std dev)
                    mean_elbow_release_make REAL,
                    std_elbow_release_make REAL,
                    mean_elbow_release_miss REAL,
                    std_elbow_release_miss REAL,
                    
                    mean_sequence_lag_make REAL,
                    std_sequence_lag_make REAL,
                    mean_sequence_lag_miss REAL,
                    std_sequence_lag_miss REAL,
                    
                    mean_knee_dip_make REAL,
                    std_knee_dip_make REAL,
                    mean_knee_dip_miss REAL,
                    std_knee_dip_miss REAL,
                    
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players (player_id)
                )
            """)

            # Remediations (One-Cue-at-a-Time practice loop)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS remediations (
                    remediation_id TEXT PRIMARY KEY,
                    player_id TEXT NOT NULL,
                    baseline_id TEXT,
                    targeted_flaw TEXT NOT NULL,
                    priority_tier INTEGER NOT NULL, -- 1=Sequencing, 2=Release, 3=Stability
                    recommended_drill TEXT NOT NULL,
                    drill_reps INTEGER DEFAULT 10,
                    pre_drill_metric_mean REAL,
                    post_drill_metric_mean REAL,
                    status TEXT DEFAULT 'active',   -- 'active', 'completed', 'dismissed'
                    feedback_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players (player_id),
                    FOREIGN KEY (baseline_id) REFERENCES baselines (baseline_id)
                )
            """)
            conn.commit()

    def upsert_player(self, player_id: str, name: str, height_m: Optional[float] = None, wingspan_m: Optional[float] = None) -> str:
        """Register or update player profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO players (player_id, name, height_m, wingspan_m)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(player_id) DO UPDATE SET
                    name = excluded.name,
                    height_m = COALESCE(excluded.height_m, players.height_m),
                    wingspan_m = COALESCE(excluded.wingspan_m, players.wingspan_m)
            """, (player_id, name, height_m, wingspan_m))
            conn.commit()
            return player_id

    def create_session(
        self,
        session_id: Optional[str] = None,
        player_id: str = "default_player",
        camera_view: str = "frontal",
        shot_type: str = "catch_and_shoot",
        fps: float = 30.0,
        model_version: str = "1.0.0",
        notes: Optional[str] = None
    ) -> str:
        """Create a new shot analysis session."""
        if not session_id:
            session_id = f"sess_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"
        
        # Ensure player exists
        self.upsert_player(player_id, player_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, player_id, camera_view, shot_type, fps, model_version, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, player_id, camera_view, shot_type, fps, model_version, notes))
            conn.commit()
            return session_id

    def save_shot(self, shot_data: Dict[str, Any]) -> str:
        """
        Persist a shot record. Preserves machine predictions and initializes
        annotated boundaries with machine values.
        """
        shot_id = shot_data.get("shot_id") or f"shot_{str(uuid.uuid4())[:8]}"
        now = datetime.datetime.now().isoformat()
        
        m_start = shot_data.get("start_frame") or shot_data.get("machine_start_frame")
        m_dip = shot_data.get("dip_frame") or shot_data.get("machine_dip_frame")
        m_set = shot_data.get("set_frame") or shot_data.get("machine_set_frame")
        m_release = shot_data.get("release_frame") or shot_data.get("machine_release_frame")
        m_end = shot_data.get("end_frame") or shot_data.get("machine_end_frame")
        
        a_start = shot_data.get("annotated_start_frame", m_start)
        a_dip = shot_data.get("annotated_dip_frame", m_dip)
        a_set = shot_data.get("annotated_set_frame", m_set)
        a_release = shot_data.get("annotated_release_frame", m_release)
        a_end = shot_data.get("annotated_end_frame", m_end)
        
        outcome = shot_data.get("outcome", "unknown").lower()
        if outcome not in ("make", "miss", "unknown"):
            outcome = "unknown"
            
        outcome_source = shot_data.get("outcome_source", "unlabeled")
        tracking_conf = shot_data.get("tracking_confidence", "SUFFICIENT")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO shots (
                    shot_id, session_id, player_id, camera_view, shot_type,
                    machine_start_frame, machine_dip_frame, machine_set_frame, machine_release_frame, machine_end_frame,
                    annotated_start_frame, annotated_dip_frame, annotated_set_frame, annotated_release_frame, annotated_end_frame,
                    outcome, outcome_source, review_notes,
                    tracking_confidence, valid_frame_ratio,
                    knee_angle_dip_3d, elbow_angle_release_3d, release_height_rel_m,
                    elbow_angle_release_2d, foreshortening_discrepancy_deg,
                    sequence_lag_ms, sequence_order_valid, torso_sway_deg,
                    raw_landmarks_ref, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?, ?
                )
            """, (
                shot_id,
                shot_data.get("session_id", "default_session"),
                shot_data.get("player_id", "default_player"),
                shot_data.get("camera_view", "frontal"),
                shot_data.get("shot_type", "catch_and_shoot"),
                m_start, m_dip, m_set, m_release, m_end,
                a_start, a_dip, a_set, a_release, a_end,
                outcome, outcome_source, shot_data.get("review_notes"),
                tracking_conf, shot_data.get("valid_frame_ratio", 1.0),
                shot_data.get("knee_angle_dip_3d"),
                shot_data.get("elbow_angle_release_3d"),
                shot_data.get("release_height_rel_m"),
                shot_data.get("elbow_angle_release_2d"),
                shot_data.get("foreshortening_discrepancy_deg"),
                shot_data.get("sequence_lag_ms"),
                1 if shot_data.get("sequence_order_valid", True) else 0,
                shot_data.get("torso_sway_deg"),
                shot_data.get("raw_landmarks_ref"),
                now, now
            ))
            conn.commit()
            return shot_id

    def update_shot_annotation(
        self,
        shot_id: str,
        annotated_boundaries: Optional[Dict[str, int]] = None,
        outcome: Optional[str] = None,
        outcome_source: str = "manual_review",
        review_notes: Optional[str] = None,
        tracking_confidence: Optional[str] = None
    ) -> bool:
        """
        Update human-corrected boundaries or outcome label while preserving
        machine-detected predictions intact.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shots WHERE shot_id = ?", (shot_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            updates = []
            params = []
            now = datetime.datetime.now().isoformat()
            
            if annotated_boundaries:
                if "start_frame" in annotated_boundaries:
                    updates.append("annotated_start_frame = ?")
                    params.append(annotated_boundaries["start_frame"])
                if "dip_frame" in annotated_boundaries:
                    updates.append("annotated_dip_frame = ?")
                    params.append(annotated_boundaries["dip_frame"])
                if "set_frame" in annotated_boundaries:
                    updates.append("annotated_set_frame = ?")
                    params.append(annotated_boundaries["set_frame"])
                if "release_frame" in annotated_boundaries:
                    updates.append("annotated_release_frame = ?")
                    params.append(annotated_boundaries["release_frame"])
                if "end_frame" in annotated_boundaries:
                    updates.append("annotated_end_frame = ?")
                    params.append(annotated_boundaries["end_frame"])
                    
            if outcome is not None:
                cleaned_outcome = outcome.lower()
                if cleaned_outcome in ("make", "miss", "unknown"):
                    updates.append("outcome = ?")
                    params.append(cleaned_outcome)
                    updates.append("outcome_source = ?")
                    params.append(outcome_source)
                    
            if review_notes is not None:
                updates.append("review_notes = ?")
                params.append(review_notes)
                
            if tracking_confidence is not None:
                updates.append("tracking_confidence = ?")
                params.append(tracking_confidence)
                
            updates.append("updated_at = ?")
            params.append(now)
            params.append(shot_id)
            
            sql = f"UPDATE shots SET {', '.join(updates)} WHERE shot_id = ?"
            cursor.execute(sql, tuple(params))
            conn.commit()
            return cursor.rowcount > 0

    def get_shot(self, shot_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single shot record as a dict."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shots WHERE shot_id = ?", (shot_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_shots(
        self,
        player_id: Optional[str] = None,
        session_id: Optional[str] = None,
        camera_view: Optional[str] = None,
        shot_type: Optional[str] = None,
        min_confidence: Optional[str] = "SUFFICIENT"
    ) -> List[Dict[str, Any]]:
        """Query shots with optional filters."""
        query = "SELECT * FROM shots WHERE 1=1"
        params = []
        
        if player_id:
            query += " AND player_id = ?"
            params.append(player_id)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if camera_view:
            query += " AND camera_view = ?"
            params.append(camera_view)
        if shot_type:
            query += " AND shot_type = ?"
            params.append(shot_type)
        if min_confidence:
            query += " AND tracking_confidence = ?"
            params.append(min_confidence)
            
        query += " ORDER BY created_at ASC"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    def save_baseline(self, baseline_data: Dict[str, Any]) -> str:
        """Save a computed player baseline profile."""
        baseline_id = baseline_data.get("baseline_id") or f"base_{str(uuid.uuid4())[:8]}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO baselines (
                    baseline_id, player_id, camera_view, shot_type,
                    sample_size_makes, sample_size_misses,
                    mean_elbow_release_make, std_elbow_release_make,
                    mean_elbow_release_miss, std_elbow_release_miss,
                    mean_sequence_lag_make, std_sequence_lag_make,
                    mean_sequence_lag_miss, std_sequence_lag_miss,
                    mean_knee_dip_make, std_knee_dip_make,
                    mean_knee_dip_miss, std_knee_dip_miss,
                    computed_at
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    CURRENT_TIMESTAMP
                )
            """, (
                baseline_id,
                baseline_data["player_id"],
                baseline_data.get("camera_view", "frontal"),
                baseline_data.get("shot_type", "catch_and_shoot"),
                baseline_data.get("sample_size_makes", 0),
                baseline_data.get("sample_size_misses", 0),
                baseline_data.get("mean_elbow_release_make"),
                baseline_data.get("std_elbow_release_make"),
                baseline_data.get("mean_elbow_release_miss"),
                baseline_data.get("std_elbow_release_miss"),
                baseline_data.get("mean_sequence_lag_make"),
                baseline_data.get("std_sequence_lag_make"),
                baseline_data.get("mean_sequence_lag_miss"),
                baseline_data.get("std_sequence_lag_miss"),
                baseline_data.get("mean_knee_dip_make"),
                baseline_data.get("std_knee_dip_make"),
                baseline_data.get("mean_knee_dip_miss"),
                baseline_data.get("std_knee_dip_miss")
            ))
            conn.commit()
            return baseline_id

    def get_latest_baseline(self, player_id: str, camera_view: str, shot_type: str) -> Optional[Dict[str, Any]]:
        """Get the most recent baseline for a player in a specific context."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM baselines 
                WHERE player_id = ? AND camera_view = ? AND shot_type = ?
                ORDER BY computed_at DESC LIMIT 1
            """, (player_id, camera_view, shot_type))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_remediation(self, rem_data: Dict[str, Any]) -> str:
        """Save a coaching remediation recommendation."""
        rem_id = rem_data.get("remediation_id") or f"rem_{str(uuid.uuid4())[:8]}"
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO remediations (
                    remediation_id, player_id, baseline_id,
                    targeted_flaw, priority_tier, recommended_drill, drill_reps,
                    pre_drill_metric_mean, post_drill_metric_mean,
                    status, feedback_notes, created_at, updated_at
                ) VALUES (
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?, ?, ?
                )
            """, (
                rem_id,
                rem_data["player_id"],
                rem_data.get("baseline_id"),
                rem_data["targeted_flaw"],
                rem_data.get("priority_tier", 1),
                rem_data["recommended_drill"],
                rem_data.get("drill_reps", 10),
                rem_data.get("pre_drill_metric_mean"),
                rem_data.get("post_drill_metric_mean"),
                rem_data.get("status", "active"),
                rem_data.get("feedback_notes"),
                now, now
            ))
            conn.commit()
            return rem_id

    def update_remediation_status(
        self,
        remediation_id: str,
        status: str,
        post_drill_metric_mean: Optional[float] = None,
        feedback_notes: Optional[str] = None
    ) -> bool:
        """Update remediation progress and post-drill outcome."""
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = ["status = ?", "updated_at = ?"]
            params = [status, now]
            
            if post_drill_metric_mean is not None:
                updates.append("post_drill_metric_mean = ?")
                params.append(post_drill_metric_mean)
            if feedback_notes is not None:
                updates.append("feedback_notes = ?")
                params.append(feedback_notes)
                
            params.append(remediation_id)
            cursor.execute(f"UPDATE remediations SET {', '.join(updates)} WHERE remediation_id = ?", tuple(params))
            conn.commit()
            return cursor.rowcount > 0

    def get_active_remediation(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get current active remediation for a player."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM remediations
                WHERE player_id = ? AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, (player_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
