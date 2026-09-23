import numpy as np
from scipy import sparse
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# Load MH-100K dataset
dataset = np.load(
    "data/mh100k/mh100.npz",
    allow_pickle=True
)

X = dataset["data"]
y = dataset["classes"]

print("Dataset:", X.shape)
print("Labels:", y.shape)


# Convert feature matrix to sparse format
X = sparse.csr_matrix(X)


# Split into training and testing data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training:", X_train.shape)
print("Testing:", X_test.shape)


# Random Forest baseline
model = RandomForestClassifier(
    n_estimators=30,
    max_features="sqrt",
    random_state=42,
    n_jobs=2
)

print("Training Random Forest...")

model.fit(X_train, y_train)


# Prediction
print("Predicting...")

y_pred = model.predict(X_test)


# Evaluation
print("\n==============================")
print("MOSAIC-ML RANDOM FOREST BASELINE")
print("==============================")

print("\nAccuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))