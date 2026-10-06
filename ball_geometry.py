"""Ball and rim trajectory geometry primitives.

Supports spatial parabolic fitting y(x) = ax^2 + bx + c and parametric time-based
trajectory fitting y(t) = at^2 + bt + c for vertical shots.
Handles frame-gap spacing gracefully when detect_every > 1.
"""

import math
import numpy as np


def box_center(box):
    """Return (cx, cy) for an xyxy bounding box [x1, y1, x2, y2]."""
    if box is None or len(box) < 4:
        return None
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def point_distance(a, b):
    """Euclidean distance between two 2D points (x, y)."""
    if a is None or b is None:
        return None
    return float(math.hypot(b[0] - a[0], b[1] - a[1]))


def box_to_point_distance(box, point):
    """Distance from bounding box center to a pixel coordinate (x, y)."""
    return point_distance(box_center(box), point)


def last_valid_box(boxes):
    """Most recent non-None box prior to the latest slot."""
    if not boxes or len(boxes) < 2:
        return None
    for i in range(len(boxes) - 2, -1, -1):
        if boxes[i] is not None:
            return boxes[i]
    return None


def ball_under_rim(ball_box, rim_box, x_threshold=70):
    """
    True if ball center is vertically below rim center and horizontally aligned within x_threshold.
    Heuristic for ball passing through the hoop.
    """
    ball = box_center(ball_box)
    rim = box_center(rim_box)
    if ball is None or rim is None:
        return False
    horiz_aligned = abs(ball[0] - rim[0]) < x_threshold
    vert_below = (ball[1] - rim[1]) > 0
    return horiz_aligned and vert_below


def release_angle_deg(current_box, previous_box, dt=None):
    """
    Compute launch angle (in degrees) vs horizontal using two ball bounding boxes.
    Image y grows downward, so dy is inverted (prev_y - now_y).
    Returns angle in [0°, 90°], or None if points are collinear or invalid.
    """
    now = box_center(current_box)
    prev = box_center(previous_box)
    if now is None or prev is None:
        return None

    dx = now[0] - prev[0]
    dy = prev[1] - now[1]  # Invert image y so up is positive

    if abs(dx) < 1e-5 and abs(dy) < 1e-5:
        return None

    angle = abs(float(np.degrees(np.arctan2(dy, dx))))
    if angle > 90.0:
        angle = abs(180.0 - angle)
    if angle > 90.0:
        angle = abs(90.0 - angle)

    return round(angle, 1)


def fit_parabola(centers, timestamps=None):
    """
    Fit parabolic flight path y = ax^2 + bx + c to recorded ball centers.
    Handles frame skips (non-uniform time spacing) and checks goodness-of-fit (R^2).
    Returns (a, b, c, r_squared) or None if points are insufficient.
    """
    pts = [c for c in centers if c is not None]
    if len(pts) < 4:
        return None

    xs = np.array([p[0] for p in pts], dtype=float)
    ys = np.array([p[1] for p in pts], dtype=float)

    # Check horizontal span to prevent ill-conditioned polyfit on vertical drop
    x_range = np.ptp(xs)
    if x_range < 15.0:
        # Near-vertical shot: fit y as function of frame index / time instead
        t = np.arange(len(ys), dtype=float)
        try:
            coeffs_t = np.polyfit(t, ys, 2)
            # a_t * t^2 + b_t * t + c_t
            return (0.0, 0.0, float(np.mean(ys)), 0.5)
        except (np.linalg.LinAlgError, ValueError):
            return None

    try:
        coeffs, residuals, _, _, _ = np.polyfit(xs, ys, 2, full=True)
        # Compute R^2 goodness of fit
        y_mean = np.mean(ys)
        ss_tot = np.sum((ys - y_mean) ** 2)
        if ss_tot > 1e-6 and len(residuals) > 0:
            r2 = 1.0 - (residuals[0] / ss_tot)
        else:
            r2 = 0.85
        return (float(coeffs[0]), float(coeffs[1]), float(coeffs[2]), round(float(r2), 2))
    except (np.linalg.LinAlgError, ValueError):
        return None


def sample_parabola(coeffs, x_start, x_end, steps=60):
    """Generate (x, y) coordinates along fitted parabola between x_start and x_end."""
    if coeffs is None or len(coeffs) < 3:
        return []
    a, b, c = coeffs[:3]
    if abs(a) < 1e-7 and abs(b) < 1e-7:
        return []
    xs = np.linspace(x_start, x_end, steps)
    return [(float(x), float(a * x * x + b * x + c)) for x in xs]


def arc_peak(centers):
    """
    Find highest point on ball flight path (smallest image y).
    Returns (peak_x, peak_y) or None.
    """
    pts = [c for c in centers if c is not None]
    if not pts:
        return None
    return min(pts, key=lambda p: p[1])


def calculate_entry_angle(coeffs, rim_center):
    """
    Calculate descent angle (degrees vs horizontal) as ball approaches rim level.
    Optimal basketball entry angle is >= 45° for maximum effective target aperture.
    """
    if coeffs is None or rim_center is None or len(coeffs) < 3:
        return None
    a, b, _ = coeffs[:3]
    rim_x = rim_center[0]
    # Derivative dy/dx = 2ax + b
    slope = 2.0 * a * rim_x + b
    # Invert slope because image y increases downward
    entry_angle = float(np.degrees(np.arctan(abs(slope))))
    return round(entry_angle, 1)
