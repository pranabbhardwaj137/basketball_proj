"""
coach_engine.py - Hierarchical One-Cue Remediation and Follow-Up Engine.

Evaluates baseline biomechanical data against a strict 3-tier hierarchy:
  - Tier 1: Kinetic Sequencing (Energy transfer lag > threshold or sequence inversion)
  - Tier 2: Release Extension & Height (Elbow angle at release < threshold)
  - Tier 3: Set-Point Dip Stability & Balance (Torso sway > threshold)

Adheres to locked user decisions:
  - Mechanics-Based Gating: Flaws are triggered by repeating biomechanical metrics against
    configurable thresholds for the specific shot_style (jump_shot vs set_shot), not a
    noisy 1-sigma make/miss contrast.
  - Shot-Style Differentiation: Separate configurable thresholds and drills for jump_shot and set_shot.
    Thresholds and drills are treated as empirical starting defaults, not established dogmatic standards.
  - Cognitive Simplicity: Enforces the One-Cue Rule (at most one primary cue presented at a time).
  - Observational Follow-Up: Evaluates post-drill sets against baseline without a combined
    "improvement score", reporting pre/post sample counts, metric means +/- std devs,
    make percentages with explicit numerators/denominators, drill completion status, and
    purely observational language (zero causal claims).
"""

from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
from shot_lab_db import ShotLabDB

# Starting defaults for shot-style coaching evaluation (not dogmatic standards)
DEFAULT_COACHING_CONFIG = {
    "jump_shot": {
        "tier1_sequence_lag_max_ms": 100.0,
        "tier1_target_goal": "< 80 ms lag",
        "tier1_drill": "One-Motion Dip-to-Rise Wall/Rim Jumps",
        "tier1_reps": 10,
        "tier2_elbow_release_min_deg": 150.0,
        "tier2_target_goal": ">= 155 deg",
        "tier2_drill": "High-Release Form Shooting from 5 Feet",
        "tier2_reps": 15,
        "tier3_torso_sway_max_deg": 10.0,
        "tier3_target_goal": "< 8 deg sway",
        "tier3_drill": "Balanced Catch-and-Shoot Holds",
        "tier3_reps": 10,
    },
    "set_shot": {
        "tier1_sequence_lag_max_ms": 85.0,
        "tier1_target_goal": "< 70 ms lag",
        "tier1_drill": "Continuous Ground-to-Release Rhythm Shooting",
        "tier1_reps": 15,
        "tier2_elbow_release_min_deg": 145.0,
        "tier2_target_goal": ">= 150 deg",
        "tier2_drill": "One-Handed Form Push from 8 Feet",
        "tier2_reps": 15,
        "tier3_torso_sway_max_deg": 8.0,
        "tier3_target_goal": "< 6 deg sway",
        "tier3_drill": "Stationary Base Catch-and-Shoots",
        "tier3_reps": 12,
    }
}

def _mean_and_std(values: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """Calculate sample mean and sample standard deviation (N-1 degrees of freedom)."""
    valid = [v for v in values if v is not None and not math.isnan(v)]
    n = len(valid)
    if n == 0:
        return None, None
    mean = sum(valid) / n
    if n == 1:
        return round(mean, 2), 0.0
    var = sum((x - mean) ** 2 for x in valid) / (n - 1)
    return round(mean, 2), round(math.sqrt(var), 2)


class CoachEngine:
    def __init__(self, db: Optional[ShotLabDB] = None, config: Optional[Dict[str, Any]] = None):
        self.db = db or ShotLabDB()
        self.config = config or DEFAULT_COACHING_CONFIG

    def _get_style_config(self, shot_style: str) -> Dict[str, Any]:
        """Retrieve coaching config for the specified shot style, defaulting to jump_shot."""
        return self.config.get(shot_style, self.config.get("jump_shot", DEFAULT_COACHING_CONFIG["jump_shot"]))

    def generate_primary_cue(self, baseline: Dict[str, Any], save_to_db: bool = True) -> Dict[str, Any]:
        """
        Evaluate baseline kinematics against mechanics thresholds for the specific shot style
        and produce exactly ONE evidence-backed coaching cue paired with a targeted drill.
        """
        player_id = baseline["player_id"]
        baseline_id = baseline.get("baseline_id")
        shot_style = baseline.get("shot_style", "jump_shot")
        cfg = self._get_style_config(shot_style)

        # Baseline sample info
        n_tot = baseline.get("sample_size_total", 0)
        n_mk = baseline.get("sample_size_makes", 0)
        n_ms = baseline.get("sample_size_misses", 0)

        # -------------------------------------------------------------
        # Tier 1: Kinetic Sequencing (Highest Priority)
        # -------------------------------------------------------------
        seq_all = baseline.get("mean_sequence_lag_all")
        seq_all_std = baseline.get("std_sequence_lag_all", 0.0)
        has_tier1_flaw = False
        evidence_text = ""
        pre_metric = None
        pre_std = None

        if seq_all is not None and seq_all > cfg["tier1_sequence_lag_max_ms"]:
            has_tier1_flaw = True
            pre_metric = seq_all
            pre_std = seq_all_std
            evidence_text = (
                f"Across {n_tot} reviewed {shot_style} shots, kinetic transfer lag averaged "
                f"{seq_all:.1f} +/- {seq_all_std:.1f} ms (recommended starting threshold for {shot_style} is "
                f"{cfg['tier1_target_goal']}). [Measurement uncertainty: +/- 33.3 ms at 30 FPS]."
            )
            # Add descriptive make vs miss context only if both groups have >= 5 shots
            seq_mk = baseline.get("mean_sequence_lag_make")
            seq_ms = baseline.get("mean_sequence_lag_miss")
            if n_mk >= 5 and n_ms >= 5 and seq_ms is not None and seq_mk is not None:
                evidence_text += (
                    f" Descriptively, misses showed {seq_ms - seq_mk:+.1f} ms longer delay than makes "
                    f"({seq_ms:.1f} ms on misses vs {seq_mk:.1f} ms on makes)."
                )

        if has_tier1_flaw:
            cue = {
                "player_id": player_id,
                "baseline_id": baseline_id,
                "shot_style": shot_style,
                "priority_tier": 1,
                "targeted_flaw": "Kinetic Sequencing Delay",
                "cue_title": "Synchronize Knee Drive & Arm Extension",
                "biomechanical_evidence": evidence_text,
                "recommended_drill": cfg["tier1_drill"],
                "drill_reps": cfg["tier1_reps"],
                "target_metric_key": "sequence_lag_ms",
                "target_metric_name": "Kinetic Sequence Lag",
                "baseline_value": pre_metric,
                "pre_drill_metric_mean": pre_metric,
                "pre_drill_metric_std": pre_std,
                "pre_make_count": n_mk,
                "pre_total_count": n_tot,
                "target_goal": cfg["tier1_target_goal"],
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
        elbow_all_std = baseline.get("std_elbow_release_all", 0.0)
        has_tier2_flaw = False

        if elbow_all is not None and elbow_all < cfg["tier2_elbow_release_min_deg"]:
            has_tier2_flaw = True
            pre_metric = elbow_all
            pre_std = elbow_all_std
            evidence_text = (
                f"Across {n_tot} reviewed {shot_style} shots, release elbow extension averaged "
                f"{elbow_all:.1f} +/- {elbow_all_std:.1f} deg (recommended starting target for {shot_style} is "
                f"{cfg['tier2_target_goal']})."
            )
            elbow_mk = baseline.get("mean_elbow_release_make")
            elbow_ms = baseline.get("mean_elbow_release_miss")
            if n_mk >= 5 and n_ms >= 5 and elbow_mk is not None and elbow_ms is not None:
                evidence_text += (
                    f" Descriptively, makes averaged {elbow_mk - elbow_ms:+.1f} deg higher extension than misses "
                    f"({elbow_mk:.1f} deg on makes vs {elbow_ms:.1f} deg on misses)."
                )

        if has_tier2_flaw:
            cue = {
                "player_id": player_id,
                "baseline_id": baseline_id,
                "shot_style": shot_style,
                "priority_tier": 2,
                "targeted_flaw": "Incomplete Release Extension",
                "cue_title": "Full High-Release Arm Extension",
                "biomechanical_evidence": evidence_text,
                "recommended_drill": cfg["tier2_drill"],
                "drill_reps": cfg["tier2_reps"],
                "target_metric_key": "elbow_angle_release_3d",
                "target_metric_name": "3D Elbow Release Angle",
                "baseline_value": pre_metric,
                "pre_drill_metric_mean": pre_metric,
                "pre_drill_metric_std": pre_std,
                "pre_make_count": n_mk,
                "pre_total_count": n_tot,
                "target_goal": cfg["tier2_target_goal"],
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
        sway_all_std = baseline.get("std_torso_sway_all", 0.0)
        has_tier3_flaw = False

        if sway_all is not None and sway_all > cfg["tier3_torso_sway_max_deg"]:
            has_tier3_flaw = True
            pre_metric = sway_all
            pre_std = sway_all_std
            evidence_text = (
                f"Across {n_tot} reviewed {shot_style} shots, torso sway during dip averaged "
                f"{sway_all:.1f} +/- {sway_all_std:.1f} deg (recommended starting stability target is "
                f"{cfg['tier3_target_goal']})."
            )
            sway_mk = baseline.get("mean_torso_sway_make")
            sway_ms = baseline.get("mean_torso_sway_miss")
            if n_mk >= 5 and n_ms >= 5 and sway_mk is not None and sway_ms is not None:
                evidence_text += (
                    f" Descriptively, misses showed {sway_ms - sway_mk:+.1f} deg greater torso sway "
                    f"({sway_ms:.1f} deg on misses vs {sway_mk:.1f} deg on makes)."
                )

        if has_tier3_flaw:
            cue = {
                "player_id": player_id,
                "baseline_id": baseline_id,
                "shot_style": shot_style,
                "priority_tier": 3,
                "targeted_flaw": "Torso Sway / Base Instability",
                "cue_title": "Balanced Dip Posture & Solid Base",
                "biomechanical_evidence": evidence_text,
                "recommended_drill": cfg["tier3_drill"],
                "drill_reps": cfg["tier3_reps"],
                "target_metric_key": "torso_sway_deg",
                "target_metric_name": "Torso Sway",
                "baseline_value": pre_metric,
                "pre_drill_metric_mean": pre_metric,
                "pre_drill_metric_std": pre_std,
                "pre_make_count": n_mk,
                "pre_total_count": n_tot,
                "target_goal": cfg["tier3_target_goal"],
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
            "shot_style": shot_style,
            "priority_tier": 0,
            "targeted_flaw": "None",
            "cue_title": "Maintain Repeatable Form",
            "biomechanical_evidence": f"Your baseline mechanics across {n_tot} {shot_style} shots are within recommended parameters.",
            "recommended_drill": f"Game-Speed Spot-Up Shooting ({shot_style})",
            "drill_reps": 20,
            "status": "maintenance"
        }

    def evaluate_follow_up_set(
        self,
        player_id: str,
        remediation_id: str,
        follow_up_shots: List[Dict[str, Any]],
        drill_completed: bool = True,
        feedback_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a follow-up practice set (post-drill) against the active remediation target.
        Reports observational pre/post metric means +/- sample std devs, change in make percentage
        with explicit numerators and denominators, and drill completion status.
        Does NOT produce a combined 'improvement score' or claim causal certainty.
        """
        valid_shots = [s for s in follow_up_shots if s.get("tracking_confidence") == "SUFFICIENT"]
        n_follow = len(valid_shots)
        if n_follow < 3:
            return {
                "status": "INSUFFICIENT_FOLLOW_UP",
                "message": f"Need at least 3 valid shots to evaluate follow-up set (found {n_follow}).",
                "sample_size": n_follow
            }

        # Query remediation record from DB
        active_rem = self.db.get_active_remediation(player_id)
        if not active_rem or active_rem["remediation_id"] != remediation_id:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM remediations WHERE remediation_id = ?", (remediation_id,))
                row = cursor.fetchone()
                active_rem = dict(row) if row else None

        tier = active_rem.get("priority_tier", 1) if active_rem else 1
        pre_mean = active_rem.get("pre_drill_metric_mean") if active_rem else None
        pre_std = active_rem.get("pre_drill_metric_std", 0.0) if active_rem else 0.0
        pre_makes = active_rem.get("pre_make_count", 0) if active_rem else 0
        pre_total = active_rem.get("pre_total_count", 0) if active_rem else 0
        shot_style = active_rem.get("shot_style", "jump_shot") if active_rem else "jump_shot"

        # Calculate post-drill metric distributions
        if tier == 1:
            vals = [s["sequence_lag_ms"] for s in valid_shots if s.get("sequence_lag_ms") is not None]
            post_mean, post_std = _mean_and_std(vals)
            metric_name = "Kinetic sequence lag"
            unit = "ms"
            # lower lag is better
            delta = (post_mean - pre_mean) if (post_mean is not None and pre_mean is not None) else 0.0
            trend = "IMPROVED" if delta <= -15.0 else ("REGRESSED" if delta > 15.0 else "NEUTRAL")
        elif tier == 2:
            vals = [s["elbow_angle_release_3d"] for s in valid_shots if s.get("elbow_angle_release_3d") is not None]
            post_mean, post_std = _mean_and_std(vals)
            metric_name = "3D Elbow release angle"
            unit = "deg"
            # higher extension is better
            delta = (post_mean - pre_mean) if (post_mean is not None and pre_mean is not None) else 0.0
            trend = "IMPROVED" if delta >= 5.0 else ("REGRESSED" if delta < -5.0 else "NEUTRAL")
        else:
            vals = [s["torso_sway_deg"] for s in valid_shots if s.get("torso_sway_deg") is not None]
            post_mean, post_std = _mean_and_std(vals)
            metric_name = "Torso sway"
            unit = "deg"
            # lower sway is better
            delta = (post_mean - pre_mean) if (post_mean is not None and pre_mean is not None) else 0.0
            trend = "IMPROVED" if delta <= -2.0 else ("REGRESSED" if delta > 2.0 else "NEUTRAL")

        # Post-drill make percentage
        post_makes = sum(1 for s in valid_shots if s.get("outcome") == "make")
        post_total = n_follow
        pre_pct = (pre_makes / pre_total * 100.0) if pre_total > 0 else 0.0
        post_pct = (post_makes / post_total * 100.0) if post_total > 0 else 0.0
        make_pct_delta = post_pct - pre_pct

        # Construct purely observational summary statement
        summary = (
            f"Observed post-drill session ({n_follow} {shot_style} shots, drill completed: {drill_completed}): "
            f"{metric_name} changed by {delta:+.1f} {unit} "
            f"({pre_mean:.1f} +/- {pre_std:.1f} {unit} pre-drill -> {post_mean:.1f} +/- {post_std:.1f} {unit} post-drill). "
            f"Make percentage observed at {post_makes}/{post_total} ({post_pct:.1f}%) post-drill vs "
            f"{pre_makes}/{pre_total} ({pre_pct:.1f}%) pre-drill (change: {make_pct_delta:+.1f}%)."
        )

        # Update remediation record in DB
        self.db.update_remediation_status(
            remediation_id=remediation_id,
            status="completed",
            drill_completed=drill_completed,
            post_drill_metric_mean=post_mean,
            post_drill_metric_std=post_std,
            post_make_count=post_makes,
            post_total_count=post_total,
            feedback_notes=feedback_notes or summary
        )

        return {
            "status": "EVALUATION_COMPLETE",
            "remediation_id": remediation_id,
            "shot_style": shot_style,
            "sample_size_pre": pre_total,
            "sample_size_post": n_follow,
            "drill_completed": drill_completed,
            "trend": trend,
            "target_metric": metric_name,
            "pre_drill_mean": pre_mean,
            "pre_drill_std": pre_std,
            "post_drill_mean": post_mean,
            "post_drill_std": post_std,
            "delta": round(delta, 2),
            "pre_make_fraction": f"{pre_makes}/{pre_total}",
            "pre_make_pct": round(pre_pct, 1),
            "post_make_fraction": f"{post_makes}/{post_total}",
            "post_make_pct": round(post_pct, 1),
            "make_pct_delta": round(make_pct_delta, 1),
            "summary": summary,
            "observational_report": summary
        }
