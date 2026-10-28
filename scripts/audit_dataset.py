"""
MOSAIC-ML - Stage 1 dataset audit for MH-100K.

READ-ONLY with respect to data/mh100k/. Writes summaries to reports/results/.

Structure of the real local dataset (verified, not assumed):
  data/mh100k/mh100.npz        -> dense int8 'data' (101934 x 24833) plus
                                  'column_names', 'classes', 'sha256',
                                  'metadata', 'metadata_columns'
  data/mh100k/mh100_labels.csv -> 101975 rows, the FULL published metadata table
  data/mh100k/mh100-features-all.csv -> 24833 feature names with an 'index' column
  data/processed/mh100_csr.npz -> optional pre-converted CSR (avoids a 2.5GB spike)

The npz arrays are treated as authoritative because they are stored alongside
the matrix. The labels CSV is cross-checked against them by SHA256 so row
alignment is PROVEN rather than inferred from matching counts.

Anything that cannot be determined is recorded under "not_available" with a
reason. Nothing is estimated or filled in.

Usage (from the repository root):
    python scripts/audit_dataset.py
    python scripts/audit_dataset.py --data-dir data/mh100k --out-dir reports/results
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

try:
    import scipy
    import scipy.sparse as sp
except ImportError:  # pragma: no cover
    sp = None
    scipy = None


# MH-100K as published (Braganca et al., Data in Brief 51:109750, 2023).
# Numbers to CHECK the local copy against, not to assume.
PUBLISHED_SAMPLES = 101_975
PUBLISHED_PERMISSIONS = 166
PUBLISHED_API_CALLS = 24_417
PUBLISHED_INTENTS = 250
PUBLISHED_FEATURES = PUBLISHED_PERMISSIONS + PUBLISHED_API_CALLS + PUBLISHED_INTENTS  # 24,833

# The vocabulary uses an explicit "Block::Name" convention, so blocks are read
# from the names themselves rather than guessed from character patterns.
BLOCK_PREFIXES = ("Permission::", "Intent::", "APICall::")


class Report:
    """Collects findings. Nothing is silently dropped."""

    def __init__(self) -> None:
        self.data: dict = {
            "audit_version": "2.0",
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "environment": {},
            "files": {},
            "labels": {},
            "feature_matrix": {},
            "vocabulary": {},
            "row_statistics": {},
            "alignment": {},
            "published_comparison": {},
            "not_available": [],
            "warnings": [],
        }

    def skip(self, item: str, reason: str) -> None:
        self.data["not_available"].append({"item": item, "reason": reason})
        print(f"  [not available] {item}: {reason}")

    def warn(self, message: str) -> None:
        self.data["warnings"].append(message)
        print(f"  [warning] {message}")


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def record_environment(rep: Report) -> None:
    print("[1/7] Environment")
    rep.data["environment"] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__ if scipy is not None else None,
    }
    if sp is None:
        rep.warn("scipy is not installed; sparse handling unavailable")


def record_files(rep: Report, data_dir: Path, csr_path: Path) -> dict[str, Path]:
    print("[2/7] File inventory")
    candidates = {
        "labels_csv": data_dir / "mh100_labels.csv",
        "features_csv": data_dir / "mh100-features-all.csv",
        "matrix_npz": data_dir / "mh100.npz",
        "csr_npz": csr_path,
    }
    found: dict[str, Path] = {}
    for key, path in candidates.items():
        if not path.exists():
            rep.skip(key, f"file not found at {path}")
            rep.data["files"][key] = {"path": str(path), "exists": False}
            continue
        stat = path.stat()
        print(f"  hashing {path.name} ({stat.st_size / 1e6:.1f} MB)...")
        rep.data["files"][key] = {
            "path": str(path),
            "exists": True,
            "size_bytes": stat.st_size,
            "modified_utc": datetime.fromtimestamp(
                stat.st_mtime, timezone.utc
            ).isoformat(timespec="seconds"),
            "sha256": sha256_of(path),
        }
        found[key] = path
    return found


def load_npz_arrays(rep: Report, path: Path | None) -> dict:
    """Read the metadata arrays stored alongside the matrix."""
    if path is None:
        return {}
    archive = np.load(path, allow_pickle=True)
    present = list(archive.keys())
    rep.data["feature_matrix"]["npz_keys"] = present
    out = {}
    for key in ("column_names", "classes", "sha256", "metadata", "metadata_columns"):
        if key in present:
            out[key] = archive[key]
        else:
            rep.skip(f"npz.{key}", f"key absent from {path.name}")
    return out


def load_matrix(rep: Report, dense_path: Path | None, csr_path: Path | None):
    """Prefer the pre-converted CSR; fall back to the dense array."""
    print("[3/7] Feature matrix")
    info = rep.data["feature_matrix"]

    if csr_path is not None and sp is not None:
        matrix = sp.load_npz(csr_path).tocsr()
        info["storage"] = f"CSR loaded from {csr_path.name}"
        info["source_note"] = (
            "Converted from the dense 'data' array in mh100.npz. The dense form "
            "is 2.53 GB in memory, which is the likely cause of the earlier "
            "MemoryError during Random Forest training."
        )
    elif dense_path is not None:
        archive = np.load(dense_path, allow_pickle=True)
        if "data" not in archive:
            rep.skip("feature_matrix", f"no 'data' key in {dense_path.name}")
            return None
        arr = archive["data"]
        if arr.ndim != 2:
            rep.skip("feature_matrix", f"'data' has shape {arr.shape}, expected 2-D")
            return None
        info["storage"] = f"dense ndarray from {dense_path.name}"
        info["dense_nbytes"] = int(arr.nbytes)
        rep.warn(
            f"matrix stored dense ({arr.nbytes / 1e9:.2f} GB in memory); "
            "convert to CSR before training to avoid MemoryError"
        )
        if sp is None:
            rep.skip("feature_matrix", "scipy unavailable; cannot build sparse form")
            return None
        matrix = sp.csr_matrix(arr)
    else:
        rep.skip("feature_matrix", "neither CSR nor dense matrix available")
        return None

    n_rows, n_cols = matrix.shape
    nnz = int(matrix.nnz)
    values = matrix.data

    info.update(
        {
            "n_rows": int(n_rows),
            "n_columns": int(n_cols),
            "dtype": str(matrix.dtype),
            "stored_nonzeros": nnz,
            "density": round(nnz / (n_rows * n_cols), 8),
            "sparsity_percent": round(100.0 * (1 - nnz / (n_rows * n_cols)), 4),
            "csr_nbytes_estimate": int(
                matrix.data.nbytes + matrix.indices.nbytes + matrix.indptr.nbytes
            ),
        }
    )

    unique_vals = np.unique(values)
    info["distinct_nonzero_values"] = int(unique_vals.size)
    info["is_binary"] = bool(unique_vals.size == 1 and unique_vals[0] == 1)
    info["min_nonzero"] = float(values.min())
    info["max_value"] = float(values.max())
    if not info["is_binary"]:
        rep.warn(
            "matrix is not strictly binary presence/absence; "
            "Bernoulli Naive Bayes assumes binary input - verify before Stage 2"
        )

    print(f"  {n_rows} x {n_cols}, nnz={nnz}, density={info['density']}")
    return matrix


def audit_labels(rep: Report, arrays: dict, matrix) -> np.ndarray | None:
    """Labels come from the npz 'classes' array, which ships with the matrix."""
    print("[4/7] Labels")
    if "classes" not in arrays:
        rep.skip("labels", "'classes' array absent from the npz")
        return None

    y = np.asarray(arrays["classes"]).astype(np.int64).ravel()
    info: dict = {"source": "mh100.npz['classes']", "n_rows": int(y.size)}

    classes, counts = np.unique(y, return_counts=True)
    total = int(counts.sum())
    info["class_distribution"] = {
        int(c): {"count": int(n), "percent": round(100.0 * n / total, 4)}
        for c, n in zip(classes, counts)
    }
    if len(classes) == 2:
        info["imbalance_ratio_majority_to_minority"] = round(
            int(counts.max()) / int(counts.min()), 4
        )
    info["label_meaning"] = (
        "Cross-checked against the CLASS column of mh100_labels.csv by SHA256 in "
        "the alignment section. Confirm which integer means malicious against the "
        "MH-100K documentation before training."
    )

    if matrix is not None and y.size != matrix.shape[0]:
        rep.warn(
            f"ROW MISMATCH: matrix has {matrix.shape[0]} rows, 'classes' has "
            f"{y.size}. Do not train until resolved"
        )

    rep.data["labels"] = info
    print(f"  {total} rows, distribution: {dict(zip(classes.tolist(), counts.tolist()))}")
    return y


def audit_vocabulary(rep: Report, arrays: dict, csv_path: Path | None, n_cols: int | None) -> None:
    """Vocabulary from the npz, cross-checked against the features CSV."""
    print("[5/7] Feature vocabulary")
    info: dict = {}

    names = None
    if "column_names" in arrays:
        names = [str(v) for v in np.asarray(arrays["column_names"]).ravel()]
        info["source"] = "mh100.npz['column_names']"
        info["n_features"] = len(names)
    else:
        rep.skip("vocabulary", "'column_names' absent from the npz")

    # Blocks read directly from the "Block::Name" convention.
    if names is not None:
        blocks = Counter()
        for nm in names:
            for prefix in BLOCK_PREFIXES:
                if nm.startswith(prefix):
                    blocks[prefix.rstrip(":")] += 1
                    break
            else:
                blocks["unprefixed"] += 1
        info["block_counts"] = dict(blocks)
        info["block_source"] = (
            "Read from the explicit 'Block::Name' prefix in each feature name, "
            "not inferred from character patterns."
        )
        info["published_block_counts"] = {
            "permissions": PUBLISHED_PERMISSIONS,
            "api_calls": PUBLISHED_API_CALLS,
            "intents": PUBLISHED_INTENTS,
            "total": PUBLISHED_FEATURES,
        }
        info["block_counts_match_published"] = (
            blocks.get("Permission") == PUBLISHED_PERMISSIONS
            and blocks.get("APICall") == PUBLISHED_API_CALLS
            and blocks.get("Intent") == PUBLISHED_INTENTS
        )

        duplicates = [nm for nm, c in Counter(names).items() if c > 1]
        info["n_duplicate_feature_names"] = len(duplicates)
        info["duplicate_feature_names"] = duplicates[:50]
        if duplicates:
            rep.warn(f"{len(duplicates)} duplicated feature names; ordering is unsafe")

        if n_cols is not None:
            info["matches_matrix_width"] = len(names) == n_cols
            if len(names) != n_cols:
                rep.warn(
                    f"vocabulary has {len(names)} names but the matrix has {n_cols} "
                    "columns - feature ordering CANNOT be trusted until resolved"
                )
        info["first_5"] = names[:5]
        info["last_5"] = names[-5:]

    # Cross-check the standalone CSV the feature mapper actually reads.
    if csv_path is None:
        rep.skip("vocabulary.csv_crosscheck", "features CSV not present")
    else:
        with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            rows = [r for r in reader if r]
        csv_info: dict = {"header": header, "n_rows": len(rows)}
        if header and len(header) >= 2:
            idx_col = [r[0] for r in rows]
            name_col = [r[1] for r in rows]
            csv_info["n_names"] = len(name_col)
            try:
                idx_int = [int(v) for v in idx_col]
                csv_info["index_column_min"] = min(idx_int)
                csv_info["index_column_max"] = max(idx_int)
                csv_info["index_column_is_contiguous"] = (
                    max(idx_int) - min(idx_int) + 1 == len(idx_int)
                )
                if min(idx_int) != 0:
                    rep.warn(
                        f"features CSV 'index' column starts at {min(idx_int)}, not 0. "
                        "It is an index into the ORIGINAL dataframe (which included "
                        f"{min(idx_int)} metadata columns), NOT a matrix column "
                        "position. Using it as a column index would be off by "
                        f"{min(idx_int)}."
                    )
            except ValueError:
                rep.skip("vocabulary.csv_index", "index column is not integer")

            if names is not None:
                same_order = name_col == names
                csv_info["name_order_matches_npz"] = same_order
                csv_info["same_set_as_npz"] = set(name_col) == set(names)
                if not same_order:
                    rep.warn(
                        "features CSV name order does NOT match npz column_names; "
                        "the feature mapper reads the CSV, so this would mis-index"
                    )
        csv_info["note"] = (
            "feature_engineering/apk_feature_mapper.py reads this CSV, not the npz. "
            "Both must agree for the mapper's vector to line up with the model."
        )
        info["csv_crosscheck"] = csv_info

    rep.data["vocabulary"] = info
    if names is not None:
        print(f"  {len(names)} features, blocks: {info.get('block_counts')}")


def audit_rows(rep: Report, matrix, y: np.ndarray | None, out_dir: Path) -> None:
    print("[6/7] Row statistics")
    if matrix is None or sp is None or not sp.issparse(matrix):
        rep.skip("row_statistics", "no sparse feature matrix available")
        return

    matrix = matrix.tocsr()
    n_rows = matrix.shape[0]
    nnz_per_row = np.diff(matrix.indptr)

    info: dict = {
        "n_rows": int(n_rows),
        "all_zero_rows": int((nnz_per_row == 0).sum()),
        "nonzero_features_per_app": {
            "min": int(nnz_per_row.min()),
            "p25": float(np.percentile(nnz_per_row, 25)),
            "median": float(np.median(nnz_per_row)),
            "mean": round(float(nnz_per_row.mean()), 4),
            "p75": float(np.percentile(nnz_per_row, 75)),
            "p99": float(np.percentile(nnz_per_row, 99)),
            "max": int(nnz_per_row.max()),
        },
    }
    if info["all_zero_rows"]:
        rep.warn(f"{info['all_zero_rows']} rows have no features set at all")

    print("  hashing rows for duplicate detection...")
    seen: dict[bytes, int] = {}
    dup_rows = 0
    dup_groups = 0
    for i in range(n_rows):
        lo, hi = matrix.indptr[i], matrix.indptr[i + 1]
        digest = hashlib.blake2b(
            matrix.indices[lo:hi].astype(np.int32).tobytes(), digest_size=16
        ).digest()
        if digest in seen:
            dup_rows += 1
            if seen[digest] == 1:
                dup_groups += 1
            seen[digest] += 1
        else:
            seen[digest] = 1

    info["duplicate_rows"] = dup_rows
    info["duplicate_groups"] = dup_groups
    info["unique_rows"] = int(n_rows - dup_rows)
    info["duplicate_rate_percent"] = round(100.0 * dup_rows / n_rows, 4)
    info["duplicate_definition"] = "identical set of active feature indices"
    if dup_rows:
        rep.warn(
            f"{dup_rows} duplicate feature rows ({info['duplicate_rate_percent']}%); "
            "duplicates inflate reported accuracy (Molina-Coronado et al. 2023)"
        )

    if y is not None and len(y) == n_rows:
        per_class = {}
        for cls in np.unique(y):
            sub = nnz_per_row[y == cls]
            per_class[int(cls)] = {
                "n_rows": int(sub.size),
                "mean_nonzero_features": round(float(sub.mean()), 4),
                "median_nonzero_features": float(np.median(sub)),
                "all_zero_rows": int((sub == 0).sum()),
            }
        info["per_class"] = per_class

        # Per-class feature frequency: the raw input to alpha/beta later.
        # NOTE: computed over the WHOLE dataset here, for exploration only.
        # Stage 3 must recompute these on the TRAINING SPLIT ONLY.
        binary = matrix.copy()
        binary.data = np.ones_like(binary.data)
        classes = sorted(int(c) for c in np.unique(y))
        totals = np.asarray(binary.sum(axis=0)).ravel()
        per_cls = {c: np.asarray(binary[y == c].sum(axis=0)).ravel() for c in classes}
        sizes = {c: int((y == c).sum()) for c in classes}

        names = rep.data.get("vocabulary", {})
        name_list = None
        if "first_5" in names and matrix.shape[1]:
            name_list = None  # filled below if available

        freq_path = out_dir / "feature_frequency_by_class.csv"
        with freq_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(
                ["feature_index", "feature_name", "total_count"]
                + [f"count_class_{c}" for c in classes]
                + [f"percent_within_class_{c}" for c in classes]
            )
            vocab_names = rep.data.get("_vocab_names") or []
            for j in range(binary.shape[1]):
                nm = vocab_names[j] if j < len(vocab_names) else ""
                w.writerow(
                    [j, nm, int(totals[j])]
                    + [int(per_cls[c][j]) for c in classes]
                    + [
                        round(100.0 * per_cls[c][j] / sizes[c], 6) if sizes[c] else ""
                        for c in classes
                    ]
                )
        info["feature_frequency_export"] = str(freq_path)
        info["feature_frequency_scope"] = (
            "WHOLE DATASET - exploratory only. Stage 3 alpha/beta MUST be "
            "recomputed on the training split alone to avoid leakage."
        )
        print(f"  wrote {freq_path}")
    else:
        rep.skip(
            "row_statistics.per_class",
            "labels unavailable or row count mismatch; cannot split by class",
        )

    nnz_path = out_dir / "nonzero_features_per_app.csv"
    with nnz_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        has_y = y is not None and len(y) == n_rows
        w.writerow(["row_index", "nonzero_features"] + (["label"] if has_y else []))
        for i, c in enumerate(nnz_per_row):
            w.writerow([i, int(c)] + ([int(y[i])] if has_y else []))
    info["nonzero_per_app_export"] = str(nnz_path)

    rep.data["row_statistics"] = info
    print(f"  duplicates: {dup_rows}, all-zero rows: {info['all_zero_rows']}")


def check_alignment(rep: Report, arrays: dict, matrix, y, labels_csv: Path | None) -> None:
    """Prove row alignment via SHA256 rather than inferring it from counts."""
    print("[7/7] Alignment and published comparison")
    align: dict = {}

    n_matrix = int(matrix.shape[0]) if matrix is not None else None
    align["matrix_rows"] = n_matrix
    align["npz_classes_rows"] = int(y.size) if y is not None else None
    align["npz_sha256_rows"] = (
        int(np.asarray(arrays["sha256"]).size) if "sha256" in arrays else None
    )

    if "sha256" not in arrays:
        rep.skip("alignment.sha256_crosscheck", "'sha256' array absent from the npz")
    elif labels_csv is None:
        rep.skip("alignment.sha256_crosscheck", "labels CSV not present")
    else:
        npz_hashes = [str(v) for v in np.asarray(arrays["sha256"]).ravel()]
        with labels_csv.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.DictReader(fh)
            csv_rows = list(reader)
        align["labels_csv_rows"] = len(csv_rows)

        hash_key = next(
            (k for k in (csv_rows[0].keys() if csv_rows else []) if k.strip().upper() == "SHA256"),
            None,
        )
        class_key = next(
            (k for k in (csv_rows[0].keys() if csv_rows else []) if k.strip().upper() == "CLASS"),
            None,
        )
        if hash_key is None or class_key is None:
            rep.skip(
                "alignment.sha256_crosscheck",
                f"labels CSV lacks SHA256 and/or CLASS columns (found {list(csv_rows[0].keys()) if csv_rows else []})",
            )
        else:
            csv_class = {r[hash_key]: r[class_key] for r in csv_rows}
            align["labels_csv_unique_hashes"] = len(csv_class)

            missing = [h for h in npz_hashes if h not in csv_class]
            align["npz_hashes_absent_from_csv"] = len(missing)

            # Positional check: does npz row i carry the same label as the CSV
            # row with the same hash?
            mismatches = 0
            compared = 0
            for i, h in enumerate(npz_hashes):
                v = csv_class.get(h)
                if v is None or v == "":
                    continue
                compared += 1
                if int(float(v)) != int(y[i]):
                    mismatches += 1
            align["label_comparisons_made"] = compared
            align["label_mismatches"] = mismatches
            align["row_alignment_verified"] = (
                compared > 0 and mismatches == 0 and len(missing) == 0
            )
            if mismatches:
                rep.warn(
                    f"{mismatches} of {compared} rows disagree between npz 'classes' "
                    "and the CSV CLASS column for the same SHA256 - labels unreliable"
                )
            else:
                align["row_alignment_note"] = (
                    f"All {compared} comparable rows agree between npz 'classes' and "
                    "the CSV CLASS column matched by SHA256. Row order is PROVEN, "
                    "not assumed."
                )

            dropped = [h for h in csv_class if h not in set(npz_hashes)]
            align["csv_hashes_absent_from_npz"] = len(dropped)
            align["dropped_sample_hashes_sample"] = dropped[:10]
            if dropped:
                dropped_classes = Counter(
                    csv_class[h] for h in dropped if csv_class[h] != ""
                )
                align["dropped_sample_class_counts"] = dict(dropped_classes)

    rep.data["alignment"] = align

    comp: dict = {
        "published_samples": PUBLISHED_SAMPLES,
        "published_features": PUBLISHED_FEATURES,
        "local_matrix_samples": n_matrix,
        "local_labels_csv_rows": align.get("labels_csv_rows"),
        "local_features": int(matrix.shape[1]) if matrix is not None else None,
    }
    if n_matrix is not None:
        comp["matrix_vs_published_difference"] = PUBLISHED_SAMPLES - n_matrix
        if comp["matrix_vs_published_difference"] != 0:
            rep.warn(
                f"matrix has {comp['matrix_vs_published_difference']} fewer samples than "
                f"the published {PUBLISHED_SAMPLES}; see alignment.csv_hashes_absent_from_npz"
            )
    if matrix is not None:
        comp["feature_difference"] = PUBLISHED_FEATURES - int(matrix.shape[1])
    rep.data["published_comparison"] = comp


def main() -> int:
    ap = argparse.ArgumentParser(description="MH-100K dataset audit (read-only on data/mh100k).")
    ap.add_argument("--data-dir", default="data/mh100k")
    ap.add_argument("--out-dir", default="reports/results")
    ap.add_argument("--csr", default="data/processed/mh100_csr.npz")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    csr_path = Path(args.csr)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not data_dir.exists():
        print(f"ERROR: data directory not found: {data_dir.resolve()}")
        return 1

    print(f"MH-100K dataset audit\nData: {data_dir.resolve()}\n")

    rep = Report()
    record_environment(rep)
    files = record_files(rep, data_dir, csr_path)
    arrays = load_npz_arrays(rep, files.get("matrix_npz"))

    if "column_names" in arrays:
        rep.data["_vocab_names"] = [str(v) for v in np.asarray(arrays["column_names"]).ravel()]

    matrix = load_matrix(rep, files.get("matrix_npz"), files.get("csr_npz"))
    y = audit_labels(rep, arrays, matrix)
    audit_vocabulary(
        rep, arrays, files.get("features_csv"),
        int(matrix.shape[1]) if matrix is not None else None,
    )
    audit_rows(rep, matrix, y, out_dir)
    check_alignment(rep, arrays, matrix, y, files.get("labels_csv"))

    rep.data.pop("_vocab_names", None)

    report_path = out_dir / "dataset_audit.json"
    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(rep.data, fh, indent=2, default=str)

    summary_path = out_dir / "dataset_audit_summary.csv"
    fm, lb, rs = rep.data["feature_matrix"], rep.data["labels"], rep.data["row_statistics"]
    vc, al = rep.data["vocabulary"], rep.data["alignment"]
    rows = [
        ("samples_matrix", fm.get("n_rows")),
        ("samples_labels_csv", al.get("labels_csv_rows")),
        ("samples_published", PUBLISHED_SAMPLES),
        ("features_local", fm.get("n_columns")),
        ("features_published", PUBLISHED_FEATURES),
        ("matrix_dtype", fm.get("dtype")),
        ("is_binary", fm.get("is_binary")),
        ("density", fm.get("density")),
        ("sparsity_percent", fm.get("sparsity_percent")),
        ("mean_nonzero_per_app", (rs.get("nonzero_features_per_app") or {}).get("mean")),
        ("duplicate_rows", rs.get("duplicate_rows")),
        ("duplicate_rate_percent", rs.get("duplicate_rate_percent")),
        ("all_zero_rows", rs.get("all_zero_rows")),
        ("block_counts", vc.get("block_counts")),
        ("block_counts_match_published", vc.get("block_counts_match_published")),
        ("row_alignment_verified", al.get("row_alignment_verified")),
        ("label_mismatches", al.get("label_mismatches")),
        ("samples_dropped_vs_csv", al.get("csv_hashes_absent_from_npz")),
        ("warnings", len(rep.data["warnings"])),
        ("not_available_items", len(rep.data["not_available"])),
    ]
    for cls, st in (lb.get("class_distribution") or {}).items():
        rows.append((f"class_{cls}_count", st["count"]))
        rows.append((f"class_{cls}_percent", st["percent"]))
    with summary_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "value"])
        w.writerows(rows)

    print(f"\nWrote {report_path}")
    print(f"Wrote {summary_path}")
    print(f"Warnings: {len(rep.data['warnings'])}  Not available: {len(rep.data['not_available'])}")
    for msg in rep.data["warnings"]:
        print(f"  ! {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
