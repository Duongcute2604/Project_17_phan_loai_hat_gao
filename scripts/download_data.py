#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script tai du lieu Rice (Cammeo and Osmancik) tu UCI Machine Learning Repository.

Nguon chinh thuc:
    https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik
    DOI: https://doi.org/10.24432/C5MW4Z
    Giay phep: CC BY 4.0

Cach dung:
    python scripts/download_data.py

Ket qua:
    data/raw/rice+cammeo+and+osmancik.zip   (file zip goc tai tu UCI)
    data/raw/uci_545/Rice_Cammeo_Osmancik.arff
    data/raw/uci_545/Citation_Request.txt
    data/rice.csv                            (ban CSV de pandas doc)
    data/checksums.txt                       (SHA256 de kiem chung)
"""

from __future__ import annotations

import csv
import hashlib
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

# ---------------------------------------------------------------------------
# Duong dan
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
EXTRACT_DIR = RAW_DIR / "uci_545"
CSV_PATH = ROOT / "data" / "rice.csv"
CHECKSUM_PATH = ROOT / "data" / "checksums.txt"

ZIP_URL = "https://archive.ics.uci.edu/static/public/545/rice+cammeo+and+osmancik.zip"

# Cac cot dac trung va nhan, dung thu tu trong ARFF
FEATURE_COLUMNS = [
    "Area",
    "Perimeter",
    "Major_Axis_Length",
    "Minor_Axis_Length",
    "Eccentricity",
    "Convex_Area",
    "Extent",
]
TARGET_COLUMN = "Class"


def sha256_of(path: Path) -> str:
    """Tinh SHA256 cua mot tep de chung minh du lieu khong bi thay doi."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, destination: Path) -> None:
    """Tai tep tu URL ve dia chi cua chinh."""
    print(f"  Dang tai: {url}")
    with urlopen(url, timeout=120) as response:
        payload = response.read()
    destination.write_bytes(payload)
    print(f"  OK -> {destination.name} ({len(payload):,} bytes)")


def arff_to_csv(arff_path: Path, csv_path: Path) -> int:
    """
    Doc file ARFF va chuyen thanh CSV.

    File ARFF co cau truc:
        @RELATION ...     - ten quan he
        @ATTRIBUTE ...    - ten cot + kieu du lieu
        @DATA             - sau dong nay la du lieu
        15231,525.57,...  - cac dong so, tach bang dau phay

    Ta chi lay cac dong sau @DATA, tach bang dau phay,
    viet tieu de cot sang dong dau tien (header).
    """
    rows: list[list[str]] = []
    in_data = False

    with arff_path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            # Comment bat dau bang %
            if line.startswith("%"):
                continue
            # Bat dau phan du lieu
            if line.upper().startswith("@DATA"):
                in_data = True
                continue
            # Bo qua cac dong dinh nghia (@RELATION, @ATTRIBUTE)
            if line.startswith("@"):
                continue
            if in_data:
                rows.append([value.strip() for value in line.split(",")])

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(FEATURE_COLUMNS + [TARGET_COLUMN])
        writer.writerows(rows)

    return len(rows)


def main() -> int:
    print("=" * 60)
    print("TAI DU LIEU: Rice (Cammeo and Osmancik) - UCI ML Repository")
    print("=" * 60)

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Buoc 1: tai file zip goc
    zip_path = RAW_DIR / "rice+cammeo+and+osmancik.zip"
    if zip_path.exists():
        print(f"  File zip da ton tai, bo qua tai lai: {zip_path.name}")
    else:
        download(ZIP_URL, zip_path)

    # Buoc 2: giai nen
    print("\nDang giai nen zip...")
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(EXTRACT_DIR)
    for item in sorted(EXTRACT_DIR.rglob("*")):
        if item.is_file():
            print(f"  {item.name} ({item.stat().st_size:,} bytes)")

    # Buoc 3: chuyen ARFF sang CSV
    arff_path = EXTRACT_DIR / "Rice_Cammeo_Osmancik.arff"
    if not arff_path.exists():
        print(f"LOI: khong tim thay {arff_path}", file=sys.stderr)
        return 1

    print("\nDang chuyen ARFF sang CSV...")
    n_rows = arff_to_csv(arff_path, CSV_PATH)
    print(f"  Da ghi {n_rows:,} dong vao {CSV_PATH.relative_to(ROOT)}")
    print(f"  Cot: {', '.join(FEATURE_COLUMNS + [TARGET_COLUMN])}")

    # Buoc 4: ghi checksum de chung minh du lieu nguyen ven
    print("\nDang ghi checksum SHA256...")
    targets = [zip_path, arff_path, CSV_PATH]
    CHECKSUM_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CHECKSUM_PATH.open("w", encoding="utf-8") as handle:
        for path in targets:
            try:
                relative = path.relative_to(ROOT).as_posix()
            except ValueError:
                relative = path.name
            handle.write(f"{sha256_of(path)}  {relative}\n")
            print(f"  {sha256_of(path)[:16]}...  {relative}")

    print("\n" + "=" * 60)
    print("HOAN TAT. Chay tiep:  python src/data.py")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
