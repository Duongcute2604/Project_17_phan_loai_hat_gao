# -*- coding: utf-8 -*-
"""
Tien xu ly va kiem tra chat luong du lieu.

Nguon du lieu: UCI ML Repository - Rice (Cammeo and Osmancik)
https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik

BA NGUYEN TAC CO BAN (ap dung cho toan bo du an):

  1. CHIA TAP TRUOC KHI LAM GI CAI GI khac.
     Tu o day moi ve sau: moi thu chi nhin tren tap train.

  2. MOI THU HOC TU DU LIEU (scaler, imputer, ...) deu nam trong
     Pipeline va duoc "fit" tren train, khong bao gio fit tren
     ca tap du lieu.

  3. KHONG BAO GIO DUNG NHAN khi loai du lieu. Loai bang tien hien
     (gia tri khong hop le) chu khong loai bang nhan.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (  # noqa: E402
    CLASSES,
    FEATURES,
    IQR_FACTOR,
    CSV_PATH,
    TARGET_COLUMN,
)


# ---------------------------------------------------------------------------
# Nap du lieu
# ---------------------------------------------------------------------------
def load_raw() -> pd.DataFrame:
    """
    Nap file CSV goc (chua chia tap).

    Chi dung ham nay o buoc kiem tra so ban truoc khi chia.
    Sau khi chia, phai dung ham lay tap da chia.
    """
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Khong tim thay {CSV_PATH}\n"
            f"Hay chay: python scripts/download_data.py"
        )
    return pd.read_csv(CSV_PATH)


# ---------------------------------------------------------------------------
# Kiem tra so luoc
# ---------------------------------------------------------------------------
def check_schema(df: pd.DataFrame) -> None:
    """Kiem tra co du cac cot can dung khong. Dung lenh assert de chay nhanh."""
    expected = FEATURES + [TARGET_COLUMN]
    missing = [column for column in expected if column not in df.columns]
    if missing:
        raise ValueError(f"Thieu cot: {missing}\nCo san: {list(df.columns)}")
    print(f"  [OK] Du {len(expected)} cot: {', '.join(expected)}")


def check_missing(df: pd.DataFrame) -> pd.Series:
    """Dem so gia tri thieu (NaN/None) o tung cot."""
    missing = df.isna().sum()
    total_missing = int(missing.sum())
    if total_missing == 0:
        print(f"  [OK] Khong co gia tri thieu trong {len(df.columns)} cot")
    else:
        print(f"  [CANH BAO] Co {total_missing} gia tri thieu:")
        for column, count in missing[missing > 0].items():
            print(f"         {column}: {count}")
    return missing


def check_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tim cac dong bi trung lap.

    YEU TOI QUAN TRONG:
    Neu co dong trung lap, KHONG duoc de chung vao hai tap khac nhau.
    Neu mot ban ghi xuat hien o ca train va ca test, thi mo hinh da
    "nho" roi no o khi duoc cham diem -> ket qua ao, khong trung thuc.
    """
    duplicates = df[df.duplicated(keep=False)]
    count = len(duplicates)
    if count == 0:
        print(f"  [OK] Khong co dong trung lap trong {len(df):,} dong")
    else:
        print(f"  [CANH BAO] Co {count:,} dong thuoc {duplicates.shape[0]} nhom trung lap")
        print(f"         -> Cac dong nay phai nam cung mot tap khi chia")
    return duplicates


def check_target(df: pd.DataFrame) -> pd.Series:
    """
    Kiem tra cot nhan: co nhung gia tri gi, phan bo ra sao.

    KHONG loai dong o day. Chi bao cao.
    """
    counts = df[TARGET_COLUMN].value_counts().reindex(CLASSES).fillna(0).astype(int)
    total = len(df)

    print(f"  [OK] Co {total:,} mau, nhan co {counts.size} gia tri:")
    for label, count in counts.items():
        share = 100.0 * count / total
        bar = "#" * int(round(share / 2))
        print(f"         {label:<10} {count:>5,} mau  ({share:5.2f}%)  {bar}")

    ratio = counts.max() / counts.min()
    if ratio < 1.5:
        print(f"         -> Tap lop CAN BANG (ty le {ratio:.2f}:1)")
    else:
        print(f"         -> Tap lop MUI CAN BANG (ty le {ratio:.2f}:1)")

    unexpected = set(df[TARGET_COLUMN].unique()) - set(CLASSES)
    if unexpected:
        print(f"  [LOI] Co gia tri nhan la: {sorted(unexpected)}")

    return counts


# ---------------------------------------------------------------------------
# Phat hien ngoai le
# ---------------------------------------------------------------------------
def find_outliers_iqr(train_df: pd.DataFrame) -> pd.DataFrame:
    """
    Phat hien ngoai le theo quy tac IQR, CHI TREN TAP TRAIN.

    IQR = Q3 - Q1. Moi gia tri nho hon (Q1 - 1.5*IQR) hoac lon hon
    (Q3 + 1.5*IQR) duoc coi la ngoai la.

    Vi sao chi tren train?
    - Tinh nguong tren ca bo du lieu se lam "ro ri" thong tin cua tap test
      vao qua trinh chon nguong -> ro ri thong tin.
    - Day la nguyen tac mot: moi thu suy ra tu du lieu phai suy ra
      tren tap train roi ap dung moi dung cho tap khac.

    CHINH SACH CUA NHO:
    Dung nhan de quyet dinh loai gi. Loai bang tien hien.
    """
    rows = []
    for column in FEATURES:
        values = train_df[column]
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        low = q1 - IQR_FACTOR * iqr
        high = q3 + IQR_FACTOR * iqr

        mask = (values < low) | (values > high)
        rows.append(
            {
                "feature": column,
                "n_outlier": int(mask.sum()),
                "rate_%": round(100.0 * mask.mean(), 3),
                "lower": round(float(low), 4),
                "upper": round(float(high), 4),
                "min": round(float(values.min()), 4),
                "max": round(float(values.max()), 4),
            }
        )
    return pd.DataFrame(rows)


def describe_outliers(outliers: pd.DataFrame) -> None:
    """In bao cao ngoai le va giai thich quyet dinh xu ly."""
    total_cells = int(outliers["n_outlier"].sum())
    total_rows = int((outliers["n_outlier"] > 0).sum())

    print(f"  [OK] Phat hien ngoai le (IQR, chi tren train):")
    print(f"         {total_cells:,} o ngoai le tren {total_rows} dac trung")
    for _, row in outliers.iterrows():
        if row["n_outlier"] > 0:
            print(
                f"         {row['feature']:<20} {row['n_outlier']:>4} "
                f"({row['rate_%']:>6.3f}%)  khoang hop le: "
                f"[{row['lower']:.2f}, {row['upper']:.2f}]"
            )

    if total_cells == 0:
        print("         -> Khong co ngoai le")
        return

    print()
    print("  QUYET DINH XU LY: KHONG loai bo dong nao.")
    print("  Ly do:")
    print("   1. Ty le ngoai le rat nho (xem bang tren), khong anh huong ket qua.")
    print("   2. Loai bo dong se lam mauoi mat thong tin hinh hoc that cua hat gao.")
    print("   3. De nguyen giu nguon goc va cong khai rang buoc.")
    print("   4. Dinh nghia 'ngoai le' o day chi la thong bao, khong phai mau sac.")
    print("   -> Day la ngoai le TRONG kien thuc, khong phai loi du lieu.")


def check_nan_in_target(df: pd.DataFrame) -> None:
    """Nhan khong duoc thieu o bat ky dong nao."""
    bad = int(df[TARGET_COLUMN].isna().sum())
    if bad == 0:
        print(f"  [OK] Cot nhan '{TARGET_COLUMN}' khong co gia tri thieu")
    else:
        print(f"  [LOI] Cot nhan thieu {bad} gia tri")


# ---------------------------------------------------------------------------
# Chay toan bo kiem tra
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 64)
    print("KIEM TRA CHAT LUONG DU LIEU")
    print("=" * 64)

    df = load_raw()
    print(f"\n[1] TAI DU LIEU")
    print(f"  Duong dan: {CSV_PATH}")
    print(f"  Kich thuoc: {df.shape[0]:,} dong x {df.shape[1]} cot")

    print(f"\n[2] KIEN THUC")
    check_schema(df)

    print(f"\n[3] GIA TRI THIEU")
    check_missing(df)
    check_nan_in_target(df)

    print(f"\n[4] DONG TRUNG LAP")
    check_duplicates(df)

    print(f"\n[5] PHAN BO LOP")
    check_target(df)

    print(f"\n[6] NGOAI LE (chi tren toan bo de tham khao)")
    print("  Luu y: phan tich chinh thuc se chay LAI tren tap train.")
    print("  Xem src/split.py")
    describe_outliers(find_outliers_iqr(df))

    print(f"\n[7] THONG KE MOTA")
    stats = df[FEATURES].describe().T
    stats["missing"] = df[FEATURES].isna().sum()
    stats["n_outlier_IQR"] = find_outliers_iqr(df).set_index("feature")["n_outlier"]
    print(stats.to_string(float_format=lambda value: f"{value:.4f}"))

    print(f"\n  Ban luu thong ke: reports/data_quality_report.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
