import numpy as np
from scipy import sparse


FEATURE_FILE = "data/mh100k/mh100-features-all.csv"


def load_feature_dictionary():

    feature_data = np.genfromtxt(
        FEATURE_FILE,
        delimiter=",",
        dtype=str,
        skip_header=1
    )

    feature_names = feature_data[:, 1]

    return feature_names


def extract_apk_features(apk_info):

    features = set()

    # Android permissions
    for permission in apk_info.get("permissions", []):

        # Convert:
        # android.permission.WAKE_LOCK
        #
        # into:
        # Permission::WAKE_LOCK

        if permission.startswith("android.permission."):

            permission_name = permission.replace(
                "android.permission.",
                "",
                1
            )

            features.add(
                "Permission::" + permission_name
            )

    # Activities
    for activity in apk_info.get("activities", []):

        features.add(
            "Activity::" + activity
        )

    # Services
    for service in apk_info.get("services", []):

        features.add(
            "Service::" + service
        )

    # Receivers
    for receiver in apk_info.get("receivers", []):

        features.add(
            "Receiver::" + receiver
        )

    # Providers
    for provider in apk_info.get("providers", []):

        features.add(
            "Provider::" + provider
        )

    return features


def create_feature_vector(apk_info):

    feature_names = load_feature_dictionary()

    apk_features = extract_apk_features(
        apk_info
    )

    feature_index = {
        feature: index
        for index, feature in enumerate(feature_names)
    }

    vector = np.zeros(
        len(feature_names),
        dtype=np.int8
    )

    matched_features = []

    for feature in apk_features:

        if feature in feature_index:

            index = feature_index[feature]

            vector[index] = 1

            matched_features.append(feature)

    return (
        sparse.csr_matrix(vector),
        matched_features
    )


if __name__ == "__main__":

    print("MOSAIC-ML Feature Mapper")

    features = load_feature_dictionary()

    print(
        "Total MH-100K features:",
        len(features)
    )