"""
MOSAIC-ML - Permission-based risk scoring.

Adapted from:
    Ogwara, N. O., Petrova, K., Yang, M. L., & MacDonell, S. G. (2024).
    A Risk Assessment Framework for Mobile Apps in Mobile Cloud Computing
    Environments. Future Internet, 16(8), 271.
    https://doi.org/10.3390/fi16080271

This is an ADAPTATION evaluated on MH-100K. It is not a universal standard, and
the cited paper did not validate this implementation or this dataset.

Method
------
For each selected dangerous permission P_i, using TRAINING DATA ONLY:

    alpha_i = (malicious training apps requesting P_i) / (all malicious training apps)
    beta_i  = (benign    training apps requesting P_i) / (all benign    training apps)
    r_i     = sqrt(alpha_i * (1 - beta_i))

For an APK a:

    lambda(a,i) = 1 if a requests P_i else 0
    k(a)        = sum_i lambda(a,i)
    R_perm(a)   = ( sum_i lambda(a,i) * r_i ) / k(a)        for k(a) > 0

R_perm(a) lies in [0, 1] because every r_i lies in [0, 1] and the result is a
mean over the requested permissions.

If k(a) == 0 the score is UNDEFINED. This module returns None with the status
"insufficient_permission_evidence". It never returns 0.0 in that case, because
"no evidence" and "no risk" are different statements.

Leakage policy
--------------
alpha, beta and r are fitted on the training split only. They are never computed
from validation data, test data, or from the APK under analysis. Weights are
persisted with the split seed and dataset fingerprint so a scored APK can always
be traced to the exact weights used.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

SCHEMA_VERSION = "permission-risk/1.0"

# The 15 dangerous permissions used by Ogwara et al. (2024), Table 1 (P1-P15).
# All 15 are present in the MH-100K 166-permission block (verified).
PERMISSION_SET_OGWARA15 = (
    "WRITE_EXTERNAL_STORAGE",
    "READ_PHONE_STATE",
    "ACCESS_COARSE_LOCATION",
    "ACCESS_FINE_LOCATION",
    "GET_TASKS",
    "READ_EXTERNAL_STORAGE",
    "SYSTEM_ALERT_WINDOW",
    "READ_LOGS",
    "MOUNT_UNMOUNT_FILESYSTEMS",
    "CAMERA",
    "RECORD_AUDIO",
    "GET_ACCOUNTS",
    "CALL_PHONE",
    "WRITE_SETTINGS",
    "SEND_SMS",
)

INSUFFICIENT = "insufficient_permission_evidence"
OK = "ok"


def canonical_permission(name: str) -> str:
    """Reduce a permission string to its bare constant name.

    'android.permission.SEND_SMS' -> 'SEND_SMS'
    'Permission::SEND_SMS'        -> 'SEND_SMS'
    'SEND_SMS'                    -> 'SEND_SMS'

    Vendor-prefixed permissions (com.google.*, etc.) keep only the final
    segment, which is why the selected set must be matched explicitly rather
    than by substring.
    """
    n = str(name).strip()
    if "::" in n:
        n = n.split("::", 1)[1]
    if "." in n:
        n = n.rsplit(".", 1)[1]
    return n.upper()


@dataclass(frozen=True)
class PermissionWeight:
    permission: str
    alpha: float            # prevalence among malicious training apps
    beta: float             # prevalence among benign training apps
    r: float                # sqrt(alpha * (1 - beta))
    n_malicious_using: int
    n_benign_using: int


def fit_permission_weights(
    X_train,
    y_train: np.ndarray,
    vocabulary: Sequence[str],
    permission_set: Sequence[str] = PERMISSION_SET_OGWARA15,
    malicious_label: int = 1,
) -> list[PermissionWeight]:
    """Fit alpha, beta and r on the TRAINING SPLIT ONLY.

    X_train must be a binary (presence/absence) sparse or dense matrix whose
    columns correspond positionally to `vocabulary`.
    """
    if X_train.shape[0] != len(y_train):
        raise ValueError(
            f"row mismatch: X_train has {X_train.shape[0]} rows, y_train has {len(y_train)}"
        )
    if X_train.shape[1] != len(vocabulary):
        raise ValueError(
            f"column mismatch: X_train has {X_train.shape[1]} columns, "
            f"vocabulary has {len(vocabulary)} entries"
        )

    index = {}
    for j, name in enumerate(vocabulary):
        s = str(name)
        if s.startswith("Permission::"):
            index[canonical_permission(s)] = j

    y_train = np.asarray(y_train).ravel()
    mal = y_train == malicious_label
    ben = ~mal
    n_mal, n_ben = int(mal.sum()), int(ben.sum())
    if n_mal == 0 or n_ben == 0:
        raise ValueError(
            f"training split must contain both classes (malicious={n_mal}, benign={n_ben})"
        )

    # Binarise defensively: the formula is defined on presence/absence.
    import scipy.sparse as sp

    Xb = X_train.tocsr(copy=True) if sp.issparse(X_train) else sp.csr_matrix(X_train)
    Xb.data = np.ones_like(Xb.data)

    weights: list[PermissionWeight] = []
    missing: list[str] = []
    for perm in permission_set:
        key = canonical_permission(perm)
        j = index.get(key)
        if j is None:
            missing.append(perm)
            continue
        col = Xb[:, j]
        a_cnt = int(col[mal].sum())
        b_cnt = int(col[ben].sum())
        alpha = a_cnt / n_mal
        beta = b_cnt / n_ben
        r = math.sqrt(alpha * (1.0 - beta))
        weights.append(
            PermissionWeight(key, alpha, beta, r, a_cnt, b_cnt)
        )

    if missing:
        raise KeyError(
            "permissions absent from the vocabulary: "
            + ", ".join(missing)
            + ". Define the selected set against the dataset vocabulary."
        )
    return weights


def compute_permission_score(
    requested_permissions: Iterable[str],
    weights: Sequence[PermissionWeight],
) -> dict:
    """Compute R_perm(a) for one APK.

    Returns a dict that always reports its own evidence basis. When the APK
    requests none of the selected permissions, `score` is None and `status` is
    "insufficient_permission_evidence" - never 0.0.
    """
    by_name = {w.permission: w for w in weights}
    requested = {canonical_permission(p) for p in requested_permissions}

    matched = sorted(requested & set(by_name))
    k = len(matched)

    if k == 0:
        return {
            "score": None,
            "score_0_100": None,
            "status": INSUFFICIENT,
            "k": 0,
            "selected_set_size": len(by_name),
            "matched_permissions": [],
            "contributions": [],
            "explanation": (
                "The APK requests none of the selected dangerous permissions. "
                "A permission-risk score is undefined here. This is an absence "
                "of evidence, not evidence of low risk."
            ),
        }

    contributions = [
        {"permission": p, "r": by_name[p].r, "alpha": by_name[p].alpha, "beta": by_name[p].beta}
        for p in matched
    ]
    total = sum(c["r"] for c in contributions)
    score = total / k

    # Guard against a weight table that has been tampered with.
    if not (0.0 - 1e-9 <= score <= 1.0 + 1e-9):
        raise ValueError(f"score {score} outside [0,1]; weight table is invalid")
    score = min(1.0, max(0.0, score))

    return {
        "score": score,
        "score_0_100": round(score * 100, 2),
        "status": OK,
        "k": k,
        "selected_set_size": len(by_name),
        "matched_permissions": matched,
        "contributions": sorted(contributions, key=lambda c: -c["r"]),
        "explanation": (
            f"Mean risk weight of the {k} selected dangerous permission(s) this APK "
            f"requests, out of {len(by_name)} in the set. The 0-100 form is a display "
            f"rescaling, not a probability of malware."
        ),
    }


def save_weights(path: str | Path, weights: Sequence[PermissionWeight], metadata: dict) -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "Ogwara et al. 2024, Future Internet 16(8) 271 - adapted to MH-100K",
        "formula": "r_i = sqrt(alpha_i * (1 - beta_i)); R(a) = sum(lambda*r)/k, k>0",
        "fitted_on": "TRAINING SPLIT ONLY",
        "metadata": metadata,
        "weights": [asdict(w) for w in weights],
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_weights(path: str | Path) -> tuple[list[PermissionWeight], dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"weight file schema {payload.get('schema_version')!r} != expected {SCHEMA_VERSION!r}"
        )
    weights = [PermissionWeight(**w) for w in payload["weights"]]
    return weights, payload.get("metadata", {})


def score_matrix(X, vocabulary: Sequence[str], weights: Sequence[PermissionWeight]):
    """Vectorised scoring for evaluation. Returns (scores, k) with NaN where k == 0."""
    import scipy.sparse as sp

    index = {}
    for j, name in enumerate(vocabulary):
        s = str(name)
        if s.startswith("Permission::"):
            index[canonical_permission(s)] = j

    cols, rvals = [], []
    for w in weights:
        j = index.get(w.permission)
        if j is None:
            raise KeyError(f"{w.permission} absent from vocabulary")
        cols.append(j)
        rvals.append(w.r)

    Xb = X.tocsr(copy=True) if sp.issparse(X) else sp.csr_matrix(X)
    Xb.data = np.ones_like(Xb.data)
    sub = Xb[:, cols]

    k = np.asarray(sub.sum(axis=1)).ravel()
    weighted = np.asarray(sub.dot(np.array(rvals))).ravel()

    scores = np.full(k.shape, np.nan, dtype=float)
    nz = k > 0
    scores[nz] = weighted[nz] / k[nz]
    return scores, k.astype(int)
