# -*- coding: utf-8 -*-
"""
Chia du lieu thanh 3 tap: train / validation / test.

=====================================================================
BAO CAO PHONG CHONG ROI RI THONG TIN (DATA LEAKAGE) - DOC KY
=====================================================================

ROI RI THONG TIN la gi?
    Khi thong tin cua tap KIEM TRA (test) "ro ri" vao qua trinh xay dung
    mo hinh. Luc do, diem bao cao khong con phan anh nang luc that cua
    mo hinh tren du lieu chua tung thay.

Vi du sai (thuong gap nhat):
    1. Chay model tren ca tap du lieu, lay diem test -> thay tham so
       -> chay lai tren ca tap du lieu -> lay diem test -> ...
       -> chon bo tham so cho diem cao nhat.
       => Moi thu ban vua dung la: ban KHONG con thu muc dich.
       => Tuong duong lam bai thi: lam het, xem diem, thi lai.

    2. Dung chuan hoa / chon dac trung tren CA tap du lieu roi moi chia.
       => Gia tri trung binh, do lon da "biot" thong tin tu tap test.

    3. Chon dac trung / bien transform dua tren ket qua cua tap test.

CACH CHONG TRONG DU AN NAY:
    A. CHIA TAP TRUOC TAT CA. Khong dung gi tu du lieu truoc khi chia.
    B. Chi fit Pipeline tren TAP TRAIN.
    C. Chon mo hinh / tham so bang TAP VALIDATION.
    D. TAP TEST chi dung MOT LAN o cuoi cung, de bao cao.
    E. Moi thu suy ra tu du lieu (nguong ngoai la,...) deu tinh tren
       TAP TRAIN roi moi ap dung cho tap khac.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (  # noqa: E402
    CLASSES,
    FEATURES,
    IQR_FACTOR,
    POS_LABEL,
    RANDOM_STATE,
    TARGET_COLUMN,
    TEST_SIZE,
    VALID_SIZE,
)
from src.data import find_outliers_iqr, load_raw  # noqa: E402


# ---------------------------------------------------------------------------
# Chia tap
# ---------------------------------------------------------------------------
def split_data(
    df: pd.DataFrame,
    test_size: float = TEST_SIZE,
    valid_size: float = VALID_SIZE,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Chia du lieu thanh train / validation / test.

    VAI TRO CUA TUNG TAP - can nho dung:
    ----------------------------------
    train      : dung de DAY mo hinh (hoc duoc gi, tu duoc gi).
    validation : dung de CHON mo hinh va tham so (cau hinh nao tot nhat).
    test       : dung MOT LAN de BAO CAO ket qua cuoi cung.

    stratify y = gi duy tri ty le lop trong moi tap.
        Vi du goc: 42.78% Cammeo / 57.22% Osmancik.
        Sau khi chia: moi tap van ~42.78% / ~57.22%.
        => Khong co tap nao "bi lech" ve ty le lop, so sanh cong bang.
    """
    # Buoc 1: tach tap test ra truoc.
    # Day la tap "dong bang" - chua duoc cham vao den lan cuoi cung.
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df[TARGET_COLUMN],
    )

    # Buoc 2: tach tap validation tu phan con lai.
    # train_test_split tra ve (tap_giu_lai, tap_tach_ra).
    # Ta muon giu lai TRAIN, tach ra VALIDATION.
    train_df, valid_df = train_test_split(
        train_df,
        # valid_size la ty le so voi phan con lai, khong phai so voi tong:
        # 0.15 / 0.85 = 0.1765
        test_size=valid_size / (1.0 - test_size),
        random_state=random_state,
        stratify=train_df[TARGET_COLUMN],
    )

    train_df = train_df.reset_index(drop=True)
    valid_df = valid_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    # Kiem tra bat buoc: train phai LON NHAT, test va validation phai bang nhau.
    # (Neu bao loi "train nho hon validation", nghia la da gan nham bien.)
    assert len(train_df) > len(valid_df), (
        f"LOI CHIA TAP: train={len(train_df)} phai lon hon validation={len(valid_df)}"
    )
    assert len(train_df) > len(test_df), (
        f"LOI CHIA TAP: train={len(train_df)} phai lon hon test={len(test_df)}"
    )
    assert abs(len(valid_df) - len(test_df)) <= 1, (
        f"LOI CHIA TAP: validation={len(valid_df)} va test={len(test_df)} phai gan bang nhau"
    )

    return train_df, valid_df, test_df


# ---------------------------------------------------------------------------
# Bao cao
# ---------------------------------------------------------------------------
def split_report(
    train_df: pd.DataFrame, valid_df: pd.DataFrame, test_df: pd.DataFrame
) -> pd.DataFrame:
    """
    In bang kich thuoc va phan bo lop cua 3 tap.

    BANG NAY LA BANG QUAN TRONG NHAT TRONG BAO CAO.
    No chung minh hai dieu:
      1. Ba tap co dung ty le lop nhu nhau -> so sanh cong bang.
      2. Khong co dong nao bi trung giua cac tap -> khong ro ri.
    """
    rows = []
    total = len(train_df) + len(valid_df) + len(test_df)

    for name, part in (
        ("train", train_df),
        ("validation", valid_df),
        ("test", test_df),
    ):
        row = {
            "tap": name,
            "so_mau": len(part),
            "ty_le_%": round(100.0 * len(part) / total, 2),
        }
        counts = part[TARGET_COLUMN].value_counts()
        for label in CLASSES:
            count = int(counts.get(label, 0))
            row[label] = count
            row[f"{label}_%"] = round(100.0 * count / len(part), 2)
        rows.append(row)

    report = pd.DataFrame(rows)

    print("=" * 66)
    print("BANG CHIA TAP")
    print("=" * 66)
    print(report.to_string(index=False))
    print()

    # Kiem tra ty le lop co nhat quan giua cac tap khong
    print("KIEM TRA TINH CONSISTENT CUA TY LE LOP:")
    for label in CLASSES:
        shares = [row[f"{label}_%"] for row in rows]
        spread = max(shares) - min(shares)
        status = "OK" if spread <= 1.0 else "LECH"
        print(f"  {label:<10} cac tap: {shares}  -> bien dong {spread:.2f} pp  [{status}]")
    print()

    return report


def check_overlap(
    train_df: pd.DataFrame, valid_df: pd.DataFrame, test_df: pd.DataFrame
) -> None:
    """
    Kiem tra co dong nao trung lap giua cac tap khong.

    Day la phan "chan doan ro ri thong tin" duoc ghi vao bao cao.
    Neu khong co dong trung, phan doan nay khong phat hien gi.
    """
    print("=" * 66)
    print("KIEM TRA TRANH LAP GIUA CAC TAP")
    print("=" * 66)

    def key(frame: pd.DataFrame) -> set:
        return set(map(tuple, frame[FEATURES + [TARGET_COLUMN]].to_numpy()))

    train_keys = key(train_df)
    valid_keys = key(valid_df)
    test_keys = key(test_df)

    pairs = [
        ("train", "validation", train_keys & valid_keys),
        ("train", "test", train_keys & test_keys),
        ("validation", "test", valid_keys & test_keys),
    ]
    total_overlap = 0
    for left, right, overlap in pairs:
        count = len(overlap)
        total_overlap += count
        status = "OK - khong trung" if count == 0 else f"[LOI] {count} dong trung!"
        print(f"  {left:<11} vs {right:<11} : {status}")

    print()
    if total_overlap == 0:
        print("  -> KHONG co dong nao xuat hien o ca hai tap.")
        print("     Khong ton tai ro ri thong tin do ban ghi trung lap.")
    else:
        print("  -> CANH BAO: co ban ghi bi trung giua cac tap.")
        print("     Phai gom chung vao mot tap de tranh ro ri thong tin.")
    print()


def outlier_report_on_train(train_df: pd.DataFrame) -> pd.DataFrame:
    """
    Phat hien ngoai le CHI TREN TAP TRAIN roi ap dung cho cac tap khac.

    Ly do khong tinh tren ca du lieu:
        Neu nguong ngoai le duoc tinh tren ca tap (ca test),
        nguong do da "biot" thong tin cua tap test -> ro ri thong tin.
    """
    outliers = find_outliers_iqr(train_df)
    print("=" * 66)
    print("NGOAI LE - TINH TREN TAP TRAIN ROI AP DUNG CHO TAP KHAC")
    print("=" * 66)
    print(f"  Quy tac IQR: ngoai [Q1 - {IQR_FACTOR}*IQR, Q3 + {IQR_FACTOR}*IQR]")
    print()
    for _, row in outliers.iterrows():
        flag = "" if row["n_outlier"] == 0 else "   <-- co ngoai le"
        print(
            f"  {row['feature']:<20} train: {row['n_outlier']:>4} o "
            f"({row['rate_%']:>6.3f}%)  [hop le: {row['lower']:.2f}, {row['upper']:.2f}]{flag}"
        )
    print()
    print("  -> Chi thong bao, KHONG loai dong. Xem ly do trong src/data.py")
    print()
    return outliers


def apply_outlier_flags(
    train_df: pd.DataFrame, other_df: pd.DataFrame
) -> pd.Series:
    """
    Gan nhan ngoai le cho mot tap bat ky, dung nguong da tinh tren train.

    Tra ve Series boolean: True = dong bi gan co ngoai le.
    Day la thong bao, KHONG dung de loai dong.
    """
    flag = pd.Series(False, index=other_df.index)
    for column in FEATURES:
        values = train_df[column]
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        low = q1 - IQR_FACTOR * iqr
        high = q3 + IQR_FACTOR * iqr
        flag |= (other_df[column] < low) | (other_df[column] > high)
    return flag


# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 66)
    print("CHIA DU LIEU - BUOC QUAN TRONG NHAT DE CHONG ROI RI THONG TIN")
    print("=" * 66)
    print()
    print(f"random_state = {RANDOM_STATE}   (dung mot con so duy nhat cho moi thu)")
    print(f"test_size    = {TEST_SIZE}")
    print(f"valid_size   = {VALID_SIZE}")
    print()

    # 1. Nap du lieu
    df = load_raw()
    print(f"Tai duoc {len(df):,} dong.")
    print()

    # 2. CHIA TRUOC - khong lam gi khac truoc buoc nay
    train_df, valid_df, test_df = split_data(df)

    # 3. Bao cao
    report = split_report(train_df, valid_df, test_df)
    check_overlap(train_df, valid_df, test_df)
    outliers = outlier_report_on_train(train_df)

    # 4. Luu lai de cac buoc sau dung chung mot phep chia
    REPORTS = Path(__file__).resolve().parent.parent / "reports"
    REPORTS.mkdir(parents=True, exist_ok=True)
    report.to_csv(REPORTS / "split_report.csv", index=False, encoding="utf-8")
    outliers.to_csv(REPORTS / "outlier_report.csv", index=False, encoding="utf-8")

    # 5. In ra tien xu ly cho tung tap, chi lay dac trung + nhan
    print("=" * 66)
    print("MAU DAU TIEN CUA MOI TAP")
    print("=" * 66)
    for name, part in (
        ("train", train_df),
        ("validation", valid_df),
        ("test", test_df),
    ):
        head = part[FEATURES + [TARGET_COLUMN]].head(2)
        print(f"\n[{name}]")
        print(head.to_string(index=False))

    print()
    print("=" * 66)
    print("DA LUU: reports/split_report.csv, reports/outlier_report.csv")
    print("=" * 66)
    print()
    print("QUAN TRONG: TAP TEST PHAI DUOC GIU NGUYEN, KHONG DUNG DE CHON GI")
    print("  - Chon mo hinh / tham so: dung TAP VALIDATION")
    print("  - Bao cao ket qua cuoi cung: dung TAP TEST, MOT LAN")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
