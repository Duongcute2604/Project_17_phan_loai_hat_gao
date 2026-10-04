# -*- coding: utf-8 -*-
"""
BASELINE - doi thu yeu de chung minh mo hinh chinh that su tot hon.

=====================================================================
BASELINE LA GI?
=====================================================================
    Baseline (duong co so) la mot mo hinh DUONG BIET - giong nhat,
    lam duoc ngay, khong ton cong su hoc - ma moi mo hinh phuc tap
    deu phai dat duoc neu muon chung minh la tot hon.

Vi du ve doi voi bai toan phan loai gao:
    1. Duong co so 1: don gian nhat - LUON doan mot lop.
       Khong can hoc gi ca, chi can biet lop nao nhieu hon.
    2. Duong co so 2: cay chi mot nhan (depth=1) - "neu dac trung A
       lon hon nguong T thi la lop 1, nguoc lai la lop 2".

    Chi mot nhan la cau hoi "mot dac trung nao phan loai duoc tot nhat?"
    -> day la buc toi thieu ma mo hinh chinh phai vuot qua.

    3. Quy tac don gian day: chon nganh dich,
       vi du "Area nho -> Cammeo, Area lon -> Osmancik".
       -> Co y nghia vat ly, de hieu, de giai thich khi van dap.

=====================================================================
Tại sao can baseline?
=====================================================================
    Do duoc 99% KHONG CO Y NGHI GIA:
    - Neu chi do mot mo hinh, khong biet 99% la tot hay do tai.
    - Baseline cho mot moc: "mo hinh tao duoc 99%, baseline 57% =>
      mo hinh tot hon that, va con 42 diem phan biet".

    Day cung la ly do de tao RO CHONG GI do dat - con kiem so.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.tree import DecisionTreeClassifier, export_text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (  # noqa: E402
    CLASSES,
    FEATURES,
    POS_LABEL,
    RANDOM_STATE,
    TARGET_COLUMN,
)


# ---------------------------------------------------------------------------
# Tien xu ly dung chung cho moi mo hinh
# ---------------------------------------------------------------------------
def xy(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Tach dac trung va nhan tu mot tap du lieu."""
    return frame[FEATURES].copy(), frame[TARGET_COLUMN].copy()


# ---------------------------------------------------------------------------
# Danh gia
# ---------------------------------------------------------------------------
def positive_proba(model, X: pd.DataFrame) -> np.ndarray:
    """
    Lay xac suat duong cho lop POS_LABEL.

    predict_proba tra ve xac suat theo thu tu model.classes_.
    Ta phai lay dung COT ung voi POS_LABEL, khong gia dinh cot nao.
    """
    proba = model.predict_proba(X)
    column = list(model.classes_).index(POS_LABEL)
    return proba[:, column]


def evaluate(y_true: pd.Series, y_pred: np.ndarray, proba_pos: np.ndarray | None) -> dict:
    """
    Tinh cac chi so danh gia tren MOT tap.

    CAC CHI SO:
    -----------
    accuracy     : tong so du doan dung / tong so mau.
                   Luu y: co the bi "lua" khi tap lop mat can bang,
                   vi no bo qua tinh hinh Cac lop bi sai bao nhieu.

    precision    : tren mau duoc duoi positive, bao nhieu thi DUNG.
                   = TP / (TP + FP)

    recall       : tren thuc te la positive, tim duoc bao nhieu.
                   = TP / (TP + FN)

    f1           : trung binh harmonic cua precision va recall.
                   Thap khi mot trong hai thap. Day la chi so chinh
                   cua nhom vi no khong bo qua mot phia nao.

    roc_auc      : kha nang phan biet hai lop, xem "duong cong ROC"
                   - 0.5 = ngau nhien (may dong coin)
                   - 1.0 = phan biet hoan hao
                   - Khong phu thuoc nguong quyet dinh -> do "nang luc"
                   cua mo hinh, khong phai mot diem cat cu the.
                   (Luu y: phai truyen xac suat CUA LOP DUONG, khong phai
                   ma tran 2 cot nguyen.)

    Ma tran nham nhieu: confusion_matrix
                   - TN: dung Cammeo
                   - FP: duoi la Osmancik nhung that ra Cammeo
                   - FN: duoi la Cammeo nhung that ra Osmancik
                   - TP: dung Osmancik
                   (Theo thu tu lop cua model.classes_)
    """
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(
            y_true, y_pred, pos_label=POS_LABEL, zero_division=0
        ),
        "recall": recall_score(y_true, y_pred, pos_label=POS_LABEL, zero_division=0),
        "f1": f1_score(y_true, y_pred, pos_label=POS_LABEL, zero_division=0),
    }

    if proba_pos is not None:
        # roc_auc_score ky vong xac suat cua lop duong.
        # Do "Cammeo" la lop khong chuan, ta doi nhan thanh 0/1 truoc.
        binary = (y_true.to_numpy() == POS_LABEL).astype(int)
        metrics["roc_auc"] = roc_auc_score(binary, proba_pos)

    # Ma tran nham nhieu theo thu tu lop cua bai
    metrics["cm"] = confusion_matrix(y_true, y_pred, labels=CLASSES)
    return metrics


# ---------------------------------------------------------------------------
# Cac baseline
# ---------------------------------------------------------------------------
def baseline_most_frequent(X_train, y_train, X_eval, y_eval, name: str) -> dict:
    """
    Duong co so 1: LUON doan lop nhieu hon.

    Khong dung gi ca, khong hoc gi ca. Chi can dem lop nao nhieu hon.
    """
    model = DummyClassifier(strategy="most_frequent")
    model.fit(X_train, y_train)

    start = time.perf_counter()
    y_pred = model.predict(X_eval)
    duration = time.perf_counter() - start

    dominant = model.classes_[np.argmax(model.class_prior_)]
    metrics = evaluate(y_eval, y_pred, None)
    metrics.update(
        {
            "model": name,
            "train_time_s": 0.0,
            "predict_time_s": duration,
            "n_features": 0,
            "note": f"Luon doan '{dominant}'",
        }
    )
    return metrics


def baseline_stump(X_train, y_train, X_eval, y_eval, name: str = "Baseline: cay depth=1") -> dict:
    """
    Duong co so 2: cay quyet dinh chi MOT NHAN (depth=1).

    Hoc duoc dung thong tin cua mot dac trung:
        "neu Area <= 13000 thi Cammeo, nguoc lai Osmancik"

    Day la cay toi thieu ma mo hinh chinh phai vuot qua.
    Chi mot nhan la cau hoi "mot dac trung co tach duoc hai lop khong?".
    """
    model = DecisionTreeClassifier(max_depth=1, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    start = time.perf_counter()
    y_pred = model.predict(X_eval)
    duration = time.perf_counter() - start

    metrics = evaluate(y_eval, y_pred, positive_proba(model, X_eval))
    metrics.update(
        {
            "model": name,
            "train_time_s": _time_fit(model, X_train, y_train),
            "predict_time_s": duration,
            "n_features": 1,
            "note": "1 nhan phan loai",
        }
    )
    return metrics


def baseline_area_rule(X_train, y_train, X_eval, y_eval, name: str = "Baseline: nguong Area") -> dict:
    """
    Duong co so 3: quy tac nguong tren MOT dac trung.

    Y tuong truc giac: Cammeo la hat LON, Osmancik la hat NHO.
    Xac nhan tu EDA: mean Area Cammeo = 14163, Osmancik = 11550.

    => Quy tac: Area >= nguong -> Cammeo, nguoc lai -> Osmancik.

    QUA TRONG:
    - Thu ca HAI chiều cua quy tac (Area <= T va Area >= T).
      Cach nay tranh nhung gi doc sai huong nhu "Cammeo la hat nho".
    - Nguong chi tinh tren TAP TRAIN, roi ap dung cho tap danh gia.
      Neu tim nguong tren tap danh gia -> ro ri thong tin.
    """
    threshold, best_rule, best_score = best_area_threshold(X_train["Area"], y_train)

    def apply_rule(values: pd.Series) -> np.ndarray:
        if best_rule == ">=":
            return np.where(values >= threshold, "Cammeo", "Osmancik")
        return np.where(values <= threshold, "Cammeo", "Osmancik")

    start = time.perf_counter()
    y_pred = apply_rule(X_eval["Area"])
    duration = time.perf_counter() - start

    metrics = evaluate(y_eval, y_pred, None)
    metrics.update(
        {
            "model": name,
            "train_time_s": 0.0,
            "predict_time_s": duration,
            "n_features": 1,
            "note": f"Area {best_rule} {threshold:.0f} -> Cammeo",
        }
    )
    metrics["train_f1_of_rule"] = best_score
    return metrics


def best_area_threshold(area: pd.Series, y: pd.Series) -> tuple[float, str, float]:
    """
    Tim nguong Area toi uu tren TAP TRAIN, thu ca hai huong quy tac.

    Tra ve (nguong, huong quy tac, F1 dat duoc tren train).

    Ghi chu ve do phuc tap:
        So gia tri Area khac nhau la ~2000. Neu thu het moi cap giua hai
        gia tri lien tiep thi ~4000 vong lap -- cham nhung chay duoc.
        Cach nay chinh xac hon cach dung so ngan cho nhanh.
    """
    values = np.sort(area.unique())
    candidates = [(values[i] + values[i + 1]) / 2 for i in range(len(values) - 1)]

    y_values = y.to_numpy()
    area_values = area.to_numpy()

    best_f1, best_threshold, best_rule = -1.0, float(values[0]), ">="

    for threshold in candidates:
        # Thu ca hai huong: lon hon -> Cammeo, va nho hon -> Cammeo
        for rule, pred in (
            (">=", np.where(area_values >= threshold, "Cammeo", "Osmancik")),
            ("<=", np.where(area_values <= threshold, "Cammeo", "Osmancik")),
        ):
            score = f1_score(y_values, pred, pos_label=POS_LABEL, zero_division=0)
            if score > best_f1:
                best_f1, best_threshold, best_rule = score, threshold, rule

    return float(best_threshold), best_rule, float(best_f1)


def _time_fit(model, X, y) -> float:
    """Do thoi gian train. Tinh lai vi co the goi nhieu lan."""
    start = time.perf_counter()
    model.fit(X, y)
    return time.perf_counter() - start


# ---------------------------------------------------------------------------
def main() -> int:
    """
    Chay 3 baseline tren TAP VALIDATION (khong dung tap test).
    """
    from src.split import split_data
    from src.data import load_raw

    print("=" * 68)
    print("BASELINE - DUONG CO SO DE CHUNG MINH MO HINH CHIN TOT HON")
    print("=" * 68)
    print()
    print("DANH GIA TREN TAP VALIDATION (khong dung tap test)")
    print()

    df = load_raw()
    train_df, valid_df, test_df = split_data(df)

    X_train, y_train = xy(train_df)
    X_valid, y_valid = xy(valid_df)

    results = [
        baseline_most_frequent(X_train, y_train, X_valid, y_valid, "Baseline 1: lop pho bien"),
        baseline_stump(X_train, y_train, X_valid, y_valid),
        baseline_area_rule(X_train, y_train, X_valid, y_valid),
    ]

    print(f"{'Mo hinh':<34} {'Acc':>7} {'F1':>7} {'ROC-AUC':>9} {'Ghi chu'}")
    print("-" * 78)
    for r in results:
        auc = r.get("roc_auc")
        auc_str = f"{auc:>9.4f}" if auc is not None else f"{'n/a':>9}"
        print(
            f"{r['model']:<34} {r['accuracy']:>7.4f} {r['f1']:>7.4f} "
            f"{auc_str}  {r['note']}"
        )

    print()
    print("=" * 68)
    print("MA TRAN NHAM NHIEU CUA TUNG BASELINE")
    print("=" * 68)
    for r in results:
        print(f"\n[{r['model']}]  {r['note']}")
        print(_print_confusion(r["cm"]))

    # Quay tac cua cay depth=1
    print()
    print("=" * 68)
    print("QUY TAC CAY BASELINE (depth=1) - XEM NO HOC DUOC GI")
    print("=" * 68)
    stump = DecisionTreeClassifier(max_depth=1, random_state=RANDOM_STATE)
    stump.fit(X_train, y_train)
    print(export_text(stump, feature_names=FEATURES, decimals=2))

    print("NHAN XET:")
    best = max(results, key=lambda r: r["f1"])
    print(f"  Baseline tot nhat: {best['model']} voi F1 = {best['f1']:.4f}")
    print()
    print("  Day la MOC de so sanh. Mo hinh chinh phai BE HON day,")
    print("  va phai chung minh duoc bang thi moi la that su tot.")
    print()
    print("  Luu y baseline 1 chi dat ~0.5728 accuracy = ty le lop da so.")
    print("  => Neu mo hinh chinh dat 0.99, nghia la no that su hoc duoc")
    print("     nhieu hon muc ngu nhien.")
    print()

    # Luu bang ket qua
    reports = Path(__file__).resolve().parent.parent / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    flat = []
    for r in results:
        flat.append(
            {
                k: v
                for k, v in r.items()
                if k != "cm"
            }
        )
    pd.DataFrame(flat).to_csv(reports / "baseline_results.csv", index=False, encoding="utf-8")
    print(f"  Da luu: reports/baseline_results.csv")
    return 0


def _print_confusion(cm: np.ndarray) -> str:
    """In ma tran nham nhieu de doc kiem tra nhanh."""
    lines = ["              duoi Cammeo  duoi Osmancik",
             "that ra Cammeo        {:>6}          {:>6}",
             "that ra Osmancik      {:>6}          {:>6}",
             "                      (TN)          (FP)",
             "                                     (FN)          (TP)"]
    tn, fp = cm[0]
    fn, tp = cm[1]
    return "\n".join(
        [
            "              duoi Cammeo  duoi Osmancik",
            f"that ra Cammeo {tn:>14} {fp:>15}",
            f"that ra Osmancik {fn:>12} {tp:>16}",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
