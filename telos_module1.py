#import libraries
import cv2
import mediapipe as mp
import numpy as np
import csv
import time
import os
from datetime import datetime
#define constants
camera index = 0
PINCH_Closed_PX = 40
PINCH_OPEN_PX    = 120    
OUTPUT_DIR       = "telos_data"
#MediaPipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6,
)
#Camera setup using OpenCv
cap = cv2.VideoCapture(camera_index)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
#CSV file setup
session_id= datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = 0s.path.join(OUTPUT_DIR, f"session_{session_id}.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

csv_file = open(csv_path, "w", newline="")
fieldnames = ["timestamp", "frame",
              "pinch_distance_px", "gripper_value", "gripper_state",
              "thumb_tip_px", "thumb_tip_py",
              "index_tip_px", "index_tip_py"]

csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
csv_writer.writeheader()

#Main loop

# The loop Opening & Frame Capture 
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    frame_count += 1

    # Feeding the Frame to MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_frame.flags.writeable = False
    results = hands.process(rgb_frame)
    rgb_frame.flags.writeable = True

    #Extracting the Data
    if results.multi_hand_landmarks:
        hand_lm = results.multi_hand_landmarks[0]
        landmarks = hand_lm.landmarks

        thumb_x = int(landmarks[4].x * w)
        thumb_y = int(landmarks[4].y * h)
        index_x = int(landmarks[8].x * w)
        index_y = int(landmarks[8].y * h)

        pinch-distance = float(np.linalg.norm(
            np.array([thumb_x, thumb_y]) - np.array([index_x, index_y])
        ))
#The math formula to find the gripper value if its between a 0-1
        gripper_value = float(np.clip(
            (pinch_distance - PINCH_Closed_PX) / (PINCH_OPEN_PX - PINCH_Closed_PX),
            0.0, 1.0
        ))

        if gripper_value < 0.2:
            gripper_state = "ClOSED"
        elif gripper_value < 0.5:
            gripper_state = "PARTIAL"
        else:
            gripper_state = "OPEN"

# Drawing & Logging 
     mp_drawing.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)

        cv2.circle(frame, (thumb_x, thumb_y), 10, (0, 255, 255), -1)
        cv2.circle(frame, (index_x, index_y), 10, (255, 0, 255), -1)
        cv2.line(frame, (thumb_x, thumb_y), (index_x, index_y), (255, 255, 255), 2)

        cv2.putText(frame, f"Gripper: {gripper_state} ({gripper_value:.2f})",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        csv_writer.writerow({
            "timestamp":         time.time(),
            "frame":             frame_count,
            "pinch_distance_px": pinch_distance,
            "gripper_value":     gripper_value,
            "gripper_state":     gripper_state,
            "thumb_tip_px":      thumb_x,
            "thumb_tip_py":      thumb_y,
            "index_tip_px":      index_x,
            "index_tip_py":      index_y,
        })
    
# Display & Exit the script or main loop
    cv2.imshow("Telos Module 1", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup closes all tools
    cap.release()
    cv2.destroyAllWindows()
    hands.close()
    csv_file.close()

    print(f"Session saved to {csv_path}")
