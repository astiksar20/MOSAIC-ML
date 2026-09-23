def calculate_risk_score(
    ml_probability,
    hids_score,
    cvss_scores
):
    """
    Calculate MOSAIC-ML prototype risk score (0-100).

    Components:
    - ML malware probability: 40%
    - HIDS score: 40%
    - CVSS vulnerability severity: 20%
    """

    # ML signal
    ml_score = ml_probability * 100

    # HIDS signal
    hids_component = hids_score

    # CVSS signal
    if cvss_scores:
        max_cvss = max(cvss_scores)
        cvss_component = (max_cvss / 10) * 100
    else:
        cvss_component = 0

    # Combined score
    risk_score = (
        0.40 * ml_score +
        0.40 * hids_component +
        0.20 * cvss_component
    )

    return round(
        min(risk_score, 100),
        2
    )


def classify_risk(risk_score):

    if risk_score < 30:
        return "LOW"

    elif risk_score < 70:
        return "MEDIUM"

    else:
        return "HIGH"


def generate_recommendation(risk_category):

    if risk_category == "LOW":
        return "Monitor application"

    elif risk_category == "MEDIUM":
        return "Monitor closely and review application permissions"

    else:
        return "Restrict application and investigate further"


def generate_risk_report(
    ml_probability,
    hids_score,
    cvss_scores
):

    risk_score = calculate_risk_score(
        ml_probability,
        hids_score,
        cvss_scores
    )

    category = classify_risk(
        risk_score
    )

    recommendation = generate_recommendation(
        category
    )

    return {
        "risk_score": risk_score,
        "risk_category": category,
        "recommendation": recommendation
    }


if __name__ == "__main__":

    print("MOSAIC-ML RISK ENGINE")
    print("==============================")


    # Example values
    ml_probability = 0.1333

    hids_score = 30.67

    cvss_scores = [
        7.5
    ]


    report = generate_risk_report(
        ml_probability,
        hids_score,
        cvss_scores
    )


    print("\nRisk Score:")
    print(report["risk_score"])

    print("\nRisk Category:")
    print(report["risk_category"])

    print("\nRecommendation:")
    print(report["recommendation"])
    