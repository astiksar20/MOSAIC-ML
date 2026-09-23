import numpy as np
from scipy import sparse
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from joblib import dump


DATASET = "data/mh100k/mh100.npz"
MODEL_PATH = "ml/random_forest_model.joblib"


print("Loading MH-100K dataset...")

dataset = np.load(
    DATASET,
    allow_pickle=True
)

X = dataset["data"]
y = dataset["classes"]

print("Dataset:", X.shape)
print("Labels:", y.shape)


# Convert to sparse format
X = sparse.csr_matrix(X)


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print("Training:", X_train.shape)
print("Testing:", X_test.shape)


# Random Forest
model = RandomForestClassifier(
    n_estimators=30,
    max_features="sqrt",
    random_state=42,
    n_jobs=2
)


print("Training Random Forest...")

model.fit(
    X_train,
    y_train
)


# Save trained model
dump(
    model,
    MODEL_PATH
)


print("\n==============================")
print("MODEL TRAINING COMPLETE")
print("==============================")

print("Model saved to:")
print(MODEL_PATH)