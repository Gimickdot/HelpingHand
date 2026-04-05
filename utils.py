# utils.py
import json

def extract_landmarks(results):
    landmark_list = []
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            for i, landmark in enumerate(hand_landmarks.landmark):
                landmark_list.append({
                    "id": i,
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z
                })
    return landmark_list

def save_landmarks_to_json(landmarks, filename='hand_landmarks.json'):
    with open(filename, 'w') as f:
        json.dump(landmarks, f, indent=2)
