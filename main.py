import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# User Settings
RIGHT_HANDED_DOMINANT = True # Set False if you're left-handed
SMOOTHING = 5                # Higher = smoother cursor, Lower = faster
FRAME_REDUCTION = 100        # Margin around the camera view
CLICK_COOLDOWN = 1.0         # Seconds to wait between right clicks

pyautogui.FAILSAFE = False
SCREEN_W, SCREEN_H = pyautogui.size()
CAM_W, CAM_H = 640, 480

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# State Variables
prevX, prevY = 0, 0 # Previous Location (for smoothing)
currX, currY = 0, 0 # Current Location
dragging = False
last_right_click_time = 0

def get_finger_states(hand_landmarks):
    """
    Returns Boolean List: [Thumb, Index, Middle, Ring, Pinky]
    True = Finger is UP (Open), False = Finger is DOWN (Closed)
    """
    # Finger tip IDs: Thumb=4, Index=8, Middle=12, Ring=16, Pinky=20
    tips_ids = [4, 8, 12, 16, 20]
    states = []
    
    # Check 4 fingers (Index to Pinky)
    # If Tip y is less than Pip y (inverted y in image coords), finger is UP
    for i in range(1, 5): 
        tip_y = hand_landmarks.landmark[tips_ids[i]].y
        pip_y = hand_landmarks.landmark[tips_ids[i] - 2].y
        states.append(tip_y < pip_y)
        
    # Check if tip far from palm
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]
    pinky_mcp = hand_landmarks.landmark[17]
    states.insert(0, abs(thumb_tip.x - pinky_mcp.x) > abs(thumb_ip.x - pinky_mcp.x))
    
    return states # [Thumb, Index, Middle, Ring, Pinky]

def main():
    global prevX, prevY, currX, currY, dragging, last_right_click_time
    
    cap = cv2.VideoCapture(0)
    cap.set(3, CAM_W)
    cap.set(4, CAM_H)

    print("Started. Press ESC to quit.")

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        # Flip and Convert
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        # Draw visual guide for mouse control
        cv2.rectangle(frame, (FRAME_REDUCTION, FRAME_REDUCTION), 
                     (CAM_W - FRAME_REDUCTION, CAM_H - FRAME_REDUCTION),
                     (255, 0, 255), 2)

        left_hand = None
        right_hand = None

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                # Identify Hand (Left or Right)
                label = handedness.classification[0].label.lower()
                
                if label == 'left':
                    # If user is right-handed dominant, the camera's "Left" is usually their left hand 
                    # (since we flipped the image).
                    right_hand = hand_landmarks
                else:
                    left_hand = hand_landmarks

        # Gesture Controls

        # Scroll: Only left hand visible + All fingers open
        if left_hand and not right_hand:
            states = get_finger_states(left_hand)
            if all(states[1:]): # All fingers open (no need to check thumb)
                wrist_y = left_hand.landmark[0].y
                
                # Visual Feedback
                cv2.putText(frame, "SCROLLIN", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

                if wrist_y < 0.4: # Hand High
                    pyautogui.scroll(20)
                elif wrist_y > 0.6: # Hand Low
                    pyautogui.scroll(-20)

        # Move: Both hands open
        elif left_hand and right_hand:
            l_states = get_finger_states(left_hand)
            r_states = get_finger_states(right_hand)

            if all(l_states[1:]) and all(r_states[1:]): # All fingers up on both hands
                # Using index finger for better precision
                target_x = left_hand.landmark[8].x * CAM_W
                target_y = left_hand.landmark[8].y * CAM_H

                # Interpolate (map camera coordinates to screen coordinates)
                screen_x = np.interp(target_x, (FRAME_REDUCTION, CAM_W - FRAME_REDUCTION), (0, SCREEN_W))
                screen_y = np.interp(target_y, (FRAME_REDUCTION, CAM_H - FRAME_REDUCTION), (0, SCREEN_H))

                # Smooth the movement
                currX = prevX + (screen_x - prevX) / SMOOTHING
                currY = prevY + (screen_y - prevY) / SMOOTHING

                pyautogui.moveTo(currX, currY)
                prevX, prevY = currX, currY
                
                cv2.putText(frame, "MOVE MODE", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

        # Left Click + Drag: Left hand pinch
        if left_hand:
            # Measure distance between Thumb and index
            thumb_tip = left_hand.landmark[4]
            index_tip = left_hand.landmark[8]
            
            # Euclidean distance
            dist = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
            
            # Threshold for pinch
            if dist < 0.1:
                if not dragging:
                    pyautogui.mouseDown()
                    dragging = True
                    cv2.circle(frame, (int(index_tip.x*CAM_W), int(index_tip.y*CAM_H)), 15, (0, 255, 0), cv2.FILLED)
            else:
                if dragging:
                    pyautogui.mouseUp()
                    dragging = False

        # Righ Click: Right hand fist
        if right_hand:
            r_states = get_finger_states(right_hand)
            # If no fingers are up (Fist)
            if not any(r_states): 
                current_time = time.time()
                # Only click if enough time has passed
                if current_time - last_right_click_time > CLICK_COOLDOWN:
                    pyautogui.click(button='right')
                    last_right_click_time = current_time
                    cv2.putText(frame, "RIGHT CLICK", (CAM_W - 200, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

        # Show Output
        cv2.imshow("Hand Mouse - Original Config", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()