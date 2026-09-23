import numpy as np
from sklearn.ensemble import IsolationForest


def train_isolation_forest(runtime_data):

    model = IsolationForest(
        n_estimators=100,
        contamination=0.10,
        random_state=42
    )

    model.fit(runtime_data)

    return model


def detect_anomalies(model, runtime_data):

    predictions = model.predict(runtime_data)

    scores = model.decision_function(runtime_data)

    results = []

    for prediction, score in zip(
        predictions,
        scores
    ):

        if prediction == -1:
            status = "ANOMALY"
        else:
            status = "NORMAL"

        results.append({
            "status": status,
            "anomaly_score": float(score)
        })

    return results


if __name__ == "__main__":

    print("MOSAIC-ML Isolation Forest")
    print("==============================")

    # Example runtime behavior features
    #
    # Columns:
    # [network_connections,
    #  sms_activity,
    #  file_access,
    #  process_activity]

    runtime_data = np.array([
        [1, 0, 2, 1],
        [2, 0, 1, 1],
        [1, 0, 2, 2],
        [2, 1, 2, 1],
        [1, 0, 1, 1],
        [20, 15, 30, 25],
    ])

    model = train_isolation_forest(
        runtime_data
    )

    results = detect_anomalies(
        model,
        runtime_data
    )

    print("\nDetection Results:")

    for result in results:
        print(result)