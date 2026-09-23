from androguard.core.apk import APK


def analyze_apk(apk_path):
    apk = APK(apk_path)

    return {
        "package_name": apk.get_package(),
        "permissions": apk.get_permissions(),
        "activities": apk.get_activities(),
        "services": apk.get_services(),
        "receivers": apk.get_receivers(),
        "providers": apk.get_providers(),
    }


if __name__ == "__main__":
    print("MOSAIC-ML APK Analyzer")
    print("Analyzer module loaded successfully.")