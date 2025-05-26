"""
Main Window UI Module
Primary user interface for the gesture control system
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import time
from typing import Optional, Any
import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ui.camera_preview import CameraPreview


class MainWindow:
    """Main application window with camera preview and controls"""
    
    def __init__(self, root: tk.Tk, gesture_system, config_manager, performance_monitor):
        self.root = root
        self.gesture_system = gesture_system
        self.config_manager = config_manager
        self.performance_monitor = performance_monitor
        self.logger = logging.getLogger(__name__)
        
        # UI update control
        self.ui_update_active = True
        self.ui_update_thread = None
        
        # Current gesture display
        self.current_gesture = None
        self.current_confidence = 0.0
        
        # Performance metrics
        self.fps_counter = 0
        self.last_fps_time = time.time()
        
        # Initialize UI
        self.setup_window()
        self.create_widgets()
        self.start_ui_updates()
        
        self.logger.info("MainWindow initialized")
    
    def setup_window(self):
        """Configure main window properties"""
        self.root.title("Gesture Control System")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Set window icon (if available)
        try:
            # You could add an icon file here
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass
        
        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Style configuration
        self.style = ttk.Style()
        
        # Configure colors and fonts
        self.colors = {
            'bg_primary': '#2C3E50',
            'bg_secondary': '#34495E',
            'accent': '#3498DB',
            'success': '#27AE60',
            'warning': '#F39C12',
            'danger': '#E74C3C',
            'text_light': '#ECF0F1',
            'text_dark': '#2C3E50'
        }
    
    def create_widgets(self):
        """Create and arrange UI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=2)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Left panel - Camera and gesture display
        self.create_camera_panel(main_frame)
        
        # Right panel - Controls and status
        self.create_control_panel(main_frame)
        
        # Bottom status bar
        self.create_status_bar()
    
    def create_camera_panel(self, parent):
        """Create camera preview and gesture display panel"""
        camera_frame = ttk.LabelFrame(parent, text="Camera & Gesture Recognition", padding="10")
        camera_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        camera_frame.grid_rowconfigure(0, weight=1)
        camera_frame.grid_columnconfigure(0, weight=1)
        
        # Camera preview
        self.camera_preview = CameraPreview(
            camera_frame, 
            self.gesture_system,
            width=640, 
            height=480
        )
        self.camera_preview.frame.grid(row=0, column=0, sticky="nsew")
        
        # Gesture status display
        gesture_status_frame = ttk.Frame(camera_frame)
        gesture_status_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        gesture_status_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(gesture_status_frame, text="Current Gesture:").grid(row=0, column=0, sticky="w")
        self.gesture_label = ttk.Label(gesture_status_frame, text="None", font=("Arial", 12, "bold"))
        self.gesture_label.grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        ttk.Label(gesture_status_frame, text="Confidence:").grid(row=1, column=0, sticky="w")
        self.confidence_label = ttk.Label(gesture_status_frame, text="0.0%")
        self.confidence_label.grid(row=1, column=1, sticky="w", padx=(10, 0))
        
        # Confidence progress bar
        self.confidence_progress = ttk.Progressbar(
            gesture_status_frame, 
            length=200, 
            mode='determinate'
        )
        self.confidence_progress.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
    
    def create_control_panel(self, parent):
        """Create control panel with settings and status"""
        control_frame = ttk.LabelFrame(parent, text="Controls & Status", padding="10")
        control_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # System controls
        self.create_system_controls(control_frame)
        
        # Performance monitor
        self.create_performance_display(control_frame)
        
        # Gesture mappings
        self.create_gesture_mappings(control_frame)
        
        # Settings
        self.create_settings_panel(control_frame)
    
    def create_system_controls(self, parent):
        """Create system control buttons"""
        controls_frame = ttk.LabelFrame(parent, text="System Controls", padding="10")
        controls_frame.pack(fill="x", pady=(0, 10))
        
        # Emergency stop button
        self.emergency_button = ttk.Button(
            controls_frame,
            text="Emergency Stop",
            command=self.emergency_stop,
            style="Danger.TButton"
        )
        self.emergency_button.pack(fill="x", pady=(0, 5))
        
        # Pause/Resume button
        self.pause_button = ttk.Button(
            controls_frame,
            text="Pause Recognition",
            command=self.toggle_recognition
        )
        self.pause_button.pack(fill="x", pady=(0, 5))
        
        # Reset button
        reset_button = ttk.Button(
            controls_frame,
            text="Reset System",
            command=self.reset_system
        )
        reset_button.pack(fill="x")
    
    def create_performance_display(self, parent):
        """Create performance monitoring display"""
        perf_frame = ttk.LabelFrame(parent, text="Performance", padding="10")
        perf_frame.pack(fill="x", pady=(0, 10))
        
        # FPS display
        fps_frame = ttk.Frame(perf_frame)
        fps_frame.pack(fill="x")
        ttk.Label(fps_frame, text="FPS:").pack(side="left")
        self.fps_label = ttk.Label(fps_frame, text="0", font=("Arial", 10, "bold"))
        self.fps_label.pack(side="right")
        
        # CPU usage
        cpu_frame = ttk.Frame(perf_frame)
        cpu_frame.pack(fill="x")
        ttk.Label(cpu_frame, text="CPU:").pack(side="left")
        self.cpu_label = ttk.Label(cpu_frame, text="0%")
        self.cpu_label.pack(side="right")
        
        # Memory usage
        mem_frame = ttk.Frame(perf_frame)
        mem_frame.pack(fill="x")
        ttk.Label(mem_frame, text="Memory:").pack(side="left")
        self.memory_label = ttk.Label(mem_frame, text="0 MB")
        self.memory_label.pack(side="right")
        
        # Detection rate
        detect_frame = ttk.Frame(perf_frame)
        detect_frame.pack(fill="x")
        ttk.Label(detect_frame, text="Detection Rate:").pack(side="left")
        self.detection_label = ttk.Label(detect_frame, text="0%")
        self.detection_label.pack(side="right")
    
    def create_gesture_mappings(self, parent):
        """Create gesture mappings display"""
        mappings_frame = ttk.LabelFrame(parent, text="Gesture Mappings", padding="10")
        mappings_frame.pack(fill="x", pady=(0, 10))
        
        # Get gesture mappings from system controller
        try:
            mappings = self.gesture_system.system_controller.get_gesture_mappings()
            
            for gesture, action in mappings.items():
                mapping_frame = ttk.Frame(mappings_frame)
                mapping_frame.pack(fill="x", pady=1)
                
                ttk.Label(mapping_frame, text=f"{gesture}:", width=12).pack(side="left")
                ttk.Label(mapping_frame, text=action, font=("Arial", 8)).pack(side="left", padx=(5, 0))
                
        except Exception as e:
            self.logger.error(f"Error creating gesture mappings display: {e}")
    
    def create_settings_panel(self, parent):
        """Create settings adjustment panel"""
        settings_frame = ttk.LabelFrame(parent, text="Settings", padding="10")
        settings_frame.pack(fill="x")
        
        # Gesture threshold
        threshold_frame = ttk.Frame(settings_frame)
        threshold_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(threshold_frame, text="Gesture Threshold:").pack(side="left")
        
        self.threshold_var = tk.DoubleVar(value=self.config_manager.get_gesture_threshold())
        threshold_scale = ttk.Scale(
            threshold_frame,
            from_=0.5,
            to=1.0,
            orient="horizontal",
            variable=self.threshold_var,
            command=self.update_gesture_threshold
        )
        threshold_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Detection confidence
        confidence_frame = ttk.Frame(settings_frame)
        confidence_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(confidence_frame, text="Detection Confidence:").pack(side="left")
        
        self.detection_var = tk.DoubleVar(value=self.config_manager.get_detection_confidence())
        detection_scale = ttk.Scale(
            confidence_frame,
            from_=0.5,
            to=1.0,
            orient="horizontal",
            variable=self.detection_var,
            command=self.update_detection_confidence
        )
        detection_scale.pack(side="right", fill="x", expand=True, padx=(10, 0))
        
        # Save settings button
        save_button = ttk.Button(
            settings_frame,
            text="Save Settings",
            command=self.save_settings
        )
        save_button.pack(pady=(10, 0))
    
    def create_status_bar(self):
        """Create bottom status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(
            self.status_frame,
            text="System Ready",
            relief="sunken",
            anchor="w"
        )
        self.status_label.pack(side="left", fill="x", expand=True)
        
        # System time
        self.time_label = ttk.Label(self.status_frame, text="")
        self.time_label.pack(side="right")
    
    def start_ui_updates(self):
        """Start UI update thread"""
        self.ui_update_thread = threading.Thread(target=self.update_ui_loop, daemon=True)
        self.ui_update_thread.start()
        self.logger.info("UI update thread started")
    
    def update_ui_loop(self):
        """Main UI update loop running in separate thread"""
        while self.ui_update_active:
            try:
                # Update UI elements
                self.root.after(0, self.update_ui_elements)
                time.sleep(1/30)  # 30 FPS UI updates
                
            except Exception as e:
                self.logger.error(f"Error in UI update loop: {e}")
                time.sleep(0.1)
    
    def update_ui_elements(self):
        """Update UI elements with current system state"""
        try:
            # Update camera preview
            if hasattr(self.camera_preview, 'update_frame'):
                self.camera_preview.update_frame()
            
            # Get latest gesture data
            frame_data, gesture_data = self.gesture_system.get_latest_frame_data()
            
            if gesture_data:
                gesture = gesture_data.get('gesture', 'None')
                confidence = gesture_data.get('confidence', 0.0)
                
                self.current_gesture = gesture
                self.current_confidence = confidence
                
                # Update gesture display
                self.gesture_label.config(text=gesture or "None")
                self.confidence_label.config(text=f"{confidence*100:.1f}%")
                self.confidence_progress['value'] = confidence * 100
            
            # Update performance metrics
            self.update_performance_display()
            
            # Update status bar
            current_time = time.strftime("%H:%M:%S")
            self.time_label.config(text=current_time)
            
        except Exception as e:
            self.logger.error(f"Error updating UI elements: {e}")
    
    def update_performance_display(self):
        """Update performance metrics display"""
        try:
            # Get performance data
            perf_data = self.performance_monitor.get_current_metrics()
            
            # Update FPS
            fps = perf_data.get('fps', 0)
            self.fps_label.config(text=f"{fps:.1f}")
            
            # Update CPU usage
            cpu_usage = perf_data.get('cpu_percent', 0)
            self.cpu_label.config(text=f"{cpu_usage:.1f}%")
            
            # Update memory usage
            memory_mb = perf_data.get('memory_mb', 0)
            self.memory_label.config(text=f"{memory_mb:.1f} MB")
            
            # Update detection rate
            detection_rate = perf_data.get('detection_rate', 0)
            self.detection_label.config(text=f"{detection_rate*100:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error updating performance display: {e}")
    
    def update_gesture_threshold(self, value):
        """Update gesture recognition threshold"""
        try:
            threshold = float(value)
            self.config_manager.set_gesture_threshold(threshold)
            self.update_status(f"Gesture threshold updated to {threshold:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error updating gesture threshold: {e}")
    
    def update_detection_confidence(self, value):
        """Update detection confidence threshold"""
        try:
            confidence = float(value)
            self.config_manager.set_detection_confidence(confidence)
            self.update_status(f"Detection confidence updated to {confidence:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error updating detection confidence: {e}")
    
    def save_settings(self):
        """Save current settings to configuration file"""
        try:
            self.config_manager.save_config()
            self.update_status("Settings saved successfully")
            messagebox.showinfo("Settings", "Settings saved successfully!")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def emergency_stop(self):
        """Emergency stop all gesture recognition"""
        try:
            self.gesture_system.system_controller.emergency_stop()
            self.update_status("Emergency stop activated")
            messagebox.showwarning("Emergency Stop", "All gesture recognition stopped!")
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
    
    def toggle_recognition(self):
        """Toggle gesture recognition on/off"""
        try:
            # This would pause/resume the gesture recognition system
            # Implementation depends on the gesture system's pause functionality
            self.update_status("Recognition toggled")
            
        except Exception as e:
            self.logger.error(f"Error toggling recognition: {e}")
    
    def reset_system(self):
        """Reset the gesture recognition system"""
        try:
            if messagebox.askyesno("Reset System", "Are you sure you want to reset the system?"):
                # Reset gesture recognition buffers
                self.gesture_system.gesture_recognizer.reset_buffers()
                self.gesture_system.performance_monitor.reset_metrics()
                self.update_status("System reset completed")
                
        except Exception as e:
            self.logger.error(f"Error resetting system: {e}")
    
    def update_status(self, message: str):
        """Update status bar message"""
        try:
            self.status_label.config(text=message)
            self.logger.info(f"Status: {message}")
            
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
    
    def cleanup(self):
        """Cleanup UI resources"""
        try:
            self.ui_update_active = False
            
            if self.ui_update_thread and self.ui_update_thread.is_alive():
                self.ui_update_thread.join(timeout=1.0)
            
            if hasattr(self.camera_preview, 'cleanup'):
                self.camera_preview.cleanup()
            
            self.logger.info("MainWindow cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
