# AI Models in Intelligent Basketball Performance Analysis System
### A Deep Technical Reference for Academic Viva

---

## Overview: The Full AI Stack

```
Video Frame
    ↓
[BlazePose Detector]         → finds person in frame
    ↓
[BlazePose Landmark Model]   → outputs 33 joint coordinates
    ↓
[Coordinate Math Layer]      → angles, velocity, trajectory
    ↓
[Feedback Logic Layer]       → coaching output
    ↓
[Optional: Ball Detector]    → YOLO / custom model for basketball
```

Every frame that enters the system passes through at least two neural networks before your code even touches the data.

---

## Model 1: BlazePose Detector

**Type:** Convolutional Neural Network (CNN)  
**Role:** Person detection — finds WHERE the human is in the frame  
**Output:** Bounding box coordinates `(x, y, width, height)`

### How It Works

Before locating joints, the system needs to know where the person is. The Detector solves this with a **Single Shot Detector (SSD)** architecture.

```
Input Image (Full Frame)
      ↓
Feature Pyramid Network (FPN)
      ↓
Multi-scale Feature Maps
      ↓
Anchor Box Predictions
      ↓
Non-Max Suppression (NMS)
      ↓
Final Bounding Box
```

**Feature Pyramid Network (FPN):** Extracts features at multiple scales simultaneously — detects a far-away player (small in frame) and a close-up player (large in frame) with equal accuracy.

**Anchor Boxes:** Pre-defined boxes of various shapes/sizes placed across the image. The model predicts offsets to adjust these boxes to fit the actual person.

**Non-Max Suppression (NMS):** If 5 anchor boxes all think they found the same person, NMS keeps only the one with highest confidence and discards the rest.

### Why BlazePose Detector Specifically

Google designed BlazePose for **mobile real-time use**. It uses a small 4-layer CNN for initial ROI estimation, which is fast enough to run at 30+ FPS on a laptop CPU — no GPU required.

---

## Model 2: BlazePose Landmark Model (The Core AI)

**Type:** CNN + Regression Head (based on MobileNetV2 + GHUM body model)  
**Role:** Given a cropped image of a person, output 33 joint positions  
**File:** `pose_landmarker_heavy.task` (~29MB)  
**Output:** 33 landmarks × (x, y, z, visibility) = 132 values per frame

### Architecture Breakdown

```
Cropped Person Image (256×256 px)
            ↓
    ┌───────────────────┐
    │  MobileNetV2      │  ← Encoder (Feature Extractor)
    │  Depthwise Conv   │
    │  Bottleneck Blocks│
    └───────────────────┘
            ↓
    Feature Vector (1280 numbers)
            ↓
    ┌───────────────────┐
    │  Heatmap Head     │  ← predicts probability maps per joint
    └───────────────────┘
            ↓
    ┌───────────────────┐
    │  Regression Head  │  ← refines to precise (x, y, z) per joint
    └───────────────────┘
            ↓
    33 landmarks
```

### MobileNetV2 — The Encoder

MobileNetV2 is the feature extraction backbone. It compresses a 256×256×3 image (196,608 numbers) down to a 1280-dimensional feature vector — a compact mathematical "understanding" of the image.

**Key innovation — Depthwise Separable Convolutions:**

Normal convolution: one filter across all 3 channels simultaneously  
Depthwise separable: one filter per channel THEN combine → **9x fewer calculations**

```
Normal Conv:      3×3 kernel × 3 channels × N filters = expensive
Depthwise:        3×3 kernel × 1 channel (×3 times)   = cheap
Pointwise:        1×1 kernel × 3 channels × N filters  = cheap
Combined result:  same output, ~9x fewer multiply-adds
```

This is why it runs on CPU without lag.

**Inverted Residual Blocks (Bottleneck Blocks):**

```
Input (low channels)
    → Expand (increase channels 6x)   ← learn rich features
    → Depthwise Conv                  ← spatial filtering
    → Project (compress back down)    ← reduce computation
    → Skip connection (add input)     ← preserve original info
Output
```

Skip connections are crucial — they let gradients flow directly during training, preventing the "vanishing gradient" problem in deep networks.

### Heatmap Head — Where the Magic Happens

Rather than directly guessing "elbow is at pixel (234, 187)", the model first generates **probability heatmaps**:

```
For each of 33 landmarks:
  → Generate a 64×64 probability grid
  → Each cell = P(landmark is at this location)

High confidence:          Low confidence:
  0 0 0 0 0               0 1 2 1 0
  0 0 1 0 0               1 3 5 3 1
  0 1 9 1 0               2 5 9 5 2  ← spread out = uncertain
  0 0 1 0 0               1 3 5 3 1
  0 0 0 0 0               0 1 2 1 0
```

Peak of heatmap = predicted joint location. Wide heatmap = model is uncertain. This is more robust than direct regression because the model can express uncertainty spatially.

### GHUM Body Model — The 3D Prior

**GHUM = Generative Human Unified Model** — a statistical 3D human body model.

Google trained BlazePose using GHUM as a constraint. This is why the model can:
- Estimate Z (depth) from a 2D image
- Maintain anatomically plausible poses (elbow doesn't appear behind the head)
- Recover from partial occlusion (if hand is hidden, it infers likely position)

GHUM encodes thousands of real human body shapes and poses as mathematical distributions. When the landmark model predicts joints, GHUM acts as a prior that says "this combination of joint positions is anatomically possible" — filtering out physically impossible predictions.

**The Z coordinate specifically:**
- Not true metric depth (not in meters)
- Relative to hip midpoint (landmark 23-24 center)
- Estimated using learned body proportions
- Accurate enough for angle analysis, not for 3D distance measurement

### Model Variants

| Variant | Size | Speed | Accuracy | Use Case |
|---|---|---|---|---|
| `pose_landmarker_lite.task` | ~5MB | ~60 FPS | Lower | Mobile apps, live demo |
| `pose_landmarker_full.task` | ~13MB | ~40 FPS | Medium | Balanced real-time use |
| `pose_landmarker_heavy.task` | ~29MB | ~20 FPS | Highest | **Our project** — offline analysis |

We use Heavy because accuracy matters more than speed for biomechanical coaching.

---

## The ROI Tracking System (Between-Frame Optimization)

This is what makes the system feel smooth rather than jittery.

```
Frame 1:
  → Run full Detector (expensive, ~50ms)
  → Get bounding box
  → Run Landmark Model on crop
  → Compute output bounding box from landmarks
  → Save as ROI

Frame 2, 3, 4...:
  → SKIP the Detector entirely
  → Crop frame using saved ROI (with padding)
  → Run Landmark Model only (~15ms)
  → Update ROI from new landmark positions

Frame N:
  → If tracking_confidence < threshold → reset, re-run Detector
  → Otherwise continue tracking
```

This is a **predict-then-verify** loop. It's essentially Kalman filtering at the detector level — assume previous position is a good prior for the next frame, only re-detect when confidence drops.

**What min_tracking_confidence controls:**
- `0.5` = reset tracking when 50% uncertain (default — good balance)
- `0.8` = resets more often — better for fast movements like jump shots
- `0.3` = almost never resets — smoother but drifts on fast movement

For basketball (fast movements), consider setting this to `0.7`.

---

## The Math Layer — What Our Code Does

### Vector-Based Angle Calculation

```python
def get_angle(a, b, c):
    ba = a - b   # vector from b to a
    bc = c - b   # vector from b to c
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
```

This is the **Law of Cosines** in vector form:

```
cos(θ) = (BA⃗ · BC⃗) / (|BA⃗| × |BC⃗|)
```

Example — Elbow Angle Calculation:
```
Shoulder = (0.4, 0.3)
Elbow    = (0.5, 0.5)   ← angle calculated here
Wrist    = (0.6, 0.4)

BA = Shoulder - Elbow = (-0.1, -0.2)
BC = Wrist    - Elbow = ( 0.1, -0.1)

dot(BA, BC)  = (-0.1)(0.1) + (-0.2)(-0.1) = -0.01 + 0.02 = 0.01
|BA|         = √(0.01 + 0.04) = 0.2236
|BC|         = √(0.01 + 0.01) = 0.1414

cos(θ) = 0.01 / (0.2236 × 0.1414) = 0.316
θ = arccos(0.316) ≈ 71.6°
```

`np.clip(-1.0, 1.0)` prevents floating point errors (e.g., `1.0000002`) from crashing `arccos` which only accepts values in [-1, 1].

### Key Biomechanical Angles for Basketball

| Angle | Landmarks | Ideal Range (Shooting) | What It Tells You |
|---|---|---|---|
| Elbow angle at release | 12, 14, 16 | 160–175° | Arm extension |
| Knee bend before jump | 24, 26, 28 | 100–130° | Jump power |
| Hip angle | 12, 24, 26 | 150–170° | Posture/lean |
| Wrist-elbow alignment | 14, 16, 18 | < 15° deviation | Shot straightness |
| Shoulder elevation | 11, 12, 0 | Symmetrical | Balance |

---

## Other AI Models We Could Use (Alternatives & Enhancements)

### 1. YOLOv8-Pose (Best Alternative for Pose)

**What it is:** YOLO (You Only Look Once) v8 with a pose estimation head  
**Why it's better for basketball:**
- Detects **multiple players simultaneously** (full team analysis)
- Faster inference — 60+ FPS even with multiple people
- Simultaneously detects the **basketball** as an object

```python
# How to use
from ultralytics import YOLO
model = YOLO('yolov8m-pose.pt')
results = model('basketball_shot.mp4')
# Outputs: bounding boxes + 17 keypoints per person + ball location
```

**Trade-off:** 17 keypoints (COCO format) vs MediaPipe's 33 — less detailed hands/face.

### 2. ViTPose (Most Accurate Pose Model Available)

**What it is:** Vision Transformer-based pose estimation  
**Architecture:** ViT (Vision Transformer) backbone instead of CNN

CNNs process local patches. Transformers use **self-attention** — every joint attends to every other joint simultaneously:

```
"Where is the wrist?" 
→ Attends to elbow: "elbow is here, so wrist is probably..."
→ Attends to shoulder: "arm direction is this way, so..."
→ Final answer is context-aware
```

This makes it much more accurate on occluded or unusual poses — exactly what basketball involves (player crouching, jumping, turning).

**Trade-off:** Computationally heavy — needs GPU for real-time. Good for post-game video analysis.

### 3. Ball Detection: YOLOv8 Object Detection

Basketball cannot be ignored in a basketball coaching tool. MediaPipe doesn't detect balls — we need a separate model.

```python
from ultralytics import YOLO
ball_model = YOLO('yolov8n.pt')  # 'n' = nano, fastest

results = ball_model(frame)
for r in results:
    for box in r.boxes:
        if r.names[int(box.cls)] == 'sports ball':
            bx, by = int(box.xywh[0][0]), int(box.xywh[0][1])
            # bx, by = ball center coordinates
```

With ball + pose together:
- Compute **release angle** (angle of wrist-to-ball trajectory at release moment)
- Compute **arc height** of ball trajectory
- Compute **release point** (how high above ground the ball leaves the hand)

**To train a custom basketball detector** (more accurate than generic 'sports ball'):
- Collect 500+ images of basketballs in various lighting/angles
- Label them using **Roboflow** (free tool)
- Fine-tune YOLOv8 on that dataset: `model.train(data='basketball.yaml', epochs=50)`

### 4. Action Recognition: SlowFast / VideoSwin Transformer

**What it is:** A video-level classifier — not per-frame, but across a temporal sequence  
**Role:** Automatically detect "this is a jump shot" vs "this is a dribble" vs "this is a layup"

Without action recognition, your system is always analyzing — even when the player is just standing. With it:

```
Frame sequence → SlowFast → "Jump Shot Detected" → trigger analysis
                          → "Dribbling" → skip
                          → "Layup" → different angle thresholds
```

**SlowFast Architecture:**
- **Slow pathway:** Processes frames at low frame rate (captures appearance/posture)
- **Fast pathway:** Processes frames at high frame rate (captures motion/movement)
- Both pathways are fused for final classification

### 5. Shooting Feedback with LSTM (Custom Temporal Model)

**What it is:** Long Short-Term Memory network — processes sequences of data  
**Role:** Learn what a "good shot" looks like as a **sequence of angles**, not a single frame

Data structure:
```python
# One shot = sequence of angle measurements
shot = [
    [elbow_angle_t0, knee_angle_t0, hip_angle_t0],
    [elbow_angle_t1, knee_angle_t1, hip_angle_t1],
    ...  # 30 frames = 1 second of motion
]
label = 1  # made it / 0 = missed
```

After collecting 200+ labeled shots, train a small LSTM:
```python
from tensorflow.keras.layers import LSTM, Dense
model = Sequential([
    LSTM(64, input_shape=(30, 3)),  # 30 timesteps, 3 angle features
    Dense(32, activation='relu'),
    Dense(1, activation='sigmoid')  # 0 = bad form, 1 = good form
])
```

This is truly AI-powered coaching — the model **learns** good form from data rather than having rules manually coded.

### 6. MediaPipe Hands (Wrist/Finger Tracking)

**What it is:** Separate MediaPipe model for 21 hand landmarks  
**Role:** Analyze wrist snap, finger placement on ball at release

The pose model only gives you 1 point per wrist. The hand model gives:
- 21 landmarks per hand (fingertips, knuckles, palm)
- Wrist rotation angle
- Finger spread at release

For free throw analysis, the wrist snap in the last milliseconds before release determines backspin — which affects whether near-misses go in. This is the detail professional NBA coaches look for.

### 7. Pose3D: Lifting 2D to 3D (VideoPose3D)

**What it is:** A model that takes 2D keypoints and lifts them to 3D space  
**Why it matters:** A 2D camera can't capture side-to-side movement (lateral body sway)

```
2D Pose (x, y) × 33 landmarks
            ↓
    VideoPose3D (Transformer)
            ↓
3D Pose (x, y, z in meters) × 33 landmarks
```

With true 3D coordinates:
- Measure actual **lateral body sway** during shooting
- Calculate **3D release angle** (not just 2D projection)
- Detect **off-axis shooting** (ball released to left/right of target)

---

## Proposed Full System Architecture (Enhanced)

```
Input Layer
├── Webcam / Smartphone Video
└── Pre-recorded Game Footage
        ↓
Detection Layer
├── BlazePose (pose landmarks)        ← CURRENT
├── YOLOv8 (basketball detection)     ← ADD NEXT
└── MediaPipe Hands (wrist snap)      ← FUTURE
        ↓
Analysis Layer
├── Angle Computation (numpy)         ← CURRENT
├── Trajectory Tracking (OpenCV)      ← ADD NEXT
├── Ball Arc Analysis                 ← ADD NEXT
└── Temporal Consistency (LSTM)       ← FUTURE
        ↓
Feedback Layer
├── Rule-Based Feedback               ← CURRENT
├── AI-Generated Feedback (LSTM)      ← FUTURE
└── Voice Feedback (TTS)              ← FUTURE
        ↓
Output Layer
├── Annotated Video                   ← CURRENT
├── Session Report (PDF)              ← ADD NEXT
├── Progress Dashboard (web app)      ← FUTURE
└── Comparison vs Pro Players         ← FUTURE
```

---

## Model Comparison Table

| Model | Task | Speed | Accuracy | Hardware | Our Use |
|---|---|---|---|---|---|
| BlazePose Heavy | Pose Estimation | Medium | High | CPU | ✅ Current |
| YOLOv8-Pose | Multi-person Pose | Fast | High | CPU | 🔜 Next |
| ViTPose | Pose Estimation | Slow | Highest | GPU | 🔮 Future |
| YOLOv8n | Ball Detection | Very Fast | High | CPU | 🔜 Next |
| Custom YOLO | Basketball Detection | Very Fast | Very High | CPU | 🔮 Future |
| SlowFast | Action Recognition | Medium | High | GPU | 🔮 Future |
| LSTM | Shot Quality Classification | Fast | Trainable | CPU | 🔮 Future |
| VideoPose3D | 3D Pose Lifting | Medium | High | CPU/GPU | 🔮 Future |
| MediaPipe Hands | Hand/Wrist Tracking | Fast | High | CPU | 🔮 Future |

---

## Key Technical Terms for Viva

**Inference:** Running a trained model on new data (as opposed to training). Our system only does inference — we don't train anything.

**Landmark:** A specific point on the body (joint, feature point) detected by the model. MediaPipe detects 33.

**Confidence Score:** A value from 0–1 representing how certain the model is about a detection. Below the threshold we set (0.5), detections are discarded.

**Bounding Box:** A rectangle defining the region in an image where an object (person) is located. Expressed as (x, y, width, height).

**Feature Map:** Intermediate representation learned by a CNN layer — think of it as the model's internal "sketch" of what it sees, highlighting edges, textures, shapes.

**ROI (Region of Interest):** The cropped sub-region of a frame sent to the landmark model, determined by the previous frame's bounding box. Enables fast tracking.

**Heatmap:** A 2D grid where each cell contains the probability that a landmark exists at that location. Peak of heatmap = predicted landmark position.

**Regression:** Predicting a continuous value (like x=0.45, y=0.62) rather than a class label. The landmark model is a regression model.

**FPS (Frames Per Second):** How many frames the pipeline processes per second. 30 FPS = real-time. Our heavy model runs ~20 FPS on CPU.

**Depthwise Separable Convolution:** A computationally efficient convolution used in MobileNetV2 that achieves similar accuracy to standard convolution with ~9x fewer operations.

**Self-Attention (Transformer):** Mechanism where every element in a sequence (every patch of an image) looks at every other element to build context. More powerful than CNN for complex pose estimation.

**Temporal Analysis:** Analysis across time (across multiple frames) rather than a single frame. LSTM and SlowFast operate temporally.

---

## Why This Approach Is Innovative

1. **No Wearables Needed:** Traditional sports labs use $50,000+ motion capture suits. We use a $0 webcam and open-source AI.

2. **Edge Deployment:** Everything runs on a standard laptop CPU. No cloud, no internet, no latency — can work in a local gym.

3. **Sport-Specific Feedback:** Unlike generic pose tools, we define basketball-specific angle thresholds and metrics aligned with professional coaching standards.

4. **Scalable Architecture:** Modular design means each component (detector, analyzer, feedback engine) can be independently upgraded without rebuilding the whole system.

5. **Democratization:** The same quality of biomechanical analysis available to NBA teams can now run on any player's phone or laptop.

---

*Document prepared for BCS506 Major Project Viva — Intelligent Sports Performance Analysis System Using Computer Vision, BMSIT&M 2025-26*
