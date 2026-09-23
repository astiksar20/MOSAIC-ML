from androguard.core.apk import APK


def analyze_apk(apk_path):
    apk = APK(apk_path)

    result = {
        "package_name": apk.get_package(),
        "permissions": apk.get_permissions(),
        "activities": apk.get_activities(),
        "services": apk.get_services(),
        "receivers": apk.get_receivers(),
        "providers": apk.get_providers(),
    }

    return result


def get_cve_search_components(apk_info):
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
    print("MOSAIC-ML APK Analyzer ready")