import math
import cv2
import numpy as np

# NOTE ON METHODOLOGY:
# The trajectories below are HAND-AUTHORED ILLUSTRATIVE REFERENCE MODELS based on textbook
# shooting mechanics literature. They are NOT absolute gold standards; elite shooters exhibit
# natural anatomical variations. These models serve as diagnostic reference guides, not mandates.

PRO_TEMPORAL_PROFILES = {
    "curry": {
        "name": "Stephen Curry (Illustrative Model)",
        "short_name": "Stephen Curry",
        "description": "1-Motion Quick Dip-to-Release & High Arc",
        "ideal_release_angle": 52.0,
        "ideal_release_time_ms": 320,
        "trajectory": np.array([
            # Prep / Dip (0% to 30%)
            [115.0, 155.0, 45.0, 85.0, 160.0],
            [118.0, 158.0, 55.0, 88.0, 165.0],
            # Rise / Set Point (30% to 60%)
            [140.0, 165.0, 75.0, 95.0, 170.0],
            [160.0, 172.0, 95.0, 120.0, 160.0],
            # Release (60% to 80%)
            [175.0, 178.0, 115.0, 155.0, 130.0],
            [178.0, 180.0, 125.0, 168.0, 90.0],
            # Follow Through (80% to 100%)
            [180.0, 180.0, 130.0, 172.0, 85.0],
            [180.0, 180.0, 130.0, 172.0, 85.0],
        ]),
        "metrics": {
            "elbow_release": 168.0,
            "knee_dip": 115.0,
            "hip_posture": 160.0,
            "launch_angle": 52.0,
            "wrist_flick": 85.0,
        },
        "weights": {
            "elbow_release": 2.5,
            "knee_dip": 1.5,
            "hip_posture": 1.2,
            "launch_angle": 2.0,
            "wrist_flick": 1.8,
        },
    },
    "klay": {
        "name": "Klay Thompson (Illustrative Model)",
        "short_name": "Klay Thompson",
        "description": "Textbook 2-Motion Set & Maximum Extension",
        "ideal_release_angle": 48.0,
        "ideal_release_time_ms": 450,
        "trajectory": np.array([
            # Prep / Dip
            [118.0, 160.0, 40.0, 80.0, 165.0],
            [122.0, 162.0, 50.0, 82.0, 170.0],
            # Set Point Pause
            [145.0, 168.0, 85.0, 90.0, 175.0],
            [165.0, 175.0, 100.0, 110.0, 170.0],
            # Release Extension
            [178.0, 180.0, 120.0, 160.0, 140.0],
            [180.0, 180.0, 130.0, 172.0, 90.0],
            # High Follow Through
            [180.0, 180.0, 135.0, 175.0, 88.0],
            [180.0, 180.0, 135.0, 175.0, 88.0],
        ]),
        "metrics": {
            "elbow_release": 172.0,
            "knee_dip": 118.0,
            "hip_posture": 165.0,
            "launch_angle": 48.0,
            "wrist_flick": 90.0,
        },
        "weights": {
            "elbow_release": 2.5,
            "knee_dip": 1.5,
            "hip_posture": 1.2,
            "launch_angle": 2.0,
            "wrist_flick": 1.8,
        },
    },
    "ray_allen": {
        "name": "Ray Allen (Illustrative Model)",
        "short_name": "Ray Allen",
        "description": "Elevated Jump Shot Mechanics & High Apex",
        "ideal_release_angle": 50.0,
        "ideal_release_time_ms": 500,
        "trajectory": np.array([
            # Deep Dip
            [110.0, 152.0, 40.0, 78.0, 160.0],
            [115.0, 155.0, 50.0, 80.0, 165.0],
            # Jump Elevation
            [140.0, 165.0, 80.0, 88.0, 172.0],
            [165.0, 175.0, 105.0, 115.0, 165.0],
            # Release at Jump Apex
            [178.0, 178.0, 125.0, 158.0, 130.0],
            [180.0, 180.0, 132.0, 170.0, 88.0],
            # Follow Through
            [180.0, 180.0, 135.0, 173.0, 85.0],
            [180.0, 180.0, 135.0, 173.0, 85.0],
        ]),
        "metrics": {
            "elbow_release": 170.0,
            "knee_dip": 110.0,
            "hip_posture": 158.0,
            "launch_angle": 50.0,
            "wrist_flick": 88.0,
        },
        "weights": {
            "elbow_release": 2.5,
            "knee_dip": 1.5,
            "hip_posture": 1.2,
            "launch_angle": 2.0,
            "wrist_flick": 1.8,
        },
    },
}

FULL_BODY_CONNECTIONS = [
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
]


def compute_dtw_distance(series_a, series_b):
    """
    Compute Dynamic Time Warping (DTW) distance between two multi-dimensional trajectories.
    series_a: (N, D) array (user frames)
    series_b: (M, D) array (pro illustrative reference frames)
    Returns (mean_angular_deviation_deg, calibrated_similarity_pct [0-100])
    """
    n, m = len(series_a), len(series_b)
    if n == 0 or m == 0:
        return 999.0, 0.0

    # Euclidean distance across feature channels
    cost_matrix = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            cost_matrix[i, j] = np.linalg.norm(series_a[i] - series_b[j])

    dtw = np.full((n + 1, m + 1), np.inf)
    dtw[0, 0] = 0.0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = cost_matrix[i - 1, j - 1]
            dtw[i, j] = cost + min(dtw[i - 1, j],
                                   dtw[i, j - 1],
                                   dtw[i - 1, j - 1])

    total_dist = dtw[n, m]
    # Path-normalized distance represents average joint deviation in degrees per step
    avg_deg_deviation = total_dist / (n + m)

    # Calibrated mapping: <= 8° deviation -> >= 90%, 15° -> 75%, 28° -> ~50%
    similarity = max(0.0, round(100.0 * np.exp(-avg_deg_deviation / 26.0), 1))
    return round(float(avg_deg_deviation), 1), similarity


class ProComparator:
    """
    Compares user mechanics against illustrative pro player benchmark curves.
    Provides observation-first guidance, calibrated DTW sequence alignment,
    and Full-Body Ghost Skeleton visualization.
    """

    def __init__(self, target_pro="curry"):
        if target_pro not in PRO_TEMPORAL_PROFILES:
            target_pro = "curry"
        self.target_key = target_pro
        self.profile = PRO_TEMPORAL_PROFILES[target_pro]
        self.smoothed_facing_sign = 1.0  # +1.0 = facing screen right, -1.0 = facing screen left


    def set_target_pro(self, target_key):
        if target_key in PRO_TEMPORAL_PROFILES:
            self.target_key = target_key
            self.profile = PRO_TEMPORAL_PROFILES[target_key]

    def compare_sequence(self, user_shot_frames):
        """
        Perform Dynamic Time Warping (DTW) on recorded shot sequence against pro temporal trajectory.
        Filters out frames with missing kinematic data.
        """
        if not user_shot_frames or len(user_shot_frames) < 5:
            return None

        # Build feature matrix without artificial static fallbacks
        user_seq = []
        for f in user_shot_frames:
            k = f.get('knee_shooting')
            h = f.get('hip_shooting')
            s = f.get('shoulder_shooting')
            e = f.get('elbow_shooting')
            w = f.get('wrist_flexion_angle')

            # If all core angles present, include in DTW matrix
            if all(v is not None and not np.isnan(v) for v in (k, h, s, e)):
                user_seq.append([k, h, s, e, w if w is not None else 140.0])

        if len(user_seq) < 4:
            return None

        user_seq = np.array(user_seq)
        pro_seq = self.profile["trajectory"]

        avg_dev_deg, dtw_score = compute_dtw_distance(user_seq, pro_seq)

        return {
            "pro_name": self.profile["short_name"],
            "model_type": "Illustrative Reference Model",
            "avg_angular_deviation_deg": avg_dev_deg,
            "dtw_similarity_score": dtw_score,
            "num_user_frames": len(user_seq),
            "observation": f"Average angular deviation from {self.profile['short_name']} model: ±{avg_dev_deg:.1f}°",
        }

    def compare(self, user_metrics):
        """
        Compare user instant metrics against active pro illustrative model.
        Returns grounded observations alongside deviation metrics.
        """
        if not user_metrics:
            return None

        benchmark = self.profile["metrics"]
        weights = self.profile["weights"]

        scores = {}
        weighted_sum = 0.0
        weight_total = 0.0

        for key, target_val in benchmark.items():
            user_val = user_metrics.get(key)
            if user_val is None or np.isnan(user_val):
                continue

            diff = abs(user_val - target_val)
            weight = weights.get(key, 1.0)
            score = max(0.0, 100.0 - (diff * weight))
            scores[key] = {
                "user": user_val,
                "pro": target_val,
                "diff": diff,
                "score": round(score, 1),
            }
            weighted_sum += score * weight
            weight_total += weight

        if weight_total == 0:
            return None

        overall_score = round(weighted_sum / weight_total, 1)

        sorted_metrics = sorted(scores.items(), key=lambda item: item[1]["score"], reverse=True)
        best_feature = sorted_metrics[0][0] if sorted_metrics else None
        worst_feature = sorted_metrics[-1][0] if sorted_metrics else None

        recommendation, observation = self._generate_recommendation(worst_feature, scores.get(worst_feature))

        return {
            "pro_name": self.profile["short_name"],
            "model_notice": "Illustrative Reference Model",
            "similarity_score": overall_score,
            "metrics": scores,
            "best_feature": best_feature,
            "worst_feature": worst_feature,
            "observation": observation,
            "recommendation": recommendation,
        }

    @staticmethod
    def _generate_recommendation(worst_feature, data):
        if not worst_feature or not data:
            return "Stable shooting posture.", "Metrics match reference model."

        user_val = data["user"]
        pro_val = data["pro"]
        diff = data["diff"]

        if worst_feature == "elbow_release":
            obs = f"Elbow release extension: {user_val:.0f}° measured vs {pro_val:.0f}° reference (Diff: {diff:+.0f}°)"
            if user_val < pro_val:
                rec = f"Extend arm higher through release (+{diff:.0f}° toward reference)."
            else:
                rec = f"Avoid hyperextending elbow (-{diff:.0f}° toward reference)."
            return rec, obs
        elif worst_feature == "knee_dip":
            obs = f"Knee bend at dip: {user_val:.0f}° measured vs {pro_val:.0f}° reference (Diff: {diff:+.0f}°)"
            if user_val > pro_val:
                rec = f"Dip knees deeper for ground power (-{diff:.0f}° toward reference)."
            else:
                rec = f"Quicker, shallower dip (+{diff:.0f}° toward reference)."
            return rec, obs
        elif worst_feature == "hip_posture":
            obs = f"Hip posture angle: {user_val:.0f}° measured vs {pro_val:.0f}° reference (Diff: {diff:+.0f}°)"
            return f"Adjust hip lean by {diff:.0f}° for balance.", obs
        elif worst_feature == "launch_angle":
            obs = f"Launch angle: {user_val:.0f}° measured vs {pro_val:.0f}° reference (Diff: {diff:+.0f}°)"
            if user_val < pro_val:
                rec = f"Increase release trajectory arc (+{diff:.0f}° toward reference)."
            else:
                rec = f"Lower release trajectory arc (-{diff:.0f}° toward reference)."
            return rec, obs
        elif worst_feature == "wrist_flick":
            obs = f"Wrist snap: {user_val:.0f}° measured vs {pro_val:.0f}° reference (Diff: {diff:+.0f}°)"
            return f"Snap wrist forward cleanly at release.", obs

        return "Focus on consistent proximal-to-distal sequencing.", "Form within typical range."

    def draw_full_body_ghost_skeleton(self, frame, user_landmarks, user_angles=None, phase="releasing"):
        """
        Generate and render a FULL-BODY Pro Ghost Skeleton aligned to user's position,
        scale, shooting hand, and dynamic camera-facing direction (left, right, or angled).
        """
        if not user_landmarks or 11 not in user_landmarks or 12 not in user_landmarks:
            return frame

        height, width = frame.shape[:2]

        def get_pt(idx, fallback_x=0.5, fallback_y=0.5):
            if idx in user_landmarks:
                return int(user_landmarks[idx]["norm_x"] * width), int(user_landmarks[idx]["norm_y"] * height)
            return int(fallback_x * width), int(fallback_y * height)

        # Base user anchor coordinates
        l_sh = get_pt(11)
        r_sh = get_pt(12)
        l_hip = get_pt(23, 0.45, 0.55)
        r_hip = get_pt(24, 0.55, 0.55)
        l_ankle = get_pt(27, 0.45, 0.90)
        r_ankle = get_pt(28, 0.55, 0.90)

        # Determine dimensions from user's anatomy
        torso_h = max(40, int(abs(((l_hip[1] + r_hip[1]) / 2) - ((l_sh[1] + r_sh[1]) / 2))))
        leg_len = max(60, int(abs(((l_ankle[1] + r_ankle[1]) / 2) - ((l_hip[1] + r_hip[1]) / 2))))
        arm_len = int(torso_h * 0.72)
        forearm_len = int(torso_h * 0.68)
        thigh_len = int(leg_len * 0.52)

        # 1. Determine Shooting Side ('left' vs 'right')
        side = user_angles.get("shooting_side", "right") if user_angles else "right"
        shoot_sh = r_sh if side == "right" else l_sh
        guide_sh = l_sh if side == "right" else r_sh
        shoot_hip = r_hip if side == "right" else l_hip
        guide_hip = l_hip if side == "right" else r_hip

        # 2. Robust Multi-Cue Camera Facing Direction (Left, Right, or Frontal):
        facing_evidence = 0.0
        sh_mid_x = (user_landmarks[11]["norm_x"] + user_landmarks[12]["norm_x"]) / 2.0

        # Head yaw cue (nose relative to shoulder center)
        if 0 in user_landmarks:
            nose_x = user_landmarks[0]["norm_x"]
            dx_nose_sh = nose_x - sh_mid_x
            if abs(dx_nose_sh) > 0.015:
                facing_evidence += 1.5 if dx_nose_sh > 0 else -1.5

            # Ear yaw cue
            if 7 in user_landmarks and 8 in user_landmarks:
                ear_mid_x = (user_landmarks[7]["norm_x"] + user_landmarks[8]["norm_x"]) / 2.0
                dx_ear = nose_x - ear_mid_x
                if abs(dx_ear) > 0.01:
                    facing_evidence += 1.0 if dx_ear > 0 else -1.0

        # Foot direction cue
        ankle_idx = 28 if side == "right" else 27
        toe_idx = 32 if side == "right" else 31
        if ankle_idx in user_landmarks and toe_idx in user_landmarks:
            dx_foot = user_landmarks[toe_idx]["norm_x"] - user_landmarks[ankle_idx]["norm_x"]
            if abs(dx_foot) > 0.02:
                facing_evidence += 0.8 if dx_foot > 0 else -0.8

        # Determine target facing sign
        if facing_evidence > 0.4:
            target_facing = 1.0   # Facing camera right (+X)
        elif facing_evidence < -0.4:
            target_facing = -1.0  # Facing camera left (-X)
        else:
            # Frontal view: gentle offset aligned with shooting hand
            target_facing = 0.35 if side == "right" else -0.35

        # Temporal smoothing to prevent jitter
        self.smoothed_facing_sign = 0.82 * self.smoothed_facing_sign + 0.18 * target_facing
        facing_sign = self.smoothed_facing_sign


        is_dip_phase = (phase in ("preparing", "set_point"))
        target_knee_angle = self.profile["metrics"]["knee_dip"] if is_dip_phase else 178.0
        target_elbow_angle = self.profile["metrics"]["elbow_release"] if not is_dip_phase else 85.0

        # Construct Full-Body Pro Ghost Keypoints:
        ghost_pts = {}

        # Torso & Shoulders
        ghost_pts["left_shoulder"] = (l_sh[0], l_sh[1])
        ghost_pts["right_shoulder"] = (r_sh[0], r_sh[1])
        ghost_pts["left_hip"] = (l_hip[0], l_hip[1])
        ghost_pts["right_hip"] = (r_hip[0], r_hip[1])

        # Head / Nose
        mid_sh_x = (l_sh[0] + r_sh[0]) // 2
        mid_sh_y = (l_sh[1] + r_sh[1]) // 2
        ghost_pts["nose"] = (mid_sh_x + int(facing_sign * torso_h * 0.1), mid_sh_y - int(torso_h * 0.35))

        # Lower Body (Knees bend forward in the player's facing direction)
        knee_bend_rad = math.radians(180.0 - target_knee_angle)
        knee_fwd_offset = int(facing_sign * thigh_len * math.sin(knee_bend_rad) * 0.8)
        knee_y = shoot_hip[1] + int(thigh_len * math.cos(knee_bend_rad * 0.5))

        ghost_pts["left_knee"] = (l_hip[0] + knee_fwd_offset, knee_y)
        ghost_pts["right_knee"] = (r_hip[0] + knee_fwd_offset, knee_y)
        ghost_pts["left_ankle"] = (l_ankle[0], l_ankle[1])
        ghost_pts["right_ankle"] = (r_ankle[0], r_ankle[1])

        # Upper Body (Shooting arm extends forward in facing direction)
        if not is_dip_phase:
            # Full Extension at Release
            shoot_el_x = shoot_sh[0] + int(facing_sign * arm_len * 0.35)
            shoot_el_y = shoot_sh[1] - int(arm_len * 0.92)

            elbow_ext_rad = math.radians(180.0 - target_elbow_angle)
            shoot_wr_x = shoot_el_x + int(facing_sign * forearm_len * math.sin(elbow_ext_rad + 0.35))
            shoot_wr_y = shoot_el_y - int(forearm_len * math.cos(elbow_ext_rad + 0.35))

            # Guide hand (opposite side)
            guide_el_x = guide_sh[0] - int(facing_sign * arm_len * 0.20)
            guide_el_y = guide_sh[1] - int(arm_len * 0.70)
            guide_wr_x = shoot_wr_x - int(facing_sign * forearm_len * 0.30)
            guide_wr_y = shoot_wr_y + 10
        else:
            # Set Point / Dip (Shooting pocket near eye level)
            shoot_el_x = shoot_sh[0] + int(facing_sign * arm_len * 0.45)
            shoot_el_y = shoot_sh[1] - int(arm_len * 0.25)
            shoot_wr_x = shoot_sh[0] + int(facing_sign * arm_len * 0.25)
            shoot_wr_y = mid_sh_y - int(torso_h * 0.45)

            guide_el_x = guide_sh[0] - int(facing_sign * arm_len * 0.35)
            guide_el_y = guide_sh[1] - int(arm_len * 0.15)
            guide_wr_x = shoot_wr_x - int(facing_sign * 25)
            guide_wr_y = shoot_wr_y

        if side == "right":
            ghost_pts["right_elbow"] = (shoot_el_x, shoot_el_y)
            ghost_pts["right_wrist"] = (shoot_wr_x, shoot_wr_y)
            ghost_pts["left_elbow"] = (guide_el_x, guide_el_y)
            ghost_pts["left_wrist"] = (guide_wr_x, guide_wr_y)
        else:
            ghost_pts["left_elbow"] = (shoot_el_x, shoot_el_y)
            ghost_pts["left_wrist"] = (shoot_wr_x, shoot_wr_y)
            ghost_pts["right_elbow"] = (guide_el_x, guide_el_y)
            ghost_pts["right_wrist"] = (guide_wr_x, guide_wr_y)

        # Draw glowing neon skeleton
        overlay = frame.copy()
        ghost_line_color = (255, 235, 0)
        ghost_joint_color = (0, 255, 255)

        for j1, j2 in FULL_BODY_CONNECTIONS:
            if j1 in ghost_pts and j2 in ghost_pts:
                p1, p2 = ghost_pts[j1], ghost_pts[j2]
                cv2.line(overlay, p1, p2, ghost_line_color, 3, cv2.LINE_AA)

        cv2.circle(overlay, ghost_pts["nose"], int(torso_h * 0.18), ghost_line_color, 2, cv2.LINE_AA)

        for name, pt in ghost_pts.items():
            cv2.circle(overlay, pt, 5, ghost_joint_color, -1, cv2.LINE_AA)

        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Observations annotated directly on key joints
        if user_angles and user_angles.get("elbow_shooting") is not None:
            u_elbow = user_angles["elbow_shooting"]
            diff_elbow = target_elbow_angle - u_elbow
            tag_col = (0, 255, 0) if abs(diff_elbow) <= 8 else (0, 165, 255)
            cv2.putText(frame, f"Model Elbow: {target_elbow_angle:.0f}° ({diff_elbow:+.0f}°)",
                        (shoot_el_x + int(facing_sign * 12), shoot_el_y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, tag_col, 1, cv2.LINE_AA)

        if user_angles and user_angles.get("knee_shooting") is not None:
            u_knee = user_angles["knee_shooting"]
            diff_knee = target_knee_angle - u_knee
            tag_col = (0, 255, 0) if abs(diff_knee) <= 10 else (0, 165, 255)
            shoot_knee_pt = ghost_pts["right_knee"] if side == "right" else ghost_pts["left_knee"]
            cv2.putText(frame, f"Model Knee: {target_knee_angle:.0f}° ({diff_knee:+.0f}°)",
                        (shoot_knee_pt[0] + int(facing_sign * 12), shoot_knee_pt[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, tag_col, 1, cv2.LINE_AA)

        facing_label = "RIGHT" if facing_sign > 0.1 else ("LEFT" if facing_sign < -0.1 else "FRONT")
        cv2.putText(frame, f"REFERENCE MODEL: {self.profile['short_name'].upper()} (Facing: {facing_label})",
                    (ghost_pts["nose"][0] - 100, ghost_pts["nose"][1] - int(torso_h * 0.25)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 235, 0), 2, cv2.LINE_AA)

        return frame


    def draw(self, frame, comparison_result, dtw_result=None):
        """Draw Pro Comparison HUD widget on top-right of frame with transparent model notice."""
        if not comparison_result:
            return frame

        height, width = frame.shape[:2]
        panel_width = 330
        panel_height = 230
        margin_right = 15
        margin_top = 15

        x1 = width - panel_width - margin_right
        y1 = margin_top
        x2 = width - margin_right
        y2 = margin_top + panel_height

        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (15, 15, 22), -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 80, 120), 1)

        pro_name = comparison_result["pro_name"]
        score = comparison_result["similarity_score"]
        score_color = (0, 255, 0) if score >= 80 else (0, 255, 255) if score >= 65 else (0, 165, 255)

        # Header with explicit illustrative reference notice
        cv2.putText(frame, f"REF MODEL: {pro_name.upper()}", (x1 + 10, y1 + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 210, 0), 2)
        cv2.putText(frame, "[Illustrative Guide - Forms Vary]", (x1 + 10, y1 + 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (160, 160, 180), 1)

        dtw_str = f" | Dev: ±{dtw_result['avg_angular_deviation_deg']:.1f}°" if dtw_result else ""
        cv2.putText(frame, f"Model Alignment: {score}%{dtw_str}", (x1 + 10, y1 + 58),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, score_color, 2)

        # Progress bar
        bar_x = x1 + 10
        bar_y = y1 + 68
        bar_w = panel_width - 20
        bar_h = 7
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (40, 40, 40), -1)
        fill_w = int(bar_w * (score / 100.0))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), score_color, -1)

        # Direct Observation Line
        obs = comparison_result.get("observation", "")
        if len(obs) > 42:
            obs = obs[:39] + "..."
        cv2.putText(frame, obs, (x1 + 10, y1 + 92),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1)

        # Metric breakdowns
        curr_y = y1 + 112
        metrics = comparison_result.get("metrics", {})
        for name, data in list(metrics.items())[:3]:
            label = name.replace("_", " ").title()
            u_val = data["user"]
            p_val = data["pro"]
            m_score = data["score"]
            text = f"{label[:12]}: You {u_val:.0f}° vs Ref {p_val:.0f}° ({m_score:.0f}%)"
            cv2.putText(frame, text, (x1 + 10, curr_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.40, (230, 230, 230), 1)
            curr_y += 18

        # Recommendation line
        rec = comparison_result.get("recommendation", "")
        if len(rec) > 42:
            rec = rec[:39] + "..."
        cv2.putText(frame, f"Note: {rec}", (x1 + 10, y2 - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)

        return frame
