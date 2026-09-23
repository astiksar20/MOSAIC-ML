# MOSAIC-ML Host-Based Intrusion Detection System (HIDS)

SUSPICIOUS_EVENTS = {
    "unexpected_sms",
    "unknown_network_connection",
    "suspicious_file_access",
    "privilege_change",
    "unexpected_process",
}


def detect_rule_based_events(events):
    """
    Detect predefined suspicious runtime events.

    Parameters:
        events: list of runtime event names

    Returns:
        list of detected suspicious events
    """

    alerts = []

    for event in events:

        if event in SUSPICIOUS_EVENTS:

            alerts.append({
                "event": event,
                "alert": "SUSPICIOUS_ACTIVITY",
                "severity": "HIGH"
            })

    return alerts


def calculate_rule_score(alerts):
    """
    Convert rule-based alerts into a simple
    0-100 anomaly score.
    """

    if not alerts:
        return 0

    score = len(alerts) * 20

    return min(score, 100)


if __name__ == "__main__":

    print("MOSAIC-ML HIDS")
    print("==============================")

    # Example runtime events
    test_events = [
        "normal_file_access",
        "unexpected_sms",
        "unknown_network_connection",
    ]

    alerts = detect_rule_based_events(test_events)

    score = calculate_rule_score(alerts)

    print("\nRuntime Events:")
    print(test_events)

    print("\nHIDS Alerts:")

    for alert in alerts:
        print(alert)

    print("\nHIDS Anomaly Score:", score)