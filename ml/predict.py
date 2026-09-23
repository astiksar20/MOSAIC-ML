import joblib
import numpy as np


MODEL_PATH = "ml/random_forest_model.joblib"


def load_model():
    return joblib.load(MODEL_PATH)


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
        "benign_probability": float(probability[0])
    }


if __name__ == "__main__":

    print("MOSAIC-ML ML Prediction Module")

    model = load_model()

    print("Model loaded successfully.")

    print(
        "Number of features expected:",
        model.n_features_in_
    )