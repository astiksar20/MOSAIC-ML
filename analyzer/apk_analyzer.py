"""
MOSAIC-ML - Static APK analysis.

Extracts the three feature families the MH-100K vocabulary is built from:

    Permission::  166 entries
    Intent::      250 entries
    APICall::   24,417 entries

The previous version extracted permissions and manifest components only.
Components (activities, services, receivers, providers) do NOT appear in the
MH-100K vocabulary at all, so they contributed nothing to the feature vector -
that left 24,667 of 24,833 features (99.33%) unreachable.

APKs are never executed. All analysis is static.
"""

import logging
import re

# androguard logs every AXML/DEX parsing step at DEBUG. One APK produces
# thousands of lines, which floods API logs and hides real errors.
# Set MOSAIC_ANDROGUARD_DEBUG=1 to restore it when debugging extraction.
import os as _os

if not _os.environ.get("MOSAIC_ANDROGUARD_DEBUG"):
    logging.getLogger("androguard").setLevel(logging.ERROR)
    try:
        from loguru import logger as _loguru_logger

        _loguru_logger.remove()
        _loguru_logger.add(lambda _m: None, level="ERROR")
    except Exception:
        pass

from androguard.core.apk import APK

try:
    from androguard.misc import AnalyzeAPK
    _DEX_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DEX_AVAILABLE = False


# Matches android.intent.action.X and android.intent.category.X in the manifest.
_INTENT_RE = re.compile(
    r'android:name="android\.intent\.(?:action|category)\.([A-Z_0-9]+)"'
)


def _extract_intents(apk):
    """Intent actions and categories declared in the manifest."""
    try:
        xml = apk.get_android_manifest_axml().get_xml()
        text = xml.decode("utf-8", errors="replace")
        return sorted(set(_INTENT_RE.findall(text)))
    except Exception:
        return []


def _extract_api_calls(apk_path, dex_timeout_note=None):
    """Framework methods the APK calls, in MH-100K's naming form.

    androguard gives a class name like 'Landroid/app/Activity;' and a method
    name like 'onCreate'. MH-100K writes that as:

        Landroid/app/Activity.onCreate()

    Returns (api_calls, error). On failure the error is returned rather than
    raised, so a DEX problem degrades the analysis instead of failing the scan.
    """
    if not _DEX_AVAILABLE:
        return [], "androguard.misc.AnalyzeAPK unavailable"

    try:
        _, _, dx = AnalyzeAPK(apk_path)
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"

    calls = set()
    for method in dx.get_external_methods():
        try:
            class_name = method.get_class_name().rstrip(";")
            calls.add(f"{class_name}.{method.name}()")
        except Exception:
            continue
    return sorted(calls), None


def analyze_apk(apk_path, include_api_calls=True):
    """Static analysis of one APK.

    include_api_calls=False skips DEX analysis. That is much faster but leaves
    24,417 of the 24,833 model features unpopulated, so the ML prediction
    should not be trusted when it is disabled.
    """
    apk = APK(apk_path)

    api_calls, api_error = ([], "disabled by caller")
    if include_api_calls:
        api_calls, api_error = _extract_api_calls(apk_path)

    return {
        "package_name": apk.get_package(),
        "permissions": apk.get_permissions(),
        "activities": apk.get_activities(),
        "services": apk.get_services(),
        "receivers": apk.get_receivers(),
        "providers": apk.get_providers(),

        # Feature families used by the model.
        "intents": _extract_intents(apk),
        "api_calls": api_calls,

        # Non-fatal problems, surfaced rather than hidden.
        "extraction_errors": (
            {"api_calls": api_error} if api_error else {}
        ),
    }


def get_cve_search_components(apk_info):
    """Candidate strings for a CVE keyword search.

    NOTE: permissions and component class names are not software products, so a
    keyword hit on them does not establish that the APK is affected by a CVE.
    Treat every result as an unverified candidate match.
    """
    components = []

    components.extend(apk_info.get("permissions", []))
    components.extend(apk_info.get("activities", []))
    components.extend(apk_info.get("services", []))
    components.extend(apk_info.get("receivers", []))
    components.extend(apk_info.get("providers", []))

    # Remove duplicates
    components = list(set(components))

    return components


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else (
        "test_apks/com.github.yeriomin.smsscheduler_5.apk"
    )
    info = analyze_apk(path)

    print("MOSAIC-ML APK Analyzer")
    print("=" * 46)
    print("package    :", info["package_name"])
    print("permissions:", len(info["permissions"]))
    print("intents    :", len(info["intents"]))
    print("api calls  :", len(info["api_calls"]))
    print("activities :", len(info["activities"]))
    if info["extraction_errors"]:
        print("errors     :", info["extraction_errors"])
