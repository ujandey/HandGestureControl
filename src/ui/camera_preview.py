"""
Camera Preview Widget
Displays live camera feed with hand landmark overlay
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import logging
import threading
import time
from typing import Optional, Any


class CameraPreview:
    """Camera preview widget with hand landmark visualization"""
    
    def __init__(self, parent, gesture_system, width=640, height=480):
        self.parent = parent
        self.gesture_system = gesture_system
        self.width = width
        self.height = height
        self.logger = logging.getLogger(__name__)
        
        # UI elements
        self.frame = ttk.Frame(parent)
        self.canvas = None
        self.photo = None
        
        # Update control
        self.update_active = True
        self.last_update_time = time.time()
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
        # Drawing settings
        self.show_landmarks = True
        self.show_connections = True
        self.show_gesture_info = True
        
        # Colors for visualization
        self.colors = {
            'landmarks': (0, 255, 0),      # Green
            'connections': (255, 255, 255), # White
            'gesture_text': (255, 255, 0),  # Yellow
            'confidence_bar': (0, 255, 255) # Cyan
        }
        
        # Initialize UI
        self.create_widgets()
        
        self.logger.info("CameraPreview initialized")
    
    def create_widgets(self):
        """Create camera preview widgets"""
        # Main canvas for camera display
        self.canvas = tk.Canvas(
            self.frame,
            width=self.width,
            height=self.height,
            bg='black'
        )
        self.canvas.pack(pady=(0, 10))
        
        # Control buttons
        controls_frame = ttk.Frame(self.frame)
        controls_frame.pack(fill="x")
        
        # Toggle landmarks button
        self.landmarks_button = ttk.Button(
            controls_frame,
            text="Hide Landmarks",
            command=self.toggle_landmarks
        )
        self.landmarks_button.pack(side="left", padx=(0, 5))
        
        # Toggle connections button
        self.connections_button = ttk.Button(
            controls_frame,
            text="Hide Connections",
            command=self.toggle_connections
        )
        self.connections_button.pack(side="left", padx=(0, 5))
        
        # Toggle gesture info button
        self.info_button = ttk.Button(
            controls_frame,
            text="Hide Info",
            command=self.toggle_gesture_info
        )
        self.info_button.pack(side="left")
        
        # FPS display
        self.fps_label = ttk.Label(controls_frame, text="FPS: 0")
        self.fps_label.pack(side="right")
    
    def update_frame(self):
        """Update camera preview with latest frame"""
        try:
            # Get latest frame and gesture data
            frame_data, gesture_data = self.gesture_system.get_latest_frame_data()
            
            if frame_data is None:
                return
            
            # Process frame for display
            display_frame = self.process_frame_for_display(frame_data, gesture_data)
            
            # Convert to PhotoImage and display
            self.display_frame(display_frame)
            
            # Update FPS counter
            self.update_fps_counter()
            
        except Exception as e:
            self.logger.error(f"Error updating camera frame: {e}")
    
    def process_frame_for_display(self, frame: np.ndarray, gesture_data: Optional[dict]) -> np.ndarray:
        """Process frame for display with overlays"""
        try:
            # Create a copy for modification
            display_frame = frame.copy()
            
            # Resize frame to canvas size
            display_frame = cv2.resize(display_frame, (self.width, self.height))
            
            # Get hand landmarks if available
            hands_landmarks = None
            if hasattr(self.gesture_system, 'hand_detector'):
                hands_landmarks = self.gesture_system.hand_detector.detect_hands(display_frame)
            
            # Draw hand landmarks and connections
            if hands_landmarks and (self.show_landmarks or self.show_connections):
                display_frame = self.draw_hand_overlays(display_frame, hands_landmarks)
            
            # Draw gesture information
            if gesture_data and self.show_gesture_info:
                display_frame = self.draw_gesture_info(display_frame, gesture_data)
            
            # Draw system status
            display_frame = self.draw_system_status(display_frame)
            
            return display_frame
            
        except Exception as e:
            self.logger.error(f"Error processing frame for display: {e}")
            return frame
    
    def draw_hand_overlays(self, frame: np.ndarray, hands_landmarks) -> np.ndarray:
        """Draw hand landmarks and connections on frame"""
        try:
            if not hands_landmarks:
                return frame
            
            for landmarks in hands_landmarks:
                # Draw connections between landmarks
                if self.show_connections:
                    frame = self.draw_hand_connections(frame, landmarks)
                
                # Draw individual landmarks
                if self.show_landmarks:
                    frame = self.draw_hand_landmarks(frame, landmarks)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error drawing hand overlays: {e}")
            return frame
    
    def draw_hand_landmarks(self, frame: np.ndarray, landmarks) -> np.ndarray:
        """Draw hand landmark points"""
        try:
            for i, (x, y, z) in enumerate(landmarks):
                # Different colors for different types of landmarks
                if i in [4, 8, 12, 16, 20]:  # Finger tips
                    color = (0, 255, 0)  # Green
                    radius = 6
                elif i in [2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15, 17, 18, 19]:  # Joints
                    color = (255, 255, 0)  # Yellow
                    radius = 4
                else:  # Wrist and palm
                    color = (255, 0, 0)  # Red
                    radius = 5
                
                # Draw landmark point
                cv2.circle(frame, (int(x), int(y)), radius, color, -1)
                
                # Draw landmark number (optional, for debugging)
                if i in [0, 4, 8, 12, 16, 20]:  # Key landmarks only
                    cv2.putText(frame, str(i), (int(x) + 10, int(y) - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error drawing hand landmarks: {e}")
            return frame
    
    def draw_hand_connections(self, frame: np.ndarray, landmarks) -> np.ndarray:
        """Draw connections between hand landmarks"""
        try:
            # MediaPipe hand connections
            connections = [
                # Thumb
                (0, 1), (1, 2), (2, 3), (3, 4),
                # Index finger
                (0, 5), (5, 6), (6, 7), (7, 8),
                # Middle finger
                (0, 9), (9, 10), (10, 11), (11, 12),
                # Ring finger
                (0, 13), (13, 14), (14, 15), (15, 16),
                # Pinky
                (0, 17), (17, 18), (18, 19), (19, 20),
                # Palm
                (5, 9), (9, 13), (13, 17)
            ]
            
            for start_idx, end_idx in connections:
                if start_idx < len(landmarks) and end_idx < len(landmarks):
                    start_point = landmarks[start_idx]
                    end_point = landmarks[end_idx]
                    
                    cv2.line(frame,
                            (int(start_point[0]), int(start_point[1])),
                            (int(end_point[0]), int(end_point[1])),
                            self.colors['connections'], 2)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error drawing hand connections: {e}")
            return frame
    
    def draw_gesture_info(self, frame: np.ndarray, gesture_data: dict) -> np.ndarray:
        """Draw gesture information overlay"""
        try:
            gesture = gesture_data.get('gesture', 'None')
            confidence = gesture_data.get('confidence', 0.0)
            
            # Draw gesture name
            text = f"Gesture: {gesture}"
            cv2.putText(frame, text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.colors['gesture_text'], 2)
            
            # Draw confidence score
            confidence_text = f"Confidence: {confidence*100:.1f}%"
            cv2.putText(frame, confidence_text, (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.colors['gesture_text'], 2)
            
            # Draw confidence bar
            bar_width = 200
            bar_height = 10
            bar_x = 10
            bar_y = 70
            
            # Background bar
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height),
                         (100, 100, 100), -1)
            
            # Confidence level bar
            conf_width = int(bar_width * confidence)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + conf_width, bar_y + bar_height),
                         self.colors['confidence_bar'], -1)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error drawing gesture info: {e}")
            return frame
    
    def draw_system_status(self, frame: np.ndarray) -> np.ndarray:
        """Draw system status information"""
        try:
            # Draw FPS in bottom right
            fps_text = f"FPS: {self.fps_counter:.1f}"
            text_size = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.putText(frame, fps_text,
                       (self.width - text_size[0] - 10, self.height - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Draw system status indicator
            status_color = (0, 255, 0) if self.gesture_system.running else (0, 0, 255)
            cv2.circle(frame, (self.width - 20, 20), 8, status_color, -1)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error drawing system status: {e}")
            return frame
    
    def display_frame(self, frame: np.ndarray):
        """Display processed frame on canvas"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convert to PhotoImage
            self.photo = ImageTk.PhotoImage(image=pil_image)
            
            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
        except Exception as e:
            self.logger.error(f"Error displaying frame: {e}")
    
    def update_fps_counter(self):
        """Update FPS counter"""
        try:
            current_time = time.time()
            
            # Calculate FPS every second
            if current_time - self.fps_start_time >= 1.0:
                # Update FPS label
                self.fps_label.config(text=f"FPS: {self.fps_counter:.1f}")
                
                # Reset counter
                self.fps_counter = 0
                self.fps_start_time = current_time
            else:
                self.fps_counter += 1
            
        except Exception as e:
            self.logger.error(f"Error updating FPS counter: {e}")
    
    def toggle_landmarks(self):
        """Toggle landmark display"""
        self.show_landmarks = not self.show_landmarks
        button_text = "Show Landmarks" if not self.show_landmarks else "Hide Landmarks"
        self.landmarks_button.config(text=button_text)
        self.logger.info(f"Landmarks display: {self.show_landmarks}")
    
    def toggle_connections(self):
        """Toggle connection lines display"""
        self.show_connections = not self.show_connections
        button_text = "Show Connections" if not self.show_connections else "Hide Connections"
        self.connections_button.config(text=button_text)
        self.logger.info(f"Connections display: {self.show_connections}")
    
    def toggle_gesture_info(self):
        """Toggle gesture information display"""
        self.show_gesture_info = not self.show_gesture_info
        button_text = "Show Info" if not self.show_gesture_info else "Hide Info"
        self.info_button.config(text=button_text)
        self.logger.info(f"Gesture info display: {self.show_gesture_info}")
    
    def set_display_settings(self, landmarks=True, connections=True, gesture_info=True):
        """Set display settings programmatically"""
        self.show_landmarks = landmarks
        self.show_connections = connections
        self.show_gesture_info = gesture_info
        
        # Update button texts
        self.landmarks_button.config(
            text="Hide Landmarks" if landmarks else "Show Landmarks"
        )
        self.connections_button.config(
            text="Hide Connections" if connections else "Show Connections"
        )
        self.info_button.config(
            text="Hide Info" if gesture_info else "Show Info"
        )
    
    def cleanup(self):
        """Cleanup camera preview resources"""
        try:
            self.update_active = False
            
            if self.canvas:
                self.canvas.delete("all")
            
            self.logger.info("CameraPreview cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
