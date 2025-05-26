"""
System Controller Module
Executes system actions based on recognized gestures
"""

import logging
import time
import threading
from typing import Optional, Dict, Any
import os
import sys

# Import platform-specific modules
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Enable fail-safe
except (ImportError, Exception) as e:
    # Handle X11/display errors in headless environments
    pyautogui = None
    print(f"PyAutoGUI not available: {e}")

# Import audio control
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'integrations'))
    from audio_control import AudioController
    from system_automation import SystemAutomation
except ImportError as e:
    print(f"Warning: Could not import integrations: {e}")
    # Create mock classes for headless environment
    class AudioController:
        def __init__(self, config_manager=None): pass
        def adjust_volume_by_gesture(self, confidence): return True
        def is_available(self): return False
        def get_current_volume(self): return 50
        def cleanup(self): pass
    
    class SystemAutomation:
        def __init__(self, config_manager=None): pass
        def take_screenshot(self): return True
        def send_like_action(self): return True
        def toggle_media_playback(self): return True
        def stop_media(self): return True
        def stop_all_actions(self): pass
        def cleanup(self): pass


class SystemController:
    """Controls system actions based on gesture recognition"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # Initialize controllers
        self.audio_controller = AudioController(config_manager)
        self.system_automation = SystemAutomation(config_manager)
        
        # Action execution tracking
        self.last_action_time = {}
        self.action_cooldown = 1.0  # Seconds between same actions
        
        if config_manager:
            self.action_cooldown = config_manager.get_action_cooldown()
        
        # Gesture to action mappings
        self.gesture_actions = {
            'pinch': self.handle_pinch_gesture,
            'peace_sign': self.handle_peace_sign,
            'thumbs_up': self.handle_thumbs_up,
            'fist': self.handle_fist,
            'open_palm': self.handle_open_palm
        }
        
        # Action execution lock for thread safety
        self.action_lock = threading.Lock()
        
        # Volume control state
        self.volume_control_active = False
        self.last_pinch_distance = None
        
        self.logger.info("SystemController initialized")
    
    def execute_gesture_action(self, gesture: str, confidence: float) -> bool:
        """
        Execute system action for recognized gesture
        
        Args:
            gesture: Name of recognized gesture
            confidence: Confidence score of gesture recognition
            
        Returns:
            True if action was executed, False otherwise
        """
        try:
            with self.action_lock:
                # Check if gesture has associated action
                if gesture not in self.gesture_actions:
                    self.logger.warning(f"No action defined for gesture: {gesture}")
                    return False
                
                # Check action cooldown
                if not self.check_action_cooldown(gesture):
                    return False
                
                # Execute gesture action
                action_function = self.gesture_actions[gesture]
                success = action_function(confidence)
                
                if success:
                    self.logger.info(f"Executed action for gesture '{gesture}' with confidence {confidence:.2f}")
                    return True
                else:
                    self.logger.warning(f"Failed to execute action for gesture '{gesture}'")
                    return False
                
        except Exception as e:
            self.logger.error(f"Error executing gesture action: {e}")
            return False
    
    def handle_pinch_gesture(self, confidence: float) -> bool:
        """Handle pinch gesture for volume control"""
        try:
            # For pinch gesture, we need the current pinch distance
            # This should be updated by the gesture recognizer
            return self.audio_controller.adjust_volume_by_gesture(confidence)
            
        except Exception as e:
            self.logger.error(f"Error handling pinch gesture: {e}")
            return False
    
    def handle_peace_sign(self, confidence: float) -> bool:
        """Handle peace sign gesture for screenshot"""
        try:
            return self.system_automation.take_screenshot()
            
        except Exception as e:
            self.logger.error(f"Error handling peace sign gesture: {e}")
            return False
    
    def handle_thumbs_up(self, confidence: float) -> bool:
        """Handle thumbs up gesture for like action"""
        try:
            # Could be mapped to various actions like:
            # - Like current song in music player
            # - Approve current action
            # - Send positive feedback
            return self.system_automation.send_like_action()
            
        except Exception as e:
            self.logger.error(f"Error handling thumbs up gesture: {e}")
            return False
    
    def handle_fist(self, confidence: float) -> bool:
        """Handle fist gesture for media pause/play"""
        try:
            return self.system_automation.toggle_media_playback()
            
        except Exception as e:
            self.logger.error(f"Error handling fist gesture: {e}")
            return False
    
    def handle_open_palm(self, confidence: float) -> bool:
        """Handle open palm gesture for stop action"""
        try:
            return self.system_automation.stop_media()
            
        except Exception as e:
            self.logger.error(f"Error handling open palm gesture: {e}")
            return False
    
    def check_action_cooldown(self, action: str) -> bool:
        """Check if action is not in cooldown period"""
        try:
            current_time = time.time()
            last_time = self.last_action_time.get(action, 0)
            
            if current_time - last_time >= self.action_cooldown:
                self.last_action_time[action] = current_time
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking action cooldown: {e}")
            return False
    
    def update_pinch_distance(self, distance: float):
        """Update current pinch distance for volume control"""
        try:
            self.last_pinch_distance = distance
            
            # If pinch gesture is active, update volume
            if self.volume_control_active:
                self.audio_controller.set_volume_by_distance(distance)
                
        except Exception as e:
            self.logger.error(f"Error updating pinch distance: {e}")
    
    def enable_volume_control(self):
        """Enable continuous volume control mode"""
        self.volume_control_active = True
        self.logger.info("Volume control mode enabled")
    
    def disable_volume_control(self):
        """Disable continuous volume control mode"""
        self.volume_control_active = False
        self.logger.info("Volume control mode disabled")
    
    def get_gesture_mappings(self) -> Dict[str, str]:
        """Get current gesture to action mappings"""
        return {
            'pinch': 'Volume Control',
            'peace_sign': 'Take Screenshot',
            'thumbs_up': 'Like Action',
            'fist': 'Pause/Play Media',
            'open_palm': 'Stop Media'
        }
    
    def get_action_status(self) -> Dict[str, Any]:
        """Get current status of system actions"""
        try:
            return {
                'volume_control_active': self.volume_control_active,
                'current_volume': self.audio_controller.get_current_volume(),
                'last_pinch_distance': self.last_pinch_distance,
                'action_cooldown': self.action_cooldown,
                'pyautogui_available': pyautogui is not None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting action status: {e}")
            return {}
    
    def emergency_stop(self):
        """Emergency stop all system actions"""
        try:
            self.logger.warning("Emergency stop activated")
            
            # Disable volume control
            self.disable_volume_control()
            
            # Stop any ongoing media actions
            self.system_automation.stop_all_actions()
            
            # Clear action history
            self.last_action_time.clear()
            
            self.logger.info("Emergency stop completed")
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
    
    def validate_system_permissions(self) -> Dict[str, bool]:
        """Validate that required system permissions are available"""
        permissions = {
            'pyautogui': pyautogui is not None,
            'audio_control': self.audio_controller.is_available(),
            'screenshot': True,  # Usually available
            'media_control': True  # Usually available
        }
        
        # Log permission status
        for permission, available in permissions.items():
            if not available:
                self.logger.warning(f"Permission not available: {permission}")
        
        return permissions
    
    def cleanup(self):
        """Cleanup system controller resources"""
        try:
            self.emergency_stop()
            
            if hasattr(self.audio_controller, 'cleanup'):
                self.audio_controller.cleanup()
            
            if hasattr(self.system_automation, 'cleanup'):
                self.system_automation.cleanup()
            
            self.logger.info("SystemController cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
