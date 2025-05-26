"""
Hand Detection Module using MediaPipe
Handles real-time hand landmark detection and tracking
"""

import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import List, Tuple, Optional


class HandDetector:
    """Real-time hand detection using MediaPipe"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Configure hand detection parameters
        self.min_detection_confidence = 0.7
        self.min_tracking_confidence = 0.5
        self.max_num_hands = 2
        
        if config_manager:
            self.min_detection_confidence = config_manager.get_detection_confidence()
            self.min_tracking_confidence = config_manager.get_tracking_confidence()
            self.max_num_hands = config_manager.get_max_hands()
        
        # Initialize MediaPipe Hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=self.max_num_hands,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        
        # Performance tracking
        self.frame_count = 0
        self.detection_count = 0
        
        self.logger.info("HandDetector initialized with MediaPipe")
    
    def detect_hands(self, frame: np.ndarray) -> Optional[List[List[Tuple[float, float, float]]]]:
        """
        Detect hands in the given frame and return landmark coordinates
        
        Args:
            frame: Input BGR image from camera
            
        Returns:
            List of hand landmarks, each hand has 21 landmarks with (x, y, z) coordinates
            Returns None if no hands detected
        """
        try:
            self.frame_count += 1
            
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                self.detection_count += 1
                
                # Extract landmark coordinates
                hands_landmarks = []
                
                for hand_landmarks in results.multi_hand_landmarks:
                    # Convert normalized coordinates to pixel coordinates
                    height, width, _ = frame.shape
                    landmarks = []
                    
                    for landmark in hand_landmarks.landmark:
                        x = landmark.x * width
                        y = landmark.y * height
                        z = landmark.z  # Relative depth
                        landmarks.append((x, y, z))
                    
                    hands_landmarks.append(landmarks)
                
                return hands_landmarks
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in hand detection: {e}")
            return None
    
    def draw_landmarks(self, frame: np.ndarray, hands_landmarks: List[List[Tuple[float, float, float]]]) -> np.ndarray:
        """
        Draw hand landmarks and connections on the frame
        
        Args:
            frame: Input BGR image
            hands_landmarks: List of hand landmarks
            
        Returns:
            Frame with drawn landmarks
        """
        try:
            if not hands_landmarks:
                return frame
            
            # Convert landmarks back to MediaPipe format for drawing
            height, width, _ = frame.shape
            
            for landmarks in hands_landmarks:
                # Create MediaPipe landmark object
                hand_landmarks = self.mp_hands.HandLandmark
                landmark_list = []
                
                for x, y, z in landmarks:
                    # Convert back to normalized coordinates
                    norm_x = x / width
                    norm_y = y / height
                    
                    # Create landmark point
                    landmark_point = type('obj', (object,), {
                        'x': norm_x,
                        'y': norm_y,
                        'z': z
                    })
                    landmark_list.append(landmark_point)
                
                # Create hand landmarks object
                hand_landmarks_obj = type('obj', (object,), {
                    'landmark': landmark_list
                })
                
                # Draw landmarks and connections
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks_obj,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error drawing landmarks: {e}")
            return frame
    
    def get_hand_center(self, landmarks: List[Tuple[float, float, float]]) -> Tuple[float, float]:
        """
        Calculate the center point of a hand
        
        Args:
            landmarks: List of 21 hand landmarks
            
        Returns:
            (x, y) coordinates of hand center
        """
        try:
            if len(landmarks) != 21:
                return (0, 0)
            
            # Calculate center as average of all landmark positions
            x_coords = [landmark[0] for landmark in landmarks]
            y_coords = [landmark[1] for landmark in landmarks]
            
            center_x = sum(x_coords) / len(x_coords)
            center_y = sum(y_coords) / len(y_coords)
            
            return (center_x, center_y)
            
        except Exception as e:
            self.logger.error(f"Error calculating hand center: {e}")
            return (0, 0)
    
    def get_finger_tip_positions(self, landmarks: List[Tuple[float, float, float]]) -> dict:
        """
        Get the positions of all finger tips
        
        Args:
            landmarks: List of 21 hand landmarks
            
        Returns:
            Dictionary with finger tip positions
        """
        try:
            if len(landmarks) != 21:
                return {}
            
            # MediaPipe hand landmark indices for finger tips
            finger_tips = {
                'thumb': 4,
                'index': 8,
                'middle': 12,
                'ring': 16,
                'pinky': 20
            }
            
            tip_positions = {}
            for finger, index in finger_tips.items():
                tip_positions[finger] = landmarks[index]
            
            return tip_positions
            
        except Exception as e:
            self.logger.error(f"Error getting finger tip positions: {e}")
            return {}
    
    def calculate_finger_distances(self, landmarks: List[Tuple[float, float, float]]) -> dict:
        """
        Calculate distances between finger tips and other landmarks
        
        Args:
            landmarks: List of 21 hand landmarks
            
        Returns:
            Dictionary with various distance measurements
        """
        try:
            if len(landmarks) != 21:
                return {}
            
            distances = {}
            
            # Thumb tip to index tip (pinch distance)
            thumb_tip = landmarks[4]
            index_tip = landmarks[8]
            distances['thumb_index'] = np.sqrt(
                (thumb_tip[0] - index_tip[0])**2 + 
                (thumb_tip[1] - index_tip[1])**2
            )
            
            # Index tip to middle tip
            middle_tip = landmarks[12]
            distances['index_middle'] = np.sqrt(
                (index_tip[0] - middle_tip[0])**2 + 
                (index_tip[1] - middle_tip[1])**2
            )
            
            # Wrist to index tip
            wrist = landmarks[0]
            distances['wrist_index'] = np.sqrt(
                (wrist[0] - index_tip[0])**2 + 
                (wrist[1] - index_tip[1])**2
            )
            
            # Palm center to fingers (using landmark 9 as palm center)
            palm_center = landmarks[9]
            for finger, tip_idx in [('thumb', 4), ('index', 8), ('middle', 12), ('ring', 16), ('pinky', 20)]:
                tip = landmarks[tip_idx]
                distances[f'palm_{finger}'] = np.sqrt(
                    (palm_center[0] - tip[0])**2 + 
                    (palm_center[1] - tip[1])**2
                )
            
            return distances
            
        except Exception as e:
            self.logger.error(f"Error calculating finger distances: {e}")
            return {}
    
    def get_detection_stats(self) -> dict:
        """Get detection performance statistics"""
        detection_rate = 0
        if self.frame_count > 0:
            detection_rate = self.detection_count / self.frame_count
        
        return {
            'total_frames': self.frame_count,
            'detections': self.detection_count,
            'detection_rate': detection_rate
        }
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'hands'):
                self.hands.close()
            self.logger.info("HandDetector cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
