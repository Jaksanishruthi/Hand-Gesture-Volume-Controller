import cv2
import mediapipe as mp
import numpy as np
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Initialize Mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# Initialize Pycaw for volume control
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# Get the volume range
vol_range = volume.GetVolumeRange()
min_vol = vol_range[0]
max_vol = vol_range[1]

# Start capturing video
cap = cv2.VideoCapture(0)

with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the frame horizontally for a later selfie-view display
        frame = cv2.flip(frame, 1)

        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame and detect hands
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get the landmarks for the index finger tip and thumb tip
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

                # Convert the landmarks to pixel coordinates
                h, w, c = frame.shape
                index_finger_tip_coords = (int(index_finger_tip.x * w), int(index_finger_tip.y * h))
                thumb_tip_coords = (int(thumb_tip.x * w), int(thumb_tip.y * h))

                # Calculate the distance between the index finger tip and thumb tip
                distance = np.linalg.norm(np.array(index_finger_tip_coords) - np.array(thumb_tip_coords))

                # Map the distance to the volume range
                vol = np.interp(distance, [30, 150], [min_vol, max_vol])
                volume.SetMasterVolumeLevel(vol, None)

                # Draw landmarks and connections on the frame
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Display the volume level on the frame
                cv2.putText(frame, f'Volume: {int(vol)}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        # Display the frame
        cv2.imshow('Hand Gesture Volume Controller', frame)

        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# Release the video capture and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()