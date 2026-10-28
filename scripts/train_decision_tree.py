from pathlib import Path
import numpy as np
import joblib
from scipy import sparse
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUTPUT = ROOT / "ml" / "models" / "decision_tree.joblib"

print("Loading dataset...", flush=True)
X = sparse.load_npz(DATA / "mh100_csr.npz")
y = np.load(DATA / "classes.npy")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

print("Training Decision Tree...", flush=True)
model = DecisionTreeClassifier(random_state=42)
model.fit(X_train, y_train)

print("Checking test accuracy...", flush=True)
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

joblib.dump(model, OUTPUT, compress=1)

print(f"Saved model: {OUTPUT}", flush=True)
print(f"Test accuracy: {accuracy:.4%}", flush=True)
print("Training complete.", flush=True)
