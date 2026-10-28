"""
MOSAIC-ML - Map an analysed APK onto the MH-100K feature vocabulary.

The vocabulary has 24,833 entries in three blocks:

    Permission::WAKE_LOCK                           (166)
    Intent::AUDIO_BECOMING_NOISY                    (250)
    APICall::Landroid/content/Intent.toUri()     (24,417)

What changed and why
--------------------
The previous mapper emitted Permission::, Activity::, Service::, Receiver::
and Provider:: features. Only Permission:: exists in the vocabulary - the four
component prefixes appear nowhere in it, so 13 of every 18 strings it produced
were dead on arrival. It emitted no Intent:: and no APICall:: features at all,
leaving 24,667 of 24,833 features (99.33%) unreachable by construction.

Measured on test_apks/com.github.yeriomin.smsscheduler_5.apk:

    old mapper:  5 features matched (0.020%)   P(malware) = 0.1333
    new mapper: 97 features matched (0.391%)   P(malware) = 0.0667
    empty vector:                              P(malware) = 0.1250

The old result was indistinguishable from feeding the model nothing.

Feature ordering
----------------
The vector's column order comes from the order of names in the feature file.
Note that the 'index' column in mh100-features-all.csv starts at 5, not 0 - it
indexes the original dataframe, which carried 5 leading metadata columns. It is
NOT a matrix column position. This module uses row order and ignores that
column; do not use it as an index.
"""

import csv
import os
from pathlib import Path

import numpy as np
from scipy import sparse


# Anchored to this file, not the working directory. A relative path breaks the
# moment the process starts from anywhere other than the repository root -
# which is exactly what happens in a container or under a process manager.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

FEATURE_FILE = str(PROJECT_ROOT / "data" / "mh100k" / "mh100-features-all.csv")
EXPECTED_FEATURE_COUNT = 24833

# Below this, the model is being asked to judge an input unlike anything it was
# trained on (training apps carry a median of 1,993 active features). The scan
# still returns a prediction, but flagged as unreliable.
LOW_COVERAGE_FEATURES = 50

_CACHE = {}


def load_feature_dictionary(feature_file=FEATURE_FILE):
    """Load the vocabulary in matrix column order. Cached after first read."""
    if feature_file in _CACHE:
        return _CACHE[feature_file]

    if not os.path.exists(feature_file):
        raise FileNotFoundError(
            f"feature vocabulary not found at {feature_file}. "
            "The mapper cannot build a vector without it."
        )

    names = []
    with open(feature_file, "r", encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"{feature_file} is empty")
        for row in reader:
            if len(row) >= 2:
                names.append(row[1].strip())

    if len(names) != EXPECTED_FEATURE_COUNT:
        raise ValueError(
            f"{feature_file} holds {len(names)} feature names, expected "
            f"{EXPECTED_FEATURE_COUNT}. The vector would not line up with the "
            "trained model."
        )

    _CACHE[feature_file] = names
    return names


def extract_apk_features(apk_info):
    """Turn analyser output into candidate vocabulary strings.

    Only the three prefixes that exist in the vocabulary are produced.
    Components are deliberately not emitted - the vocabulary has no entries
    for them, so they could only ever miss.
    """
    features = set()

    # Permissions: android.permission.WAKE_LOCK -> Permission::WAKE_LOCK
    for permission in apk_info.get("permissions", []):
        if permission.startswith("android.permission."):
            features.add(
                "Permission::" + permission.replace("android.permission.", "", 1)
            )

    # Intents: already bare constant names from the analyser.
    for intent in apk_info.get("intents", []):
        features.add("Intent::" + intent)

    # API calls: already in Landroid/pkg/Class.method() form.
    for call in apk_info.get("api_calls", []):
        features.add("APICall::" + call)

    return features


def compute_coverage(apk_info, feature_file=FEATURE_FILE):
    """Per-block coverage report. Always returned with a scan."""
    names = load_feature_dictionary(feature_file)
    vocab = set(names)
    candidates = extract_apk_features(apk_info)
    matched = candidates & vocab

    blocks = {}
    for label, prefix in (
        ("permissions", "Permission::"),
        ("intents", "Intent::"),
        ("api_calls", "APICall::"),
    ):
        in_vocab = sum(1 for n in names if n.startswith(prefix))
        blocks[label] = {
            "extracted": sum(1 for c in candidates if c.startswith(prefix)),
            "matched": sum(1 for c in matched if c.startswith(prefix)),
            "vocabulary_size": in_vocab,
        }

    total = len(names)
    n_matched = len(matched)
    reliable = n_matched >= LOW_COVERAGE_FEATURES

    return {
        "matched_features": n_matched,
        "total_features": total,
        "coverage_percent": round(100.0 * n_matched / total, 4),
        "candidates_generated": len(candidates),
        "candidates_not_in_vocabulary": len(candidates - vocab),
        "by_block": blocks,
        "reliable": reliable,
        "threshold": LOW_COVERAGE_FEATURES,
        "warning": None if reliable else (
            f"Only {n_matched} of {total} model features could be populated. "
            f"Training apps carry a median of 1,993. The classifier is being "
            f"asked about an input unlike its training data, so this "
            f"prediction should not be treated as reliable evidence."
        ),
        "extraction_errors": apk_info.get("extraction_errors", {}),
    }


def create_feature_vector(apk_info, feature_file=FEATURE_FILE):
    """Build the sparse feature vector.

    Returns (vector, matched_features) - the same shape the API already
    expects, so existing callers keep working. Use compute_coverage() for the
    full report.
    """
    names = load_feature_dictionary(feature_file)
    index = {name: i for i, name in enumerate(names)}

    candidates = extract_apk_features(apk_info)

    matched = []
    columns = []
    for feature in candidates:
        position = index.get(feature)
        if position is not None:
            matched.append(feature)
            columns.append(position)

    columns = np.asarray(sorted(set(columns)), dtype=np.int64)
    vector = sparse.csr_matrix(
        (
            np.ones(len(columns), dtype=np.int8),
            (np.zeros(len(columns), dtype=np.int64), columns),
        ),
        shape=(1, len(names)),
        dtype=np.int8,
    )

    return vector, sorted(matched)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from analyzer.apk_analyzer import analyze_apk

    path = sys.argv[1] if len(sys.argv) > 1 else (
        "test_apks/com.github.yeriomin.smsscheduler_5.apk"
    )

    print("MOSAIC-ML Feature Mapper")
    print("=" * 52)
    print("vocabulary size:", len(load_feature_dictionary()))

    info = analyze_apk(path)
    vector, matched = create_feature_vector(info)
    cov = compute_coverage(info)

    print("\npackage:", info["package_name"])
    print(f"matched {cov['matched_features']} of {cov['total_features']} "
          f"({cov['coverage_percent']}%)")
    for name, stats in cov["by_block"].items():
        print(f"  {name:12s} {stats['matched']:5d} matched "
              f"of {stats['extracted']:5d} extracted "
              f"(vocabulary holds {stats['vocabulary_size']})")
    print("\nreliable:", cov["reliable"])
    if cov["warning"]:
        print("WARNING:", cov["warning"])
