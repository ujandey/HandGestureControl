#!/usr/bin/env python3
"""
Advanced Hand Gesture PC Control System
Main entry point for the gesture recognition application
"""

import sys
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox
import cv2
import logging
import os

# Set environment for headless operation
os.environ['DISPLAY'] = ':0'
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.hand_detector import HandDetector
from core.gesture_recognizer import GestureRecognizer
from core.system_controller import SystemController
from ui.main_window import MainWindow
from utils.config_manager import ConfigManager
from utils.performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gesture_control.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class GestureControlSystem:
    """Main application class that coordinates all system components"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.threads = []
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.performance_monitor = PerformanceMonitor()
        self.hand_detector = HandDetector(self.config_manager)
        self.gesture_recognizer = GestureRecognizer(self.config_manager)
        self.system_controller = SystemController(self.config_manager)
        
        # Initialize camera
        self.camera = None
        self.camera_lock = threading.Lock()
        
        # Initialize UI
        self.root = None
        self.main_window = None
        
        # Thread management
        self.capture_thread = None
        self.processing_thread = None
        self.ui_thread = None
        
        # Shared data structures
        self.frame_queue = []
        self.gesture_queue = []
        self.queue_lock = threading.Lock()
        
    def initialize_camera(self):
        """Initialize camera with error handling"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise Exception("Could not open camera")
                
            # Set camera properties for optimal performance
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.logger.info("Camera initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            messagebox.showerror("Camera Error", 
                               f"Could not initialize camera: {e}\n"
                               "Please check camera permissions and availability.")
            return False
    
    def capture_frames(self):
        """Capture frames from camera in separate thread"""
        self.logger.info("Starting frame capture thread")
        
        while self.running:
            try:
                with self.camera_lock:
                    if self.camera is None or not self.camera.isOpened():
                        break
                        
                    ret, frame = self.camera.read()
                    if not ret:
                        continue
                
                # Add frame to queue (keep only latest frame to prevent lag)
                with self.queue_lock:
                    self.frame_queue = [frame]  # Replace with latest frame
                
                # Control frame rate
                time.sleep(1/30)  # Target 30 FPS
                
            except Exception as e:
                self.logger.error(f"Error in frame capture: {e}")
                break
        
        self.logger.info("Frame capture thread stopped")
    
    def process_gestures(self):
        """Process gestures in separate thread"""
        self.logger.info("Starting gesture processing thread")
        
        while self.running:
            try:
                # Get latest frame
                frame = None
                with self.queue_lock:
                    if self.frame_queue:
                        frame = self.frame_queue[0]
                
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Detect hands
                hand_landmarks = self.hand_detector.detect_hands(frame)
                
                if hand_landmarks:
                    # Recognize gesture
                    gesture, confidence = self.gesture_recognizer.recognize_gesture(hand_landmarks)
                    
                    if gesture and confidence > self.config_manager.get_gesture_threshold():
                        # Add to gesture queue
                        with self.queue_lock:
                            self.gesture_queue.append({
                                'gesture': gesture,
                                'confidence': confidence,
                                'timestamp': time.time(),
                                'landmarks': hand_landmarks
                            })
                        
                        # Execute system action
                        self.system_controller.execute_gesture_action(gesture, confidence)
                
                # Update performance metrics
                self.performance_monitor.update_frame_processed()
                
            except Exception as e:
                self.logger.error(f"Error in gesture processing: {e}")
                time.sleep(0.1)
        
        self.logger.info("Gesture processing thread stopped")
    
    def start_threads(self):
        """Start all processing threads"""
        self.running = True
        
        # Start capture thread
        self.capture_thread = threading.Thread(target=self.capture_frames, daemon=True)
        self.capture_thread.start()
        self.threads.append(self.capture_thread)
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self.process_gestures, daemon=True)
        self.processing_thread.start()
        self.threads.append(self.processing_thread)
        
        self.logger.info("All processing threads started")
    
    def stop_threads(self):
        """Stop all processing threads gracefully"""
        self.logger.info("Stopping all threads...")
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        # Release camera
        with self.camera_lock:
            if self.camera:
                self.camera.release()
                self.camera = None
        
        self.logger.info("All threads stopped")
    
    def get_latest_frame_data(self):
        """Get latest frame and gesture data for UI"""
        frame_data = None
        gesture_data = None
        
        with self.queue_lock:
            if self.frame_queue:
                frame_data = self.frame_queue[0].copy()
            
            if self.gesture_queue:
                # Get most recent gesture
                gesture_data = self.gesture_queue[-1]
                # Keep only recent gestures (last 10)
                self.gesture_queue = self.gesture_queue[-10:]
        
        return frame_data, gesture_data
    
    def run(self):
        """Main application entry point"""
        self.logger.info("Starting Gesture Control System")
        
        try:
            # Initialize camera
            if not self.initialize_camera():
                return
            
            # Start background threads
            self.start_threads()
            
            # Initialize and start UI
            self.root = tk.Tk()
            self.main_window = MainWindow(
                self.root, 
                self, 
                self.config_manager,
                self.performance_monitor
            )
            
            # Set up proper shutdown
            self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
            
            # Start UI main loop
            self.logger.info("Starting UI main loop")
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Critical error in main application: {e}")
            messagebox.showerror("Critical Error", f"Application failed: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown of the application"""
        self.logger.info("Shutting down application")
        
        # Stop processing threads
        self.stop_threads()
        
        # Destroy UI
        if self.root:
            self.root.quit()
            self.root.destroy()
        
        self.logger.info("Application shutdown complete")


def main():
    """Application entry point"""
    try:
        # Create and run the application
        app = GestureControlSystem()
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        print(f"Critical error: {e}")
    finally:
        # Ensure OpenCV windows are closed
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
