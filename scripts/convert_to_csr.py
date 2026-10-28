"""
Convert the dense MH-100K matrix into a sparse CSR artifact.

Why this exists
---------------
data/mh100k/mh100.npz stores its feature matrix as a DENSE int8 array of shape
(101934, 24833). That is 2.53 GB once decompressed in memory, which is the
direct cause of the MemoryError seen during earlier Random Forest training.

This script converts it once, in row blocks so peak memory stays bounded, and
writes a CSR artifact that every later script loads instead.

data/mh100k/ is never modified. Output goes to data/processed/.

Usage (from the repository root):
    python scripts/convert_to_csr.py
"""

from __future__ import annotations

import argparse
import gc
from pathlib import Path

import numpy as np
import scipy.sparse as sp


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert dense MH-100K npz to CSR.")
    ap.add_argument("--src", default="data/mh100k/mh100.npz")
    ap.add_argument("--out-dir", default="data/processed")
    ap.add_argument("--chunk", type=int, default=5000)
    args = ap.parse_args()

    src = Path(args.src)
    out_dir = Path(args.out_dir)

    if not src.exists():
        print(f"ERROR: source not found: {src.resolve()}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    csr_path = out_dir / "mh100_csr.npz"
    meta_path = out_dir / "mh100_meta.npz"

    if csr_path.exists():
        print(f"{csr_path} already exists. Delete it to rebuild.")
        return 0

    print(f"Loading {src} (decompressing a ~2.5 GB dense array)...", flush=True)
    archive = np.load(src, allow_pickle=True)

    missing = [k for k in ("data", "column_names", "classes", "sha256") if k not in archive]
    if missing:
        print(f"ERROR: expected arrays absent from {src.name}: {missing}")
        print(f"       arrays present: {list(archive.keys())}")
        return 1

    dense = archive["data"]
    n_rows, n_cols = dense.shape
    print(f"dense: {dense.shape} {dense.dtype} ({dense.nbytes / 1e9:.2f} GB)", flush=True)

    blocks = []
    for start in range(0, n_rows, args.chunk):
        end = min(start + args.chunk, n_rows)
        blocks.append(sp.csr_matrix(dense[start:end]))
        print(f"  rows {start:>7,} - {end:>7,}", flush=True)

    X = sp.vstack(blocks, format="csr")
    del blocks, dense
    gc.collect()

    density = X.nnz / (n_rows * n_cols)
    print(f"\nCSR: {X.shape}  nnz={X.nnz:,}  density={density:.4%}", flush=True)

    sp.save_npz(csr_path, X)

    np.savez_compressed(
        meta_path,
        column_names=archive["column_names"],
        classes=archive["classes"],
        sha256=archive["sha256"],
        metadata=archive["metadata"] if "metadata" in archive else np.array([]),
        metadata_columns=archive["metadata_columns"]
        if "metadata_columns" in archive
        else np.array([]),
    )

    print(f"wrote {csr_path} ({csr_path.stat().st_size / 1e6:.1f} MB)")
    print(f"wrote {meta_path} ({meta_path.stat().st_size / 1e6:.1f} MB)")
    print("\ndata/mh100k/ was not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
