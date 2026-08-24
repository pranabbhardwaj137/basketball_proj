import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

# Setup
base_options = python.BaseOptions(model_asset_path='pose_landmarker.task') #model
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    num_poses=1,              # detect max 1 person (increase for multi-person)
    min_pose_detection_confidence=0.1,  # 50% sure = count as detected
    min_tracking_confidence=0.9         # 50% sure = keep tracking between frames
)


detector = vision.PoseLandmarker.create_from_options(options)

# Landmark connections to draw skeleton
CONNECTIONS = [
    (11,12),(11,13),(13,15),(12,14),(14,16),  # arms
    (11,23),(12,24),(23,24),                   # torso
    (23,25),(25,27),(24,26),(26,28)            # legs
]

def get_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

cap = cv2.VideoCapture(0)  # or "your_video.mp4"

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = detector.detect(mp_image)

    if result.pose_landmarks:
        lm = result.pose_landmarks[0]  # first person

        # Draw skeleton
        for a, b in CONNECTIONS:
            x1, y1 = int(lm[a].x * w), int(lm[a].y * h)
            x2, y2 = int(lm[b].x * w), int(lm[b].y * h)
            cv2.line(frame, (x1,y1), (x2,y2), (0,255,0), 2)

        # Draw dots
        for landmark in lm:
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (cx, cy), 4, (0,0,255), -1)

        # Elbow angle (shooting arm - right side)
        shoulder = [lm[12].x, lm[12].y]
        elbow    = [lm[14].x, lm[14].y]
        wrist    = [lm[16].x, lm[16].y]
        elbow_angle = get_angle(shoulder, elbow, wrist)

        # Knee angle (right)
        hip   = [lm[24].x, lm[24].y]
        knee  = [lm[26].x, lm[26].y]
        ankle = [lm[28].x, lm[28].y]
        knee_angle = get_angle(hip, knee, ankle)

        # already computing knee_angle, just add:
        if knee_angle < 120:
            knee_feedback = "Good knee bend for jump!"
        else:
            knee_feedback = "Bend knees more before shooting"

        cv2.putText(frame, knee_feedback, (30, 180), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

        # Display angles
        cv2.putText(frame, f"Elbow: {elbow_angle:.1f}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)
        cv2.putText(frame, f"Knee:  {knee_angle:.1f}", (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0), 2)

        # Basic feedback
        feedback = "Good form!" if elbow_angle > 150 else "Extend your arm more"
        cv2.putText(frame, feedback, (30, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

    cv2.imshow("Basketball Coach", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
detector.close()