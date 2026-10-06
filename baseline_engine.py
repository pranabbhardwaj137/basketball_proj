"""
baseline_engine.py - Personal Shot Lab Baseline and Make vs. Miss Association Engine.

Calculates player-specific baseline kinematic profiles and identifies statistically
meaningful differences between made and missed shots.
Adheres to strict scientific honesty: minimum N >= 5 sample gates, sample standard
deviations (± s) for continuous metrics, temporal quantization bounds for timing,
and descriptive associations (no causal certainty claims).
"""

from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
from shot_lab_db import ShotLabDB

MIN_BASELINE_SAMPLE_SIZE = 5

def _mean_and_std(values: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """Calculate sample mean and sample standard deviation (N-1 degrees of freedom)."""
    valid_vals = [v for v in values if v is not None and not math.isnan(v)]
    n = len(valid_vals)
    if n == 0:
        return None, None
    mean = sum(valid_vals) / n
    if n == 1:
        return round(mean, 2), 0.0
    variance = sum((x - mean) ** 2 for x in valid_vals) / (n - 1)
    std_dev = math.sqrt(variance)
    return round(mean, 2), round(std_dev, 2)


class BaselineEngine:
    def __init__(self, db: Optional[ShotLabDB] = None):
        self.db = db or ShotLabDB()

    def compute_baseline(
        self,
        player_id: str,
        camera_view: str = "frontal",
        shot_type: str = "catch_and_shoot",
        save_to_db: bool = True
    ) -> Dict[str, Any]:
        """
        Compute personal baseline from valid shots in the database for the given
        matched context (player_id, camera_view, shot_type).
        """
        shots = self.db.get_shots(
            player_id=player_id,
            camera_view=camera_view,
            shot_type=shot_type,
            min_confidence="SUFFICIENT"
        )

        n_total = len(shots)
        if n_total < MIN_BASELINE_SAMPLE_SIZE:
            return {
                "status": "INSUFFICIENT_SAMPLE",
                "player_id": player_id,
                "camera_view": camera_view,
                "shot_type": shot_type,
                "sample_size": n_total,
                "min_required": MIN_BASELINE_SAMPLE_SIZE,
                "message": f"Baseline Pending: Collected {n_total}/{MIN_BASELINE_SAMPLE_SIZE} valid shots for {camera_view} {shot_type}."
            }

        makes = [s for s in shots if s["outcome"] == "make"]
        misses = [s for s in shots if s["outcome"] == "miss"]
        unknowns = [s for s in shots if s["outcome"] == "unknown"]

        # Extract kinematic metric series
        elbow_makes = [s["elbow_angle_release_3d"] for s in makes]
        elbow_misses = [s["elbow_angle_release_3d"] for s in misses]
        elbow_all = [s["elbow_angle_release_3d"] for s in shots]

        seq_makes = [s["sequence_lag_ms"] for s in makes]
        seq_misses = [s["sequence_lag_ms"] for s in misses]
        seq_all = [s["sequence_lag_ms"] for s in shots]

        knee_makes = [s["knee_angle_dip_3d"] for s in makes]
        knee_misses = [s["knee_angle_dip_3d"] for s in misses]
        knee_all = [s["knee_angle_dip_3d"] for s in shots]

        sway_makes = [s["torso_sway_deg"] for s in makes]
        sway_misses = [s["torso_sway_deg"] for s in misses]
        sway_all = [s["torso_sway_deg"] for s in shots]

        mean_elbow_mk, std_elbow_mk = _mean_and_std(elbow_makes)
        mean_elbow_ms, std_elbow_ms = _mean_and_std(elbow_misses)
        mean_elbow_all, std_elbow_all = _mean_and_std(elbow_all)

        mean_seq_mk, std_seq_mk = _mean_and_std(seq_makes)
        mean_seq_ms, std_seq_ms = _mean_and_std(seq_misses)
        mean_seq_all, std_seq_all = _mean_and_std(seq_all)

        mean_knee_mk, std_knee_mk = _mean_and_std(knee_makes)
        mean_knee_ms, std_knee_ms = _mean_and_std(knee_misses)
        mean_knee_all, std_knee_all = _mean_and_std(knee_all)

        mean_sway_mk, std_sway_mk = _mean_and_std(sway_makes)
        mean_sway_ms, std_sway_ms = _mean_and_std(sway_misses)
        mean_sway_all, std_sway_all = _mean_and_std(sway_all)

        baseline_dict = {
            "player_id": player_id,
            "camera_view": camera_view,
            "shot_type": shot_type,
            "sample_size_makes": len(makes),
            "sample_size_misses": len(misses),
            "sample_size_unknowns": len(unknowns),
            "sample_size_total": n_total,
            
            # Elbow release angle (deg)
            "mean_elbow_release_make": mean_elbow_mk,
            "std_elbow_release_make": std_elbow_mk,
            "mean_elbow_release_miss": mean_elbow_ms,
            "std_elbow_release_miss": std_elbow_ms,
            "mean_elbow_release_all": mean_elbow_all,
            "std_elbow_release_all": std_elbow_all,
            
            # Kinetic sequence lag (ms)
            "mean_sequence_lag_make": mean_seq_mk,
            "std_sequence_lag_make": std_seq_mk,
            "mean_sequence_lag_miss": mean_seq_ms,
            "std_sequence_lag_miss": std_seq_ms,
            "mean_sequence_lag_all": mean_seq_all,
            "std_sequence_lag_all": std_seq_all,
            
            # Knee dip angle (deg)
            "mean_knee_dip_make": mean_knee_mk,
            "std_knee_dip_make": std_knee_mk,
            "mean_knee_dip_miss": mean_knee_ms,
            "std_knee_dip_miss": std_knee_ms,
            "mean_knee_dip_all": mean_knee_all,
            "std_knee_dip_all": std_knee_all,

            # Torso sway (deg)
            "mean_torso_sway_make": mean_sway_mk,
            "std_torso_sway_make": std_sway_mk,
            "mean_torso_sway_miss": mean_sway_ms,
            "std_torso_sway_miss": std_sway_ms,
            "mean_torso_sway_all": mean_sway_all,
            "std_torso_sway_all": std_sway_all,
        }

        # Generate descriptive associations report
        associations = self._generate_descriptive_associations(baseline_dict)
        baseline_dict["descriptive_associations"] = associations

        if save_to_db:
            base_id = self.db.save_baseline(baseline_dict)
            baseline_dict["baseline_id"] = base_id

        baseline_dict["status"] = "VALID_BASELINE"
        return baseline_dict

    def _generate_descriptive_associations(self, b: Dict[str, Any]) -> List[str]:
        """Format make vs. miss observations using strictly descriptive language."""
        statements = []
        n_mk = b["sample_size_makes"]
        n_ms = b["sample_size_misses"]

        if n_mk >= 2 and n_ms >= 2:
            # 1. Elbow release angle comparison
            if b["mean_elbow_release_make"] is not None and b["mean_elbow_release_miss"] is not None:
                diff_elbow = b["mean_elbow_release_make"] - b["mean_elbow_release_miss"]
                if abs(diff_elbow) >= 4.0:
                    dir_str = "higher" if diff_elbow > 0 else "lower"
                    statements.append(
                        f"In your {n_mk} makes vs {n_ms} misses, makes were associated with {abs(diff_elbow):.1f} deg {dir_str} "
                        f"elbow extension at release ({b['mean_elbow_release_make']:.1f} +/- {b['std_elbow_release_make']:.1f} deg vs "
                        f"{b['mean_elbow_release_miss']:.1f} +/- {b['std_elbow_release_miss']:.1f} deg)."
                    )

            # 2. Kinetic sequencing lag comparison
            if b["mean_sequence_lag_make"] is not None and b["mean_sequence_lag_miss"] is not None:
                diff_lag = b["mean_sequence_lag_miss"] - b["mean_sequence_lag_make"]
                if abs(diff_lag) >= 25.0:
                    dir_str = "tighter/smoother" if diff_lag > 0 else "longer"
                    statements.append(
                        f"Makes were associated with {abs(diff_lag):.1f} ms {dir_str} kinetic energy transfer lag "
                        f"({b['mean_sequence_lag_make']:.1f} +/- {b['std_sequence_lag_make']:.1f} ms vs "
                        f"{b['mean_sequence_lag_miss']:.1f} +/- {b['std_sequence_lag_miss']:.1f} ms). "
                        f"[Note: Video frame quantization uncertainty is +/- 33.3 ms at 30 FPS]."
                    )

            # 3. Torso sway balance comparison
            if b["mean_torso_sway_make"] is not None and b["mean_torso_sway_miss"] is not None:
                diff_sway = b["mean_torso_sway_miss"] - b["mean_torso_sway_make"]
                if diff_sway >= 3.0:
                    statements.append(
                        f"Misses showed {diff_sway:.1f} deg greater torso sway during the shot "
                        f"({b['mean_torso_sway_miss']:.1f} +/- {b['std_torso_sway_miss']:.1f} deg on misses vs "
                        f"{b['mean_torso_sway_make']:.1f} +/- {b['std_torso_sway_make']:.1f} deg on makes)."
                    )
        else:
            statements.append(
                f"Baseline established across {b['sample_size_total']} shots ({n_mk} makes, {n_ms} misses, {b['sample_size_unknowns']} unknown). "
                f"Need at least 2 makes and 2 misses to report make-vs-miss contrast."
            )

        return statements
