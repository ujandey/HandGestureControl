#!/usr/bin/env python3
"""
Hand Gesture Recognition Demo
A simplified version that works in headless environments
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import math
from typing import List, Tuple, Optional, Dict

class GestureRecognitionDemo:
    """Simplified gesture recognition demo"""
    
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Configure hand detection
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Gesture recognition state
        self.current_gesture = "None"
        self.confidence = 0.0
        self.frame_count = 0
        self.detection_count = 0
        
        print("Gesture Recognition Demo Initialized")
        print("Supported gestures: pinch, peace_sign, thumbs_up, fist, open_palm")
    
    def detect_hands(self, frame):
        """Detect hands and return landmarks"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                self.detection_count += 1
                landmarks_list = []
                
                for hand_landmarks in results.multi_hand_landmarks:
                    height, width, _ = frame.shape
                    landmarks = []
                    
                    for landmark in hand_landmarks.landmark:
                        x = landmark.x * width
                        y = landmark.y * height
                        z = landmark.z
                        landmarks.append((x, y, z))
                    
                    landmarks_list.append(landmarks)
                
                return landmarks_list
            
            return None
            
        except Exception as e:
            print(f"Error in hand detection: {e}")
            return None
    
    def recognize_gesture(self, landmarks_list):
        """Recognize gesture from hand landmarks"""
        if not landmarks_list:
            return "None", 0.0
        
        # Use first hand
        landmarks = landmarks_list[0]
        if len(landmarks) != 21:
            return "None", 0.0
        
        try:
            # Extract finger tip and base positions
            finger_tips = {
                'thumb': landmarks[4],
                'index': landmarks[8],
                'middle': landmarks[12],
                'ring': landmarks[16],
                'pinky': landmarks[20]
            }
            
            finger_bases = {
                'thumb': landmarks[2],
                'index': landmarks[5],
                'middle': landmarks[9],
                'ring': landmarks[13],
                'pinky': landmarks[17]
            }
            
            # Calculate finger curl ratios
            curl_ratios = {}
            for finger in ['index', 'middle', 'ring', 'pinky']:
                tip = finger_tips[finger]
                base = finger_bases[finger]
                
                tip_to_base = math.sqrt((tip[0] - base[0])**2 + (tip[1] - base[1])**2)
                max_distance = 100  # Approximate max finger length
                curl_ratio = 1 - min(tip_to_base / max_distance, 1.0)
                curl_ratios[finger] = curl_ratio
            
            # Thumb curl ratio
            thumb_tip = finger_tips['thumb']
            thumb_base = finger_bases['thumb']
            thumb_distance = math.sqrt((thumb_tip[0] - thumb_base[0])**2 + (thumb_tip[1] - thumb_base[1])**2)
            curl_ratios['thumb'] = 1 - min(thumb_distance / 80, 1.0)
            
            # Gesture classification
            gesture_scores = {}
            
            # Pinch gesture (thumb and index close)
            thumb_index_dist = math.sqrt(
                (finger_tips['thumb'][0] - finger_tips['index'][0])**2 + 
                (finger_tips['thumb'][1] - finger_tips['index'][1])**2
            )
            if thumb_index_dist < 50:
                gesture_scores['pinch'] = 1 - (thumb_index_dist / 50)
            
            # Peace sign (index and middle extended, others curled)
            if (curl_ratios['index'] < 0.3 and curl_ratios['middle'] < 0.3 and 
                curl_ratios['ring'] > 0.7 and curl_ratios['pinky'] > 0.7):
                gesture_scores['peace_sign'] = 0.9
            
            # Thumbs up (thumb extended, others curled)
            if (curl_ratios['thumb'] < 0.3 and curl_ratios['index'] > 0.7 and 
                curl_ratios['middle'] > 0.7 and curl_ratios['ring'] > 0.7 and 
                curl_ratios['pinky'] > 0.7):
                gesture_scores['thumbs_up'] = 0.9
            
            # Fist (all fingers curled)
            if all(curl_ratios[finger] > 0.8 for finger in curl_ratios):
                gesture_scores['fist'] = 0.95
            
            # Open palm (all fingers extended)
            if all(curl_ratios[finger] < 0.3 for finger in curl_ratios):
                gesture_scores['open_palm'] = 0.9
            
            # Return best gesture
            if gesture_scores:
                best_gesture = max(gesture_scores, key=gesture_scores.get)
                best_confidence = gesture_scores[best_gesture]
                
                if best_confidence >= 0.8:
                    return best_gesture, best_confidence
            
            return "None", 0.0
            
        except Exception as e:
            print(f"Error in gesture recognition: {e}")
            return "None", 0.0
    
    def draw_landmarks(self, frame, landmarks_list):
        """Draw hand landmarks on frame"""
        if not landmarks_list:
            return frame
        
        for landmarks in landmarks_list:
            # Draw landmark points
            for i, (x, y, z) in enumerate(landmarks):
                if i in [4, 8, 12, 16, 20]:  # Finger tips
                    color = (0, 255, 0)  # Green
                    radius = 6
                else:
                    color = (255, 255, 0)  # Yellow
                    radius = 4
                
                cv2.circle(frame, (int(x), int(y)), radius, color, -1)
            
            # Draw connections
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                (0, 5), (5, 6), (6, 7), (7, 8),  # Index
                (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
                (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
                (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
                (5, 9), (9, 13), (13, 17)  # Palm
            ]
            
            for start_idx, end_idx in connections:
                if start_idx < len(landmarks) and end_idx < len(landmarks):
                    start_point = landmarks[start_idx]
                    end_point = landmarks[end_idx]
                    
                    cv2.line(frame,
                            (int(start_point[0]), int(start_point[1])),
                            (int(end_point[0]), int(end_point[1])),
                            (255, 255, 255), 2)
        
        return frame
    
    def process_frame(self, frame):
        """Process a single frame"""
        self.frame_count += 1
        
        # Detect hands
        landmarks_list = self.detect_hands(frame)
        
        # Recognize gesture
        gesture, confidence = self.recognize_gesture(landmarks_list)
        
        # Update current state
        if confidence > 0.8:
            self.current_gesture = gesture
            self.confidence = confidence
        
        # Draw landmarks
        if landmarks_list:
            frame = self.draw_landmarks(frame, landmarks_list)
        
        # Draw gesture info
        cv2.putText(frame, f"Gesture: {self.current_gesture}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, f"Confidence: {self.confidence*100:.1f}%", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Draw performance info
        detection_rate = (self.detection_count / self.frame_count) * 100 if self.frame_count > 0 else 0
        cv2.putText(frame, f"Frames: {self.frame_count} | Detection Rate: {detection_rate:.1f}%", 
                   (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def run_demo(self, duration=30):
        """Run gesture recognition demo"""
        print(f"\nRunning gesture recognition demo for {duration} seconds...")
        print("Show your hand to the camera and try different gestures!")
        
        # Try to open camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Warning: Camera not available, creating test frames...")
            # Create synthetic test frame
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(test_frame, "GESTURE RECOGNITION DEMO", 
                       (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            cv2.putText(test_frame, "Camera not available in this environment", 
                       (80, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(test_frame, "But the gesture recognition system is ready!", 
                       (60, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            processed_frame = self.process_frame(test_frame.copy())
            
            # Save demo frame
            cv2.imwrite("gesture_demo_frame.jpg", processed_frame)
            print("Demo frame saved as 'gesture_demo_frame.jpg'")
            return
        
        start_time = time.time()
        frame_count = 0
        
        try:
            while time.time() - start_time < duration:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                processed_frame = self.process_frame(frame)
                
                # Save periodic frames
                if frame_count % 30 == 0:  # Every 30 frames
                    cv2.imwrite(f"gesture_frame_{frame_count}.jpg", processed_frame)
                
                frame_count += 1
                
                # Limit frame rate
                time.sleep(1/30)  # 30 FPS
                
        except KeyboardInterrupt:
            print("\nDemo stopped by user")
        finally:
            cap.release()
            
        print(f"\nDemo completed!")
        print(f"Total frames processed: {self.frame_count}")
        print(f"Detections: {self.detection_count}")
        print(f"Final gesture: {self.current_gesture} (confidence: {self.confidence*100:.1f}%)")

def main():
    """Main demo function"""
    try:
        demo = GestureRecognitionDemo()
        demo.run_demo(duration=10)  # Run for 10 seconds
        
    except Exception as e:
        print(f"Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()