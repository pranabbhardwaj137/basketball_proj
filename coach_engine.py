"""
coach_engine.py - Hierarchical One-Cue Remediation and Follow-Up Engine.

Evaluates baseline biomechanical data against a strict 3-tier hierarchy:
  - Tier 1: Kinetic Sequencing (Energy transfer lag > 100ms or sequence inversion)
  - Tier 2: Release Extension & Height (Elbow angle at release < 150 deg)
  - Tier 3: Set-Point Dip Stability & Balance (Torso sway > 10 deg)

Enforces the One-Cue Rule (at most one primary cue presented at a time) and
tracks follow-up practice sets against baseline targets.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from shot_lab_db import ShotLabDB

class CoachEngine:
    def __init__(self, db: Optional[ShotLabDB] = None):
        self.db = db or ShotLabDB()

    def generate_primary_cue(self, baseline: Dict[str, Any], save_to_db: bool = True) -> Dict[str, Any]:
        """
        Evaluate baseline kinematics and produce exactly ONE evidence-backed coaching cue
        paired with a targeted drill.
        """
        player_id = baseline["player_id"]
        baseline_id = baseline.get("baseline_id")

        # -------------------------------------------------------------
        # Tier 1: Kinetic Sequencing (Highest Priority)
        # -------------------------------------------------------------
        seq_all = baseline.get("mean_sequence_lag_all")
        seq_miss = baseline.get("mean_sequence_lag_miss")
        seq_make = baseline.get("mean_sequence_lag_make")
        
        has_tier1_flaw = False
        evidence_text = ""
        pre_metric = None

        if seq_miss is not None and seq_make is not None and (seq_miss - seq_make) >= 40.0:
            has_tier1_flaw = True
            pre_metric = seq_miss
            evidence_text = (
                f"Missed shots showed {seq_miss - seq_make:.1f} ms longer kinetic delay between knee drive and arm extension "
                f"({seq_miss:.1f} ms on misses vs {seq_make:.1f} ms on makes)."
            )
        elif seq_all is not None and seq_all > 100.0:
            has_tier1_flaw = True
            pre_metric = seq_all
            evidence_text = f"Overall kinetic transfer lag averaged {seq_all:.1f} ms (recommended fluid threshold is < 80 ms)."

        if has_tier1_flaw:
            cue = {
                "player_id": player_id,
                "baseline_id": baseline_id,
                "priority_tier": 1,
                "targeted_flaw": "Kinetic Sequencing Delay",
                "cue_title": "Synchronize Knee Drive & Arm Extension",
                "biomechanical_evidence": evidence_text,
                "recommended_drill": "One-Motion Dip-to-Rise Wall/Rim Jumps",
                "drill_reps": 10,
                "target_metric_key": "sequence_lag_ms",
                "target_metric_name": "Kinetic Sequence Lag",
                "baseline_value": pre_metric,
                "pre_drill_metric_mean": pre_metric,
                "target_goal": "< 80 ms lag",
                "status": "active"
            }
            if save_to_db:
                rem_id = self.db.save_remediation(cue)
                cue["remediation_id"] = rem_id
            return cue

        # -------------------------------------------------------------
        # Tier 2: Release Extension & Height (Second Priority)
        # -------------------------------------------------------------
        elbow_all = baseline.get("mean_elbow_release_all")
        elbow_miss = baseline.get("mean_elbow_release_miss")
        elbow_make = baseline.get("mean_elbow_release_make")

        has_tier2_flaw = False
        if elbow_make is not None and elbow_miss is not None and (elbow_make - elbow_miss) >= 12.0:
            has_tier2_flaw = True
            pre_metric = elbow_miss
            evidence_text = (
                f"Missed shots exhibited {elbow_make - elbow_miss:.1f} deg lower elbow extension at release "
                f"({elbow_miss:.1f} deg on misses vs {elbow_make:.1f} deg on makes)."
            )
        elif elbow_all is not None and elbow_all < 150.0:
            has_tier2_flaw = True
            pre_metric = elbow_all
            evidence_text = f"Overall elbow extension at release averaged {elbow_all:.1f} deg (recommended target is >= 155 deg)."

        if has_tier2_flaw:
            cue = {
                "player_id": player_id,
                "baseline_id": baseline_id,
                "priority_tier": 2,
                "targeted_flaw": "Incomplete Release Extension",
                "cue_title": "Full High-Release Arm Extension",
                "biomechanical_evidence": evidence_text,
                "recommended_drill": "High-Release Form Shooting from 5 Feet",
                "drill_reps": 15,
                "target_metric_key": "elbow_angle_release_3d",
                "target_metric_name": "3D Elbow Release Angle",
                "baseline_value": pre_metric,
                "pre_drill_metric_mean": pre_metric,
                "target_goal": ">= 155 deg",
                "status": "active"
            }
            if save_to_db:
                rem_id = self.db.save_remediation(cue)
                cue["remediation_id"] = rem_id
            return cue

        # -------------------------------------------------------------
        # Tier 3: Set-Point Dip Stability & Posture (Third Priority)
        # -------------------------------------------------------------
        sway_all = baseline.get("mean_torso_sway_all")
        sway_miss = baseline.get("mean_torso_sway_miss")
        sway_make = baseline.get("mean_torso_sway_make")

        has_tier3_flaw = False
        if sway_make is not None and sway_miss is not None and (sway_miss - sway_make) >= 3.5:
            has_tier3_flaw = True
            pre_metric = sway_miss
            evidence_text = (
                f"Missed shots showed {sway_miss - sway_make:.1f} deg greater torso sway during shot preparation "
                f"({sway_miss:.1f} deg on misses vs {sway_make:.1f} deg on makes)."
            )
        elif sway_all is not None and sway_all > 10.0:
            has_tier3_flaw = True
            pre_metric = sway_all
            evidence_text = f"Torso posture tilt averaged {sway_all:.1f} deg sway during dip (recommended balance is < 8 deg)."

        if has_tier3_flaw:
            cue = {
                "player_id": player_id,
                "baseline_id": baseline_id,
                "priority_tier": 3,
                "targeted_flaw": "Torso Sway / Base Instability",
                "cue_title": "Balanced Dip Posture & Solid Base",
                "biomechanical_evidence": evidence_text,
                "recommended_drill": "Balanced Catch-and-Shoot Holds",
                "drill_reps": 10,
                "target_metric_key": "torso_sway_deg",
                "target_metric_name": "Torso Sway",
                "baseline_value": pre_metric,
                "pre_drill_metric_mean": pre_metric,
                "target_goal": "< 8 deg sway",
                "status": "active"
            }
            if save_to_db:
                rem_id = self.db.save_remediation(cue)
                cue["remediation_id"] = rem_id
            return cue


        # No critical flaw found
        return {
            "player_id": player_id,
            "baseline_id": baseline_id,
            "priority_tier": 0,
            "targeted_flaw": "None",
            "cue_title": "Maintain Repeatable Form",
            "biomechanical_evidence": "Your baseline mechanics are consistent and within recommended parameters.",
            "recommended_drill": "Game-Speed Spot-Up Shooting (20 reps)",
            "drill_reps": 20,
            "status": "maintenance"
        }

    def evaluate_follow_up_set(
        self,
        player_id: str,
        remediation_id: str,
        follow_up_shots: List[Dict[str, Any]],
        feedback_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a follow-up practice set (post-drill) against the active remediation target.
        """
        valid_shots = [s for s in follow_up_shots if s.get("tracking_confidence") == "SUFFICIENT"]
        n_follow = len(valid_shots)
        if n_follow < 3:
            return {
                "status": "INSUFFICIENT_FOLLOW_UP",
                "message": f"Need at least 3 valid shots to evaluate follow-up set (found {n_follow}).",
                "sample_size": n_follow
            }

        # Query remediation record
        active_rem = self.db.get_active_remediation(player_id)
        if not active_rem or active_rem["remediation_id"] != remediation_id:
            # Fallback query from db
            pass

        tier = active_rem["priority_tier"] if active_rem else 1
        pre_mean = active_rem["pre_drill_metric_mean"] if active_rem else 0.0

        if tier == 1:
            # Kinetic sequence lag (lower is better)
            vals = [s["sequence_lag_ms"] for s in valid_shots if s.get("sequence_lag_ms") is not None]
            post_mean = sum(vals) / len(vals) if vals else pre_mean
            delta = post_mean - pre_mean
            improved = (post_mean < pre_mean) and (delta <= -15.0)
            trend = "IMPROVED" if improved else ("REGRESSED" if delta > 15.0 else "NEUTRAL")
            summary = f"Kinetic sequence lag changed by {delta:+.1f} ms ({pre_mean:.1f} ms pre-drill -> {post_mean:.1f} ms post-drill)."
        elif tier == 2:
            # Elbow release angle (higher is better)
            vals = [s["elbow_angle_release_3d"] for s in valid_shots if s.get("elbow_angle_release_3d") is not None]
            post_mean = sum(vals) / len(vals) if vals else pre_mean
            delta = post_mean - pre_mean
            improved = (post_mean > pre_mean) and (delta >= 5.0)
            trend = "IMPROVED" if improved else ("REGRESSED" if delta < -5.0 else "NEUTRAL")
            summary = f"3D Elbow release angle changed by {delta:+.1f} deg ({pre_mean:.1f} deg pre-drill -> {post_mean:.1f} deg post-drill)."
        else:
            # Torso sway (lower is better)
            vals = [s["torso_sway_deg"] for s in valid_shots if s.get("torso_sway_deg") is not None]
            post_mean = sum(vals) / len(vals) if vals else pre_mean
            delta = post_mean - pre_mean
            improved = (post_mean < pre_mean) and (delta <= -2.0)
            trend = "IMPROVED" if improved else ("REGRESSED" if delta > 2.0 else "NEUTRAL")
            summary = f"Torso sway changed by {delta:+.1f} deg ({pre_mean:.1f} deg pre-drill -> {post_mean:.1f} deg post-drill)."

        # Update remediation in DB
        self.db.update_remediation_status(
            remediation_id=remediation_id,
            status="completed",
            post_drill_metric_mean=round(post_mean, 2),
            feedback_notes=feedback_notes or summary
        )

        return {
            "status": "EVALUATION_COMPLETE",
            "remediation_id": remediation_id,
            "trend": trend,
            "pre_drill_mean": round(pre_mean, 2) if pre_mean else None,
            "post_drill_mean": round(post_mean, 2),
            "delta": round(delta, 2),
            "summary": summary,
            "sample_size": n_follow
        }
