import requests


NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def search_cve(keyword):
    params = {
        "keywordSearch": keyword,
        "resultsPerPage": 5
    }

    response = requests.get(
        NVD_API_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def extract_cve_information(data):
    results = []

    for item in data.get("vulnerabilities", []):

        cve = item.get("cve", {})

        # CVE ID
        cve_id = cve.get("id")

        # Description
        description = ""

        descriptions = cve.get("descriptions", [])

        if descriptions:
            description = descriptions[0].get("value", "")

        # CVSS
        cvss_score = None
        cvss_severity = None

        metrics = cve.get("metrics", {})

        if "cvssMetricV31" in metrics:
            cvss = metrics["cvssMetricV31"][0]["cvssData"]
            cvss_score = cvss.get("baseScore")
            cvss_severity = cvss.get("baseSeverity")

        elif "cvssMetricV30" in metrics:
            cvss = metrics["cvssMetricV30"][0]["cvssData"]
            cvss_score = cvss.get("baseScore")
            cvss_severity = cvss.get("baseSeverity")

        elif "cvssMetricV2" in metrics:
            cvss = metrics["cvssMetricV2"][0]["cvssData"]
            cvss_score = cvss.get("baseScore")

        # CWE
        cwe = None

        weaknesses = cve.get("weaknesses", [])

        if weaknesses:

            weakness_descriptions = weaknesses[0].get(
                "description",
                []
            )

            if weakness_descriptions:
                cwe = weakness_descriptions[0].get("value")

        results.append({
            "cve_id": cve_id,
            "description": description,
            "cvss_score": cvss_score,
            "cvss_severity": cvss_severity,
            "cwe": cwe
        })

    return results


def search_multiple_components(components):

    all_results = []

    for component in components:

        print("\nSearching NVD for:", component)

        data = search_cve(component)

        results = extract_cve_information(data)

        for result in results:
            result["searched_component"] = component

        all_results.extend(results)

    return all_results


if __name__ == "__main__":

    # Example Android components
    components = [
        "Android Bionic",
        "Android WebKit"
    ]

    results = search_multiple_components(components)

    print("\n==============================")
    print("MOSAIC-ML CVE/NVD RESULTS")
    print("==============================")

    for item in results:

        print("\n------------------------------")

        print("Component:", item["searched_component"])
        print("CVE:", item["cve_id"])
        print("CVSS:", item["cvss_score"])
        print("Severity:", item["cvss_severity"])
        print("CWE:", item["cwe"])
        print(
            "Description:",
            item["description"][:200]
        )