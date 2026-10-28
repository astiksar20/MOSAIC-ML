"""
MOSAIC-ML - NVD / CVE lookup client.

What changed and why
--------------------
The previous client called response.raise_for_status() with no exception
handling, so any network error, 403 or 429 propagated out of
search_multiple_components() and took down the whole /analyze-apk request.
Confirmed in testing: one blocked NVD request produced an HTTP 500 and the
caller received no ML result, no permission score, nothing.

It also issued one unthrottled request per component. NVD allows 5 requests
per 30 seconds without an API key and 50 with one, so a scan that searched
10 components was guaranteed to be rate-limited.

Three outcomes are now reported distinctly, because collapsing them is how a
tool ends up claiming an app has no vulnerabilities when it never looked:

    "records_returned"  - the query ran and matched CVE records
    "zero_records"      - the query ran and matched nothing
    "lookup_failed"     - the query did not complete (timeout, 403, 429, ...)

A keyword match is a CANDIDATE. Permission and component names are not software
products, so a hit on them does not establish that the APK is affected.

Set NVD_API_KEY in the environment to raise the rate limit.
"""

import os
import time

import requests


NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

API_KEY = os.environ.get("NVD_API_KEY", "").strip() or None

# NVD: 5 requests / 30s unauthenticated, 50 / 30s with a key.
DELAY_SECONDS = 0.8 if API_KEY else 6.5
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

RECORDS_RETURNED = "records_returned"
ZERO_RECORDS = "zero_records"
LOOKUP_FAILED = "lookup_failed"

_CACHE = {}


def search_cve(keyword, results_per_page=5):
    """One NVD query. Returns (data, status, error) and never raises."""
    if keyword in _CACHE:
        return _CACHE[keyword]

    headers = {"apiKey": API_KEY} if API_KEY else {}
    params = {"keywordSearch": keyword, "resultsPerPage": results_per_page}

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                NVD_API_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                total = data.get("totalResults", 0)
                status = RECORDS_RETURNED if total else ZERO_RECORDS
                result = (data, status, None)
                _CACHE[keyword] = result
                return result

            if response.status_code in (429, 503):
                wait = (2 ** attempt) * 6
                last_error = f"HTTP {response.status_code} (rate limited)"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)
                    continue

            last_error = f"HTTP {response.status_code}"
            break

        except requests.exceptions.Timeout:
            last_error = f"timeout after {REQUEST_TIMEOUT}s"
        except requests.exceptions.RequestException as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        except ValueError as exc:
            last_error = f"invalid JSON: {exc}"
            break

        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    result = (None, LOOKUP_FAILED, last_error)
    _CACHE[keyword] = result
    return result


def extract_cve_information(data):
    """Parse the NVD payload. Handles CVSS v3.1, v3.0 and v2, plus CWE."""
    results = []
    if not data:
        return results

    for item in data.get("vulnerabilities", []):
        cve = item.get("cve", {})
        cve_id = cve.get("id")

        description = ""
        descriptions = cve.get("descriptions", [])
        if descriptions:
            description = descriptions[0].get("value", "")

        cvss_score = None
        cvss_severity = None
        cvss_version = None
        metrics = cve.get("metrics", {})

        for key, version in (
            ("cvssMetricV40", "4.0"),
            ("cvssMetricV31", "3.1"),
            ("cvssMetricV30", "3.0"),
            ("cvssMetricV2", "2.0"),
        ):
            if key in metrics and metrics[key]:
                cvss = metrics[key][0].get("cvssData", {})
                cvss_score = cvss.get("baseScore")
                cvss_severity = cvss.get("baseSeverity")
                cvss_version = version
                break

        cwe = None
        weaknesses = cve.get("weaknesses", [])
        if weaknesses:
            descs = weaknesses[0].get("description", [])
            if descs:
                cwe = descs[0].get("value")

        results.append({
            "cve_id": cve_id,
            "description": description,
            "cvss_score": cvss_score,
            "cvss_severity": cvss_severity,
            "cvss_version": cvss_version,
            "cwe": cwe,
            "source_url": (
                f"https://nvd.nist.gov/vuln/detail/{cve_id}" if cve_id else None
            ),
            "applicability": "unverified_keyword_match",
            "applicability_note": (
                "Matched by keyword only. Affected product, component and "
                "version were not verified, so this does not establish that "
                "the APK is affected."
            ),
        })

    return results


def search_multiple_components(components, max_components=5):
    """Search several components. Never raises; always reports what happened."""
    searched = list(components)[:max_components]

    all_results = []
    per_component = []
    counts = {RECORDS_RETURNED: 0, ZERO_RECORDS: 0, LOOKUP_FAILED: 0}

    for i, component in enumerate(searched):
        if i > 0:
            time.sleep(DELAY_SECONDS)

        data, status, error = search_cve(component)
        counts[status] = counts.get(status, 0) + 1

        records = extract_cve_information(data) if status == RECORDS_RETURNED else []
        for record in records:
            record["searched_component"] = component

        per_component.append({
            "component": component,
            "status": status,
            "error": error,
            "records": len(records),
        })
        all_results.extend(records)

    return {
        "results": all_results,
        "per_component": per_component,
        "components_searched": len(searched),
        "components_available": len(list(components)),
        "status_counts": counts,
        "api_key_configured": API_KEY is not None,
        "rate_limit": (
            "50 requests / 30s (key configured)" if API_KEY
            else "5 requests / 30s (no NVD_API_KEY set)"
        ),
        "interpretation": (
            "Zero records returned means no keyword match was found. It does "
            "NOT mean the APK has no vulnerabilities. A failed lookup means "
            "the question was never answered."
        ),
    }


if __name__ == "__main__":
    print("MOSAIC-ML NVD client")
    print("=" * 46)
    print("API key configured:", API_KEY is not None)
    print("delay between requests:", DELAY_SECONDS, "s")

    report = search_multiple_components(["Android WebView", "Android Bionic"])
    print("\nstatus counts:", report["status_counts"])
    for entry in report["per_component"]:
        print(f"  {entry['component']:<24} {entry['status']:<18} "
              f"records={entry['records']} {entry['error'] or ''}")
    for record in report["results"][:3]:
        print(f"\n  {record['cve_id']} | CVSS {record['cvss_score']} "
              f"({record['cvss_version']}) | {record['applicability']}")
