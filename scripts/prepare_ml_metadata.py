import zipfile
from pathlib import Path

src = Path("data/mh100k/mh100.npz")
out = Path("data/processed")
out.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(src) as z:
    for name in ("classes.npy", "column_names.npy", "sha256.npy"):
        target = out / name
        if not target.exists():
            target.write_bytes(z.read(name))

print("Labels and feature metadata extracted.")
print("Original dataset and existing model unchanged.")
