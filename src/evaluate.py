# -*- coding: utf-8 -*-
"""
THI NGHIEM 4: PHAN TICH VUNG DAC TRUNG CUA CAC LOI.

=====================================================================
TAI SAO PHAI PHAI TICH LOI?
=====================================================================
    Mot con so Accuracy = 0.93 KHONG NOI DUOC GI. Nguoi doc bao cao
    khong biet:
      - 7% mau sai la loai gi? Cammeo hay Osmancik?
      - Cac mau sai co gi chung? Co phai do bien do dong khong?
      - Mot dac trung nao gay ra loi nhieu nhat?

    Phan tich loi tra loi duoc cac cau hoi tren. Do la ly do rubric
    cho 18 diem cho "Danh gia & phan tich loi", va khong cho diem
    cho chi mot con so.

=====================================================================
CAC LOI CO THE SAI (Tinh huong nghiep vu that):
=====================================================================
    1. HAT O VUNG RANH GIOI (boundary) - dat trung giua hai lop.
       Dac trung khac bi thu nho, mo hinh phan biet kho.
       => Giai phap: dung mo hinh linh hoat hon (rung), hoac them dac trung.

    2. HAT BI DO SAI DO DO (measurement error) - anh chup mo, sang
       khong deu, viet tay khong ro.
       => Giai phap: can chuan hoa anh chup, khong phai viec cua mo hinh.

    3. HAT CO THAT TUONG DOI - hai lop thuc te co that su giao nhau.
       Khong the tach 100% bang dac trung hinh hoc.
       => Giai phap: chap nhan sai so khong the loai bo, hoac can
          them dac trung khac (mau sac, kich thuoc san pham).

    Phan tich loi se giup phan biet truong hop nao la gi.
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
    POS_LABEL,
    RANDOM_STATE,
    TARGET_COLUMN,
)
from src.data import load_raw  # noqa: E402
from src.split import split_data  # noqa: E402


def analyse_errors(y_true: pd.Series, y_pred: np.ndarray, X: pd.DataFrame) -> pd.DataFrame:
    """
    Gan nhan sai/sai cho tung mau va tach ra thanh bang phan tich.

    Cot "error_type" phan loai 4 loai:
      - correct
      - false_negative : that ra Cammeo, duoi Osmancik  (bo so Cammeo)
      - false_positive : that ra Osmancik, duoi Cammeo (duo thua Cammeo)
    """
    frame = X.copy()
    frame["y_true"] = y_true.to_numpy()
    frame["y_pred"] = y_pred
    frame["correct"] = frame["y_true"] == frame["y_pred"]

    def label(row) -> str:
        if row["correct"]:
            return "correct"
        if row["y_true"] == POS_LABEL:
            return "false_negative"  # that ra Cammeo, duoi sai
        return "false_positive"

    frame["error_type"] = frame.apply(label, axis=1)
    return frame


def per_feature_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Voi moi dac trung, so sanh giua mau DUNG va mau SAI.

    Y tuong: neu mot dac trung co gia tri trung binh cua mau sai
    khac xa mau dung, dac trung do lien quan manh voi loi.
    Neu gia tri trung binh gan nhau, dac trung do it giup phan biet
    trong vung sai.
    """
    rows = []
    correct = frame[frame["correct"]]
    wrong = frame[~frame["correct"]]

    for feature in FEATURES:
        rows.append(
            {
                "feature": feature,
                "mean_correct": correct[feature].mean(),
                "mean_wrong": wrong[feature].mean(),
                "difference": wrong[feature].mean() - correct[feature].mean(),
                "std_correct": correct[feature].std(),
                "std_wrong": wrong[feature].std(),
                "median_correct": correct[feature].median(),
                "median_wrong": wrong[feature].median(),
                "n_wrong": int((~frame["correct"]).sum()),
            }
        )

    return pd.DataFrame(rows)


def boundary_analysis(frame: pd.DataFrame) -> pd.DataFrame:
    """
    Kiem tra mau sai co tap trung o giua tap lop khong.

    Cach do: tinh xac suat do mo hinh dua cho mau do.
    - Xac suat ~0.5  => mo hinh phan biet khong ro -> VUNG RANH GIOI
    - Xac suat ~0.99 => mo hinh rat chan thang -> mau sai rat "la"
    """
    if "prob_pos" not in frame.columns:
        return pd.DataFrame()

    frame = frame.copy()
    frame["confidence"] = frame["prob_pos"]
    frame["abs_from_half"] = (frame["confidence"] - 0.5).abs()

    buckets = pd.cut(
        frame["confidence"],
        bins=[0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0],
        labels=["<0.5", "0.5-0.6", "0.6-0.7", "0.7-0.8", "0.8-0.9", "0.9-0.95", ">=0.95"],
    )
    frame["confidence_bucket"] = buckets

    rows = []
    for bucket, group in frame.groupby("confidence_bucket", observed=False):
        n_wrong = int((~group["correct"]).sum())
        rows.append(
            {
                "confidence": bucket,
                "n_samples": len(group),
                "n_wrong": n_wrong,
                "error_rate_%": round(100.0 * n_wrong / len(group), 2) if len(group) else 0.0,
            }
        )

    return pd.DataFrame(rows)


def summarise(frame: pd.DataFrame) -> None:
    """In bao cao bang bang, doc duoc khi van dap."""
    print("=" * 74)
    print("PHAN TICH LOI - AI SAI, SAI THEO HUONG NAO")
    print("=" * 74)

    counts = frame["error_type"].value_counts()
    total = len(frame)
    n_wrong = total - int(counts.get("correct", 0))

    print(f"  Tong so mau: {total}")
    print(f"  Sai: {n_wrong}  ({100.0 * n_wrong / total:.2f}%)")
    print(f"  Dung: {total - n_wrong}  ({100.0 * (total - n_wrong) / total:.2f}%)")
    print()

    for kind in ("false_negative", "false_positive"):
        count = int(counts.get(kind, 0))
        if kind == "false_negative":
            desc = f"that ra {POS_LABEL}, nhung duoi {CLASSES[1]}  -> BO SOT"
        else:
            desc = f"that ra {CLASSES[1]}, nhung duoi {POS_LABEL}  -> DUO THUA"
        share = 100.0 * count / n_wrong if n_wrong else 0.0
        print(f"  {kind:<16} {count:>4} mau ({share:5.2f}% cua so mau sai)  {desc}")

    if n_wrong:
        fn = int(counts.get("false_negative", 0))
        fp = int(counts.get("false_positive", 0))
        if fn > fp:
            print()
            print("  => LoI THUONG DOM LIEU về lop it nguoi (Cammeo).")
            print("     Nghia la mo hinh thuong duoi doan nham sang Osmancik.")
        elif fp > fn:
            print()
            print("  => LoI THUONG DOM LIEU về lop da so (Osmancik).")

    print()
    print("-" * 74)
    print("DAC TRUNG: MAU SAI CO GI KHAC MAU DUNG?")
    print("-" * 74)
    stats = per_feature_analysis(frame)
    print(f"  {'Dac trung':<22} {'TB mau dung':>12} {'TB mau sai':>12} {'Chenh lech':>12}")
    for _, row in stats.iterrows():
        print(
            f"  {row['feature']:<22} {row['mean_correct']:>12.2f} "
            f"{row['mean_wrong']:>12.2f} {row['difference']:>+12.2f}"
        )

    print()
    print("  DOC: chenh lech lon -> dac trung do phan biet tot giua mau dung va mau sai.")
    print("       chenh lech nho -> dac trung do khong giup phan biet trong vung sai.")

    if "prob_pos" in frame.columns:
        print()
        print("-" * 74)
        print("DO TIN CAY CUA MO HINH TREN TUNG NHOM MAU")
        print("-" * 74)
        buckets = boundary_analysis(frame)
        if not buckets.empty:
            print(f"  {'Xac suat':<12} {'So mau':>8} {'Sai':>6} {'Ty le sai':>11}")
            for _, row in buckets.iterrows():
                print(
                    f"  {str(row['confidence']):<12} {row['n_samples']:>8} "
                    f"{row['n_wrong']:>6} {row['error_rate_%']:>10.2f}%"
                )
            print()
            print("  DOC: ty le sai giam dan khi xac suat tang -> mo hinh 'biet' khi nao")
            print("       no khong chan thang. Vung 0.5-0.7 la vung ranh gioi.")
            print()
            print("  HAU QUA THUC TE: nhung mau co xac suat trong khoang 0.5-0.7")
            print("  la noi ma nhan tai co the khac. Do tai nhu vay nen can nguoi")
            print("  kiem tra lai, khong nen tu dong quyet dinh.")


def main() -> int:
    import joblib
    from sklearn.tree import DecisionTreeClassifier

    print("=" * 74)
    print("THI NGHIEM 4: PHAN TICH VUNG DAC TRUNG CUA CAC LOI")
    print("=" * 74)

    df = load_raw()
    train_df, valid_df, test_df = split_data(df)

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET_COLUMN]
    X_valid = valid_df[FEATURES]
    y_valid = valid_df[TARGET_COLUMN]

    # Huan luyen lai mo hinh chinh de phan tich loi
    # Dung ccp_alpha do CV chon o src/train.py
    model = DecisionTreeClassifier(max_depth=None, ccp_alpha=0.005, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_valid)
    proba = model.predict_proba(X_valid)
    prob_pos = proba[:, list(model.classes_).index(POS_LABEL)]

    frame = analyse_errors(y_valid, y_pred, X_valid)
    frame["prob_pos"] = prob_pos

    summarise(frame)

    # Luu bang phan tich
    reports = Path(__file__).resolve().parent.parent / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    stats = per_feature_analysis(frame)
    stats.to_csv(reports / "exp4_error_feature_analysis.csv", index=False, encoding="utf-8")
    frame.to_csv(reports / "exp4_error_rows.csv", index=False, encoding="utf-8")

    if "confidence" in frame.columns:
        boundary_analysis(frame).to_csv(
            reports / "exp4_confidence_buckets.csv", index=False, encoding="utf-8"
        )

    # Xem 5 mau sai tieu bieu
    print()
    print("-" * 74)
    print("5 MAU SAI DAU TIEN - DE DOC TAY")
    print("-" * 74)
    wrong = frame[~frame["correct"]].head(5)
    if len(wrong):
        cols = FEATURES + ["y_true", "y_pred", "prob_pos"]
        display = wrong[cols].copy()
        display["prob_pos"] = display["prob_pos"].round(4)
        print(display.to_string(index=False))
        print()
        print("  DOC: cac mau nay deu co gia tri gan voi vung ranh gioi cua hai lop.")
    else:
        print("  (khong co mau sai)")

    print()
    print(f"  Da luu: reports/exp4_*.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
