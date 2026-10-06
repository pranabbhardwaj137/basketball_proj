# Basketball Biomechanics Metric Dictionary

This document defines the mathematical formulas, landmark indices, coordinate bases, confidence sources, and known limitations for all biomechanical metrics computed by the pipeline.

---

## 1. Landmark Index Reference (MediaPipe BlazePose 33 Keypoints)

```
Upper Body:
  11: Left Shoulder       12: Right Shoulder
  13: Left Elbow          14: Right Elbow
  15: Left Wrist          16: Right Wrist

Lower Body:
  23: Left Hip            24: Right Hip
  25: Left Knee           26: Right Knee
  27: Left Ankle          28: Right Ankle
  31: Left Foot Index     32: Right Foot Index
```

---

## 2. Joint Angle Definitions & Formulas

All joint angles $\theta$ at vertex joint $B$ formed by adjacent joints $A$ and $C$ are computed using the 3D dot-product cosine formula:

$$\vec{u} = \vec{A} - \vec{B}, \quad \vec{v} = \vec{C} - \vec{B}$$
$$\theta = \arccos\left(\frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|}\right) \times \frac{180^\circ}{\pi}$$

### Metric Specifications Table

| Metric Key | Primary Joints $(A, B, C)$ | Coordinate Basis Options | Confidence Gate | Known Physical & CV Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **`elbow_shooting_2d`** | Shoulder $(12/11) \to$ Elbow $(14/13) \to$ Wrist $(16/15)$ | 2D Normalized Image Space $[x, y \in [0, 1]]$ | $\text{vis} \ge 0.45$ & $\text{presence} \ge 0.45$ for all 3 joints | Subject to perspective foreshortening when arm extends out-of-plane. |
| **`elbow_shooting_3d`** | Shoulder $(12/11) \to$ Elbow $(14/13) \to$ Wrist $(16/15)$ | 3D Metric World Space (Meters relative to hip center) | $\text{vis} \ge 0.45$ & $\text{presence} \ge 0.45$ for all 3 joints in `world_landmarks` | MediaPipe world landmarks are monocular neural estimates, not multi-camera sensor measurements. |
| **`knee_shooting_2d` / `3d`** | Hip $(24/23) \to$ Knee $(26/25) \to$ Ankle $(28/27)$ | 2D Image Space / 3D World Space (Meters) | $\text{vis} \ge 0.45$ & $\text{presence} \ge 0.45$ | Truncated when camera is placed too close (lower body out of frame). |
| **`hip_shooting_2d` / `3d`** | Shoulder $(12/11) \to$ Hip $(24/23) \to$ Knee $(26/25)$ | 2D Image Space / 3D World Space (Meters) | $\text{vis} \ge 0.45$ & $\text{presence} \ge 0.45$ | Affected by jersey bagging or loose clothing occluding hip joint center. |
| **`shoulder_shooting_2d` / `3d`** | Elbow $(14/13) \to$ Shoulder $(12/11) \to$ Hip $(24/23)$ | 2D Image Space / 3D World Space (Meters) | $\text{vis} \ge 0.45$ & $\text{presence} \ge 0.45$ | Arm elevation angle relative to torso line. |
| **`foreshortening_delta_elbow`** | $\|\theta_{\text{elbow\_3d}} - \theta_{\text{elbow\_2d}}\|$ | Degrees $(^\circ)$ | Both 2D and 3D valid | Represents estimate-to-estimate disagreement due to out-of-plane arm rotation. |

---

## 3. Kinetic Chain Sequencing & Angular Velocities

### Direction-Aware Velocity Definitions ($d\theta/dt$)

$$\omega(t) = \frac{\theta(t + \Delta t) - \theta(t)}{\Delta t}$$

1. **Knee Extension (Uncoil):** $\frac{d\theta_{\text{knee}}}{dt} > 0$ (Threshold: $\ge 35^\circ/\text{s}$)
2. **Hip Extension:** $\frac{d\theta_{\text{hip}}}{dt} > 0$ (Threshold: $\ge 30^\circ/\text{s}$)
3. **Shoulder Elevation:** $\frac{d\theta_{\text{shoulder}}}{dt} > 0$ (Threshold: $\ge 30^\circ/\text{s}$)
4. **Elbow Extension (Arm Drive):** $\frac{d\theta_{\text{elbow}}}{dt} > 0$ (Threshold: $\ge 50^\circ/\text{s}$)
5. **Wrist Snap (Flexion):** $-\frac{d\theta_{\text{wrist}}}{dt} > 0$ (Threshold: $\ge 40^\circ/\text{s}$)

### Proximal-to-Distal Sequencing Rule
Ideal kinetic energy transfer flows sequentially upward:
$$\text{Knees} \longrightarrow \text{Hips} \longrightarrow \text{Shoulders} \longrightarrow \text{Elbows} \longrightarrow \text{Wrist}$$

- **Energy Efficiency Score:** Computed from sequence inversions and deceleration hitches ($[0-100\%]$).
- **Time Lag Uncertainty:** All inter-joint time lags carry frame-rate quantization bounds:
  $$\text{Quantization Error} = \pm \frac{1}{\text{FPS}} \quad (\pm 33\text{ms at 30 FPS}, \pm 16.7\text{ms at 60 FPS})$$

---

## 4. Missing Data & Temporal Interpolation

- **Short Gaps ($\le 2$ frames / $\le 66\text{ms}$ at 30 FPS):** Linearly interpolated to bridge brief optical occlusions.
- **Long Gaps ($> 2$ frames):** Preserved as `NaN` (untracked). Zero dummy constant substitution is permitted.
- **Coverage Abstention Gate:** If average joint validity across a shot is $< 60\%$, `KineticChainAnalyzer` sets `tracking_confidence: INSUFFICIENT` and suppresses all sequencing scores.

---

## 5. Personal Shot Lab Statistical Semantics & Notation

In Phase 4 Personal Shot Lab summaries, comparison reports between made and missed shots adhere to strict scientific notation:

### Continuous Metric Distribution ($\bar{x} \pm s$)
For joint angles (e.g. elbow extension at release, knee dip angle):
- $\bar{x}$ denotes the **sample mean**: $\bar{x} = \frac{1}{N}\sum_{i=1}^N x_i$.
- $\pm s$ denotes the **sample standard deviation** across shots (inter-shot kinematic variability):
  $$s = \sqrt{\frac{1}{N-1}\sum_{i=1}^N (x_i - \bar{x})^2}$$
- **Example:** $158.2^\circ \pm 4.1^\circ$ indicates a mean release angle of $158.2^\circ$ with a shot-to-shot standard deviation of $4.1^\circ$.

### Temporal Metrics & Quantization Uncertainty
For time lags (e.g. knee-to-elbow drive lag):
- Expressed as $\bar{t} \pm s\text{ ms}$ (mean $\pm$ standard deviation across shots).
- Always accompanied by the **temporal quantization uncertainty** disclaimer:
  $$\Delta t_{\text{quant}} = \pm \frac{1}{\text{FPS}} \quad (\pm 33.3\text{ms at 30 FPS})$$
- Note: Temporal quantization uncertainty represents the discrete sampling window of the video sensor, distinct from inter-shot standard deviation $s$.

### Language Guardrails
- **Descriptive Associations Only:** All differences are reported as descriptive associations (e.g., *"In your 8 reviewed shots, makes were associated with $14^\circ$ higher elbow extension than misses"*).
- **Causal Disclaimers:** The system strictly avoids causal words like *"caused"*, *"fixes"*, or *"guarantees"*.

