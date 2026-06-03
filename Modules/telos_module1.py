#import libraries
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import csv
import time
import os
from datetime import datetime
#define constants
camera_index = 0
PINCH_Closed_PX = 40
PINCH_OPEN_PX = 120    
OUTPUT_DIR = "telos_data"
MODEL_PATH = "models/hand_landmarker.task"  # the model file you downloaded

#MediaPipe setup
#Pull the 2 classes you need from the task api
BaseOptions = mp.tasks.BaseOptions # The model class for configurations
HandLandmarker = mp.tasks.vision.HandLandmarker # Creates the detector object 
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions # Configuration object 
VisionRunningMode = mp.tasks.vision.RunningMode # The class for Vision Mode 


options = HandLandmarkerOptions(
    base_options = BaseOptions(model_asset_path = MODEL_PATH),
    # VIDEO mode uses the previous frame to help track — smoother than IMAGE mode
    running_mode=VisionRunningMode.VIDEO,
    num_hands=1,                    # only track one hand for teleoperation
    min_hand_detection_confidence=0.7,  # how confident before declaring a hand found
    min_hand_presence_confidence=0.7,   # how confident to keep a hand in frame
    min_tracking_confidence=0.6,        # how confident to keep tracking vs re-detect
)
# HandLandmarker class creates a detector object to be used.
detector = HandLandmarker.create_from_options(options)

#Camera setup using OpenCv
cap = cv2.VideoCapture(camera_index)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

#CSV file setup

# create the data folder if it doesnt exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# build a unique filename using the current time
session_id= datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = os.path.join(OUTPUT_DIR, f"session_{session_id}.csv")

# Open the csv file 
csv_file = open(csv_path, "w", newline="")
fieldnames = ["timestamp", "frame",
              "pinch_distance_px", "gripper_value", "gripper_state",
              "thumb_tip_px", "thumb_tip_py",
              "index_tip_px", "index_tip_py"]

csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
csv_writer.writeheader()

# Main loop

# The loop Opening & Frame Capture 
frame_count = 0

while True:
    ret, frame = cap.read()      # Grab the latest frame from the webcam
    if not ret:
        break                    # stop if camera fails 

    frame = cv2.flip(frame, 1)   # Mirror so movements are not inverted 
    h, w, _ = frame.shape        # Get height and width for pixel conversion
    frame_count += 1

    # Feeding the Frame to MediaPipe
    # convert BGR (opencv) to RGB (mediapipe) then wrap in a mediapipe Image object
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

     # detect — VIDEO mode requires a timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)
    results = detector.detect_for_video(mp_image, timestamp_ms)

    # Extracting the Data
    # Check if a hand was found this frame 
    if results.hand_landmarks:
        landmarks = results.hand_landmarks[0] # First hand in the list
        

        # convert normalized landmarks to pixel coordinates
        thumb_x = int(landmarks[4].x * w)
        thumb_y = int(landmarks[4].y * h)
        index_x = int(landmarks[8].x * w)
        index_y = int(landmarks[8].y * h)
        
        # calculate straight line distance between thumb and index tip
        pinch_distance = float(np.linalg.norm(
            np.array([thumb_x, thumb_y]) - np.array([index_x, index_y])
        ))
        # map pinch distance to a 0.0 - 1.0 gripper value
        gripper_value = float(np.clip(
            (pinch_distance - PINCH_Closed_PX) / (PINCH_OPEN_PX - PINCH_Closed_PX),
            0.0, 1.0
        ))
        # human readable label
        if gripper_value < 0.2:
            gripper_state = "ClOSED"
        elif gripper_value < 0.5:
            gripper_state = "PARTIAL"
        else:
            gripper_state = "OPEN"

        # Drawing & Logging
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

    else:
        # no hand found this frame
        cv2.putText(frame, "Show your hand to the camera",
                    (w // 2 - 200, h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (100, 100, 255), 2)

    cv2.imshow("Telos Module 1", frame)     # display the frame
    if cv2.waitKey(1) & 0xFF == ord('q'):   # press Q to quit
        break

# Cleanup closes all tools
cap.release()
cv2.destroyAllWindows()
detector.close()
csv_file.close()

print(f"Session saved to {csv_path}")
