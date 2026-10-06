# Real-Video Dataset Collection & Annotation Protocol

This protocol defines the standardized procedure for capturing, annotating, and benchmarking real-world basketball shooting clips to evaluate the single-camera analysis pipeline.

---

## 1. Video Recording Setup Guidelines

To ensure reproducible measurements and minimize perspective distortions:

| Parameter | Specification | Notes |
| :--- | :--- | :--- |
| **Camera Viewpoints** | $90^\circ$ Side Profile, $45^\circ$ Diagonal, $0^\circ$ Frontal | Evaluate each view separately to quantify angle distortion. |
| **Camera Distance** | 3.5 – 4.5 meters from shooter | Captures full body from feet/ankles to overhead ball release. |
| **Camera Height** | Waist/Chest level (approx. 1.1 – 1.3 meters) | Avoid steep downward or upward tilt angles ($<15^\circ$). |
| **Frame Rate** | $\ge 30\text{ FPS}$ ($60\text{ FPS}$ recommended) | Higher frame rate reduces motion blur during rapid release. |
| **Resolution** | 720p or 1080p | Clear landmark visibility without excessive compute latency. |
| **Lighting & Background** | High contrast, uniform lighting | Avoid direct backlighting behind the shooter. |

---

## 2. Ground-Truth Annotation Schema (`annotations.json`)

Each test clip must be annotated with the following standardized JSON structure:

```json
{
  "clip_id": "clip_001_side_playerA",
  "metadata": {
    "camera_view": "side_90deg",
    "distance_meters": 4.0,
    "fps": 30.0,
    "player_id": "player_01",
    "shooting_hand": "right",
    "shot_type": "catch_and_shoot"
  },
  "events": {
    "shot_start_frame": 45,
    "peak_dip_frame": 62,
    "release_frame": 78,
    "follow_through_frame": 88
  },
  "outcome": {
    "result": "made",
    "rim_contact": "swish",
    "verifier": "human_reviewer"
  },
  "occlusions": {
    "lower_body_occluded": false,
    "shooting_arm_occluded": false
  }
}
```

---

## 3. Evaluation Metrics & Error Quantification

When running `evaluate_video.py --annotation annotations.json`:

1. **Shot Detection Precision & Recall:**
   $$\text{Precision} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}, \quad \text{Recall} = \frac{\text{True Positives}}{\text{True Positives} + \text{False Negatives}}$$

2. **Phase Timing Error (Mean Absolute Error):**
   $$\text{MAE}_{\text{release}} = \frac{1}{N} \sum_{i=1}^N |\text{Detected Release Frame}_i - \text{Annotated Release Frame}_i| \times \frac{1000}{\text{FPS}} \quad (\text{ms})$$

3. **Estimate-to-Estimate Disagreement:**
   - Reports the difference between 2D image projection and MediaPipe 3D world estimates ($\pm \Delta^\circ$).
   - Note: Labeled strictly as estimate disagreement due to perspective foreshortening, not laboratory ground-truth error.

4. **Abstention & Coverage Rate:**
   $$\text{Coverage Rate} = \frac{\text{Frames with HIGH or MODERATE Confidence}}{\text{Total Clip Frames}}$$
