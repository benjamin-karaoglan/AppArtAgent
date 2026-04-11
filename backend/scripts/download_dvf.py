#!/usr/bin/env python3
"""
Download a DVF dataset file into data/dvf/.

Handles .gz and .zip archives automatically.

Usage:
    uv run download-dvf <url>
    uv run download-dvf https://static.data.gouv.fr/.../dvf.csv.gz
"""

import gzip
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "dvf"


def download(url: str) -> None:
    if not url.startswith("https://"):
        print("ERROR: URL must use HTTPS")
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    filename = url.split("/")[-1].split("?")[0]
    dest = DATA_DIR / filename

    print(f"Downloading {url}")
    with (
        urllib.request.urlopen(url, timeout=120) as resp,  # noqa: S310
        open(dest, "wb") as out,
    ):
        shutil.copyfileobj(resp, out)
    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"Saved {dest.name} ({size_mb:.1f} MB)")

    # Extract if compressed
    if dest.suffix == ".gz":
        out = dest.with_suffix("")
        print(f"Extracting {dest.name} -> {out.name}")
        with gzip.open(dest, "rb") as f_in:
            with open(out, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        dest.unlink()
        out_mb = out.stat().st_size / (1024 * 1024)
        print(f"Extracted {out.name} ({out_mb:.1f} MB)")

    elif dest.suffix == ".zip":
        print(f"Extracting {dest.name}")
        with zipfile.ZipFile(dest) as zf:
            zf.extractall(DATA_DIR)
        dest.unlink()
        print("Extracted all files")

    print()
    print(f"Files in {DATA_DIR}:")
    for f in sorted(DATA_DIR.iterdir()):
        if f.name.startswith("."):
            continue
        size = f.stat().st_size / 1024 / 1024
        print(f"  {f.name} ({size:.1f} MB)")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: uv run download-dvf <url>")
        sys.exit(1)
    download(sys.argv[1])


if __name__ == "__main__":
    main()
