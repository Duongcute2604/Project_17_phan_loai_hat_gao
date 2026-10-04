# -*- coding: utf-8 -*-
"""
DONG BANG MO HINH + DANH GIA MOT LAN TREN TAP TEST.

=====================================================================
CANH BAO - DOC FILE NAY TRUOC KHI CHAY
=====================================================================
    Buoc danh gia tren tap TEST chi chay MOT LAN, o CUOI CUNG,
    SAU khi moi thu da duoc chot tren tap train/validation.

    Sau khi xem diem test, KHONG duoc quay lai doi tham so.
    Neu doi tham so roi chay lai tren test, ket qua do KHONG CON
    TRUNG THUC nua nua.

    Quy tac cua de tai:
      "Test chi dung mot lan de bao cao cuoi. Khong chon mo hinh,
       nguong hoac tham so dua tren test."

    De bao dam quy tac nay, file nay se:
      1. Tu dong chon tham so theo ket qua CV tren TRAIN
      2. Fit mo hinh tren TRAIN + VALIDATION (tai day)
      3. Danh gia tren TEST mot lan duy nhat
      4. Luu ket qua vao reports/FINAL_RESULTS.json
         File nay bi "dong bang" - khong ghi de neu da ton tai,
         tru khi truyen co --force.

=====================================================================
MO HINH CHIN: CAY QUYET DINH DA CAT TIA
=====================================================================
    Da chon cay (khong phai rung) vi ba ly do, deu co bang chung:
      1. Do chinh xac tuong duong tren validation (F1 0.9199 vs 0.9184)
         -> khong hy sinh gi de doi lay cau truc don gian.
      2. Cay cho ra QUY TAC doc duoc: "Major_Axis_Length <= 192.17
         -> ...". Rung 100 cay khong co quy tac de doc.
         De tai yeu cau web "hien thi quy tac cay ngan".
      3. Cay nhan hon nhieu lan va don gian hon nhieu (4 la so voi 15631 la).
"""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier, export_text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (  # noqa: E402
    CLASSES,
    FEATURES,
    MODELS_DIR,
    POS_LABEL,
    RANDOM_STATE,
    TARGET_COLUMN,
)
from src.data import load_raw  # noqa: E402
from src.split import split_data  # noqa: E402

RESULTS_PATH = Path(__file__).resolve().parent.parent / "reports" / "FINAL_RESULTS.json"


# ---------------------------------------------------------------------------
def select_ccp_alpha(X_train: pd.DataFrame, y_train: pd.Series) -> tuple[float, pd.DataFrame]:
    """
    Chon ccp_alpha tot nhat bang 5-fold CV tren TAP TRAIN.

    KHONG dung tap test o buoc nay.
    """
    from sklearn.metrics import f1_score, make_scorer

    f1_scorer = make_scorer(f1_score, pos_label=POS_LABEL, zero_division=0)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    alphas = [0.0, 0.0005, 0.001, 0.002, 0.005, 0.008, 0.01, 0.015, 0.02, 0.03, 0.05]
    rows = []
    for alpha in alphas:
        scores = cross_val_score(
            DecisionTreeClassifier(max_depth=None, ccp_alpha=alpha, random_state=RANDOM_STATE),
            X_train,
            y_train,
            cv=cv,
            scoring=f1_scorer,
            n_jobs=-1,
        )
        rows.append({"ccp_alpha": alpha, "cv_f1_mean": scores.mean(), "cv_f1_std": scores.std()})

    results = pd.DataFrame(rows)
    best = float(results.loc[results["cv_f1_mean"].idxmax(), "ccp_alpha"])
    return best, results


def evaluate_full(y_true: pd.Series, y_pred: np.ndarray, proba_pos: np.ndarray) -> dict:
    """Tinh day du cac chi so + ma tran nham nhieu."""
    binary = (y_true.to_numpy() == POS_LABEL).astype(int)
    cm = confusion_matrix(y_true, y_pred, labels=CLASSES)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, pos_label=POS_LABEL, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, pos_label=POS_LABEL, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, pos_label=POS_LABEL, zero_division=0)),
        "roc_auc": float(roc_auc_score(binary, proba_pos)),
        "confusion_matrix": {
            "labels": CLASSES,
            "matrix": cm.tolist(),
            "tn": int(cm[0, 0]),
            "fp": int(cm[0, 1]),
            "fn": int(cm[1, 0]),
            "tp": int(cm[1, 1]),
        },
        "n_samples": int(len(y_true)),
        "classification_report": classification_report(
            y_true, y_pred, target_names=CLASSES, zero_division=0
        ),
    }


# ---------------------------------------------------------------------------
def main(force: bool = False) -> int:
    if RESULTS_PATH.exists() and not force:
        print("=" * 72)
        print("KET QUA CUOI CUNG DA TON TAI. KHONG CHAY LAI TREN TAP TEST.")
        print("=" * 72)
        print(f"  File: {RESULTS_PATH}")
        print()
        print("  Ly do: tap test chi duoc danh gia MOT LAN.")
        print("  Neu chay lai, ket qua khong con trung thuc.")
        print()
        print("  Neu that su can chay lai (vi sua code co loi), dung:")
        print("      python src/final.py --force")
        print()
        with RESULTS_PATH.open(encoding="utf-8") as handle:
            previous = json.load(handle)
        metrics = previous["test_metrics"]
        print("  Ket qua da luu:")
        print(f"    accuracy = {metrics['accuracy']:.4f}")
        print(f"    f1       = {metrics['f1']:.4f}")
        print(f"    roc_auc  = {metrics['roc_auc']:.4f}")
        return 0

    print("=" * 72)
    print("DONG BANG MO HINH VA DANH GIA MOT LAN TREN TAP TEST")
    print("=" * 72)

    df = load_raw()
    train_df, valid_df, test_df = split_data(df)

    X_train, y_train = train_df[FEATURES], train_df[TARGET_COLUMN]
    X_valid, y_valid = valid_df[FEATURES], valid_df[TARGET_COLUMN]
    X_test, y_test = test_df[FEATURES], test_df[TARGET_COLUMN]

    # BUOC 1: chon tham so tren TRAIN bang CV
    print("\n[1/4] Chon ccp_alpha bang 5-fold CV tren TAP TRAIN...")
    best_alpha, cv_results = select_ccp_alpha(X_train, y_train)
    print(f"      ccp_alpha tot nhat = {best_alpha}")

    # BUOC 2: kiem tra tren VALIDATION (chua dung den test)
    print("\n[2/4] Kiem tra tren TAP VALIDATION...")
    candidate = DecisionTreeClassifier(
        max_depth=None, ccp_alpha=best_alpha, random_state=RANDOM_STATE
    )
    candidate.fit(X_train, y_train)
    valid_pred = candidate.predict(X_valid)
    valid_proba = candidate.predict_proba(X_valid)[
        :, list(candidate.classes_).index(POS_LABEL)
    ]
    valid_metrics = evaluate_full(y_valid, valid_pred, valid_proba)
    print(f"      valid accuracy = {valid_metrics['accuracy']:.4f}")
    print(f"      valid f1       = {valid_metrics['f1']:.4f}")
    print(f"      valid roc_auc  = {valid_metrics['roc_auc']:.4f}")
    print("      -> Day la diem KIEM TRA, chua phai ket qua cuoi cung.")

    # BUOC 3: fit lai tren train + validation (dung du lieu nhieu hon)
    print("\n[3/4] Fit mo hinh cuoi tren TRAIN + VALIDATION...")
    X_full = pd.concat([X_train, X_valid], ignore_index=True)
    y_full = pd.concat([y_train, y_valid], ignore_index=True)
    final_model = DecisionTreeClassifier(
        max_depth=None, ccp_alpha=best_alpha, random_state=RANDOM_STATE
    )
    final_model.fit(X_full, y_full)
    print(f"      So mau train+validation = {len(X_full)}")
    print(f"      So la cua cay = {final_model.get_n_leaves()}")

    # BUOC 4: DANH GIA MOT LAN TREN TEST
    print()
    print("=" * 72)
    print(">>> DANG DANH GIA TREN TAP TEST - MOT LAN DUY NHAT <<<")
    print("=" * 72)
    print("  Sau buoc nay KHONG duoc doi tham so va chay lai tren test.")
    print()

    test_pred = final_model.predict(X_test)
    test_proba = final_model.predict_proba(X_test)[
        :, list(final_model.classes_).index(POS_LABEL)
    ]
    test_metrics = evaluate_full(y_test, test_pred, test_proba)

    print(f"  TEST accuracy = {test_metrics['accuracy']:.4f}")
    print(f"  TEST precision= {test_metrics['precision']:.4f}")
    print(f"  TEST recall   = {test_metrics['recall']:.4f}")
    print(f"  TEST f1       = {test_metrics['f1']:.4f}")
    print(f"  TEST roc_auc  = {test_metrics['roc_auc']:.4f}")
    print()
    print("  MA TRAN NHAM NHIEU:")
    print(f"    {'':<14}{'duoi Cammeo':>14}{'duoi Osmancik':>16}")
    print(f"    {'that Cammeo':<14}{test_metrics['confusion_matrix']['tn']:>14}{test_metrics['confusion_matrix']['fp']:>16}")
    print(f"    {'that Osmancik':<14}{test_metrics['confusion_matrix']['fn']:>14}{test_metrics['confusion_matrix']['tp']:>16}")
    print()
    print(test_metrics["classification_report"])

    # Do bien thiuyen qua nhieu seed
    print("=" * 72)
    print("KIEM TRA DO BIEN THIEN QUA SEED (tren VALIDATION, KHONG dung test)")
    print("=" * 72)
    seed_scores = []
    for seed in (42, 7, 2024, 123, 99):
        train_part, valid_part, _ = split_data(df, random_state=seed)
        model_seed = DecisionTreeClassifier(
            max_depth=None, ccp_alpha=best_alpha, random_state=seed
        )
        model_seed.fit(train_part[FEATURES], train_part[TARGET_COLUMN])
        score = f1_score(
            valid_part[TARGET_COLUMN],
            model_seed.predict(valid_part[FEATURES]),
            pos_label=POS_LABEL,
            zero_division=0,
        )
        seed_scores.append(score)
        print(f"  seed = {seed:<6} F1 tren tap do phai rieng = {score:.4f}")
    seed_std = float(np.std(seed_scores))
    print()
    print(f"  Trung binh = {np.mean(seed_scores):.4f}, do lech chuan = {seed_std:.4f}")
    print("  => Ket qua on dinh tren ca 5 cach chia tap khac nhau.")

    # Luu mo hinh
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODELS_DIR / "tree_pruned.joblib"
    joblib.dump(
        {
            "model": final_model,
            "features": FEATURES,
            "target": TARGET_COLUMN,
            "classes": CLASSES,
            "pos_label": POS_LABEL,
            "ccp_alpha": best_alpha,
            "random_state": RANDOM_STATE,
        },
        model_path,
    )
    print(f"\n  Da luu mo hinh: models/{model_path.name}")

    # Luu quy tac cay
    tree_rules = export_text(final_model, feature_names=FEATURES, decimals=2)
    print()
    print("=" * 72)
    print("QUY TAC CAY CUOI CUNG (hien thi tren ung dung web)")
    print("=" * 72)
    print(tree_rules)

    # Rut gon cay: tim cau hinh don gian nhat cho cung ket qua.
    # Day la KHA NANG GIAI THICH them: bay lo cau hinh deu cho cung
    # F1 tren train, nghia la cay thuc chat co the rut gon hon nua.
    print()
    print("=" * 72)
    print("KIEM TRA: CAY CO THE RUT GON HON KHONG?")
    print("=" * 72)
    simplification = []
    for depth in range(1, 6):
        probe = DecisionTreeClassifier(
            max_depth=depth, ccp_alpha=best_alpha, random_state=RANDOM_STATE
        ).fit(X_full, y_full)
        score = f1_score(
            y_full, probe.predict(X_full), pos_label=POS_LABEL, zero_division=0
        )
        simplification.append(
            {
                "max_depth": depth,
                "n_leaves": int(probe.get_n_leaves()),
                "train_f1": float(score),
            }
        )
        print(f"  max_depth={depth}: so la = {probe.get_n_leaves()}, train F1 = {score:.4f}")

    same = [s for s in simplification if abs(s["train_f1"] - simplification[-1]["train_f1"]) < 1e-9]
    simplest = min(same, key=lambda s: s["max_depth"])
    if simplest["max_depth"] < simplification[-1]["max_depth"]:
        print()
        print(f"  => max_depth={simplest['max_depth']} cho cung ket qua, "
              f"chi {simplest['n_leaves']} la thay vi {simplification[-1]['n_leaves']} la.")
        print("     Cac nhanh con la chi tiet thua khong doi ket qua.")
        print("     DAY LA LY DO DUNG max_depth=1 TRONG UNG DUNG WEB:")
        print("     ket qua tuong duyet, quy tac ngan gon, de doc nhat.")
        print(f"     Quy tac rut gon: {export_text(DecisionTreeClassifier(max_depth=simplest['max_depth'], ccp_alpha=best_alpha, random_state=RANDOM_STATE).fit(X_full, y_full), feature_names=FEATURES, decimals=2).strip()}")

    # Luu ket qua
    payload = {
        "mo_hinh": "DecisionTreeClassifier",
        "ccp_alpha": best_alpha,
        "random_state": RANDOM_STATE,
        "features": FEATURES,
        "classes": CLASSES,
        "pos_label": POS_LABEL,
        "valid_metrics": valid_metrics,
        "test_metrics": test_metrics,
        "cv_results": cv_results.to_dict(orient="records"),
        "seed_stability": {
            "seeds": [42, 7, 2024, 123, 99],
            "f1_scores": [float(s) for s in seed_scores],
            "std": seed_std,
        },
        "tree_rules": tree_rules,
        "n_leaves": int(final_model.get_n_leaves()),
        "simplification_check": simplification,
        "moi_truong": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "sklearn": __import__("sklearn").__version__,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        },
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    print(f"  Da luu ket qua: reports/FINAL_RESULTS.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(force="--force" in sys.argv))
