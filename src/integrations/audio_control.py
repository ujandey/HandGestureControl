"""
Audio Control Module
Cross-platform audio control with gesture integration
"""

import logging
import platform
import subprocess
import os
from typing import Optional, Union
import time

# Platform-specific imports
try:
    if platform.system() == "Windows":
        from pycaw.pycaw import AudioUtilities, AudioSession, ISimpleAudioVolume
        from comtypes import CLSCTX_ALL
        from pycaw.api.endpointvolume import IAudioEndpointVolume
        import comtypes
    else:
        # For non-Windows platforms, we'll use system commands
        pass
except ImportError as e:
    # Handle missing dependencies gracefully
    pass


class AudioController:
    """Cross-platform audio control with gesture integration"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.platform = platform.system()
        
        # Audio control settings
        self.volume_step = 5
        self.min_volume = 0
        self.max_volume = 100
        self.current_volume = 50
        self.is_muted = False
        
        # Load settings from config
        if config_manager:
            self.volume_step = config_manager.get_volume_step()
        
        # Platform-specific initialization
        self.audio_interface = None
        self.volume_interface = None
        self._initialize_audio_interface()
        
        # Gesture-based volume control
        self.pinch_volume_active = False
        self.last_pinch_distance = None
        self.volume_sensitivity = 2.0  # Sensitivity multiplier
        
        self.logger.info(f"AudioController initialized for {self.platform}")
    
    def _initialize_audio_interface(self):
        """Initialize platform-specific audio interface"""
        try:
            if self.platform == "Windows":
                self._initialize_windows_audio()
            elif self.platform == "Darwin":  # macOS
                self._initialize_macos_audio()
            elif self.platform == "Linux":
                self._initialize_linux_audio()
            else:
                self.logger.warning(f"Unsupported platform: {self.platform}")
                
        except Exception as e:
            self.logger.error(f"Error initializing audio interface: {e}")
    
    def _initialize_windows_audio(self):
        """Initialize Windows audio interface using pycaw"""
        try:
            # Get the default audio device
            devices = AudioUtilities.GetSpeakers()
            self.audio_interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_interface = self.audio_interface.QueryInterface(IAudioEndpointVolume)
            
            # Get current volume
            self.current_volume = int(self.volume_interface.GetMasterScalarVolume() * 100)
            self.is_muted = self.volume_interface.GetMute()
            
            self.logger.info("Windows audio interface initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing Windows audio: {e}")
            self.volume_interface = None
    
    def _initialize_macos_audio(self):
        """Initialize macOS audio interface using osascript"""
        try:
            # Test if osascript is available
            result = subprocess.run(['osascript', '-e', 'get volume settings'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Parse current volume from output
                output = result.stdout.strip()
                if "output volume:" in output:
                    volume_str = output.split("output volume:")[1].split(",")[0].strip()
                    self.current_volume = int(volume_str)
                
                self.logger.info("macOS audio interface initialized")
            else:
                self.logger.error("osascript not available or failed")
                
        except Exception as e:
            self.logger.error(f"Error initializing macOS audio: {e}")
    
    def _initialize_linux_audio(self):
        """Initialize Linux audio interface using amixer"""
        try:
            # Test if amixer is available
            result = subprocess.run(['amixer', 'get', 'Master'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Parse current volume from amixer output
                output = result.stdout
                if "[" in output and "]" in output:
                    # Extract percentage value
                    for line in output.split('\n'):
                        if '[' in line and '%' in line:
                            start = line.find('[') + 1
                            end = line.find('%')
                            if start < end:
                                volume_str = line[start:end]
                                try:
                                    self.current_volume = int(volume_str)
                                    break
                                except ValueError:
                                    continue
                
                self.logger.info("Linux audio interface initialized")
            else:
                self.logger.error("amixer not available or failed")
                
        except Exception as e:
            self.logger.error(f"Error initializing Linux audio: {e}")
    
    def get_current_volume(self) -> int:
        """Get current system volume level (0-100)"""
        try:
            if self.platform == "Windows" and self.volume_interface:
                self.current_volume = int(self.volume_interface.GetMasterScalarVolume() * 100)
            elif self.platform == "Darwin":
                result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'],
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    self.current_volume = int(result.stdout.strip())
            elif self.platform == "Linux":
                result = subprocess.run(['amixer', 'get', 'Master'],
                                      capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    # Parse volume from amixer output
                    output = result.stdout
                    for line in output.split('\n'):
                        if '[' in line and '%' in line:
                            start = line.find('[') + 1
                            end = line.find('%')
                            if start < end:
                                volume_str = line[start:end]
                                try:
                                    self.current_volume = int(volume_str)
                                    break
                                except ValueError:
                                    continue
            
            return self.current_volume
            
        except Exception as e:
            self.logger.error(f"Error getting current volume: {e}")
            return self.current_volume
    
    def set_volume(self, volume: int) -> bool:
        """Set system volume level (0-100)"""
        try:
            # Clamp volume to valid range
            volume = max(self.min_volume, min(self.max_volume, volume))
            
            if self.platform == "Windows" and self.volume_interface:
                # Set volume using Windows API
                scalar_volume = volume / 100.0
                self.volume_interface.SetMasterScalarVolume(scalar_volume, None)
                success = True
                
            elif self.platform == "Darwin":
                # Set volume using osascript
                result = subprocess.run(['osascript', '-e', f'set volume output volume {volume}'],
                                      capture_output=True, timeout=3)
                success = result.returncode == 0
                
            elif self.platform == "Linux":
                # Set volume using amixer
                result = subprocess.run(['amixer', 'set', 'Master', f'{volume}%'],
                                      capture_output=True, timeout=3)
                success = result.returncode == 0
            else:
                self.logger.warning(f"Volume control not supported on {self.platform}")
                success = False
            
            if success:
                self.current_volume = volume
                self.logger.debug(f"Volume set to {volume}%")
                return True
            else:
                self.logger.error("Failed to set volume")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting volume: {e}")
            return False
    
    def adjust_volume(self, delta: int) -> bool:
        """Adjust volume by delta amount"""
        try:
            current = self.get_current_volume()
            new_volume = current + delta
            return self.set_volume(new_volume)
            
        except Exception as e:
            self.logger.error(f"Error adjusting volume: {e}")
            return False
    
    def volume_up(self) -> bool:
        """Increase volume by step amount"""
        return self.adjust_volume(self.volume_step)
    
    def volume_down(self) -> bool:
        """Decrease volume by step amount"""
        return self.adjust_volume(-self.volume_step)
    
    def mute(self) -> bool:
        """Mute system audio"""
        try:
            if self.platform == "Windows" and self.volume_interface:
                self.volume_interface.SetMute(1, None)
                success = True
                
            elif self.platform == "Darwin":
                result = subprocess.run(['osascript', '-e', 'set volume with output muted'],
                                      capture_output=True, timeout=3)
                success = result.returncode == 0
                
            elif self.platform == "Linux":
                result = subprocess.run(['amixer', 'set', 'Master', 'mute'],
                                      capture_output=True, timeout=3)
                success = result.returncode == 0
            else:
                success = False
            
            if success:
                self.is_muted = True
                self.logger.info("Audio muted")
                return True
            else:
                self.logger.error("Failed to mute audio")
                return False
                
        except Exception as e:
            self.logger.error(f"Error muting audio: {e}")
            return False
    
    def unmute(self) -> bool:
        """Unmute system audio"""
        try:
            if self.platform == "Windows" and self.volume_interface:
                self.volume_interface.SetMute(0, None)
                success = True
                
            elif self.platform == "Darwin":
                result = subprocess.run(['osascript', '-e', 'set volume without output muted'],
                                      capture_output=True, timeout=3)
                success = result.returncode == 0
                
            elif self.platform == "Linux":
                result = subprocess.run(['amixer', 'set', 'Master', 'unmute'],
                                      capture_output=True, timeout=3)
                success = result.returncode == 0
            else:
                success = False
            
            if success:
                self.is_muted = False
                self.logger.info("Audio unmuted")
                return True
            else:
                self.logger.error("Failed to unmute audio")
                return False
                
        except Exception as e:
            self.logger.error(f"Error unmuting audio: {e}")
            return False
    
    def toggle_mute(self) -> bool:
        """Toggle mute state"""
        try:
            if self.is_muted:
                return self.unmute()
            else:
                return self.mute()
                
        except Exception as e:
            self.logger.error(f"Error toggling mute: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if audio control is available"""
        if self.platform == "Windows":
            return self.volume_interface is not None
        elif self.platform in ["Darwin", "Linux"]:
            return True  # Assume system commands are available
        else:
            return False
    
    def adjust_volume_by_gesture(self, confidence: float) -> bool:
        """Adjust volume based on gesture confidence"""
        try:
            # Map confidence (0.0-1.0) to volume change
            # Higher confidence = more volume change
            volume_delta = int((confidence - 0.5) * self.volume_step * 2)
            
            if abs(volume_delta) >= 1:  # Only adjust if change is significant
                return self.adjust_volume(volume_delta)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adjusting volume by gesture: {e}")
            return False
    
    def set_volume_by_distance(self, distance: float, max_distance: float = 200.0) -> bool:
        """Set volume based on pinch distance"""
        try:
            # Map distance to volume (0-100)
            # Closer pinch = lower volume, wider = higher volume
            normalized_distance = min(distance / max_distance, 1.0)
            target_volume = int(normalized_distance * 100)
            
            # Apply smoothing to prevent rapid changes
            current = self.get_current_volume()
            volume_diff = abs(target_volume - current)
            
            if volume_diff > 5:  # Only adjust if difference is significant
                # Smooth the transition
                if target_volume > current:
                    new_volume = current + min(volume_diff // 2, 10)
                else:
                    new_volume = current - min(volume_diff // 2, 10)
                
                return self.set_volume(new_volume)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting volume by distance: {e}")
            return False
    
    def start_pinch_volume_control(self):
        """Start continuous pinch-based volume control"""
        self.pinch_volume_active = True
        self.logger.info("Pinch volume control started")
    
    def stop_pinch_volume_control(self):
        """Stop continuous pinch-based volume control"""
        self.pinch_volume_active = False
        self.last_pinch_distance = None
        self.logger.info("Pinch volume control stopped")
    
    def update_pinch_volume(self, pinch_distance: float) -> bool:
        """Update volume based on current pinch distance"""
        try:
            if not self.pinch_volume_active:
                return False
            
            # Store the distance for continuous control
            self.last_pinch_distance = pinch_distance
            
            # Set volume based on pinch distance
            return self.set_volume_by_distance(pinch_distance)
            
        except Exception as e:
            self.logger.error(f"Error updating pinch volume: {e}")
            return False
    
    def get_audio_status(self) -> dict:
        """Get current audio status"""
        try:
            return {
                'current_volume': self.get_current_volume(),
                'is_muted': self.is_muted,
                'platform': self.platform,
                'available': self.is_available(),
                'pinch_control_active': self.pinch_volume_active,
                'last_pinch_distance': self.last_pinch_distance,
                'volume_step': self.volume_step
            }
            
        except Exception as e:
            self.logger.error(f"Error getting audio status: {e}")
            return {}
    
    def set_volume_step(self, step: int):
        """Set volume adjustment step size"""
        try:
            self.volume_step = max(1, min(20, step))  # Clamp between 1-20
            self.logger.info(f"Volume step set to {self.volume_step}")
            
        except Exception as e:
            self.logger.error(f"Error setting volume step: {e}")
    
    def set_volume_sensitivity(self, sensitivity: float):
        """Set volume control sensitivity for gestures"""
        try:
            self.volume_sensitivity = max(0.1, min(5.0, sensitivity))  # Clamp between 0.1-5.0
            self.logger.info(f"Volume sensitivity set to {self.volume_sensitivity}")
            
        except Exception as e:
            self.logger.error(f"Error setting volume sensitivity: {e}")
    
    def test_audio_control(self) -> dict:
        """Test audio control functionality"""
        results = {
            'platform': self.platform,
            'available': False,
            'get_volume': False,
            'set_volume': False,
            'mute_control': False,
            'errors': []
        }
        
        try:
            # Test availability
            results['available'] = self.is_available()
            
            if results['available']:
                # Test getting volume
                try:
                    initial_volume = self.get_current_volume()
                    results['get_volume'] = True
                except Exception as e:
                    results['errors'].append(f"Get volume failed: {e}")
                
                # Test setting volume
                try:
                    test_volume = max(10, min(90, initial_volume + 5))
                    if self.set_volume(test_volume):
                        time.sleep(0.1)
                        # Restore original volume
                        self.set_volume(initial_volume)
                        results['set_volume'] = True
                except Exception as e:
                    results['errors'].append(f"Set volume failed: {e}")
                
                # Test mute control
                try:
                    original_mute_state = self.is_muted
                    if self.toggle_mute():
                        time.sleep(0.1)
                        # Restore original mute state
                        if original_mute_state != self.is_muted:
                            self.toggle_mute()
                        results['mute_control'] = True
                except Exception as e:
                    results['errors'].append(f"Mute control failed: {e}")
            
        except Exception as e:
            results['errors'].append(f"Test failed: {e}")
        
        return results
    
    def cleanup(self):
        """Cleanup audio controller resources"""
        try:
            self.stop_pinch_volume_control()
            
            if self.platform == "Windows" and self.volume_interface:
                # Release COM objects
                try:
                    self.volume_interface = None
                    self.audio_interface = None
                except:
                    pass
            
            self.logger.info("AudioController cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
