# -*- coding: utf-8 -*-
"""
Cau hinh chung cho toan bo du an.

Moi tham so dung trong du an deu ke tu file nay,
de bao dam moi lan chay ra cung ket qua.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Console Windows mac dinh dung bang ma cp1258 -> khong in duoc tieng Viet co dau.
# Ep UTF-8 truoc khi in bat ky thu gi de chay o moi may ra cung ket qua.
# ---------------------------------------------------------------------------
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # pragma: no cover
            pass

# ---------------------------------------------------------------------------
# Duong dan
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CSV_PATH = DATA_DIR / "rice.csv"
FIGURES_DIR = ROOT / "reports" / "figures"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR = ROOT / "models"

# ---------------------------------------------------------------------------
# Random state - bat buoc theo de tai
# ---------------------------------------------------------------------------
# Dinh mot con so duy nhat, dung xuyen suot cho moi thu vien
# va moi thay doi. Doi con so nay -> ket qua khac.
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Ten lop - CHON MOT LAN, DUNG XUYEN SUOT
# ---------------------------------------------------------------------------
# "Cammeo" la lop IT nguoi hon, nen F1 tinh cho lop nay
# moi co y nghia (neu F1 tinh cho lop da so thi rat de dat -> it y nghia).
POS_LABEL = "Cammeo"
TARGET_COLUMN = "Class"
CLASSES = ["Cammeo", "Osmancik"]

# ---------------------------------------------------------------------------
# Dac trung
# ---------------------------------------------------------------------------
FEATURES = [
    "Area",
    "Perimeter",
    "Major_Axis_Length",
    "Minor_Axis_Length",
    "Eccentricity",
    "Convex_Area",
    "Extent",
]

# ---------------------------------------------------------------------------
# Chia tap
# ---------------------------------------------------------------------------
# 70 / 15 / 15
TEST_SIZE = 0.15
VALID_SIZE = 0.15

# ---------------------------------------------------------------------------
# Kiem tra du lieu
# ---------------------------------------------------------------------------
# He so ngoai lai theo quy tac IQR: duoi (Q1 - 1.5*IQR) hoac tren (Q3 + 1.5*IQR)
IQR_FACTOR = 1.5

# ---------------------------------------------------------------------------
# Tu do hoa
# ---------------------------------------------------------------------------
# Matplotlib may tinh font tieng Viet co dau
plt_style = "seaborn-v0_8-whitegrid"
