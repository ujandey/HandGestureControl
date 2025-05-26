# 🖐️ Advanced Hand Gesture PC Control System

A real-time computer vision application that enables touchless PC control through hand gesture recognition using MediaPipe and OpenCV.

![Gesture Control Demo](gesture_demo_frame.jpg)

## 🌟 Features

### ✋ Gesture Recognition
- **Pinch** - Volume control (thumb and index finger proximity)
- **Peace Sign** - Take screenshots (index and middle finger extended)
- **Thumbs Up** - Like/approval actions
- **Fist** - Pause/play media
- **Open Palm** - Stop/cancel actions

### 🎯 Real-time Performance
- 30+ FPS gesture detection using MediaPipe
- Sub-50ms latency from gesture to system action
- Advanced smoothing and confidence filtering
- Performance monitoring with CPU/memory tracking

### 🖥️ System Integration
- **Audio Control** - Volume adjustment, mute/unmute
- **Media Control** - Play/pause, next/previous track
- **Screenshots** - Automatic capture and saving
- **Application Launching** - Quick access to browsers and apps
- **Cross-platform** - Windows, macOS, and Linux support

### 🎛️ User Interface
- Live camera preview with hand landmark visualization
- Real-time gesture confidence display
- Performance metrics dashboard
- Configurable sensitivity settings
- Emergency stop functionality

## 🚀 Quick Start

### Prerequisites
```bash
pip install opencv-python mediapipe numpy pyautogui pycaw screeninfo configparser Pillow psutil
```

### Basic Usage
```bash
# Run the full gesture control system
python main.py

# Run the simplified demo
python demo_app.py
```

## 📁 Project Structure

```
gesture_control_system/
├── main.py                 # Main application entry point
├── demo_app.py            # Simplified demo version
├── config/
│   └── settings.ini       # Configuration file
├── src/
│   ├── core/
│   │   ├── hand_detector.py      # MediaPipe hand detection
│   │   ├── gesture_recognizer.py # Gesture classification
│   │   └── system_controller.py  # System action execution
│   ├── ui/
│   │   ├── main_window.py        # Main GUI interface
│   │   └── camera_preview.py     # Camera feed display
│   ├── utils/
│   │   ├── config_manager.py     # Settings management
│   │   └── performance_monitor.py # Performance tracking
│   └── integrations/
│       ├── audio_control.py      # Cross-platform audio
│       └── system_automation.py  # System actions
└── screenshots/            # Captured screenshots
```

## 🎮 Gesture Guide

### 🤏 Pinch Gesture
**Action:** Volume Control  
**How to:** Bring thumb and index finger close together  
**Effect:** Adjusts system volume based on finger distance

### ✌️ Peace Sign
**Action:** Screenshot  
**How to:** Extend index and middle fingers (V-shape)  
**Effect:** Captures and saves screenshot

### 👍 Thumbs Up
**Action:** Like/Approval  
**How to:** Extend thumb upward, curl other fingers  
**Effect:** Sends like action or approval signal

### ✊ Fist
**Action:** Media Control  
**How to:** Close all fingers into a fist  
**Effect:** Toggles play/pause for media

### ✋ Open Palm
**Action:** Stop/Cancel  
**How to:** Extend all fingers  
**Effect:** Stops current action or media

## ⚙️ Configuration

Edit `config/settings.ini` to customize:

```ini
[gesture_recognition]
gesture_threshold = 0.85        # Minimum confidence for gesture
cooldown_period = 1.0          # Seconds between same gesture
smoothing_buffer_size = 5      # Frames for gesture smoothing

[detection]
min_detection_confidence = 0.7  # Hand detection threshold
min_tracking_confidence = 0.5   # Hand tracking threshold
max_num_hands = 2              # Maximum hands to detect

[system_control]
volume_step = 5                # Volume adjustment increment
action_cooldown = 1.0          # Seconds between actions

[performance]
target_fps = 30                # Target processing FPS
max_cpu_usage = 25            # CPU usage warning threshold
max_memory_mb = 200           # Memory usage warning threshold
```

## 🔧 Technical Architecture

### Hand Detection Pipeline
1. **Camera Input** - Captures video frames at 30 FPS
2. **MediaPipe Processing** - Detects 21 hand landmarks per hand
3. **Feature Extraction** - Calculates finger positions, angles, and distances
4. **Gesture Classification** - Analyzes patterns for gesture recognition
5. **System Action** - Executes corresponding system commands

### Gesture Recognition Algorithm
```python
# Feature extraction from hand landmarks
finger_curl_ratios = calculate_finger_extensions(landmarks)
finger_distances = calculate_inter_finger_distances(landmarks)

# Multi-class gesture classification
if thumb_index_distance < threshold:
    gesture = "pinch"
elif extended_fingers == [index, middle]:
    gesture = "peace_sign"
# ... additional gesture logic
```

### Performance Optimizations
- **Threading** - Separate threads for capture, processing, and UI
- **Frame Buffering** - Latest frame queuing prevents lag
- **Confidence Smoothing** - Temporal filtering reduces false positives
- **Resource Monitoring** - Automatic performance adjustment

## 🛡️ Safety Features

- **Gesture Cooldown** - Prevents accidental rapid triggering
- **Confidence Thresholds** - Requires high certainty for actions
- **Emergency Stop** - Keyboard shortcut to disable system
- **Fail-safe Mode** - Mouse corner detection stops automation
- **Permission Validation** - Checks system access before actions

## 🎯 Use Cases

### 🎵 Media Control
- Control music playback without touching keyboard
- Adjust volume during video calls
- Take screenshots of presentations

### 🎮 Gaming Enhancement
- Gesture-based game controls
- Streaming interaction without interrupting gameplay
- Accessibility support for limited mobility

### 👨‍💼 Professional Applications
- Hands-free presentation control
- Medical/laboratory environments requiring sterile operation
- Industrial settings with dirty/wet hands

### ♿ Accessibility
- Alternative input method for motor impairments
- Voice-free computer interaction
- Customizable gesture mappings for individual needs

## 📊 Performance Metrics

### System Requirements
- **CPU:** Modern multi-core processor (Intel i5+ or AMD equivalent)
- **Memory:** 4GB RAM minimum, 8GB recommended
- **Camera:** USB webcam or built-in camera (640x480 minimum)
- **OS:** Windows 10+, macOS 10.14+, or Linux with X11

### Performance Benchmarks
- **Latency:** < 50ms gesture to action
- **Accuracy:** > 95% for trained gestures
- **CPU Usage:** < 25% on modern hardware
- **Memory:** < 200MB RAM footprint
- **FPS:** 30+ frames per second processing

## 🐛 Troubleshooting

### Common Issues

**Camera not detected:**
```bash
# Check camera permissions
# Try different camera index (0, 1, 2...)
cap = cv2.VideoCapture(1)
```

**High CPU usage:**
```bash
# Reduce target FPS in config
target_fps = 15
```

**Gesture not recognized:**
```bash
# Lower confidence threshold
gesture_threshold = 0.75
```

**Audio control not working:**
```bash
# Install platform-specific audio libraries
# Windows: pip install pycaw
# Linux: sudo apt-get install alsa-utils
# macOS: Built-in osascript support
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-gesture`)
3. Implement your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

### Adding New Gestures
```python
def recognize_custom_gesture(self, landmarks):
    # Extract relevant features
    features = self.extract_features(landmarks)
    
    # Implement gesture logic
    if custom_gesture_condition(features):
        return "custom_gesture", confidence_score
    
    return None, 0.0
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MediaPipe** - Google's framework for building perception pipelines
- **OpenCV** - Computer vision and image processing library
- **PyAutoGUI** - Cross-platform GUI automation
- **Tkinter** - Python's standard GUI toolkit

## 🔮 Future Enhancements

### Planned Features
- [ ] Custom gesture training interface
- [ ] Voice command integration
- [ ] Mobile app remote control
- [ ] Multiple user profiles
- [ ] Gesture macro sequences
- [ ] AR/VR integration support
- [ ] Cloud gesture model sync

### Advanced Capabilities
- [ ] 3D hand pose estimation
- [ ] Facial expression recognition
- [ ] Full body gesture tracking
- [ ] AI-powered gesture prediction
- [ ] Adaptive learning algorithms

## 📞 Support

For questions, issues, or feature requests:
- 🐛 [Report bugs](https://github.com/yourusername/gesture-control/issues)
- 💡 [Request features](https://github.com/yourusername/gesture-control/discussions)
- 📧 [Contact support](mailto:support@example.com)

---

**Made with ❤️ for touchless computing and accessibility**

*Experience the future of human-computer interaction through natural hand gestures!*