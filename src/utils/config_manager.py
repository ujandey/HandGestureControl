"""
Configuration Manager Module
Handles application settings and configuration persistence
"""

import configparser
import os
import logging
from typing import Any, Dict, Optional


class ConfigManager:
    """Manages application configuration and settings"""
    
    def __init__(self, config_file: str = "config/settings.ini"):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # Default configuration values
        self.defaults = {
            'detection': {
                'min_detection_confidence': '0.7',
                'min_tracking_confidence': '0.5',
                'max_num_hands': '2'
            },
            'gesture_recognition': {
                'gesture_threshold': '0.85',
                'cooldown_period': '1.0',
                'smoothing_buffer_size': '5'
            },
            'system_control': {
                'action_cooldown': '1.0',
                'volume_step': '5',
                'enable_audio_control': 'true'
            },
            'ui': {
                'window_width': '1000',
                'window_height': '700',
                'camera_width': '640',
                'camera_height': '480',
                'update_rate': '30'
            },
            'performance': {
                'target_fps': '30',
                'max_cpu_usage': '25',
                'max_memory_mb': '200',
                'enable_gpu_acceleration': 'false'
            },
            'logging': {
                'log_level': 'INFO',
                'log_to_file': 'true',
                'max_log_size_mb': '10'
            }
        }
        
        # Ensure config directory exists
        self.ensure_config_directory()
        
        # Load configuration
        self.load_config()
        
        self.logger.info("ConfigManager initialized")
    
    def ensure_config_directory(self):
        """Ensure configuration directory exists"""
        try:
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
                self.logger.info(f"Created config directory: {config_dir}")
                
        except Exception as e:
            self.logger.error(f"Error creating config directory: {e}")
    
    def load_config(self):
        """Load configuration from file or create with defaults"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.logger.info("Configuration file not found, creating with defaults")
                self.create_default_config()
                
            # Validate and update configuration
            self.validate_config()
            
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create configuration file with default values"""
        try:
            # Add all default sections and values
            for section, values in self.defaults.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                
                for key, value in values.items():
                    self.config.set(section, key, value)
            
            # Save to file
            self.save_config()
            self.logger.info("Default configuration created")
            
        except Exception as e:
            self.logger.error(f"Error creating default configuration: {e}")
    
    def validate_config(self):
        """Validate configuration and add missing defaults"""
        try:
            config_updated = False
            
            for section, values in self.defaults.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                    config_updated = True
                
                for key, default_value in values.items():
                    if not self.config.has_option(section, key):
                        self.config.set(section, key, default_value)
                        config_updated = True
            
            if config_updated:
                self.save_config()
                self.logger.info("Configuration updated with missing defaults")
                
        except Exception as e:
            self.logger.error(f"Error validating configuration: {e}")
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as config_file:
                self.config.write(config_file)
            self.logger.info(f"Configuration saved to {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            raise
    
    def get_value(self, section: str, key: str, fallback: Any = None) -> str:
        """Get configuration value with fallback"""
        try:
            return self.config.get(section, key, fallback=str(fallback) if fallback is not None else None)
        except Exception as e:
            self.logger.error(f"Error getting config value [{section}]{key}: {e}")
            return str(fallback) if fallback is not None else ""
    
    def set_value(self, section: str, key: str, value: Any):
        """Set configuration value"""
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            self.config.set(section, key, str(value))
            self.logger.debug(f"Set config value [{section}]{key} = {value}")
            
        except Exception as e:
            self.logger.error(f"Error setting config value [{section}]{key}: {e}")
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Get float configuration value"""
        try:
            return self.config.getfloat(section, key, fallback=fallback)
        except Exception as e:
            self.logger.error(f"Error getting float config value [{section}]{key}: {e}")
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value"""
        try:
            return self.config.getint(section, key, fallback=fallback)
        except Exception as e:
            self.logger.error(f"Error getting int config value [{section}]{key}: {e}")
            return fallback
    
    def get_boolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value"""
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except Exception as e:
            self.logger.error(f"Error getting boolean config value [{section}]{key}: {e}")
            return fallback
    
    # Detection settings
    def get_detection_confidence(self) -> float:
        """Get hand detection confidence threshold"""
        return self.get_float('detection', 'min_detection_confidence', 0.7)
    
    def set_detection_confidence(self, value: float):
        """Set hand detection confidence threshold"""
        self.set_value('detection', 'min_detection_confidence', value)
    
    def get_tracking_confidence(self) -> float:
        """Get hand tracking confidence threshold"""
        return self.get_float('detection', 'min_tracking_confidence', 0.5)
    
    def set_tracking_confidence(self, value: float):
        """Set hand tracking confidence threshold"""
        self.set_value('detection', 'min_tracking_confidence', value)
    
    def get_max_hands(self) -> int:
        """Get maximum number of hands to detect"""
        return self.get_int('detection', 'max_num_hands', 2)
    
    def set_max_hands(self, value: int):
        """Set maximum number of hands to detect"""
        self.set_value('detection', 'max_num_hands', value)
    
    # Gesture recognition settings
    def get_gesture_threshold(self) -> float:
        """Get gesture recognition confidence threshold"""
        return self.get_float('gesture_recognition', 'gesture_threshold', 0.85)
    
    def set_gesture_threshold(self, value: float):
        """Set gesture recognition confidence threshold"""
        self.set_value('gesture_recognition', 'gesture_threshold', value)
    
    def get_gesture_cooldown(self) -> float:
        """Get gesture cooldown period in seconds"""
        return self.get_float('gesture_recognition', 'cooldown_period', 1.0)
    
    def set_gesture_cooldown(self, value: float):
        """Set gesture cooldown period in seconds"""
        self.set_value('gesture_recognition', 'cooldown_period', value)
    
    def get_smoothing_buffer_size(self) -> int:
        """Get gesture smoothing buffer size"""
        return self.get_int('gesture_recognition', 'smoothing_buffer_size', 5)
    
    def set_smoothing_buffer_size(self, value: int):
        """Set gesture smoothing buffer size"""
        self.set_value('gesture_recognition', 'smoothing_buffer_size', value)
    
    # System control settings
    def get_action_cooldown(self) -> float:
        """Get system action cooldown period in seconds"""
        return self.get_float('system_control', 'action_cooldown', 1.0)
    
    def set_action_cooldown(self, value: float):
        """Set system action cooldown period in seconds"""
        self.set_value('system_control', 'action_cooldown', value)
    
    def get_volume_step(self) -> int:
        """Get volume adjustment step size"""
        return self.get_int('system_control', 'volume_step', 5)
    
    def set_volume_step(self, value: int):
        """Set volume adjustment step size"""
        self.set_value('system_control', 'volume_step', value)
    
    def is_audio_control_enabled(self) -> bool:
        """Check if audio control is enabled"""
        return self.get_boolean('system_control', 'enable_audio_control', True)
    
    def set_audio_control_enabled(self, enabled: bool):
        """Enable or disable audio control"""
        self.set_value('system_control', 'enable_audio_control', enabled)
    
    # UI settings
    def get_window_size(self) -> tuple:
        """Get main window size"""
        width = self.get_int('ui', 'window_width', 1000)
        height = self.get_int('ui', 'window_height', 700)
        return (width, height)
    
    def set_window_size(self, width: int, height: int):
        """Set main window size"""
        self.set_value('ui', 'window_width', width)
        self.set_value('ui', 'window_height', height)
    
    def get_camera_size(self) -> tuple:
        """Get camera preview size"""
        width = self.get_int('ui', 'camera_width', 640)
        height = self.get_int('ui', 'camera_height', 480)
        return (width, height)
    
    def set_camera_size(self, width: int, height: int):
        """Set camera preview size"""
        self.set_value('ui', 'camera_width', width)
        self.set_value('ui', 'camera_height', height)
    
    def get_ui_update_rate(self) -> int:
        """Get UI update rate in FPS"""
        return self.get_int('ui', 'update_rate', 30)
    
    def set_ui_update_rate(self, rate: int):
        """Set UI update rate in FPS"""
        self.set_value('ui', 'update_rate', rate)
    
    # Performance settings
    def get_target_fps(self) -> int:
        """Get target processing FPS"""
        return self.get_int('performance', 'target_fps', 30)
    
    def set_target_fps(self, fps: int):
        """Set target processing FPS"""
        self.set_value('performance', 'target_fps', fps)
    
    def get_max_cpu_usage(self) -> float:
        """Get maximum CPU usage threshold"""
        return self.get_float('performance', 'max_cpu_usage', 25.0)
    
    def set_max_cpu_usage(self, percentage: float):
        """Set maximum CPU usage threshold"""
        self.set_value('performance', 'max_cpu_usage', percentage)
    
    def get_max_memory_mb(self) -> int:
        """Get maximum memory usage in MB"""
        return self.get_int('performance', 'max_memory_mb', 200)
    
    def set_max_memory_mb(self, mb: int):
        """Set maximum memory usage in MB"""
        self.set_value('performance', 'max_memory_mb', mb)
    
    def is_gpu_acceleration_enabled(self) -> bool:
        """Check if GPU acceleration is enabled"""
        return self.get_boolean('performance', 'enable_gpu_acceleration', False)
    
    def set_gpu_acceleration_enabled(self, enabled: bool):
        """Enable or disable GPU acceleration"""
        self.set_value('performance', 'enable_gpu_acceleration', enabled)
    
    # Logging settings
    def get_log_level(self) -> str:
        """Get logging level"""
        return self.get_value('logging', 'log_level', 'INFO')
    
    def set_log_level(self, level: str):
        """Set logging level"""
        self.set_value('logging', 'log_level', level)
    
    def is_log_to_file_enabled(self) -> bool:
        """Check if logging to file is enabled"""
        return self.get_boolean('logging', 'log_to_file', True)
    
    def set_log_to_file_enabled(self, enabled: bool):
        """Enable or disable logging to file"""
        self.set_value('logging', 'log_to_file', enabled)
    
    def get_max_log_size_mb(self) -> int:
        """Get maximum log file size in MB"""
        return self.get_int('logging', 'max_log_size_mb', 10)
    
    def set_max_log_size_mb(self, mb: int):
        """Set maximum log file size in MB"""
        self.set_value('logging', 'max_log_size_mb', mb)
    
    def get_all_settings(self) -> Dict[str, Dict[str, str]]:
        """Get all configuration settings as dictionary"""
        try:
            settings = {}
            for section_name in self.config.sections():
                settings[section_name] = dict(self.config.items(section_name))
            return settings
            
        except Exception as e:
            self.logger.error(f"Error getting all settings: {e}")
            return {}
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        try:
            self.config.clear()
            self.create_default_config()
            self.logger.info("Configuration reset to defaults")
            
        except Exception as e:
            self.logger.error(f"Error resetting to defaults: {e}")
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to specified path"""
        try:
            with open(export_path, 'w') as export_file:
                self.config.write(export_file)
            self.logger.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from specified path"""
        try:
            if not os.path.exists(import_path):
                self.logger.error(f"Import file not found: {import_path}")
                return False
            
            temp_config = configparser.ConfigParser()
            temp_config.read(import_path)
            
            # Validate imported config
            self.config = temp_config
            self.validate_config()
            self.save_config()
            
            self.logger.info(f"Configuration imported from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
