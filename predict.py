import cv2
import mediapipe as mp
import joblib
import numpy as np
import time
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# Load model and scaler
model = joblib.load("asl_model.pkl")
scaler = joblib.load("asl_scaler.pkl")

# Setup MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

confidence_threshold = 0.75
spelled_text = ""
last_char = ""
last_added_time = 0
cooldown_seconds = 2

while True:
    ret, frame = cap.read()
    if not ret:
        break

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            lm_list = []
            h, w, _ = frame.shape
            x_list, y_list = [], []

            for lm in handLms.landmark:
                x, y, z = lm.x, lm.y, lm.z
                lm_list.extend([x, y, z])
                x_list.append(int(x * w))
                y_list.append(int(y * h))

            if len(lm_list) == 63:
                lm_scaled = scaler.transform([lm_list])
                proba = model.predict_proba(lm_scaled)[0]
                pred_index = np.argmax(proba)
                pred_char = str(model.classes_[pred_index])
                confidence = proba[pred_index]

                current_time = time.time()
                if confidence >= confidence_threshold:
                    if (pred_char != last_char) or (current_time - last_added_time >= cooldown_seconds):
                        if pred_char.lower() == "del":
                            spelled_text = spelled_text[:-1]
                        elif pred_char.lower() == "space":
                            spelled_text += " "
                        else:
                            spelled_text += pred_char
                        last_char = pred_char
                        last_added_time = current_time

                # Draw prediction
                x_min, x_max = min(x_list), max(x_list)
                y_min, y_max = min(y_list), max(y_list)
                cv2.putText(frame, f'{pred_char} ({confidence:.2f})',
                            (x_min, y_max + 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0), 2)

            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

    # Display spelled text at top
    cv2.putText(frame, f'Spelled: {spelled_text}', (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)

    cv2.imshow("ASL Detection", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
