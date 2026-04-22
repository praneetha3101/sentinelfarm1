import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "crop_recommendation_dataset.csv")

df = pd.read_csv(csv_path)

# Clean column names
df.columns = df.columns.str.strip()

print("Columns:", df.columns)

# Detect target column automatically
if "label" in df.columns:
    target_col = "label"
elif "crop" in df.columns:
    target_col = "crop"
elif "Crop" in df.columns:
    target_col = "Crop"
else:
    raise Exception("Target column not found in dataset")

X = df.drop(target_col, axis=1)
y = df[target_col]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X_train, y_train)

print("Model Accuracy:", model.score(X_test, y_test))

joblib.dump(model, "crop_model.pkl")
print("Model saved successfully!")