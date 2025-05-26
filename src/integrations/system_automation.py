"""
System Automation Module
Handles system actions like screenshots, media control, and application launching
"""

import logging
import platform
import subprocess
import os
import time
from typing import Optional, Dict, List, Union
from pathlib import Path

# Import pyautogui for cross-platform automation
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Enable fail-safe (move mouse to corner to stop)
    pyautogui.PAUSE = 0.1  # Add small pause between actions
except (ImportError, Exception) as e:
    # Handle X11/display errors in headless environments
    pyautogui = None
    print(f"PyAutoGUI not available: {e}")


class SystemAutomation:
    """Handles system automation tasks triggered by gestures"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.platform = platform.system()
        
        # Screenshot settings
        self.screenshot_dir = "screenshots"
        self.screenshot_format = "png"
        
        # Application registry
        self.application_registry = {}
        self._initialize_application_registry()
        
        # Media control state
        self.media_playing = False
        
        # Action history for security/logging
        self.action_history = []
        self.max_history_size = 100
        
        # Ensure screenshot directory exists
        self._ensure_screenshot_directory()
        
        self.logger.info(f"SystemAutomation initialized for {self.platform}")
    
    def _ensure_screenshot_directory(self):
        """Ensure screenshot directory exists"""
        try:
            Path(self.screenshot_dir).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Screenshot directory: {os.path.abspath(self.screenshot_dir)}")
            
        except Exception as e:
            self.logger.error(f"Error creating screenshot directory: {e}")
            self.screenshot_dir = "."  # Fallback to current directory
    
    def _initialize_application_registry(self):
        """Initialize registry of available applications"""
        try:
            if self.platform == "Windows":
                self.application_registry = {
                    "brave": self._find_windows_app([
                        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                        r"C:\Users\{username}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"
                    ]),
                    "chrome": self._find_windows_app([
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                    ]),
                    "firefox": self._find_windows_app([
                        r"C:\Program Files\Mozilla Firefox\firefox.exe",
                        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
                    ]),
                    "notepad": r"C:\Windows\System32\notepad.exe",
                    "calculator": r"C:\Windows\System32\calc.exe"
                }
                
            elif self.platform == "Darwin":  # macOS
                self.application_registry = {
                    "brave": "/Applications/Brave Browser.app",
                    "chrome": "/Applications/Google Chrome.app",
                    "firefox": "/Applications/Firefox.app",
                    "safari": "/Applications/Safari.app",
                    "notes": "/Applications/Notes.app",
                    "calculator": "/Applications/Calculator.app"
                }
                
            elif self.platform == "Linux":
                self.application_registry = {
                    "brave": "brave-browser",
                    "chrome": "google-chrome",
                    "firefox": "firefox",
                    "gedit": "gedit",
                    "calculator": "gnome-calculator"
                }
            
            # Filter out non-existent applications
            self._validate_applications()
            
        except Exception as e:
            self.logger.error(f"Error initializing application registry: {e}")
    
    def _find_windows_app(self, paths: List[str]) -> Optional[str]:
        """Find Windows application from list of possible paths"""
        try:
            username = os.environ.get('USERNAME', 'User')
            
            for path in paths:
                # Replace {username} placeholder
                full_path = path.replace('{username}', username)
                
                if os.path.exists(full_path):
                    return full_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding Windows app: {e}")
            return None
    
    def _validate_applications(self):
        """Validate that registered applications exist"""
        try:
            valid_apps = {}
            
            for app_name, app_path in self.application_registry.items():
                if app_path is None:
                    continue
                
                if self.platform == "Windows":
                    if os.path.exists(app_path):
                        valid_apps[app_name] = app_path
                elif self.platform == "Darwin":
                    if os.path.exists(app_path):
                        valid_apps[app_name] = app_path
                elif self.platform == "Linux":
                    # Check if command exists
                    try:
                        result = subprocess.run(['which', app_path], 
                                              capture_output=True, timeout=3)
                        if result.returncode == 0:
                            valid_apps[app_name] = app_path
                    except:
                        pass
            
            self.application_registry = valid_apps
            self.logger.info(f"Available applications: {list(self.application_registry.keys())}")
            
        except Exception as e:
            self.logger.error(f"Error validating applications: {e}")
    
    def take_screenshot(self, filename: Optional[str] = None) -> bool:
        """Take a screenshot and save to file"""
        try:
            if pyautogui is None:
                self.logger.error("pyautogui not available for screenshots")
                return False
            
            # Generate filename if not provided
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.{self.screenshot_format}"
            
            # Ensure filename has correct extension
            if not filename.endswith(f".{self.screenshot_format}"):
                filename += f".{self.screenshot_format}"
            
            # Full path for screenshot
            screenshot_path = os.path.join(self.screenshot_dir, filename)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)
            
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            self._log_action("screenshot", {"path": screenshot_path})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return False
    
    def launch_application(self, app_name: str) -> bool:
        """Launch an application by name"""
        try:
            app_name = app_name.lower()
            
            if app_name not in self.application_registry:
                self.logger.error(f"Application not found: {app_name}")
                return False
            
            app_path = self.application_registry[app_name]
            
            if self.platform == "Windows":
                # Use subprocess to launch Windows applications
                subprocess.Popen([app_path], shell=False)
                
            elif self.platform == "Darwin":
                # Use 'open' command for macOS applications
                subprocess.Popen(['open', app_path])
                
            elif self.platform == "Linux":
                # Launch Linux applications
                subprocess.Popen([app_path], shell=False)
            
            self.logger.info(f"Launched application: {app_name}")
            self._log_action("launch_app", {"app": app_name, "path": app_path})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error launching application {app_name}: {e}")
            return False
    
    def send_key(self, key: str) -> bool:
        """Send a key press"""
        try:
            if pyautogui is None:
                self.logger.error("pyautogui not available for key sending")
                return False
            
            pyautogui.press(key)
            self.logger.debug(f"Sent key: {key}")
            self._log_action("send_key", {"key": key})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending key {key}: {e}")
            return False
    
    def send_key_combination(self, keys: List[str]) -> bool:
        """Send a key combination (e.g., ['ctrl', 'c'])"""
        try:
            if pyautogui is None:
                self.logger.error("pyautogui not available for key combinations")
                return False
            
            pyautogui.hotkey(*keys)
            self.logger.debug(f"Sent key combination: {'+'.join(keys)}")
            self._log_action("send_key_combo", {"keys": keys})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending key combination {keys}: {e}")
            return False
    
    def toggle_media_playback(self) -> bool:
        """Toggle media playback (play/pause)"""
        try:
            # Send media play/pause key
            success = self.send_key('playpause')
            
            if success:
                self.media_playing = not self.media_playing
                action = "pause" if not self.media_playing else "play"
                self.logger.info(f"Media {action} toggled")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error toggling media playback: {e}")
            return False
    
    def stop_media(self) -> bool:
        """Stop media playback"""
        try:
            success = self.send_key('stop')
            
            if success:
                self.media_playing = False
                self.logger.info("Media stopped")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error stopping media: {e}")
            return False
    
    def next_track(self) -> bool:
        """Skip to next track"""
        try:
            return self.send_key('nexttrack')
            
        except Exception as e:
            self.logger.error(f"Error skipping to next track: {e}")
            return False
    
    def previous_track(self) -> bool:
        """Skip to previous track"""
        try:
            return self.send_key('prevtrack')
            
        except Exception as e:
            self.logger.error(f"Error skipping to previous track: {e}")
            return False
    
    def send_like_action(self) -> bool:
        """Send a 'like' action (platform specific)"""
        try:
            # This could be customized based on the active application
            # For now, we'll send a generic 'thumbs up' or 'like' action
            
            # Try common like shortcuts
            like_shortcuts = [
                ['ctrl', 'shift', 'l'],  # Some apps use this
                ['l'],                    # YouTube, etc.
                ['alt', 'l']              # Alternative
            ]
            
            for shortcut in like_shortcuts:
                try:
                    self.send_key_combination(shortcut)
                    self.logger.info("Like action sent")
                    return True
                except:
                    continue
            
            # If no shortcuts work, log the action for future customization
            self.logger.info("Like gesture detected (no specific action configured)")
            self._log_action("like_gesture", {})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending like action: {e}")
            return False
    
    def open_browser(self, url: Optional[str] = None) -> bool:
        """Open default browser or specific URL"""
        try:
            if url is None:
                # Open default browser
                if "brave" in self.application_registry:
                    return self.launch_application("brave")
                elif "chrome" in self.application_registry:
                    return self.launch_application("chrome")
                elif "firefox" in self.application_registry:
                    return self.launch_application("firefox")
                else:
                    # Try system default
                    if self.platform == "Windows":
                        os.startfile("http://")
                    elif self.platform == "Darwin":
                        subprocess.Popen(['open', 'http://'])
                    elif self.platform == "Linux":
                        subprocess.Popen(['xdg-open', 'http://'])
                    return True
            else:
                # Open specific URL
                if self.platform == "Windows":
                    os.startfile(url)
                elif self.platform == "Darwin":
                    subprocess.Popen(['open', url])
                elif self.platform == "Linux":
                    subprocess.Popen(['xdg-open', url])
                
                self.logger.info(f"Opened URL: {url}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error opening browser: {e}")
            return False
    
    def minimize_window(self) -> bool:
        """Minimize the current window"""
        try:
            if self.platform == "Windows":
                return self.send_key_combination(['win', 'down'])
            elif self.platform == "Darwin":
                return self.send_key_combination(['cmd', 'm'])
            elif self.platform == "Linux":
                return self.send_key_combination(['alt', 'f9'])
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error minimizing window: {e}")
            return False
    
    def maximize_window(self) -> bool:
        """Maximize the current window"""
        try:
            if self.platform == "Windows":
                return self.send_key_combination(['win', 'up'])
            elif self.platform == "Darwin":
                # macOS doesn't have a direct maximize shortcut
                return self.send_key_combination(['ctrl', 'cmd', 'f'])
            elif self.platform == "Linux":
                return self.send_key_combination(['alt', 'f10'])
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error maximizing window: {e}")
            return False
    
    def switch_application(self) -> bool:
        """Switch to next application (Alt+Tab / Cmd+Tab)"""
        try:
            if self.platform == "Windows" or self.platform == "Linux":
                return self.send_key_combination(['alt', 'tab'])
            elif self.platform == "Darwin":
                return self.send_key_combination(['cmd', 'tab'])
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error switching application: {e}")
            return False
    
    def close_window(self) -> bool:
        """Close the current window"""
        try:
            if self.platform == "Windows" or self.platform == "Linux":
                return self.send_key_combination(['alt', 'f4'])
            elif self.platform == "Darwin":
                return self.send_key_combination(['cmd', 'w'])
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error closing window: {e}")
            return False
    
    def _log_action(self, action_type: str, details: Dict):
        """Log system action for security and debugging"""
        try:
            action_entry = {
                'timestamp': time.time(),
                'action': action_type,
                'details': details,
                'platform': self.platform
            }
            
            self.action_history.append(action_entry)
            
            # Limit history size
            if len(self.action_history) > self.max_history_size:
                self.action_history = self.action_history[-self.max_history_size:]
            
        except Exception as e:
            self.logger.error(f"Error logging action: {e}")
    
    def get_action_history(self, limit: int = 10) -> List[Dict]:
        """Get recent action history"""
        try:
            return self.action_history[-limit:]
        except Exception as e:
            self.logger.error(f"Error getting action history: {e}")
            return []
    
    def get_available_applications(self) -> Dict[str, str]:
        """Get dictionary of available applications"""
        return self.application_registry.copy()
    
    def add_application(self, name: str, path: str) -> bool:
        """Add application to registry"""
        try:
            if self.platform == "Windows":
                if os.path.exists(path):
                    self.application_registry[name.lower()] = path
                    self.logger.info(f"Added application: {name} -> {path}")
                    return True
            elif self.platform == "Darwin":
                if os.path.exists(path):
                    self.application_registry[name.lower()] = path
                    self.logger.info(f"Added application: {name} -> {path}")
                    return True
            elif self.platform == "Linux":
                # For Linux, just add the command
                self.application_registry[name.lower()] = path
                self.logger.info(f"Added application: {name} -> {path}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error adding application: {e}")
            return False
    
    def remove_application(self, name: str) -> bool:
        """Remove application from registry"""
        try:
            name = name.lower()
            if name in self.application_registry:
                del self.application_registry[name]
                self.logger.info(f"Removed application: {name}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing application: {e}")
            return False
    
    def test_system_automation(self) -> Dict:
        """Test system automation functionality"""
        results = {
            'platform': self.platform,
            'pyautogui_available': pyautogui is not None,
            'screenshot_test': False,
            'key_sending_test': False,
            'available_apps': len(self.application_registry),
            'errors': []
        }
        
        try:
            # Test screenshot
            if pyautogui:
                try:
                    test_screenshot = pyautogui.screenshot()
                    results['screenshot_test'] = True
                except Exception as e:
                    results['errors'].append(f"Screenshot test failed: {e}")
            
            # Test key sending
            if pyautogui:
                try:
                    # Test a safe key (like pressing and releasing shift)
                    pyautogui.keyDown('shift')
                    pyautogui.keyUp('shift')
                    results['key_sending_test'] = True
                except Exception as e:
                    results['errors'].append(f"Key sending test failed: {e}")
            
        except Exception as e:
            results['errors'].append(f"Test failed: {e}")
        
        return results
    
    def stop_all_actions(self):
        """Stop all ongoing automation actions"""
        try:
            self.logger.warning("Stopping all automation actions")
            # This would stop any ongoing automated processes
            # For now, just log the action
            self._log_action("stop_all", {})
            
        except Exception as e:
            self.logger.error(f"Error stopping all actions: {e}")
    
    def cleanup(self):
        """Cleanup system automation resources"""
        try:
            self.stop_all_actions()
            
            # Clear action history
            self.action_history.clear()
            
            self.logger.info("SystemAutomation cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
