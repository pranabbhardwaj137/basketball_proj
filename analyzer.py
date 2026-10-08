import csv
import math
import os
import time
from collections import deque
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

import numpy as np


def get_angle_3d(a, b, c):
    """3D or 2D angle at joint b given coordinate dicts or lists."""
    if a is None or b is None or c is None:
        return None

    coords_a = np.array([a[0], a[1], a[2] if len(a) > 2 else 0.0])
    coords_b = np.array([b[0], b[1], b[2] if len(b) > 2 else 0.0])
    coords_c = np.array([c[0], c[1], c[2] if len(c) > 2 else 0.0])

    ba = coords_a - coords_b
    bc = coords_c - coords_b

    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-6:
        return None

    cosine = np.dot(ba, bc) / denom
    cosine = np.clip(cosine, -1.0, 1.0)
    return round(float(np.degrees(np.arccos(cosine))), 1)


def shooting_side(landmarks, valid=None):
    """Determine shooting side based on wrist position and vertical elevation."""
    if not landmarks:
        return 'right'

    left_wrist = landmarks.get(15)
    right_wrist = landmarks.get(16)

    if left_wrist and right_wrist:
        left_y = left_wrist.get('norm_y', 1.0)
        right_y = right_wrist.get('norm_y', 1.0)
        return 'left' if left_y < right_y else 'right'
    if left_wrist:
        return 'left'
    return 'right'


def compute_all_angles(landmarks, valid=None, world_landmarks=None, min_visibility=0.45):
    """
    Compute joint angles across kinetic chain with dual 2D image-space and 3D world-space representation.
    - 2D angles: Calculated from normalized image plane coordinates (norm_x, norm_y).
    - 3D estimated angles: Calculated from MediaPipe 3D metric world coordinates (world_x, world_y, world_z in meters).
      Note: 3D world coordinates are monocular neural estimates, not physical motion-capture sensors.
    - Confidence Gating: Rejects landmarks below min_visibility (returns None for occluded joints).
    """
    if not landmarks:
        return None

    def pt_2d(idx):
        if idx not in landmarks:
            return None
        lm = landmarks[idx]
        if lm.get('visibility', 1.0) < min_visibility or lm.get('presence', 1.0) < min_visibility:
            return None
        if valid is not None and not valid.get(idx, True):
            return None
        return [lm['norm_x'], lm['norm_y'], 0.0]

    def pt_3d(idx):
        # Strictly require 3D world landmarks (in meters); do NOT fall back to normalized coordinates
        # to prevent mixing coordinate spaces in angle calculations.
        if world_landmarks and idx in world_landmarks:
            w = world_landmarks[idx]
            if w.get('visibility', 1.0) >= min_visibility and w.get('presence', 1.0) >= min_visibility:
                return [w['world_x'], w['world_y'], w['world_z']]
        return None

    def calc_2d(a, b, c):
        pa, pb, pc = pt_2d(a), pt_2d(b), pt_2d(c)
        return get_angle_3d(pa, pb, pc)

    def calc_3d(a, b, c):
        pa, pb, pc = pt_3d(a), pt_3d(b), pt_3d(c)
        return get_angle_3d(pa, pb, pc)

    side = shooting_side(landmarks, valid)

    # 2D Image Space Projection Angles
    elbow_r_2d = calc_2d(12, 14, 16)
    elbow_l_2d = calc_2d(11, 13, 15)
    knee_r_2d = calc_2d(24, 26, 28)
    knee_l_2d = calc_2d(23, 25, 27)
    hip_r_2d = calc_2d(12, 24, 26)
    hip_l_2d = calc_2d(11, 23, 25)
    shoulder_r_2d = calc_2d(14, 12, 24)
    shoulder_l_2d = calc_2d(13, 11, 23)

    # 3D Metric World-Space Angles (Estimates in meters)
    elbow_r_3d = calc_3d(12, 14, 16)
    elbow_l_3d = calc_3d(11, 13, 15)
    knee_r_3d = calc_3d(24, 26, 28)
    knee_l_3d = calc_3d(23, 25, 27)
    hip_r_3d = calc_3d(12, 24, 26)
    hip_l_3d = calc_3d(11, 23, 25)
    shoulder_r_3d = calc_3d(14, 12, 24)
    shoulder_l_3d = calc_3d(13, 11, 23)

    # Active shooting side selections
    elbow_2d = elbow_l_2d if side == 'left' else elbow_r_2d
    elbow_3d = elbow_l_3d if side == 'left' else elbow_r_3d
    knee_2d = knee_l_2d if side == 'left' else knee_r_2d
    knee_3d = knee_l_3d if side == 'left' else knee_r_3d
    hip_2d = hip_l_2d if side == 'left' else hip_r_2d
    hip_3d = hip_l_3d if side == 'left' else hip_r_3d
    shoulder_2d = shoulder_l_2d if side == 'left' else shoulder_r_2d
    shoulder_3d = shoulder_l_3d if side == 'left' else shoulder_r_3d

    foreshortening_delta_elbow = (
        round(abs(elbow_3d - elbow_2d), 1)
        if (elbow_3d is not None and elbow_2d is not None)
        else None
    )

    if elbow_3d is not None and elbow_2d is not None:
        coord_frame = "DUAL_2D_AND_3D_METRIC"
    elif elbow_3d is not None:
        coord_frame = "3D_WORLD_METRIC"
    elif elbow_2d is not None:
        coord_frame = "2D_IMAGE_SPACE"
    else:
        coord_frame = "UNAVAILABLE"

    angles = {
        'shooting_side': side,
        # Standard primary angles (prefer 3D world estimates when available, fallback to 2D)
        'elbow_shooting': elbow_3d if elbow_3d is not None else elbow_2d,
        'knee_shooting': knee_3d if knee_3d is not None else knee_2d,
        'hip_shooting': hip_3d if hip_3d is not None else hip_2d,
        'shoulder_shooting': shoulder_3d if shoulder_3d is not None else shoulder_2d,
        # Explicit 2D image projections
        'elbow_shooting_2d': elbow_2d,
        'knee_shooting_2d': knee_2d,
        'hip_shooting_2d': hip_2d,
        'shoulder_shooting_2d': shoulder_2d,
        # Explicit 3D world estimates
        'elbow_shooting_3d': elbow_3d,
        'knee_shooting_3d': knee_3d,
        'hip_shooting_3d': hip_3d,
        'shoulder_shooting_3d': shoulder_3d,
        'foreshortening_delta_elbow': foreshortening_delta_elbow,
        'coordinate_frame': coord_frame,
    }
    return angles




def interpolate_kinematic_series(raw_values, max_gap=2):

    """
    Interpolate missing measurements linearly over short gaps (<= max_gap frames).
    Longer dropouts remain np.nan to avoid fabricating artificial motion data.
    Returns (cleaned_series, tracking_validity_ratio [0.0-1.0]).
    """
    n = len(raw_values)
    if n == 0:
        return np.array([]), 0.0

    arr = np.array([float(v) if v is not None and not np.isnan(v) else np.nan for v in raw_values])
    valid_count = int(np.count_nonzero(~np.isnan(arr)))
    validity_ratio = valid_count / n

    if valid_count == 0:
        return arr, 0.0

    # Linear interpolation over gaps <= max_gap
    cleaned = arr.copy()
    in_gap = False
    gap_start = 0

    for i in range(n):
        if np.isnan(cleaned[i]):
            if not in_gap:
                in_gap = True
                gap_start = i
        else:
            if in_gap:
                gap_len = i - gap_start
                if gap_len <= max_gap and gap_start > 0:
                    start_val = cleaned[gap_start - 1]
                    end_val = cleaned[i]
                    for g in range(gap_len):
                        frac = (g + 1) / (gap_len + 1)
                        cleaned[gap_start + g] = start_val + frac * (end_val - start_val)
                in_gap = False

    return cleaned, validity_ratio


class KineticChainAnalyzer:
    """
    Evaluates proximal-to-distal biomechanical energy transfer sequencing,
    fluidity, and hitch detection across the entire shooting motion.
    Eliminates dummy constant imputation and uses direction-aware angular velocities.
    """

    # Minimum angular velocity thresholds (°/sec) to qualify as an intentional kinematic drive
    VELOCITY_THRESHOLDS = {
        "knee": 35.0,       # Extension / uncoiling from dip
        "hip": 30.0,        # Extension
        "shoulder": 30.0,   # Elevation
        "elbow": 50.0,      # Arm extension
        "wrist": 40.0,      # Wrist snap / flexion
    }

    def evaluate_shot_chain(self, shot_frames):
        """
        Analyze a sequence of shot frame dicts to compute kinetic sequencing timing,
        energy flow score, and hitch detection without artificial static fallbacks.
        """
        if not shot_frames or len(shot_frames) < 6:
            return {
                "sequencing_score": None,
                "fluidity_score": None,
                "energy_efficiency": None,
                "chain_order": [],
                "time_lags_ms": {},
                "is_proximal_to_distal": False,
                "hitch_detected": False,
                "tracking_confidence": "INSUFFICIENT",
                "diagnostics": "Insufficient frame history for kinetic chain analysis.",
            }

        # Extract timestamps
        times = np.array([f.get('_timestamp_sec', 0.0) for f in shot_frames])
        dt = np.diff(times)
        dt[dt <= 1e-4] = 0.033

        # Extract raw joint series
        raw_knee = [f.get('knee_shooting') for f in shot_frames]
        raw_hip = [f.get('hip_shooting') for f in shot_frames]
        raw_shoulder = [f.get('shoulder_shooting') for f in shot_frames]
        raw_elbow = [f.get('elbow_shooting') for f in shot_frames]
        raw_wrist = [f.get('wrist_flexion_angle') for f in shot_frames]

        # Interpolate short dropouts cleanly without arbitrary constant fallbacks
        knee_s, knee_val = interpolate_kinematic_series(raw_knee)
        hip_s, hip_val = interpolate_kinematic_series(raw_hip)
        shoulder_s, sh_val = interpolate_kinematic_series(raw_shoulder)
        elbow_s, el_val = interpolate_kinematic_series(raw_elbow)
        wrist_s, wr_val = interpolate_kinematic_series(raw_wrist)

        avg_validity = (knee_val + hip_val + sh_val + el_val) / 4.0

        if avg_validity < 0.60:
            return {
                "sequencing_score": None,
                "fluidity_score": None,
                "energy_efficiency": None,
                "chain_order": [],

                "time_lags_ms": {},
                "is_proximal_to_distal": False,
                "hitch_detected": False,
                "tracking_confidence": "INSUFFICIENT",
                "diagnostics": f"Tracking confidence low ({avg_validity*100:.0f}% visible); cannot verify kinetic chain.",
            }

        # Compute Direction-Aware Velocities (dTheta/dt)
        # 1. Knee Extension: positive when uncoiling (angle increasing)
        knee_v = np.diff(knee_s) / dt
        # 2. Hip Extension: positive when extending upward
        hip_v = np.diff(hip_s) / dt
        # 3. Shoulder Elevation: positive when arm lifts
        shoulder_v = np.diff(shoulder_s) / dt
        # 4. Elbow Extension: positive when arm extends toward hoop
        elbow_v = np.diff(elbow_s) / dt
        # 5. Wrist Snap: positive when wrist flexes forward (wrist flexion angle drops, so -dTheta/dt)
        wrist_v = -np.diff(wrist_s) / dt

        def clean_and_smooth(v):
            # Replace NaNs with zeros for velocity peak analysis
            clean = np.nan_to_num(v, nan=0.0)
            if len(clean) >= 3:
                return np.convolve(clean, np.ones(3)/3.0, mode='same')
            return clean

        knee_v = clean_and_smooth(knee_v)
        hip_v = clean_and_smooth(hip_v)
        shoulder_v = clean_and_smooth(shoulder_v)
        elbow_v = clean_and_smooth(elbow_v)
        wrist_v = clean_and_smooth(wrist_v)

        mid_times = (times[:-1] + times[1:]) / 2.0

        # Helper to find valid directional peak above threshold
        def find_peak(vel_arr, threshold):
            if len(vel_arr) == 0:
                return None, 0.0
            max_idx = int(np.argmax(vel_arr))
            max_val = float(vel_arr[max_idx])
            if max_val >= threshold:
                return float(mid_times[max_idx]), max_val
            return None, max_val

        t_knee, v_knee_max = find_peak(knee_v, self.VELOCITY_THRESHOLDS["knee"])
        t_hip, v_hip_max = find_peak(hip_v, self.VELOCITY_THRESHOLDS["hip"])
        t_shoulder, v_sh_max = find_peak(shoulder_v, self.VELOCITY_THRESHOLDS["shoulder"])
        t_elbow, v_elbow_max = find_peak(elbow_v, self.VELOCITY_THRESHOLDS["elbow"])
        t_wrist, v_wrist_max = find_peak(wrist_v, self.VELOCITY_THRESHOLDS["wrist"])

        # Collect identified peaks
        detected_peaks = []
        if t_knee is not None:
            detected_peaks.append(("Knee Uncoil", t_knee, 0))
        if t_hip is not None:
            detected_peaks.append(("Hip Extension", t_hip, 1))
        if t_shoulder is not None:
            detected_peaks.append(("Shoulder Lift", t_shoulder, 2))
        if t_elbow is not None:
            detected_peaks.append(("Elbow Extension", t_elbow, 3))
        if t_wrist is not None:
            detected_peaks.append(("Wrist Snap", t_wrist, 4))

        if len(detected_peaks) < 3:
            return {
                "sequencing_score": None,
                "fluidity_score": None,
                "energy_efficiency": None,
                "chain_order": [p[0] for p in detected_peaks],
                "time_lags_ms": {},
                "is_proximal_to_distal": False,
                "hitch_detected": False,
                "tracking_confidence": "MODERATE",
                "diagnostics": "Insufficient distinct velocity peaks detected to score kinetic sequence.",
            }

        # Sort detected peaks chronologically
        sorted_peaks = sorted(detected_peaks, key=lambda x: x[1])
        chain_order = [p[0] for p in sorted_peaks]

        # Calculate chronological inversions
        inversions = 0
        total_pairs = 0
        for i in range(len(sorted_peaks)):
            for j in range(i + 1, len(sorted_peaks)):
                total_pairs += 1
                if sorted_peaks[i][2] > sorted_peaks[j][2]:
                    inversions += 1

        sequencing_score = max(0.0, round(100.0 * (1.0 - (inversions / max(1, total_pairs))), 1))
        is_proximal = (inversions <= 1)

        # Compute specific inter-joint time lags (ms)
        time_lags_ms = {}
        if t_knee is not None and t_elbow is not None:
            time_lags_ms["knee_to_elbow_lag_ms"] = round((t_elbow - t_knee) * 1000.0, 1)
        if t_elbow is not None and t_wrist is not None:
            time_lags_ms["elbow_to_wrist_lag_ms"] = round((t_wrist - t_elbow) * 1000.0, 1)

        # Hitch / Fluidity check: Look for distinct deceleration dip in upper arm extension
        hitch_detected = False
        fluidity_score = 90.0
        if len(elbow_v) > 6:
            peak_idx = int(np.argmax(elbow_v))
            if 2 < peak_idx < len(elbow_v) - 2:
                pre_peak_min = float(np.min(elbow_v[max(0, peak_idx - 3):peak_idx]))
                if pre_peak_min < -10.0:  # Deceleration dip
                    hitch_detected = True
                    fluidity_score = 65.0

        energy_efficiency = round(0.6 * sequencing_score + 0.4 * fluidity_score, 1)

        # Grounded observation-first diagnostics
        observations = []
        if is_proximal:
            lag_str = ""
            if "knee_to_elbow_lag_ms" in time_lags_ms:
                lag = time_lags_ms["knee_to_elbow_lag_ms"]
                lag_str = f" ({lag:.0f}ms lag)"
            observations.append(f"Optimal ground-up energy transfer{lag_str}.")
        else:
            first_segment = chain_order[0]
            observations.append(f"Kinetic leak: {first_segment} initiated before lower-body drive.")

        if hitch_detected:
            observations.append("Hitch detected: upper body paused before final extension.")
        else:
            observations.append("Fluid energy transfer.")

        return {
            "sequencing_score": sequencing_score,
            "fluidity_score": fluidity_score,
            "energy_efficiency": energy_efficiency,
            "chain_order": chain_order,
            "time_lags_ms": time_lags_ms,
            "is_proximal_to_distal": is_proximal,
            "hitch_detected": hitch_detected,
            "tracking_confidence": "HIGH" if avg_validity > 0.8 else "MODERATE",
            "diagnostics": " ".join(observations),
        }


class ShotPhaseDetector:
    """
    Robust Finite State Machine for basketball shot phase detection.
    Guarantees strict state transitions with configurable kinematic gates:
    IDLE -> PREPARING (Dip) / SET_POINT -> RELEASING -> FOLLOW_THROUGH -> COOLDOWN -> IDLE.

    Gates:
      - Configurable wrist-height elevation (nose/forehead for jump_shot, shoulder-level for set_shot)
      - Upward vertical velocity threshold (v_y < -0.06)
      - Dip-to-rise kinetic sequencing
      - Phase duration sanity windows (rejecting sensor jitter and static hold aborts)
      - Landmark tracking confidence gating
    """

    def __init__(
        self,
        debounce_frames: int = 2,
        shot_style: str = "jump_shot",
        wrist_elevation_threshold: Optional[float] = None,
        min_upward_velocity: float = -0.06,
    ):
        self.state = 'idle'
        self.debounce_frames = debounce_frames
        self.shot_style = shot_style.lower() if shot_style in ("jump_shot", "set_shot") else "jump_shot"
        self.wrist_elevation_threshold = wrist_elevation_threshold
        self.min_upward_velocity = min_upward_velocity

        self.candidate_state = 'idle'
        self.candidate_count = 0

        self.prev_wrist_y = None
        self.prev_elbow_angle = None
        self.prev_time = None

        self.has_entered_prep_or_set = False
        self.phase_start_time = None
        self.shot_start_time = None
        self.release_frames_count = 0
        self.follow_through_frames = 0
        self.cooldown_frames = 0
        self.min_dip_knee = 180.0
        self.knee_dip_time = None
        self.max_release_elbow = 0.0

    def _is_wrist_elevated(self, wrist_y: float, shoulder_y: float, nose_y: Optional[float]) -> bool:
        """Evaluate wrist height gate against configured shot style."""
        if self.wrist_elevation_threshold is not None:
            return wrist_y <= self.wrist_elevation_threshold
        if self.shot_style == "jump_shot":
            if nose_y is not None:
                return wrist_y <= (nose_y + 0.02)
            return wrist_y <= (shoulder_y - 0.12)
        # set_shot allows shoulder-relative threshold
        return wrist_y <= (shoulder_y - 0.05)

    def update(self, landmarks, angles, timestamp_ms=None, hand_info=None, ball_info=None):
        """
        Update state machine using kinematics, strict transition guards,
        and optional hand snap signals.
        """
        if not landmarks or not angles:
            return self.state, 0.0, 0.0

        side = angles.get('shooting_side', 'right')
        wrist_idx = 15 if side == 'left' else 16
        shoulder_idx = 11 if side == 'left' else 12
        elbow_idx = 13 if side == 'left' else 14
        nose_idx = 0

        wrist_lm = landmarks.get(wrist_idx)
        shoulder_lm = landmarks.get(shoulder_idx)
        nose_lm = landmarks.get(nose_idx)

        wrist_y = wrist_lm['norm_y'] if wrist_lm else None
        shoulder_y = shoulder_lm['norm_y'] if shoulder_lm else None
        nose_y = nose_lm['norm_y'] if nose_lm else None

        elbow_angle = angles.get('elbow_shooting')
        knee_angle = angles.get('knee_shooting')

        now = timestamp_ms / 1000.0 if timestamp_ms is not None else time.time()
        dt = max(0.016, now - self.prev_time) if self.prev_time is not None else 0.033
        self.prev_time = now

        # Landmark confidence guard: require key joints
        if wrist_y is None or shoulder_y is None:
            return self.state, 0.0, 0.0

        wrist_v_y = (wrist_y - self.prev_wrist_y) / dt if self.prev_wrist_y is not None else 0.0
        elbow_v_ang = (elbow_angle - self.prev_elbow_angle) / dt if (self.prev_elbow_angle is not None and elbow_angle is not None) else 0.0

        self.prev_wrist_y = wrist_y
        if elbow_angle is not None:
            self.prev_elbow_angle = elbow_angle

        # Cooldown guard: lock out new shot detection immediately after a completed shot
        if self.cooldown_frames > 0:
            self.cooldown_frames -= 1
            self.state = 'idle'
            self.has_entered_prep_or_set = False
            return self.state, round(wrist_v_y, 4), round(elbow_v_ang, 2)

        raw_phase = self.state
        is_hand_flick = hand_info.get('is_flick', False) if hand_info else False
        is_elevated = self._is_wrist_elevated(wrist_y, shoulder_y, nose_y)
        has_upward_drive = (wrist_v_y <= self.min_upward_velocity)

        # Track phase duration
        if self.phase_start_time is None:
            self.phase_start_time = now
        phase_duration_s = now - self.phase_start_time

        # --- STATE TRANSITION MACHINE ---

        if self.state == 'idle':
            self.has_entered_prep_or_set = False
            self.release_frames_count = 0
            self.follow_through_frames = 0
            self.shot_start_time = None
            if knee_angle is not None:
                self.min_dip_knee = knee_angle
            if elbow_angle is not None:
                self.max_release_elbow = elbow_angle

            # Transition to PREPARING: Lower-body flexion (knee < 145 deg) with arm below set point
            if knee_angle is not None and knee_angle < 145.0 and wrist_y > (shoulder_y - 0.05):
                raw_phase = 'preparing'
                self.has_entered_prep_or_set = True
                self.phase_start_time = now
                self.shot_start_time = now
                self.knee_dip_time = now

            # Transition directly to SET_POINT: Elevated wrist (near/above shoulder) with loaded elbow
            elif elbow_angle is not None and is_elevated and 60.0 <= elbow_angle <= 120.0:
                raw_phase = 'set_point'
                self.has_entered_prep_or_set = True
                self.phase_start_time = now
                self.shot_start_time = now

        elif self.state == 'preparing':
            if knee_angle is not None:
                if knee_angle < self.min_dip_knee:
                    self.min_dip_knee = knee_angle
                    self.knee_dip_time = now

            # Advance to SET_POINT when ball/wrist is raised to shoulder/head level
            if is_elevated and (elbow_angle is not None and 60.0 <= elbow_angle <= 125.0):
                raw_phase = 'set_point'
                self.has_entered_prep_or_set = True
                self.phase_start_time = now

            # Direct 1-motion upward jump into releasing: requires upward velocity + elevation gate
            elif has_upward_drive and is_elevated and (elbow_angle is not None and elbow_angle >= 115.0):
                raw_phase = 'releasing'
                self.release_frames_count = 1
                self.phase_start_time = now

            # Phase duration timeout: if preparation exceeds 1.2s or shooter stands back up
            elif phase_duration_s > 1.2 or (knee_angle is not None and knee_angle > 170.0 and wrist_y > (shoulder_y + 0.12)):
                raw_phase = 'idle'
                self.has_entered_prep_or_set = False
                self.phase_start_time = None

        elif self.state == 'set_point':
            # Rising upward extension into release: strict upward velocity + elevated wrist
            if (has_upward_drive or is_hand_flick) and is_elevated and (elbow_angle is not None and elbow_angle >= 115.0):
                raw_phase = 'releasing'
                self.release_frames_count = 1
                self.phase_start_time = now

            # Set point timeout: holding set point > 0.6s without shooting is an aborted shot / ball fake
            elif phase_duration_s > 0.6 or wrist_y > (shoulder_y + 0.18):
                raw_phase = 'idle'
                self.has_entered_prep_or_set = False
                self.phase_start_time = None

        elif self.state == 'releasing':
            self.release_frames_count += 1
            if elbow_angle is not None:
                self.max_release_elbow = max(self.max_release_elbow, elbow_angle)

            # Move into FOLLOW_THROUGH when elbow is extended high (>= 145 deg) with wrist above shoulder
            if (elbow_angle is not None and elbow_angle >= 145.0) and is_elevated:
                raw_phase = 'follow_through'
                self.follow_through_frames = 1
                self.phase_start_time = now

            # Release timeout: spent > 0.5s in releasing without follow-through
            elif self.release_frames_count > 16:
                raw_phase = 'idle'
                self.has_entered_prep_or_set = False
                self.phase_start_time = None

        elif self.state == 'follow_through':
            self.follow_through_frames += 1
            if elbow_angle is not None:
                self.max_release_elbow = max(self.max_release_elbow, elbow_angle)

            # Hold follow through for at least 3 frames, then complete shot and enter cooldown
            if self.follow_through_frames >= 3:
                raw_phase = 'idle'
                self.cooldown_frames = 20  # ~0.66 second cooldown
                self.has_entered_prep_or_set = False
                self.phase_start_time = None

        # Debounce candidate phase
        if raw_phase == self.candidate_state:
            self.candidate_count += 1
        else:
            self.candidate_state = raw_phase
            self.candidate_count = 1

        if self.candidate_count >= self.debounce_frames or raw_phase in ('follow_through', 'releasing'):
            if self.state != self.candidate_state:
                self.phase_start_time = now
            self.state = self.candidate_state

        return self.state, round(wrist_v_y, 4), round(elbow_v_ang, 2)


class SessionRecorder:
    """
    Records per-shot metrics, kinetic chain sequencing, and form repeatability index.
    Preserves audit metadata including sample size and tracking validity.
    """

    def __init__(self, pre_roll_capacity=45):
        self.shots = []
        self.current_shot = []
        self.frame_history = deque(maxlen=pre_roll_capacity)
        self.recording = False
        self.shot_count = 0
        self.session_start = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.chain_analyzer = KineticChainAnalyzer()

    def push_frame(self, angles, phase="idle", timestamp_ms=0, hand_info=None):
        """Continuously push frame angles to the rolling pre-roll buffer."""
        if angles:
            entry = {k: v for k, v in angles.items() if isinstance(v, (int, float))}
            entry['_phase'] = phase
            entry['_timestamp_sec'] = timestamp_ms / 1000.0 if timestamp_ms else 0.0
            if hand_info:
                entry['wrist_flexion_angle'] = hand_info.get('wrist_flexion_angle')
                entry['wrist_snap_velocity'] = hand_info.get('wrist_snap_velocity')
                entry['finger_spread_ratio'] = hand_info.get('finger_spread_ratio')
                entry['is_flick'] = hand_info.get('is_flick', False)

            self.frame_history.append(entry)
            if self.recording:
                self.current_shot.append(entry)

    def start_shot(self):
        """Start recording a shot, pre-populating with full ring buffer history."""
        if not self.recording:
            self.recording = True
            self.current_shot = list(self.frame_history)

    def end_shot(self, extra=None):
        """End shot recording, compute kinematic summary and kinetic chain sequencing."""
        if self.recording and len(self.current_shot) >= 6:
            # Verify shot had valid extension (> 135 deg elbow)
            elbow_vals = [f['elbow_shooting'] for f in self.current_shot if f.get('elbow_shooting') is not None]
            max_elbow = max(elbow_vals) if elbow_vals else 0.0

            if max_elbow < 135.0:
                # Discard false positive (arm was never extended into a shot)
                self.recording = False
                self.current_shot = []
                return None

            self.shot_count += 1
            summary = self._summarize_shot(self.current_shot)
            summary['shot_number'] = self.shot_count
            summary['timestamp'] = time.strftime("%H:%M:%S")

            # Evaluate kinetic chain sequencing
            chain_res = self.chain_analyzer.evaluate_shot_chain(self.current_shot)
            summary['kinetic_sequencing_score'] = chain_res['sequencing_score']
            summary['fluidity_score'] = chain_res['fluidity_score']
            summary['energy_efficiency'] = chain_res['energy_efficiency']
            summary['is_proximal_to_distal'] = chain_res['is_proximal_to_distal']
            summary['hitch_detected'] = chain_res['hitch_detected']
            summary['kinetic_diagnostics'] = chain_res['diagnostics']
            summary['tracking_confidence'] = chain_res.get('tracking_confidence', 'UNKNOWN')
            summary['sequence_lag_ms'] = chain_res.get('time_lags_ms', {}).get('knee_to_elbow_lag_ms')
            summary['elbow_angle_release_3d'] = summary.get('elbow_at_release')
            summary['elbow_angle_release_2d'] = summary.get('avg_elbow_shooting_2d') or summary.get('elbow_at_release')
            summary['knee_angle_dip_3d'] = summary.get('knee_at_dip')
            summary['torso_sway_deg'] = summary.get('std_hip_shooting') or 0.0
            if summary.get('elbow_angle_release_3d') is not None and summary.get('elbow_angle_release_2d') is not None:
                summary['foreshortening_discrepancy_deg'] = round(abs(summary['elbow_angle_release_3d'] - summary['elbow_angle_release_2d']), 1)
            else:
                summary['foreshortening_discrepancy_deg'] = 0.0

            if extra:
                summary.update(extra)

            self.shots.append(summary)

            self.recording = False
            self.current_shot = []
            return summary

        self.recording = False
        self.current_shot = []
        return None

    def _summarize_shot(self, frames):
        """
        Summarize shot: max elbow (release extension), min knee (dip depth),
        and Form Repeatability Index (formerly consistency score).
        """
        keys = [k for k in frames[0].keys() if not k.startswith('_') and k != 'shooting_side']
        summary = {}

        for key in keys:
            values = [f[key] for f in frames if f.get(key) is not None and isinstance(f[key], (int, float))]
            if not values:
                summary[f'avg_{key}'] = None
                summary[f'std_{key}'] = None
                continue
            summary[f'avg_{key}'] = round(float(np.mean(values)), 1)
            summary[f'std_{key}'] = round(float(np.std(values)), 1)

        elbow_vals = [f['elbow_shooting'] for f in frames if f.get('elbow_shooting') is not None]
        knee_vals = [f['knee_shooting'] for f in frames if f.get('knee_shooting') is not None]
        wrist_flex_vals = [f['wrist_flexion_angle'] for f in frames if f.get('wrist_flexion_angle') is not None]

        summary['elbow_at_release'] = round(float(np.max(elbow_vals)), 1) if elbow_vals else None
        summary['knee_at_dip'] = round(float(np.min(knee_vals)), 1) if knee_vals else None
        summary['wrist_flick_at_release'] = round(float(np.min(wrist_flex_vals)), 1) if wrist_flex_vals else None
        summary['frames_recorded'] = len(frames)

        # Form Repeatability Index: indicates movement repeatability, NOT overall shot quality
        elbow_std = summary.get('std_elbow_shooting') or 12.0
        knee_std = summary.get('std_knee_shooting') or 12.0
        summary['repeatability_index'] = max(0.0, round(100.0 - (elbow_std + knee_std), 1))

        return summary

    def export_csv(self, output_dir="sessions_csv"):
        """Export session data to timestamped CSV file inside sessions_csv directory."""
        if not self.shots:
            print("No shots recorded yet.")
            return None
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, f"session_{self.session_start}.csv")
        keys = []
        for shot in self.shots:
            for key in shot.keys():
                if key not in keys:
                    keys.append(key)
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.shots)
        print(f"Session saved to {filename}")
        return filename

    def get_session_stats(self):
        """Return session statistics dictionary with sample sizes and repeatability metrics."""
        if not self.shots:
            return None
        elbow_avgs = [s.get('elbow_at_release') for s in self.shots if s.get('elbow_at_release') is not None]
        repeatability_scores = [s.get('repeatability_index', 80.0) for s in self.shots]
        energy_scores = [s.get('energy_efficiency') for s in self.shots if s.get('energy_efficiency') is not None]

        return {
            'total_valid_shots': self.shot_count,
            'avg_elbow_at_release': round(float(np.mean(elbow_avgs)), 1) if elbow_avgs else None,
            'best_elbow_at_release': round(float(max(elbow_avgs)), 1) if elbow_avgs else None,
            'avg_repeatability_index': round(float(np.mean(repeatability_scores)), 1) if repeatability_scores else None,
            'avg_energy_efficiency': round(float(np.mean(energy_scores)), 1) if energy_scores else None,
            'repeatability_trend': 'Stable / Repeatable' if len(repeatability_scores) > 1 and repeatability_scores[-1] >= repeatability_scores[0] else 'Variable'
        }
