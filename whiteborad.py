import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Hands and Drawing utilities
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Initialize whiteboard canvas
canvas_height, canvas_width = 480, 640
drawing_canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255

# Drawing settings
drawing_color = (0, 0, 0)  # Black color for drawing
line_thickness = 5  # Thickness of the drawing lines

# Variables to track state
is_drawing = False
last_index_position = None

# Gesture detection functions
def detect_fist(hand_landmarks, frame_dims):
    """Detect a fist gesture by measuring the distance between the thumb and index finger tips."""
    h, w = frame_dims
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    
    # Convert normalized coordinates to pixels
    index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)
    thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
    
    # Calculate Euclidean distance
    distance = np.sqrt((index_x - thumb_x) ** 2 + (index_y - thumb_y) ** 2)
    return distance < 30  # Fist detected if distance is small

def detect_open_hand(hand_landmarks):
    """Detect an open hand gesture by checking if all finger tips are above their MCP joints."""
    tips = [
        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP],
    ]
    mcps = [
        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP],
        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP],
        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP],
        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP],
    ]
    
    return all(tip.y < mcp.y for tip, mcp in zip(tips, mcps))

# Open webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame for a mirror effect
    frame = cv2.flip(frame, 1)
    frame_height, frame_width, _ = frame.shape

    # Convert the frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe Hands
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks on the frame
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Detect gestures
            if detect_open_hand(hand_landmarks):
                # Clear the canvas if an open hand is detected
                drawing_canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255
                is_drawing = False
            elif detect_fist(hand_landmarks, (frame_height, frame_width)):
                # Stop drawing if a fist is detected
                is_drawing = False
            else:
                # Track the index finger tip for drawing
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                index_x, index_y = int(index_tip.x * frame_width), int(index_tip.y * frame_height)

                if is_drawing and last_index_position:
                    # Draw a line between the current and previous positions
                    cv2.line(drawing_canvas, last_index_position, (index_x, index_y), drawing_color, line_thickness)

                # Update state
                last_index_position = (index_x, index_y)
                is_drawing = True

    # Display the canvas and webcam feed
    cv2.imshow("Drawing Canvas", drawing_canvas)
    cv2.imshow("Hand Tracking", frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
