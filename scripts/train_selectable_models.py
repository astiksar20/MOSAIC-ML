import gc
from pathlib import Path

import numpy as np
from scipy import sparse
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import BernoulliNB
from joblib import dump

X_PATH = Path("data/processed/mh100_csr.npz")
Y_PATH = Path("data/processed/classes.npy")
OUT = Path("ml/models")
OUT.mkdir(parents=True, exist_ok=True)

print("Loading sparse dataset...", flush=True)
X = sparse.load_npz(X_PATH).tocsr()
y = np.load(Y_PATH, allow_pickle=True).ravel()
print(f"Dataset: {X.shape}; labels: {y.shape}", flush=True)

if X.shape[0] != len(y):
    raise ValueError("Dataset row count and label count do not match.")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
del X, X_test, y_test
gc.collect()

models = [
    ("logistic_regression", LogisticRegression(
        max_iter=300, solver="liblinear", random_state=42
    )),
    ("linear_svm", LinearSVC(
        dual="auto", max_iter=3000, random_state=42
    )),
    ("random_forest_100", RandomForestClassifier(
        n_estimators=100, max_features="sqrt",
        random_state=42, n_jobs=1
    )),
    ("random_forest_30", RandomForestClassifier(
        n_estimators=30, max_features="sqrt",
        random_state=42, n_jobs=1
    )),
    ("decision_tree", DecisionTreeClassifier(random_state=42)),
    ("bernoulli_nb", BernoulliNB()),
]

for name, model in models:
    target = OUT / f"{name}.joblib"
    if target.exists():
        print(f"Already saved; skipping {name}", flush=True)
        continue

    print(f"\nTraining {name}...", flush=True)
    model.fit(X_train, y_train)
    dump(model, target, compress=1)
    print(f"Saved: {target}", flush=True)
    del model
    gc.collect()

print("\nTraining process finished. Check the messages above for any errors.", flush=True)
