import cv2
import numpy as np


PRO_PROFILES = {
    "curry": {
        "name": "Stephen Curry",
        "description": "Quick Release & High Arc",
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
        "name": "Klay Thompson",
        "description": "Textbook Form & High Extension",
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
        "name": "Ray Allen",
        "description": "Elevated Jump Shot Mechanics",
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


class ProComparator:
    """Compare user mechanics against pro player benchmark shooting mechanics."""

    def __init__(self, target_pro="curry"):
        if target_pro not in PRO_PROFILES:
            target_pro = "curry"
        self.target_key = target_pro
        self.profile = PRO_PROFILES[target_pro]

    def set_target_pro(self, target_key):
        if target_key in PRO_PROFILES:
            self.target_key = target_key
            self.profile = PRO_PROFILES[target_key]

    def compare(self, user_metrics):
        """
        Compare user metrics against active pro benchmark profile.
        user_metrics: dict with keys like 'elbow_release', 'knee_dip', 'hip_posture', 'launch_angle', 'wrist_flick'
        Returns dict containing score (0-100), metric breakdowns, and feedback tips.
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
            # Penalty scales with diff and weight
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

        # Determine strongest feature and primary area to adjust
        sorted_metrics = sorted(scores.items(), key=lambda item: item[1]["score"], reverse=True)
        best_feature = sorted_metrics[0][0] if sorted_metrics else None
        worst_feature = sorted_metrics[-1][0] if sorted_metrics else None

        recommendation = self._generate_recommendation(worst_feature, scores.get(worst_feature))

        return {
            "pro_name": self.profile["name"],
            "pro_description": self.profile["description"],
            "similarity_score": overall_score,
            "metrics": scores,
            "best_feature": best_feature,
            "worst_feature": worst_feature,
            "recommendation": recommendation,
        }

    @staticmethod
    def _generate_recommendation(worst_feature, data):
        if not worst_feature or not data:
            return "Good overall mechanics."

        user_val = data["user"]
        pro_val = data["pro"]
        diff = data["diff"]

        if worst_feature == "elbow_release":
            if user_val < pro_val:
                return f"Extend shooting arm higher at release (+{diff:.1f}° to match pro)."
            return f"Avoid over-extending arm at release (-{diff:.1f}° to match pro)."
        elif worst_feature == "knee_dip":
            if user_val > pro_val:
                return f"Bend knees deeper during dip phase (-{diff:.1f}° to match pro)."
            return f"Dip less with knees for a quicker release (+{diff:.1f}° to match pro)."
        elif worst_feature == "hip_posture":
            return f"Adjust hip posture angle by {diff:.1f}° for optimal balance."
        elif worst_feature == "launch_angle":
            if user_val < pro_val:
                return f"Increase shot trajectory arc (+{diff:.1f}° release angle)."
            return f"Lower shot trajectory arc (-{diff:.1f}° release angle)."
        elif worst_feature == "wrist_flick":
            return f"Flick wrist cleanly at release ({pro_val}° target)."

        return "Focus on consistent execution."

    def draw(self, frame, comparison_result):
        """Draw Pro Comparison HUD widget on top-right of frame."""
        if not comparison_result:
            return frame

        height, width = frame.shape[:2]
        panel_width = 300
        panel_height = 200
        margin_right = 10
        margin_top = 10

        x1 = width - panel_width - margin_right
        y1 = margin_top
        x2 = width - margin_right
        y2 = margin_top + panel_height

        # Draw semi-transparent dark panel overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (20, 20, 28), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (60, 60, 90), 1)

        # Header
        pro_name = comparison_result["pro_name"]
        score = comparison_result["similarity_score"]
        score_color = (0, 255, 0) if score >= 80 else (0, 255, 255) if score >= 65 else (0, 165, 255)

        cv2.putText(frame, f"PRO MATCH: {pro_name.upper()}", (x1 + 10, y1 + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)

        cv2.putText(frame, f"Similarity: {score}%", (x1 + 10, y1 + 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, score_color, 2)

        # Draw progress bar for score
        bar_x = x1 + 10
        bar_y = y1 + 60
        bar_w = panel_width - 20
        bar_h = 8
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
        fill_w = int(bar_w * (score / 100.0))
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), score_color, -1)

        # Render top metric breakdowns
        curr_y = y1 + 88
        metrics = comparison_result.get("metrics", {})
        for name, data in list(metrics.items())[:3]:
            label = name.replace("_", " ").title()
            u_val = data["user"]
            p_val = data["pro"]
            m_score = data["score"]
            text = f"{label[:12]}: {u_val:.0f}° vs {p_val:.0f}° ({m_score:.0f}%)"
            cv2.putText(frame, text, (x1 + 10, curr_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1)
            curr_y += 18

        # Recommendation line
        rec = comparison_result.get("recommendation", "")
        if len(rec) > 36:
            rec = rec[:33] + "..."
        cv2.putText(frame, f"Tip: {rec}", (x1 + 10, y2 - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1)

        return frame
