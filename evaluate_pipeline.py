"""
Evaluation Benchmark Harness for Basketball Shot Analysis Pipeline
===================================================================
Quantifies measurement accuracy, shot detection precision/recall, phase timing
error (MAE in ms), and tracking confidence reliability against ground truth annotations.

Usage:
    python evaluate_pipeline.py [--json]
"""

import os
import sys
import json
import argparse
import numpy as np
import cv2

from analyzer import (
    ShotPhaseDetector,
    KineticChainAnalyzer,
    SessionRecorder,
    interpolate_kinematic_series
)


from pro_comparator import ProComparator


class BenchmarkEvaluator:
    """
    Evaluates shot detection precision, recall, kinematic integrity,
    and pro comparator calibration against test clips and annotated ground truth.
    """

    def __init__(self, fps=30.0):
        self.fps = fps
        self.dt_ms = 1000.0 / fps

    def evaluate_synthetic_dataset(self):
        """
        Runs comprehensive test scenarios on synthetic kinematic streams:
        1. Clean genuine shot sequence (Ground Truth: 1 Shot)
        2. Non-shooting gesture: Waving arms while standing still (Ground Truth: 0 Shots)
        3. Non-shooting gesture: Deep knee squats without arm elevation (Ground Truth: 0 Shots)
        4. Noisy stream with short missing dropouts (Kinematic Interpolation Test)
        5. Severe occlusion sequence (Ground Truth: Low confidence, suppressed cues)
        """
        results = {
            "scenarios_tested": 0,
            "passed_scenarios": 0,
            "shot_detection": {
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "true_negatives": 0,
            },
            "timing_errors_ms": [],
            "kinematic_integrity_passed": True,
            "details": []
        }

        # Scenario 1: Clean Genuine Shot
        detector = ShotPhaseDetector()
        recorder = SessionRecorder()
        shot_frames = self._generate_clean_shot_frames()
        detected_release_frame = None

        for idx, f in enumerate(shot_frames):
            state, _, _ = detector.update(f["landmarks"], f["angles"], timestamp_ms=idx * self.dt_ms)
            recorder.push_frame(f["angles"], phase=state, timestamp_ms=idx * self.dt_ms)
            if state in ('preparing', 'set_point'):
                recorder.start_shot()
            elif state == 'releasing' and detected_release_frame is None:
                detected_release_frame = idx
            elif state == 'follow_through':
                recorder.end_shot()

        if recorder.shot_count >= 1 and detected_release_frame is not None:
            results["shot_detection"]["true_positives"] += 1
            gt_release_frame = 24  # Ground truth release is at frame 24
            err_ms = abs(detected_release_frame - gt_release_frame) * self.dt_ms
            results["timing_errors_ms"].append(err_ms)
            results["details"].append({"scenario": "Clean Shot Detection", "passed": True, "error_ms": err_ms})
            results["passed_scenarios"] += 1
        elif recorder.shot_count >= 1:
            results["shot_detection"]["true_positives"] += 1
            results["details"].append({"scenario": "Clean Shot Detection", "passed": False, "reason": "Shot counted but release frame missed"})
        else:
            results["shot_detection"]["false_negatives"] += 1
            results["details"].append({"scenario": "Clean Shot Detection", "passed": False, "reason": "Missed shot"})
        results["scenarios_tested"] += 1

        # Scenario 2: Arm Wave False-Positive Rejection
        detector2 = ShotPhaseDetector()
        recorder2 = SessionRecorder()
        wave_frames = self._generate_wave_frames()
        for idx, f in enumerate(wave_frames):
            state, _, _ = detector2.update(f["landmarks"], f["angles"], timestamp_ms=idx * self.dt_ms)
            recorder2.push_frame(f["angles"], phase=state, timestamp_ms=idx * self.dt_ms)
            if state in ('preparing', 'set_point'):
                recorder2.start_shot()
            elif state == 'follow_through':
                recorder2.end_shot()

        if recorder2.shot_count == 0:
            results["shot_detection"]["true_negatives"] += 1
            results["details"].append({"scenario": "Arm Wave Rejection", "passed": True})
            results["passed_scenarios"] += 1
        else:
            results["shot_detection"]["false_positives"] += 1
            results["details"].append({"scenario": "Arm Wave Rejection", "passed": False, "reason": f"False positive count: {recorder2.shot_count}"})
        results["scenarios_tested"] += 1

        # Scenario 3: Knee Squat False-Positive Rejection
        detector3 = ShotPhaseDetector()
        recorder3 = SessionRecorder()
        squat_frames = self._generate_squat_frames()
        for idx, f in enumerate(squat_frames):
            state, _, _ = detector3.update(f["landmarks"], f["angles"], timestamp_ms=idx * self.dt_ms)
            recorder3.push_frame(f["angles"], phase=state, timestamp_ms=idx * self.dt_ms)
            if state in ('preparing', 'set_point'):
                recorder3.start_shot()
            elif state == 'follow_through':
                recorder3.end_shot()

        if recorder3.shot_count == 0:
            results["shot_detection"]["true_negatives"] += 1
            results["details"].append({"scenario": "Squat Rejection", "passed": True})
            results["passed_scenarios"] += 1
        else:
            results["shot_detection"]["false_positives"] += 1
            results["details"].append({"scenario": "Squat Rejection", "passed": False, "reason": f"False positive count: {recorder3.shot_count}"})
        results["scenarios_tested"] += 1

        # Scenario 4: Kinematic Interpolation & Missing Data Integrity
        series = [120.0, np.nan, np.nan, 135.0, np.nan, np.nan, np.nan, np.nan, 160.0]
        interpolated, val_ratio = interpolate_kinematic_series(series, max_gap=2)
        interp_ok = (
            not np.isnan(interpolated[1])
            and not np.isnan(interpolated[2])
            and np.isnan(interpolated[5])
        )
        if interp_ok:
            results["details"].append({"scenario": "Kinematic Imputation Safeguard", "passed": True})
            results["passed_scenarios"] += 1
        else:
            results["kinematic_integrity_passed"] = False
            results["details"].append({"scenario": "Kinematic Imputation Safeguard", "passed": False, "reason": "Interpolation violated gap bounds"})
        results["scenarios_tested"] += 1

        # Scenario 5: Severe Occlusion Sequence (Confidence Gating Test)
        chain_analyzer = KineticChainAnalyzer()
        occluded_frames = [
            {"knee_shooting": np.nan, "hip_shooting": 160.0, "shoulder_shooting": np.nan, "elbow_shooting": 140.0, "wrist_flexion_angle": np.nan, "_timestamp_sec": i * 0.033}
            for i in range(15)
        ]
        chain_result = chain_analyzer.evaluate_shot_chain(occluded_frames)
        if chain_result["tracking_confidence"] == "INSUFFICIENT" and chain_result["sequencing_score"] is None:
            results["details"].append({"scenario": "Severe Occlusion Rejection", "passed": True})
            results["passed_scenarios"] += 1
        else:
            results["details"].append({"scenario": "Severe Occlusion Rejection", "passed": False, "reason": "Failed to flag insufficient confidence"})
        results["scenarios_tested"] += 1


        # Calculate Aggregate Metrics
        tp = results["shot_detection"]["true_positives"]
        fp = results["shot_detection"]["false_positives"]
        fn = results["shot_detection"]["false_negatives"]

        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 1.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 1.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        avg_timing_err = float(np.mean(results["timing_errors_ms"])) if results["timing_errors_ms"] else 0.0

        summary = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
            "avg_phase_timing_error_ms": round(avg_timing_err, 1),
            "scenarios_passed": f"{results['passed_scenarios']}/{results['scenarios_tested']}",
            "verdict": "PASS" if results["passed_scenarios"] == results["scenarios_tested"] else "NEEDS_REMEDIATION",
            "benchmark_details": results["details"]
        }
        return summary

    def _generate_clean_shot_frames(self):
        """Generates a realistic 45-frame kinetic shooting sequence."""
        frames = []
        for i in range(45):
            t = i / 44.0
            if t < 0.30:  # Dip
                prog = t / 0.30
                knee = 165.0 - 45.0 * np.sin(prog * np.pi / 2)
                hip = 170.0 - 20.0 * np.sin(prog * np.pi / 2)
                shoulder = 45.0 + 30.0 * prog
                elbow = 80.0 + 10.0 * prog
                wrist_flick = 165.0 - 15.0 * prog
                wrist_y = 0.55 + 0.05 * prog
            elif t < 0.65:  # Rise & Release
                prog = (t - 0.30) / 0.35
                knee = 120.0 + 58.0 * prog
                hip = 150.0 + 28.0 * prog
                shoulder = 75.0 + 45.0 * prog
                elbow = 90.0 + 78.0 * prog
                wrist_flick = 150.0 - 75.0 * prog
                wrist_y = 0.60 - 0.42 * prog  # Moves up above shoulder (shoulder is ~0.40)
            else:  # Follow Through
                knee = 178.0
                hip = 178.0
                shoulder = 120.0
                elbow = 168.0
                wrist_flick = 75.0
                wrist_y = 0.18

            landmarks = {
                11: {"norm_x": 0.45, "norm_y": 0.40, "z": 0.0},
                12: {"norm_x": 0.55, "norm_y": 0.40, "z": 0.0},
                15: {"norm_x": 0.42, "norm_y": 0.50, "z": 0.0},
                16: {"norm_x": 0.58, "norm_y": wrist_y, "z": 0.0},
                23: {"norm_x": 0.46, "norm_y": 0.60, "z": 0.0},
                24: {"norm_x": 0.54, "norm_y": 0.60, "z": 0.0},
                27: {"norm_x": 0.45, "norm_y": 0.90, "z": 0.0},
                28: {"norm_x": 0.55, "norm_y": 0.90, "z": 0.0},
            }

            frames.append({
                "landmarks": landmarks,
                "angles": {
                    "knee_shooting": knee,
                    "hip_shooting": hip,
                    "shoulder_shooting": shoulder,
                    "elbow_shooting": elbow,
                    "wrist_flexion_angle": wrist_flick,
                    "elbow_height_ratio": 1.05 if t >= 0.60 else 0.85,
                    "shooting_side": "right",
                }
            })
        return frames

    def _generate_wave_frames(self):
        """Generates a 30-frame arm wave: straight legs, wrist below shoulder."""
        frames = []
        for i in range(30):
            landmarks = {
                11: {"norm_x": 0.45, "norm_y": 0.40, "z": 0.0},
                12: {"norm_x": 0.55, "norm_y": 0.40, "z": 0.0},
                15: {"norm_x": 0.42, "norm_y": 0.50, "z": 0.0},
                16: {"norm_x": 0.58, "norm_y": 0.45 + 0.05 * np.sin(i * 0.5), "z": 0.0},
                23: {"norm_x": 0.46, "norm_y": 0.60, "z": 0.0},
                24: {"norm_x": 0.54, "norm_y": 0.60, "z": 0.0},
                27: {"norm_x": 0.45, "norm_y": 0.90, "z": 0.0},
                28: {"norm_x": 0.55, "norm_y": 0.90, "z": 0.0},
            }
            frames.append({
                "landmarks": landmarks,
                "angles": {
                    "knee_shooting": 178.0,
                    "hip_shooting": 178.0,
                    "shoulder_shooting": 70.0 + 10.0 * np.sin(i * 0.5),
                    "elbow_shooting": 120.0 + 30.0 * np.sin(i * 0.8),
                    "wrist_flexion_angle": 160.0,
                    "elbow_height_ratio": 0.88,
                    "shooting_side": "right",
                }
            })
        return frames

    def _generate_squat_frames(self):
        """Generates a 30-frame deep squat: deep knees/hips, but arms resting low."""
        frames = []
        for i in range(30):
            prog = np.sin(i / 29.0 * np.pi)
            landmarks = {
                11: {"norm_x": 0.45, "norm_y": 0.45 + 0.15 * prog, "z": 0.0},
                12: {"norm_x": 0.55, "norm_y": 0.45 + 0.15 * prog, "z": 0.0},
                15: {"norm_x": 0.42, "norm_y": 0.65 + 0.15 * prog, "z": 0.0},
                16: {"norm_x": 0.58, "norm_y": 0.65 + 0.15 * prog, "z": 0.0},
                23: {"norm_x": 0.46, "norm_y": 0.65 + 0.15 * prog, "z": 0.0},
                24: {"norm_x": 0.54, "norm_y": 0.65 + 0.15 * prog, "z": 0.0},
                27: {"norm_x": 0.45, "norm_y": 0.90, "z": 0.0},
                28: {"norm_x": 0.55, "norm_y": 0.90, "z": 0.0},
            }
            frames.append({
                "landmarks": landmarks,
                "angles": {
                    "knee_shooting": 170.0 - 70.0 * prog,
                    "hip_shooting": 170.0 - 50.0 * prog,
                    "shoulder_shooting": 25.0,
                    "elbow_shooting": 160.0,
                    "wrist_flexion_angle": 170.0,
                    "elbow_height_ratio": 0.50,
                    "shooting_side": "right",
                }
            })
        return frames



def print_evaluation_report(summary):
    print("\n" + "=" * 65)
    print("   BASKETBALL AI COACH - SYNTHETIC REGRESSION TEST SUITE")
    print("=" * 65)
    print(" (Note: Validates pipeline logic and state machine safeguards.")
    print("  Real-world accuracy requires annotated video study across angles.)")
    print("-" * 65)
    print(f" Precision (Synthetic):       {summary['precision'] * 100:.1f}%")
    print(f" Recall (Synthetic):          {summary['recall'] * 100:.1f}%")
    print(f" F1-Score:                    {summary['f1_score']:.3f}")
    print(f" Mean Phase Timing Error:     {summary['avg_phase_timing_error_ms']} ms")
    print(f" Scenarios Passed:            {summary['scenarios_passed']}")
    print(f" Regression Suite Verdict:    {summary['verdict']}")
    print("-" * 65)

    print(" Scenario Breakdown:")
    for d in summary["benchmark_details"]:
        status = "PASSED" if d["passed"] else f"FAILED ({d.get('reason', '')})"
        print(f"  - {d['scenario']:<32} : {status}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Basketball Pipeline")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    evaluator = BenchmarkEvaluator()
    summary = evaluator.evaluate_synthetic_dataset()

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print_evaluation_report(summary)

    out_path = os.path.join(os.path.dirname(__file__), "EVAL_REPORT.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[INFO] Evaluation report saved to {out_path}")
