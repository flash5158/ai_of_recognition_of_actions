import cv2
from ultralytics import YOLO
import numpy as np
import logging

class PoseEstimator:
    def __init__(self, model_path="yolo11n-pose.pt"):
        """
        Initialize YOLOv11 Pose Estimator.
        Replaces MediaPipe to ensure compatibility with Python 3.13 and robust detections.
        """
        self.pose_model = None
        self.results = None
        
        try:
            # Initialize with verbose=False to keep logs clean
            self.pose_model = YOLO(model_path)
            logging.getLogger("panoptes.pose").info("YOLOv11-Pose Online")
        except Exception as e:
            print(f"CRITICAL_ERROR: Failed to load YOLO Pose model: {e}")
            self.pose_model = None

    def find_pose(self, frame, draw=True):
        """
        Process the frame to find pose landmarks using YOLO.
        Returns the annotated frame.
        """
        if not self.pose_model:
            return frame

        # YOLO inference
        # Classes filter not strictly needed for pose model usually, but good practice
        self.results = self.pose_model(frame, verbose=False)
        
        if draw and self.results:
            # Use Ultralytics' built-in plotter which handles skeletons beautifully
            return self.results[0].plot()
            
        return frame

    def get_position(self, frame, draw=True):
        """
        Extract landmark list from the processed results.
        Returns a list of [id, x, y, conf] for the primary detected person.
        Standardizes output for ActionClassifier.
        """
        if not self.results:
            self.find_pose(frame, draw=draw)

        lm_list = []
        
        # Check if we have results and keypoints
        if self.results and len(self.results) > 0:
            res = self.results[0]
            if res.keypoints is not None and res.keypoints.xy.shape[1] > 0:
                # We take the first person detected (index 0) to maintain single-subject logic for now
                # In the future, we can loop over all persons.
                # Shape is (NumPersons, NumKoins, 2)
                if res.keypoints.xy.shape[0] > 0:
                    person_kpts = res.keypoints.xy[0].cpu().numpy()
                    
                    # Confidences might be None depending on model export, handling that
                    if res.keypoints.conf is not None:
                        confs = res.keypoints.conf[0].cpu().numpy()
                    else:
                        confs = np.ones(len(person_kpts))

                    for i in range(len(person_kpts)):
                        x, y = person_kpts[i]
                        c = confs[i]
                        # Structure: [id, x, y, confidence]
                        lm_list.append([i, x, y, c])

        return lm_list

    def get_gait_features(self, lm_list):
        """
        Compute basic gait features for COCO Keypoints.
        COCO Indices:
        L_Ankle: 15, R_Ankle: 16
        L_Wrist: 9, R_Wrist: 10
        """
        features = {}
        if len(lm_list) >= 17:
            # Euclidean distance for stride
            left_ankle = np.array([lm_list[15][1], lm_list[15][2]])
            right_ankle = np.array([lm_list[16][1], lm_list[16][2]])
            stride_dist = np.linalg.norm(left_ankle - right_ankle)
            
            features['stride_length'] = stride_dist
            
            # Arm swing
            left_wrist = np.array([lm_list[9][1], lm_list[9][2]])
            right_wrist = np.array([lm_list[10][1], lm_list[10][2]])
            arm_spread = np.linalg.norm(left_wrist - right_wrist)
            
            features['arm_spread'] = arm_spread
            
        return features
