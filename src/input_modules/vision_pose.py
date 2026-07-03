import cv2
import mediapipe as mp
import numpy as np


class PoseTracker:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1, 
            enable_segmentation=False,
            min_detection_confidence=0.6, 
            min_tracking_confidence=0.6
        )
        self.current_tilt = 0.0      
        self.confidence_score = 0.0 

    def process_frame(self, frame):
        action = "STATIONARY"
        cv2.flip(frame, 1, dst=frame)
        h, w, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE]
            
            if nose.visibility > 0.70 and left_shoulder.visibility > 0.70 and right_shoulder.visibility > 0.70:
                self.confidence_score = (right_shoulder.visibility + left_shoulder.visibility + nose.visibility) / 3.0
                shoulder_tilt = (left_shoulder.y - right_shoulder.y) * -1
                self.current_tilt = shoulder_tilt
                THRESHOLD = 0.035
                if shoulder_tilt > THRESHOLD:
                    action = "LEFT"
                elif shoulder_tilt < -THRESHOLD:
                    action = "RIGHT"
                else:
                    action = "STATIONARY"  
                
                self.mp_drawing.draw_landmarks(
                    frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                )          
            else:
                action = "LOW CONFIDENCE"
                self.confidence_score = 0.0
                self.current_tilt = 0.0
        else:
            action = "LOW CONFIDENCE"
            self.confidence_score = 0.0
            self.current_tilt = 0.0

        if action == "LOW CONFIDENCE":
            color_bgr = (0, 0, 255)      
            text_left = "STATUS: LOW CONFIDENCE"
        elif action == "STATIONARY":
            color_bgr = (0, 255, 0)      
            text_left = f"STATUS: STATIONARY"
        else:
            color_bgr = (0, 255, 255)    
            text_left = f"MOVE: {action}"            
        cv2.putText(frame, text_left, (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_bgr, 2, cv2.LINE_AA)

        text_right = f"Confidence: {self.confidence_score:.2f}"
        cv2.putText(frame, text_right, (w - 240, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_bgr, 2, cv2.LINE_AA)
        
        return action, self.confidence_score
    
    def close(self):
        self.pose.close()