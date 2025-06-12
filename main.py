import cv2
import mediapipe as mp
import pyautogui
import sys

# User Settings
right_handed_dominant = True      # Set to False if the user is left-handed
smooth_factor = 0.2      # Lower = smoother, Higher = more responsive
dragging = False        # For drag-and-drop functionality

# initalie screen size
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

screen_w, screen_h = pyautogui.size()

# Helper Function: Finger State
def get_finger_states(hand_landmarks):
    # Returns [thumb, index, middle, ring, pinky] => True if finger is up
    tips_ids = [4, 8, 12, 16, 20]
    states = []
    for i in range(1, 5):  # index to pinky
        tip = hand_landmarks.landmark[tips_ids[i]]
        pip = hand_landmarks.landmark[tips_ids[i] - 2]
        states.append(tip.y < pip.y)  # True if finger is up
    # Thumb - based on x direction
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]
    states.insert(0, thumb_tip.x > thumb_ip.x)  # True if open (rightward)
    return states

# Camera Capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera")
    sys.exit(1)

print("Starting hand detection... Press ESC to quit")

# State Variables
prev_mouse_x, prev_mouse_y = 0, 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    left_hand = None
    right_hand = None

    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label.lower()

            # Adjust for user-handedness
            if right_handed_dominant:
                if label == 'left':
                    right_hand = hand_landmarks
                else:
                    left_hand = hand_landmarks
            else:
                if label == 'left':
                    left_hand = hand_landmarks
                else:
                    right_hand = hand_landmarks

            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Gesture Logic

    # Scroll with only Left Hand
    if left_hand and not right_hand:
        left_states = get_finger_states(left_hand)
        if all(left_states[1:]):  # All fingers up (scroll mode)
            wrist_y = left_hand.landmark[0].y * screen_h
            if wrist_y < screen_h // 2:
                pyautogui.scroll(20)
            else:
                pyautogui.scroll(-20)

    # Move Mouse with Both Hands Open
    elif left_hand and right_hand:
        left_states = get_finger_states(left_hand)
        right_states = get_finger_states(right_hand)

        if all(left_states[1:]) and all(right_states[1:]):
            lx = left_hand.landmark[0].x
            ly = left_hand.landmark[0].y
            target_x = int(lx * screen_w)
            target_y = int(ly * screen_h)

            # Smooth cursor movement
            smoothed_x = int(prev_mouse_x + (target_x - prev_mouse_x) * smooth_factor)
            smoothed_y = int(prev_mouse_y + (target_y - prev_mouse_y) * smooth_factor)
            pyautogui.moveTo(smoothed_x, smoothed_y)
            prev_mouse_x, prev_mouse_y = smoothed_x, smoothed_y

    # Left Click with Left Hand Clench OR Drag with Pinch
    if left_hand:
        left_states = get_finger_states(left_hand)

        # Dragging gesture: index + thumb together, others down
        thumb_tip = left_hand.landmark[4]
        index_tip = left_hand.landmark[8]
        middle_tip = left_hand.landmark[12]
        ring_tip = left_hand.landmark[16]
        pinky_tip = left_hand.landmark[20]

        pinch_distance = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2) ** 0.5

        # Threshold for pinch (adjust as needed)
        if pinch_distance < 0.05 and not any(left_states[2:]):  # middle, ring, pinky down
            if not dragging:
                pyautogui.mouseDown(button='left')
                dragging = True
        else:
            if dragging:
                pyautogui.mouseUp(button='left')
                dragging = False

    #  Right Click with Right Hand Clench
    if right_hand:
        right_states = get_finger_states(right_hand)
        if not any(right_states):  # All fingers down
            pyautogui.click(button='right')

    # Display Camera Feed
    cv2.imshow('Hand Mouse Control', frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()