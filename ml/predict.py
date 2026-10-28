import os
from pathlib import Path

import joblib
import numpy as np


# Anchored to this file so the model loads regardless of working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    str(PROJECT_ROOT / "ml" / "models" / "selected_model.joblib")
)

# The active model is whichever classifier scripts/tune_models.py selected on
# validation balanced accuracy, refit on train+validation and saved as
# selected_model.joblib. Set MODEL_PATH to serve a different one:
#   ml/models/logistic_regression.joblib
#   ml/models/random_forest.joblib
# ml/models/linear_svm.joblib CANNOT be served: a linear SVM outputs a margin,
# not a probability, and the API reports a probability. Converting the margin
# would mean inventing a calibration that was never fitted, so it is refused.
_MODEL = None

_NAMES = {
    "LogisticRegression": "Logistic Regression",
    "LinearSVC": "Linear SVM",
    "RandomForestClassifier": "Random Forest",
}


def model_name(model=None):
    m = model if model is not None else load_model()
    return _NAMES.get(type(m).__name__, type(m).__name__)


def load_model():
    """Loaded once and cached, not reloaded per request."""
    global _MODEL
    if _MODEL is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"model not found at {MODEL_PATH}. Set MODEL_PATH if it lives "
                "elsewhere."
            )
        model = joblib.load(MODEL_PATH)
        if not hasattr(model, "predict_proba"):
            raise ValueError(
                f"{model_name(model)} at {MODEL_PATH} gives no probability, "
                "which the API reports. Serve logistic_regression.joblib or "
                "random_forest.joblib instead."
            )
        _MODEL = model
    return _MODEL


def predict_apk(feature_vector):

    model = load_model()

    prediction = model.predict(feature_vector)[0]

    probability = model.predict_proba(feature_vector)[0]

    return {
        "prediction": int(prediction),
        "label": (
            "MALWARE"
            if prediction == 1
            else "BENIGN"
        ),
        "malware_probability": float(probability[1]),
        "benign_probability": float(probability[0]),
        "model": model_name(model),
    }


if __name__ == "__main__":

    print("MOSAIC-ML ML Prediction Module")

    model = load_model()

    print("Model loaded successfully.")

    print(
        "Number of features expected:",
        model.n_features_in_
    )