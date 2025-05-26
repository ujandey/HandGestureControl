"""
Gesture Recognition Module
Analyzes hand landmarks to recognize specific gestures
"""

import numpy as np
import logging
import time
from collections import deque
from typing import List, Tuple, Optional, Dict
import math


class GestureRecognizer:
    """Recognizes gestures from hand landmark data"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # Gesture recognition parameters
        self.gesture_threshold = 0.85
        self.cooldown_period = 1.0  # Seconds between same gesture triggers
        self.smoothing_buffer_size = 5
        
        if config_manager:
            self.gesture_threshold = config_manager.get_gesture_threshold()
            self.cooldown_period = config_manager.get_gesture_cooldown()
            self.smoothing_buffer_size = config_manager.get_smoothing_buffer_size()
        
        # Gesture smoothing buffers
        self.gesture_buffer = deque(maxlen=self.smoothing_buffer_size)
        self.confidence_buffer = deque(maxlen=self.smoothing_buffer_size)
        
        # Gesture cooldown tracking
        self.last_gesture_time = {}
        
        # Gesture definitions and thresholds
        self.gesture_thresholds = {
            'pinch': {
                'thumb_index_max': 50,  # Maximum distance for pinch
                'confidence_min': 0.8
            },
            'peace_sign': {
                'index_middle_min': 30,  # Minimum distance between index and middle
                'other_fingers_max': 0.3,  # Maximum extension of other fingers
                'confidence_min': 0.85
            },
            'thumbs_up': {
                'thumb_extension_min': 0.8,  # Minimum thumb extension
                'other_fingers_max': 0.3,  # Maximum extension of other fingers
                'confidence_min': 0.8
            },
            'fist': {
                'finger_curl_min': 0.8,  # Minimum curl for all fingers
                'confidence_min': 0.9
            },
            'open_palm': {
                'finger_extension_min': 0.7,  # Minimum extension for all fingers
                'confidence_min': 0.8
            }
        }
        
        self.logger.info("GestureRecognizer initialized")
    
    def recognize_gesture(self, hands_landmarks: List[List[Tuple[float, float, float]]]) -> Tuple[Optional[str], float]:
        """
        Recognize gesture from hand landmarks
        
        Args:
            hands_landmarks: List of hand landmarks (each hand has 21 landmarks)
            
        Returns:
            Tuple of (gesture_name, confidence) or (None, 0.0) if no gesture recognized
        """
        try:
            if not hands_landmarks or len(hands_landmarks) == 0:
                return None, 0.0
            
            # Use the first hand for gesture recognition
            landmarks = hands_landmarks[0]
            
            if len(landmarks) != 21:
                return None, 0.0
            
            # Extract features from landmarks
            features = self.extract_gesture_features(landmarks)
            
            # Classify gesture
            gesture, confidence = self.classify_gesture(features)
            
            # Apply smoothing
            smoothed_gesture, smoothed_confidence = self.apply_smoothing(gesture, confidence)
            
            # Check cooldown period
            if smoothed_gesture and self.check_gesture_cooldown(smoothed_gesture):
                return smoothed_gesture, smoothed_confidence
            
            return None, 0.0
            
        except Exception as e:
            self.logger.error(f"Error in gesture recognition: {e}")
            return None, 0.0
    
    def extract_gesture_features(self, landmarks: List[Tuple[float, float, float]]) -> Dict:
        """Extract features from hand landmarks for gesture classification"""
        try:
            features = {}
            
            # Calculate finger tip positions
            finger_tips = {
                'thumb': landmarks[4],
                'index': landmarks[8],
                'middle': landmarks[12],
                'ring': landmarks[16],
                'pinky': landmarks[20]
            }
            
            # Calculate finger base positions (MCP joints)
            finger_bases = {
                'thumb': landmarks[2],
                'index': landmarks[5],
                'middle': landmarks[9],
                'ring': landmarks[13],
                'pinky': landmarks[17]
            }
            
            # Calculate distances
            features['distances'] = {}
            
            # Thumb-index distance (for pinch detection)
            thumb_tip = finger_tips['thumb']
            index_tip = finger_tips['index']
            features['distances']['thumb_index'] = math.sqrt(
                (thumb_tip[0] - index_tip[0])**2 + (thumb_tip[1] - index_tip[1])**2
            )
            
            # Index-middle distance (for peace sign)
            middle_tip = finger_tips['middle']
            features['distances']['index_middle'] = math.sqrt(
                (index_tip[0] - middle_tip[0])**2 + (index_tip[1] - middle_tip[1])**2
            )
            
            # Calculate finger extensions (tip distance from base)
            features['extensions'] = {}
            for finger in finger_tips:
                tip = finger_tips[finger]
                base = finger_bases[finger]
                extension = math.sqrt(
                    (tip[0] - base[0])**2 + (tip[1] - base[1])**2
                )
                features['extensions'][finger] = extension
            
            # Normalize extensions relative to hand size
            wrist = landmarks[0]
            palm_center = landmarks[9]
            hand_size = math.sqrt(
                (wrist[0] - palm_center[0])**2 + (wrist[1] - palm_center[1])**2
            )
            
            if hand_size > 0:
                for finger in features['extensions']:
                    features['extensions'][finger] /= hand_size
            
            # Calculate finger curl ratios
            features['curl_ratios'] = {}
            for finger in ['index', 'middle', 'ring', 'pinky']:
                if finger == 'index':
                    pip_joint = landmarks[6]
                    dip_joint = landmarks[7]
                elif finger == 'middle':
                    pip_joint = landmarks[10]
                    dip_joint = landmarks[11]
                elif finger == 'ring':
                    pip_joint = landmarks[14]
                    dip_joint = landmarks[15]
                else:  # pinky
                    pip_joint = landmarks[18]
                    dip_joint = landmarks[19]
                
                tip = finger_tips[finger]
                base = finger_bases[finger]
                
                # Calculate curl ratio (0 = fully extended, 1 = fully curled)
                tip_to_base = math.sqrt((tip[0] - base[0])**2 + (tip[1] - base[1])**2)
                pip_to_base = math.sqrt((pip_joint[0] - base[0])**2 + (pip_joint[1] - base[1])**2)
                
                if pip_to_base > 0:
                    curl_ratio = 1 - (tip_to_base / (pip_to_base * 2))
                    features['curl_ratios'][finger] = max(0, min(1, curl_ratio))
                else:
                    features['curl_ratios'][finger] = 0
            
            # Thumb curl ratio (special case)
            thumb_tip = finger_tips['thumb']
            thumb_ip = landmarks[3]  # Thumb IP joint
            thumb_mcp = landmarks[2]  # Thumb MCP joint
            
            tip_to_mcp = math.sqrt((thumb_tip[0] - thumb_mcp[0])**2 + (thumb_tip[1] - thumb_mcp[1])**2)
            ip_to_mcp = math.sqrt((thumb_ip[0] - thumb_mcp[0])**2 + (thumb_ip[1] - thumb_mcp[1])**2)
            
            if ip_to_mcp > 0:
                thumb_curl = 1 - (tip_to_mcp / (ip_to_mcp * 1.5))
                features['curl_ratios']['thumb'] = max(0, min(1, thumb_curl))
            else:
                features['curl_ratios']['thumb'] = 0
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting gesture features: {e}")
            return {}
    
    def classify_gesture(self, features: Dict) -> Tuple[Optional[str], float]:
        """Classify gesture based on extracted features"""
        try:
            if not features:
                return None, 0.0
            
            gesture_scores = {}
            
            # Pinch gesture detection
            thumb_index_dist = features.get('distances', {}).get('thumb_index', float('inf'))
            if thumb_index_dist < self.gesture_thresholds['pinch']['thumb_index_max']:
                gesture_scores['pinch'] = 1 - (thumb_index_dist / self.gesture_thresholds['pinch']['thumb_index_max'])
            
            # Peace sign detection (index and middle extended, others curled)
            index_curl = features.get('curl_ratios', {}).get('index', 1)
            middle_curl = features.get('curl_ratios', {}).get('middle', 1)
            ring_curl = features.get('curl_ratios', {}).get('ring', 0)
            pinky_curl = features.get('curl_ratios', {}).get('pinky', 0)
            
            if (index_curl < 0.3 and middle_curl < 0.3 and 
                ring_curl > 0.7 and pinky_curl > 0.7):
                index_middle_dist = features.get('distances', {}).get('index_middle', 0)
                if index_middle_dist > self.gesture_thresholds['peace_sign']['index_middle_min']:
                    gesture_scores['peace_sign'] = 0.9
            
            # Thumbs up detection (thumb extended, others curled)
            thumb_curl = features.get('curl_ratios', {}).get('thumb', 1)
            if (thumb_curl < 0.3 and index_curl > 0.7 and middle_curl > 0.7 and 
                ring_curl > 0.7 and pinky_curl > 0.7):
                gesture_scores['thumbs_up'] = 0.9
            
            # Fist detection (all fingers curled)
            all_curled = (thumb_curl > 0.8 and index_curl > 0.8 and middle_curl > 0.8 and 
                         ring_curl > 0.8 and pinky_curl > 0.8)
            if all_curled:
                gesture_scores['fist'] = 0.95
            
            # Open palm detection (all fingers extended)
            all_extended = (thumb_curl < 0.3 and index_curl < 0.3 and middle_curl < 0.3 and 
                           ring_curl < 0.3 and pinky_curl < 0.3)
            if all_extended:
                gesture_scores['open_palm'] = 0.9
            
            # Find best gesture
            if gesture_scores:
                best_gesture = max(gesture_scores, key=gesture_scores.get)
                best_confidence = gesture_scores[best_gesture]
                
                # Check if confidence meets threshold
                min_confidence = self.gesture_thresholds[best_gesture]['confidence_min']
                if best_confidence >= min_confidence:
                    return best_gesture, best_confidence
            
            return None, 0.0
            
        except Exception as e:
            self.logger.error(f"Error in gesture classification: {e}")
            return None, 0.0
    
    def apply_smoothing(self, gesture: Optional[str], confidence: float) -> Tuple[Optional[str], float]:
        """Apply temporal smoothing to gesture recognition"""
        try:
            # Add to buffers
            self.gesture_buffer.append(gesture)
            self.confidence_buffer.append(confidence)
            
            if len(self.gesture_buffer) < self.smoothing_buffer_size:
                return gesture, confidence
            
            # Count gesture occurrences in buffer
            gesture_counts = {}
            total_confidence = 0
            valid_count = 0
            
            for i, g in enumerate(self.gesture_buffer):
                if g is not None:
                    gesture_counts[g] = gesture_counts.get(g, 0) + 1
                    total_confidence += self.confidence_buffer[i]
                    valid_count += 1
            
            if not gesture_counts:
                return None, 0.0
            
            # Find most frequent gesture
            most_frequent = max(gesture_counts, key=gesture_counts.get)
            frequency = gesture_counts[most_frequent]
            
            # Require majority consensus
            if frequency >= (self.smoothing_buffer_size // 2 + 1):
                avg_confidence = total_confidence / valid_count if valid_count > 0 else 0
                return most_frequent, avg_confidence
            
            return None, 0.0
            
        except Exception as e:
            self.logger.error(f"Error in gesture smoothing: {e}")
            return gesture, confidence
    
    def check_gesture_cooldown(self, gesture: str) -> bool:
        """Check if gesture is not in cooldown period"""
        try:
            current_time = time.time()
            last_time = self.last_gesture_time.get(gesture, 0)
            
            if current_time - last_time >= self.cooldown_period:
                self.last_gesture_time[gesture] = current_time
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking gesture cooldown: {e}")
            return False
    
    def get_gesture_info(self) -> Dict:
        """Get information about supported gestures"""
        return {
            'supported_gestures': list(self.gesture_thresholds.keys()),
            'gesture_descriptions': {
                'pinch': 'Thumb and index finger close together - controls volume',
                'peace_sign': 'Index and middle finger extended (V sign) - takes screenshot',
                'thumbs_up': 'Thumb extended upward - like action',
                'fist': 'All fingers curled into fist - pause/play media',
                'open_palm': 'All fingers extended - stop action'
            },
            'current_threshold': self.gesture_threshold,
            'cooldown_period': self.cooldown_period
        }
    
    def reset_buffers(self):
        """Reset smoothing buffers"""
        self.gesture_buffer.clear()
        self.confidence_buffer.clear()
        self.last_gesture_time.clear()
        self.logger.info("Gesture recognition buffers reset")
