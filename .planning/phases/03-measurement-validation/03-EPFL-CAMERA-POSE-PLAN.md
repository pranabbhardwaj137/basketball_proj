# Phase 3 Work Plan — EPFL SportCenter Camera Pose & Court Geometry Evaluation

**Status:** Dropped from Phase 3 Active Scope; Archived to Phase 6 Backlog  
**Archival Role:** Candidate future benchmark for Phase 6 (Court Geometry, Automatic Distance Detection, & Multi-Camera Extrinsic Calibration).  
**Dataset Nature:** Camera-pose and court-geometry calibration dataset (NOT a human-body-pose dataset).  

---

## 1. Context & Dataset Qualification Audit

An inspection of the repository at `clones/sportcenter_camerapose_dataset` establishes the true contents of this benchmark:

1. **Files Inspected:**
   - `README.txt`: Specifies the exact sequence split:
     - **Training Split (12 sequences):** `seq_9841`, `seq_9842`, `seq_9843`, `seq_9849`, `seq_9850`, `seq_171305`, `seq_171931`, `seq_172146`, `seq_172444`, `seq_173321`, `seq_173510`, `seq_173833`. Total: 28,225 frames.
     - **Testing Split (16 sequences):** `seq_9844`, `seq_9847`, `seq_9851`, `seq_9852`, `seq_9853`, `seq_9845`, `seq_9854`, `seq_9855`, `seq_9856`, `seq_9857`, `seq_172318`, `seq_172647`, `seq_172730`, `seq_173742`, `seq_174006`, `seq_174210`. Total: 21,902 frames.
     - **Dataset Total:** 28 sequences, 50,127 frames.
   - `ground_grid.json`: 480 planar 3D points $(X, Y, 0.0)$ defining court floor grid geometry in meters.
   - `homography_rectified_template.json`: $3 \times 3$ affine homography $M$ mapping world court coordinates to a $1147 \times 2000$ rectified template image.
   - `intrinsics_seq_17xxxx.json` & `intrinsics_seq_98xx.json`: Camera intrinsic matrix $K$ ($3 \times 3$), radial/tangential distortion coefficients `distCoeffs` ($1 \times 5$), image resolution ($1920 \times 1080$), and camera model descriptions (Samsung A5 and iPhone 6 at 90°).
   - `poses.json` (per sequence): Contains frame-level ground-truth camera parameters:
     - $Hr$: $3 \times 3$ plane-to-image homography matrix mapping ground plane $(Z=0)$ to pixel coordinates.
     - $R$: $3 \times 3$ camera rotation matrix (camera-to-world).
     - $t$: $3 \times 1$ camera translation vector in world coordinates.
   - `player_positions.json` (present in subsets such as `seq_173833`): 3D ground locations $[X, Y, 0.0]$ of players standing on the court floor.

2. **Definitive Qualification & Scope Fences:**
   - **Supported:** Camera calibration verification, court ground grid projection, FOV court visibility, and planar homography vs. non-linear lens distortion reprojection error analysis.
   - **Strictly Unsupported:** Human skeletal joint annotations (head, shoulders, elbows, wrists, hips, knees, ankles) are **absent**.
   - **Audit Correction:** Prior claims in `.planning` and public reports stating that EPFL provided 12/17-joint body ground truth or evaluated PCK@20% = 100% are audited and retracted. Those scores were based on synthetic sample fixtures. The dataset is now correctly treated as a camera-pose and court-geometry benchmark.

---

## 2. Mathematical Definition of Supported Checks

### 2.1 Court Grid Projection & FOV Coverage
Given 3D court grid points $P_i = [X_i, Y_i, 0]^T$ in meters:
1. Homography Projection:
   $$\tilde{p}_{Hr, i} = Hr \cdot \begin{bmatrix} X_i \\ Y_i \\ 1 \end{bmatrix}, \quad p_{Hr, i} = \begin{bmatrix} \tilde{p}_{Hr, i, x} / \tilde{p}_{Hr, i, z} \\ \tilde{p}_{Hr, i, y} / \tilde{p}_{Hr, i, z} \end{bmatrix}$$
2. Field-of-View (FOV) Coverage:
   $$\text{Coverage} = \frac{1}{N_{\text{grid}}} \sum_{i=1}^{N_{\text{grid}}} \mathbf{1}\left(\tilde{p}_{Hr, i, z} > 0 \;\land\; 0 \le p_{Hr, i, x} \le W \;\land\; 0 \le p_{Hr, i, y} \le H\right)$$

### 2.2 Planar Homography vs. Distorted Camera Projection Reprojection Check
For visible points within the camera frustum ($Z_c > 0$ and $p_{Hr} \in [0, W] \times [0, H]$):
1. World-to-camera transformation using camera-to-world extrinsics $[R | t]$:
   $$R_{wc} = R^T, \quad t_{wc} = -R^T t$$
2. Non-linear camera projection with radial distortion:
   $$p_{\text{cam}, i} = \text{cv2.projectPoints}(P_i, \text{rodrigues}(R_{wc}), t_{wc}, K, \text{distCoeffs})$$
3. Reprojection Residual:
   $$e_i = \| p_{Hr, i} - p_{\text{cam}, i} \|_2 \quad (\text{pixels})$$
   This measures the geometric residual between the ideal planar homography model and the true lens-distorted camera projection.

---

## 3. Implementation Tasks

### Task 1: Real Dataset Loader & Evaluator (`evaluate_public_datasets.py`)
- Implement a real dataset loader accepting configurable `--epfl-dir` (default `clones/sportcenter_camerapose_dataset`).
- Parse `README.txt` splits dynamically; sanitize potential JSON trailing commas.
- Ingest actual `poses.json`, `intrinsics_*.json`, and `ground_grid.json`.
- Compute actual per-split metrics:
  - Sequence counts, frame counts, player ground points.
  - FOV court grid coverage percentage.
  - Planar-vs-distorted camera projection error ($\bar{x}$, median, max pixels).
- Set `body_pose_pck_available = False` and `body_pose_mpjpe_available = False` with a clear explanation of missing human skeletal labels.

### Task 2: Audit & Correct Documentation Artifacts
- **`DATASET_MANIFEST.md` & `DATASET_MANIFEST.json`:**
  - Remove all claims of 14/17 body joint skeletons and mapping tables.
  - Document camera pose, homography, intrinsics, and ground player position schema.
- **`PUBLIC_DATASETS_REPORT.json`:**
  - Regenerate with real computed camera-pose and court-geometry statistics.
  - Eradicate hardcoded dummy sample coordinates.
- **`.planning/STATE.md` & `.planning/ROADMAP.md`:**
  - Update descriptions of EPFL from "pose keypoints PCK@20%" to "Camera-pose and court-geometry calibration benchmark".

---

## 4. Acceptance Criteria

1. **Zero Hardcoded Data:** Loader reads actual JSON records from `clones/sportcenter_camerapose_dataset`.
2. **Honest Label Representation:** Body-joint PCK/MPJPE explicitly reported as UNAVAILABLE due to lack of skeletal annotations.
3. **Reproducibility:** `evaluate_public_datasets.py` runs with exit code 0 and emits real summary metrics in `PUBLIC_DATASETS_REPORT.json`.
4. **Consistency:** All documentation in `.planning/` matches the true dataset reality.
