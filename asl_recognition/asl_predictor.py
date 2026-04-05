"""
Core ASL Prediction Module
This module wraps the existing ASL recognition functionality for use in Django.
It uses MediaPipe for hand landmark detection and a pre-trained Random Forest model.
"""

import joblib
import numpy as np
import mediapipe as mp
import warnings
from django.conf import settings
import os

warnings.filterwarnings("ignore", category=UserWarning)


class ASLPredictor:
    """ASL Sign Language Predictor using MediaPipe and Random Forest"""
    
    def __init__(self):
        # Load model and scaler from the original project files
        model_path = os.path.join(settings.BASE_DIR, 'asl_model.pkl')
        scaler_path = os.path.join(settings.BASE_DIR, 'asl_scaler.pkl')
        
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        
        # Setup MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        self.confidence_threshold = 0.15
    
    def extract_landmarks(self, image_rgb):
        """
        Extract hand landmarks from an RGB image.
        Returns: (landmarks_list, hand_landmarks_obj, normalized_coords) or (None, None, None) if no hand detected
        """
        result = self.hands.process(image_rgb)
        
        if result.multi_hand_landmarks:
            handLms = result.multi_hand_landmarks[0]  # Use first hand
            lm_list = []
            normalized_coords = []  # For drawing: list of {x, y} in 0-1 range
            
            for lm in handLms.landmark:
                x, y, z = lm.x, lm.y, lm.z
                lm_list.extend([x, y, z])
                normalized_coords.append({'x': x, 'y': y})
            
            return lm_list, handLms, normalized_coords
        
        return None, None, None
    
    def predict(self, landmarks):
        """
        Predict ASL letter from hand landmarks.
        
        Args:
            landmarks: List of 63 values (21 landmarks * 3 coordinates)
        
        Returns:
            dict with 'prediction', 'confidence', 'all_probabilities'
        """
        if len(landmarks) != 63:
            return {
                'prediction': None,
                'confidence': 0,
                'error': 'Invalid landmarks: expected 63 values (21 landmarks * 3 coordinates)'
            }
        
        # Scale landmarks
        lm_scaled = self.scaler.transform([landmarks])
        
        # Get prediction probabilities
        proba = self.model.predict_proba(lm_scaled)[0]
        pred_index = np.argmax(proba)
        pred_char = str(self.model.classes_[pred_index])
        confidence = proba[pred_index]
        
        # Build all probabilities dict
        all_probs = {str(cls): float(prob) for cls, prob in zip(self.model.classes_, proba)}
        
        return {
            'prediction': pred_char if confidence >= self.confidence_threshold else None,
            'confidence': float(confidence),
            'all_probabilities': all_probs,
            'raw_prediction': pred_char
        }
    
    def process_frame(self, image_rgb):
        """
        Process a single frame and return prediction results.
        
        Args:
            image_rgb: RGB image as numpy array
        
        Returns:
            dict with prediction results and hand landmarks for drawing
        """
        landmarks, hand_obj, normalized_coords = self.extract_landmarks(image_rgb)
        
        if landmarks is None:
            return {
                'hand_detected': False,
                'prediction': None,
                'confidence': 0,
                'landmarks': None,
                'normalized_coords': None
            }
        
        result = self.predict(landmarks)
        result['hand_detected'] = True
        result['landmarks'] = landmarks
        result['normalized_coords'] = normalized_coords
        
        return result


# Singleton instance for reuse across requests
_predictor_instance = None


def get_predictor():
    """Get or create the ASL predictor singleton"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = ASLPredictor()
    return _predictor_instance
