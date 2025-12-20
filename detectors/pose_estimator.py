import cv2
import mediapipe as mp
import numpy as np

class PoseEstimator:
    def __init__(self, mode=False, complexity=1, smooth=True, segmentation=False, detection_con=0.5, track_con=0.5):
        """
        Initialize MediaPipe Pose.
        """
        self.mp_pose = None
        self.mp_draw = None
        self.pose = None
        
        try:
            import mediapipe as mp
            try:
                self.mp_pose = mp.solutions.pose
                self.mp_draw = mp.solutions.drawing_utils
            except AttributeError:
                import mediapipe.python.solutions.pose as pose
                import mediapipe.python.solutions.drawing_utils as drawing_utils
                self.mp_pose = pose
                self.mp_draw = drawing_utils
            
            if self.mp_pose:
                self.pose = self.mp_pose.Pose(
                    static_image_mode=mode,
                    model_complexity=complexity,
                    smooth_landmarks=smooth,
                    enable_segmentation=segmentation,
                    min_detection_confidence=detection_con,
                    min_tracking_confidence=track_con
                )
        except Exception as e:
            print(f"CRITICAL_WARNING: Mediapipe initialization failed ({e}). Reverting to SAFE_MODE (Detections Only).")
        
        self.results = None

    def find_pose(self, frame, draw=True):
        """
        Process the frame to find pose landmarks.
        """
        if not self.pose:
            return frame

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(frame_rgb)

        if self.results and self.results.pose_landmarks and draw and self.mp_draw:
            self.mp_draw.draw_landmarks(frame, self.results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
        
        return frame

    def get_position(self, frame, draw=True):
        """
        Extract landmark list from the processed results.
        Runs find_pose if self.results doesn't exist.
        Returns a list of [id, x, y, z, visibility].
        """
        # Ensure we have processed the current frame
        if not self.results:
            self.find_pose(frame, draw=draw)

        lm_list = []
        if self.results and getattr(self.results, 'pose_landmarks', None):
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                lm_list.append([id, lm.x, lm.y, lm.z, lm.visibility])

        return lm_list

    def get_gait_features(self, lm_list):
        """
        Compute basic gait features: Stride length (ankle distance) and Arm Swing.
        """
        features = {}
        if len(lm_list) > 28: # Ensure we have ankle points (27, 28)
            # 23: left_hip, 24: right_hip
            # 27: left_ankle, 28: right_ankle
            # 15: left_wrist, 16: right_wrist
            
            # Simple Euclidean distance for stride (normalized by hip width optional)
            left_ankle = np.array([lm_list[27][1], lm_list[27][2]])
            right_ankle = np.array([lm_list[28][1], lm_list[28][2]])
            stride_dist = np.linalg.norm(left_ankle - right_ankle)
            
            features['stride_length'] = stride_dist
            
            # Arm swing
            left_wrist = np.array([lm_list[15][1], lm_list[15][2]])
            right_wrist = np.array([lm_list[16][1], lm_list[16][2]])
            arm_spread = np.linalg.norm(left_wrist - right_wrist)
            
            features['arm_spread'] = arm_spread
            
        return features
