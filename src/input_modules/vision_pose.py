import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

print("NEW FILE LOADED")

class PoseTracker:
    def __init__(self):
        self.mp_pose = mp_pose
        self.mp_drawing = mp_drawing
        self.pose = self.mp_pose.Pose(
            model_complexity=0, 
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        self.cap = cv2.VideoCapture(0)
        self.current_tilt = 0.0      
        self.confidence_score = 0.0 

    def update(self):
        success, frame = self.cap.read()
        if not success:
            self.confidence_score = 0.0
            return False, None
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            
            self.confidence_score = (left_shoulder.visibility + right_shoulder.visibility) / 2.0
            shoulder_tilt = right_shoulder.y - left_shoulder.y
            self.current_tilt = shoulder_tilt / 0.03  #sensitivity 
            self.current_tilt = max(-1.0, min(1.0, self.current_tilt))
            
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS
            )
        else:
            self.current_tilt = 0.0
            self.confidence_score = 0.0
        return True, frame

    def close(self):
        self.cap.release()

