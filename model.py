# model.py
import mediapipe as mp

def load_hand_model(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5):
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=static_image_mode,
        max_num_hands=max_num_hands,
        min_detection_confidence=min_detection_confidence
    )
    return hands
