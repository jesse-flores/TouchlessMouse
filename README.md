# TouchlessMouse
A Python-based virtual mouse controlled by hand gestures using MediaPipe and OpenCV.


# Hand Gesture Mouse Controller

This project allows you to control your computer's mouse using hand gestures detected via your webcam. Leveraging MediaPipe for hand tracking and PyAutoGUI for mouse control, the system detects gestures like pinches, clenches, and open palms to move the cursor, click, scroll, and drag items—completely touch-free.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#Usage)
- [Troubleshooting](#Troubleshooting)
- [Example](#example)
- [License](#license)

## Overview

This project turns your webcam into a gesture recognition interface for controlling the mouse. It detects hand positions and gestures in real-time using [MediaPipe](https://google.github.io/mediapipe/) and interprets them to perform standard mouse actions like moving the pointer, clicking, scrolling, and dragging.

It is configurable for right- or left-handed users and includes a smoothing factor to make cursor movement feel more natural.

## Features (when right-hand_dominant = false)

- Move the mouse with both hands open  
- Scroll by raising your left hand  
- Left-click by clenching your left hand  
- Drag-and-drop using a pinch gesture  
- Right-click by clenching your right hand  
- Adjustable responsiveness via smoothing  
- Support for right- and left-handed configurations  

## Requirements

Make sure the following Python packages are installed:

- `opencv-python` for accessing the webcam and video feed  
- `mediapipe` for hand detection and tracking  
- `pyautogui` for controlling the mouse  

Install them via pip:

```bash
pip install opencv-python mediapipe pyautogui
```
## Installation
1. Clone the repository
```bash
https://github.com/jesse-flores/TouchlessMouse.git
```

## Usage
Run the script:
```bash
Python hand_mouse.py
```

### Settings
Edit these at the top of the script:
```bash
right_handed_dominant = True
smooth_factor = 0.2
```

## Troubleshooting
- Ensure good lighting
- Keep hands clearly visible
- Adjust smooth_factor if cursor jumps
- Webcame not working? Try changing index in cv2.VideoCapture(0)

## Example
Soon.

## License
This project is licensed under the MIT License.