from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
import pandas as pd
import joblib

# Load data
df = pd.read_csv("asl_hand_landmarks.csv")
X = df.drop("label", axis=1)
y = df["label"]

# Encode string labels to numeric
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Stratified split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

# Define MLP model
mlp = MLPClassifier(
    hidden_layer_sizes=(256, 128, 64),
    activation='relu',
    solver='adam',
    alpha=1e-4,
    max_iter=1000,
    random_state=42,
    early_stopping=True,
    n_iter_no_change=15,
    verbose=True
)

# Train model
mlp.fit(X_train, y_train)

# Evaluate
y_pred = mlp.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print("Validation Accuracy:", accuracy)

# Save model, scaler, and label encoder
joblib.dump(mlp, "asl_model.pkl")
joblib.dump(scaler, "asl_scaler.pkl")
joblib.dump(le, "asl_label_encoder.pkl")
print("Model, scaler, and label encoder saved.")
