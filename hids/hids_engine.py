import numpy as np

from hids.hids_detector import (
    detect_rule_based_events,
    calculate_rule_score
)

from hids.isolation_detector import (
    train_isolation_forest,
    detect_anomalies
)


def calculate_hids_score(
    rule_score,
    isolation_results
):
    """
    Combine rule-based and Isolation Forest signals
    into one HIDS score from 0 to 100.
    """

    if isolation_results:

        anomaly_count = sum(
            1
            for result in isolation_results
            if result["status"] == "ANOMALY"
        )

        anomaly_ratio = (
            anomaly_count /
            len(isolation_results)
        )

        isolation_score = anomaly_ratio * 100

    else:
        isolation_score = 0


    final_score = (
        0.60 * rule_score +
        0.40 * isolation_score
    )

    return round(
        min(final_score, 100),
        2
    )


def run_hids(
    runtime_events,
    runtime_data
):
    """
    Run the complete HIDS pipeline.
    """

    alerts = detect_rule_based_events(
        runtime_events
    )

    rule_score = calculate_rule_score(
        alerts
    )

    model = train_isolation_forest(
        runtime_data
    )

    isolation_results = detect_anomalies(
        model,
        runtime_data
    )

    hids_score = calculate_hids_score(
        rule_score,
        isolation_results
    )

    return {
        "rule_alerts": alerts,
        "rule_score": rule_score,
        "isolation_results": isolation_results,
        "hids_score": hids_score
    }


if __name__ == "__main__":

    print("MOSAIC-ML HIDS ENGINE")
    print("==============================")


    runtime_events = [
        "normal_file_access",
        "unexpected_sms",
        "unknown_network_connection"
    ]


    runtime_data = np.array([
        [1, 0, 2, 1],
        [2, 0, 1, 1],
        [1, 0, 2, 2],
        [2, 1, 2, 1],
        [1, 0, 1, 1],
        [20, 15, 30, 25]
    ])


    result = run_hids(
        runtime_events,
        runtime_data
    )


    print("\nRule Score:")
    print(result["rule_score"])


    print("\nHIDS Alerts:")

    for alert in result["rule_alerts"]:
        print(alert)


    print("\nIsolation Forest Results:")

    for item in result["isolation_results"]:
        print(item)


    print("\nFinal HIDS Score:")
    print(result["hids_score"])