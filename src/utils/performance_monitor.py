"""
Performance Monitor Module
Tracks system performance metrics and resource usage
"""

import psutil
import time
import threading
import logging
from collections import deque
from typing import Dict, List, Optional
import numpy as np


class PerformanceMonitor:
    """Monitors system performance and resource usage"""
    
    def __init__(self, history_size: int = 100):
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        
        # Performance metrics storage
        self.fps_history = deque(maxlen=history_size)
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.detection_rate_history = deque(maxlen=history_size)
        
        # Frame counting
        self.frame_count = 0
        self.detection_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        # Performance thresholds (from config)
        self.max_cpu_percent = 25.0
        self.max_memory_mb = 200.0
        self.target_fps = 30.0
        
        # Monitoring control
        self.monitoring_active = True
        self.monitor_thread = None
        
        # Process reference for accurate monitoring
        self.process = psutil.Process()
        
        # Start monitoring
        self.start_monitoring()
        
        self.logger.info("PerformanceMonitor initialized")
    
    def start_monitoring(self):
        """Start performance monitoring thread"""
        try:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Performance monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting performance monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        try:
            self.monitoring_active = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2.0)
            self.logger.info("Performance monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping performance monitoring: {e}")
    
    def monitor_loop(self):
        """Main monitoring loop running in separate thread"""
        while self.monitoring_active:
            try:
                # Update system metrics
                self.update_system_metrics()
                
                # Sleep for monitoring interval
                time.sleep(1.0)  # Update every second
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)
    
    def update_system_metrics(self):
        """Update system performance metrics"""
        try:
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            self.cpu_history.append(cpu_percent)
            
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
            self.memory_history.append(memory_mb)
            
            # Calculate detection rate
            detection_rate = 0.0
            if self.frame_count > 0:
                detection_rate = self.detection_count / self.frame_count
            self.detection_rate_history.append(detection_rate)
            
            # Log warnings for high resource usage
            if cpu_percent > self.max_cpu_percent:
                self.logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory_mb > self.max_memory_mb:
                self.logger.warning(f"High memory usage: {memory_mb:.1f} MB")
            
        except Exception as e:
            self.logger.error(f"Error updating system metrics: {e}")
    
    def update_frame_processed(self):
        """Update frame processing counter"""
        try:
            self.frame_count += 1
            
            # Calculate FPS
            current_time = time.time()
            if current_time - self.last_fps_time >= 1.0:
                self.current_fps = self.frame_count / (current_time - self.last_fps_time)
                self.fps_history.append(self.current_fps)
                
                # Reset counters
                self.frame_count = 0
                self.detection_count = 0
                self.last_fps_time = current_time
                
        except Exception as e:
            self.logger.error(f"Error updating frame processed: {e}")
    
    def update_detection_processed(self):
        """Update detection processing counter"""
        try:
            self.detection_count += 1
            
        except Exception as e:
            self.logger.error(f"Error updating detection processed: {e}")
    
    def get_current_metrics(self) -> Dict:
        """Get current performance metrics"""
        try:
            return {
                'fps': self.current_fps,
                'cpu_percent': self.get_current_cpu(),
                'memory_mb': self.get_current_memory(),
                'detection_rate': self.get_current_detection_rate(),
                'frame_count': self.frame_count,
                'detection_count': self.detection_count
            }
            
        except Exception as e:
            self.logger.error(f"Error getting current metrics: {e}")
            return {}
    
    def get_current_cpu(self) -> float:
        """Get current CPU usage percentage"""
        try:
            if self.cpu_history:
                return self.cpu_history[-1]
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error getting current CPU: {e}")
            return 0.0
    
    def get_current_memory(self) -> float:
        """Get current memory usage in MB"""
        try:
            if self.memory_history:
                return self.memory_history[-1]
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error getting current memory: {e}")
            return 0.0
    
    def get_current_detection_rate(self) -> float:
        """Get current detection rate"""
        try:
            if self.detection_rate_history:
                return self.detection_rate_history[-1]
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error getting current detection rate: {e}")
            return 0.0
    
    def get_average_metrics(self, window_size: int = 10) -> Dict:
        """Get average metrics over specified window"""
        try:
            window_size = min(window_size, len(self.fps_history))
            
            if window_size == 0:
                return self.get_current_metrics()
            
            # Calculate averages
            avg_fps = np.mean(list(self.fps_history)[-window_size:])
            avg_cpu = np.mean(list(self.cpu_history)[-window_size:])
            avg_memory = np.mean(list(self.memory_history)[-window_size:])
            avg_detection_rate = np.mean(list(self.detection_rate_history)[-window_size:])
            
            return {
                'avg_fps': avg_fps,
                'avg_cpu_percent': avg_cpu,
                'avg_memory_mb': avg_memory,
                'avg_detection_rate': avg_detection_rate,
                'window_size': window_size
            }
            
        except Exception as e:
            self.logger.error(f"Error getting average metrics: {e}")
            return {}
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        try:
            current = self.get_current_metrics()
            averages = self.get_average_metrics()
            
            # Calculate performance status
            fps_status = "Good" if current.get('fps', 0) >= self.target_fps * 0.8 else "Poor"
            cpu_status = "Good" if current.get('cpu_percent', 0) <= self.max_cpu_percent else "High"
            memory_status = "Good" if current.get('memory_mb', 0) <= self.max_memory_mb else "High"
            
            return {
                'current_metrics': current,
                'average_metrics': averages,
                'performance_status': {
                    'fps': fps_status,
                    'cpu': cpu_status,
                    'memory': memory_status,
                    'overall': self.get_overall_performance_status()
                },
                'thresholds': {
                    'max_cpu_percent': self.max_cpu_percent,
                    'max_memory_mb': self.max_memory_mb,
                    'target_fps': self.target_fps
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {e}")
            return {}
    
    def get_overall_performance_status(self) -> str:
        """Get overall performance status"""
        try:
            current = self.get_current_metrics()
            
            fps = current.get('fps', 0)
            cpu = current.get('cpu_percent', 0)
            memory = current.get('memory_mb', 0)
            
            # Performance scoring
            score = 0
            
            if fps >= self.target_fps * 0.9:
                score += 3
            elif fps >= self.target_fps * 0.7:
                score += 2
            elif fps >= self.target_fps * 0.5:
                score += 1
            
            if cpu <= self.max_cpu_percent * 0.7:
                score += 3
            elif cpu <= self.max_cpu_percent:
                score += 2
            elif cpu <= self.max_cpu_percent * 1.5:
                score += 1
            
            if memory <= self.max_memory_mb * 0.7:
                score += 3
            elif memory <= self.max_memory_mb:
                score += 2
            elif memory <= self.max_memory_mb * 1.5:
                score += 1
            
            # Determine status based on score
            if score >= 8:
                return "Excellent"
            elif score >= 6:
                return "Good"
            elif score >= 4:
                return "Fair"
            else:
                return "Poor"
                
        except Exception as e:
            self.logger.error(f"Error getting overall performance status: {e}")
            return "Unknown"
    
    def get_performance_history(self) -> Dict[str, List]:
        """Get performance history data"""
        try:
            return {
                'fps_history': list(self.fps_history),
                'cpu_history': list(self.cpu_history),
                'memory_history': list(self.memory_history),
                'detection_rate_history': list(self.detection_rate_history),
                'timestamps': [time.time() - i for i in range(len(self.fps_history)-1, -1, -1)]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance history: {e}")
            return {}
    
    def check_performance_warnings(self) -> List[str]:
        """Check for performance warnings"""
        warnings = []
        
        try:
            current = self.get_current_metrics()
            
            # FPS warnings
            fps = current.get('fps', 0)
            if fps < self.target_fps * 0.5:
                warnings.append(f"Very low FPS: {fps:.1f} (target: {self.target_fps})")
            elif fps < self.target_fps * 0.8:
                warnings.append(f"Low FPS: {fps:.1f} (target: {self.target_fps})")
            
            # CPU warnings
            cpu = current.get('cpu_percent', 0)
            if cpu > self.max_cpu_percent * 1.5:
                warnings.append(f"Very high CPU usage: {cpu:.1f}% (max: {self.max_cpu_percent}%)")
            elif cpu > self.max_cpu_percent:
                warnings.append(f"High CPU usage: {cpu:.1f}% (max: {self.max_cpu_percent}%)")
            
            # Memory warnings
            memory = current.get('memory_mb', 0)
            if memory > self.max_memory_mb * 1.5:
                warnings.append(f"Very high memory usage: {memory:.1f} MB (max: {self.max_memory_mb} MB)")
            elif memory > self.max_memory_mb:
                warnings.append(f"High memory usage: {memory:.1f} MB (max: {self.max_memory_mb} MB)")
            
            # Detection rate warnings
            detection_rate = current.get('detection_rate', 0)
            if detection_rate < 0.3:
                warnings.append(f"Low detection rate: {detection_rate*100:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error checking performance warnings: {e}")
            warnings.append("Error checking performance metrics")
        
        return warnings
    
    def set_thresholds(self, max_cpu: float = None, max_memory: float = None, target_fps: float = None):
        """Set performance thresholds"""
        try:
            if max_cpu is not None:
                self.max_cpu_percent = max_cpu
            if max_memory is not None:
                self.max_memory_mb = max_memory
            if target_fps is not None:
                self.target_fps = target_fps
                
            self.logger.info(f"Performance thresholds updated: CPU={self.max_cpu_percent}%, "
                           f"Memory={self.max_memory_mb}MB, FPS={self.target_fps}")
            
        except Exception as e:
            self.logger.error(f"Error setting performance thresholds: {e}")
    
    def reset_metrics(self):
        """Reset all performance metrics"""
        try:
            self.fps_history.clear()
            self.cpu_history.clear()
            self.memory_history.clear()
            self.detection_rate_history.clear()
            
            self.frame_count = 0
            self.detection_count = 0
            self.current_fps = 0.0
            self.last_fps_time = time.time()
            
            self.logger.info("Performance metrics reset")
            
        except Exception as e:
            self.logger.error(f"Error resetting metrics: {e}")
    
    def cleanup(self):
        """Cleanup performance monitor"""
        try:
            self.stop_monitoring()
            self.logger.info("PerformanceMonitor cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
