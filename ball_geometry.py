"""Ball/rim geometry ported from clones/basketball-shot-analysis (run.py).

Original used YOLOv5 xyxy boxes and MediaPipe left-arm pose. These helpers are
API-agnostic: they only need boxes [x1, y1, x2, y2] and pixel (x, y) points.
"""

import numpy as np


def box_center(box):
    """Return (cx, cy) for an xyxy box."""
    if box is None or len(box) < 4:
        return None
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def point_distance(a, b):
    if a is None or b is None:
        return None
    return float(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5)


def box_to_point_distance(box, point):
    """Distance from box center to a pixel point (wrist, etc.)."""
    return point_distance(box_center(box), point)


def last_valid_box(boxes):
    """Most recent non-None box, skipping the current last slot (release pair)."""
    if not boxes or len(boxes) < 2:
        return None
    for i in range(len(boxes) - 2, -1, -1):
        if boxes[i] is not None:
            return boxes[i]
    return None


def ball_under_rim(ball_box, rim_box, x_threshold=70):
    """True if ball center is below the rim and roughly aligned in x (make heuristic)."""
    ball = box_center(ball_box)
    rim = box_center(rim_box)
    if ball is None or rim is None:
        return False
    return abs(ball[0] - rim[0]) < x_threshold and (ball[1] - rim[1]) > 0


def release_angle_deg(current_box, previous_box):
    """Launch angle vs horizontal using two ball boxes.

    Image y grows downward, so we flip dy. Matches the tangent-angle idea in
    get_tangent_angle() from the source repo, without the 4-tuple/2-tuple mix-up.
    """
    now = box_center(current_box)
    prev = box_center(previous_box)
    if now is None or prev is None:
        return None
    dx = now[0] - prev[0]
    dy = prev[1] - now[1]
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return None
    angle = abs(float(np.degrees(np.arctan2(dy, dx))))
    if angle > 90:
        angle = abs(90 - angle)
    return round(angle, 1)


def fit_parabola(centers):
    """Fit y = ax^2 + bx + c to ball centers. Returns (a, b, c) or None."""
    pts = [c for c in centers if c is not None]
    if len(pts) < 3:
        return None
    xs = np.array([p[0] for p in pts], dtype=float)
    ys = np.array([p[1] for p in pts], dtype=float)
    if np.allclose(xs, xs[0]):
        return None
    try:
        coeffs = np.polyfit(xs, ys, 2)
    except (np.linalg.LinAlgError, ValueError):
        return None
    return tuple(float(v) for v in coeffs)


def sample_parabola(coeffs, x_start, x_end, steps=80):
    if coeffs is None:
        return []
    a, b, c = coeffs
    xs = np.linspace(x_start, x_end, steps)
    return [(float(x), float(a * x * x + b * x + c)) for x in xs]


def arc_peak(centers):
    """Highest point on the ball path (smallest image y)."""
    pts = [c for c in centers if c is not None]
    if not pts:
        return None
    return min(pts, key=lambda p: p[1])
