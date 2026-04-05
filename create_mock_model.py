"""
Create a mock ASL model for testing the Django web interface.
This is a placeholder - replace with your trained model for actual use.
"""
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Create a simple mock model that returns random predictions
# This is just for testing the web interface

# Create sample data (63 features for 21 landmarks * 3 coordinates)
np.random.seed(42)
X = np.random.randn(1000, 63)

# Labels: A-Z, del, nothing, space
labels = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + ['del', 'nothing', 'space']
y = np.random.choice(labels, size=1000)

# Train a simple model
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = RandomForestClassifier(n_estimators=10, random_state=42)
model.fit(X_scaled, y)

# Save the model and scaler
joblib.dump(model, 'asl_model.pkl')
joblib.dump(scaler, 'asl_scaler.pkl')

print("✓ Mock model created: asl_model.pkl")
print("✓ Mock scaler created: asl_scaler.pkl")
print(f"✓ Classes: {model.classes_}")
print("\nNote: This is a RANDOM mock model for testing only!")
print("For actual ASL recognition, train with real data using: python train.py")
