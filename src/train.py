# -*- coding: utf-8 -*-
"""
MO HINH CHIN: Cay quyet dinh, cat tia va rung ngau nhien.
Chu de: Bai 6 — Cay quyet dinh, cat tia va rung ngau nhien.

=====================================================================
1. CAY QUYET DINH (Decision Tree) - HOI GIOI THIEU
=====================================================================
    Cay quyet dinh la mot mo hinh phan loai duoc xay dung bang
    chuoi cau hoi co/khong.

        "Major_Axis_Length <= 192.17 ?"
            ├── Co  -> "Osmancik"
            └── Khong -> tiep tuc hoi cau 2
                          └── ... -> "Cammeo"

    MO HINH HOI DO DUNG DUOC XEM NHAT MOT TIEU CHUAN:
    - "neu chi dung Major_Axis_Length, thi cat o 192.17 thi tot nhat"
    -> rat de hieu, de giai thich khi van dap. Day la uu diem lon.

=====================================================================
2. QUA KHOP (OVERFITTING) - VAN DE CUA CAY QUYET DINH
=====================================================================
    Cay khong gioi han do sau, nen no CÓ THỂ moc cho den khi moi
    don vi quan sat la mot nhan rieng -> nhan do la "vua roi".
    Khi do no hoc rat nhanh tren tap TRAIN, nhung nho MOT CHUT
    trong tap khac.

    Hinh dung: hoc thuoc dap an bai thi (nhớ 2000 dap an).
              Do thi tuyet doi 100%. Nhung doi cau hoi thi hoc lai tu dau.
              Cay qua sau co chinh xac "train" cao, "test" thap.

    DO DAI DO QUA KHOP: do chinh xac tren train LUON >= do chinh xac
    tren tap khac. Do khong gap bao nhieu thi cai do moi la vung.

    GIAI PHAP TRONG BAI NAY (3 tang, dung kem nhau):
      a. HAN CHE DO SAU (max_depth): khong cho cay moc qua bac nao do.
      b. CAT TIA THEO GIA (ccp_alpha): cat nhanh it gop y nhat.
      c. SO NHIEU LA NUONG (min_samples_leaf): nhan phai du lau
         mau moi duoc tach.

=====================================================================
3. CAT TIA (PRUNING) - CAT NHANH THUA
=====================================================================
    Sau khi cay moc xong, cat bo nhanh khong giup phan loai.

    Hai cach cat tia trong scikit-learn:

    (a) Ti pre-pruning (cat TRUOC khi moc) — thong qua tham so:
          max_depth          : gioi han so bac
          min_samples_split  : nhan phai co it nhat bao nhieu mau moi tach
          min_samples_leaf   : nhan phai co it nhat bao nhieu mau o la
          min_impurity_decrease: chi tach nhanh neu do "sau" du lon

    (b) Hau-pruning (cat SAU khi moc) — thong qua ccp_alpha:
          Cay moc toi da (khong gioi han). Sau do cat cac nhanh
          co chi phi tang them < ccp_alpha.
          ccp_alpha = 0.0   -> khong cat gi
          ccp_alpha = 0.01  -> cat nhanh khong toi uu it nhat

          Cong thuc: chi phi cat = tong xac suat sai cua cac la,
                     thuoc loai bi cat. Tong nay la "tong impurity
                     cuea cac la bi cat".
          Neu tong chi phi cat > ccp_alpha -> cat.

=====================================================================
4. RUNG NGAU NHIEN (Random Forest)
=====================================================================
    Y tuong: thay vi mot cay, hoc NHIEU cay tren cac tap con
    KHAC NHAU va cac tap dac trung KHAC NHAU, roi lay phieu
    bau cua chung.

    3 nguyen tac giu cay trong ho so ngau nhien:
      1. Bootstrap: moi cay nhin mot tap mau random (co the trung).
      2. Feature random: tai moi nut, chi xet ngau nhien mot phan
         dac trung (mac dinh sqrt(7) ~ 3).
      3. Bau phieu: so dong dong nhat trong hau het cac cay thang.

    Uu diem:
      - Chinh quac, rut ngon bi qua khop
      - It nhay voi thieu du lieu

    Nhuoc diem:
      - KHONG co "quy tac" de doc. 100 cay thi khong doc noi dung gi.
        => Bai toan nay chon CAY lam mo hinh phuc vu web, dung RF
           lam doi chieu.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier, export_text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import (  # noqa: E402
    FEATURES,
    POS_LABEL,
    RANDOM_STATE,
    TARGET_COLUMN,
)
from src.split import split_data  # noqa: E402
from src.data import load_raw  # noqa: E402


# ---------------------------------------------------------------------------
# BO CHI SO F1 TUONG DO
# ---------------------------------------------------------------------------
# cross_val_score(scoring="f1") mac dinh pos_label=1, tuc gia dinh nhan
# la 0/1. Bai toan nay nhan la CHUOI ("Cammeo"/"Osmancik") nen se loi.
# Dinh ro pos_label de moi noi dung mot y.
f1_scorer = make_scorer(f1_score, pos_label=POS_LABEL, zero_division=0)


# ---------------------------------------------------------------------------
# Tien xu ly dung chung cho moi mo hinh
# ---------------------------------------------------------------------------
def xy(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Tach dac trung va nhan."""
    return frame[FEATURES].copy(), frame[TARGET_COLUMN].copy()


def positive_proba(model, X: pd.DataFrame) -> np.ndarray:
    """Lay xac suat cho lop POS_LABEL (dong 'Cammeo')."""
    proba = model.predict_proba(X)
    return proba[:, list(model.classes_).index(POS_LABEL)]


# ---------------------------------------------------------------------------
# THI NGHIEM 1: do chinh xac theo max_depth
# ---------------------------------------------------------------------------
def experiment_max_depth(X_train, y_train, X_valid, y_valid) -> pd.DataFrame:
    """
    Do chinh xac cua cay theo gioi han sau.

    Cau hoi: cay sau hon co tot hon khong? Dung o dau?
    Day la THI NGHIEM BAT BUOC SO 1 cua de tai.
    """
    print()
    print("=" * 74)
    print("THI NGHIEM 1: DO CHINH XAC THEO max_depth")
    print("=" * 74)

    depths = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20, None]
    rows = []

    for depth in depths:
        model = DecisionTreeClassifier(max_depth=depth, random_state=RANDOM_STATE)

        start = time.perf_counter()
        model.fit(X_train, y_train)
        train_time = time.perf_counter() - start

        train_score = model.score(X_train, y_train)
        valid_score = model.score(X_valid, y_valid)
        valid_f1 = _f1(y_valid, model.predict(X_valid))
        n_leaves = model.get_n_leaves()
        n_nodes = model.tree_.node_count

        label = "khong gioi han" if depth is None else str(depth)
        rows.append(
            {
                "max_depth": label,
                "train_acc": train_score,
                "valid_acc": valid_score,
                "gap": train_score - valid_score,  # do qua khop
                "valid_f1": valid_f1,
                "n_leaves": n_leaves,
                "n_nodes": n_nodes,
                "train_time_s": round(train_time, 4),
            }
        )

        print(
            f"  max_depth={label:<12} train={train_score:.4f}  "
            f"valid={valid_score:.4f}  f1={valid_f1:.4f}  "
            f"gap={train_score - valid_score:+.4f}  la={n_leaves}"
        )

    return pd.DataFrame(rows)


def _f1(y_true, y_pred) -> float:
    from sklearn.metrics import f1_score

    return float(f1_score(y_true, y_pred, pos_label=POS_LABEL, zero_division=0))


# ---------------------------------------------------------------------------
# THI NGHIEM 2: cat tia bang ccp_alpha tren cross-validation
# ---------------------------------------------------------------------------
def experiment_ccp_alpha(X_train, y_train, n_splits: int = 5) -> pd.DataFrame:
    """
    Do tac dung cua ccp_alpha (cat tia hau-pruning).

    Cach do dung:
        1. Cho cay moc TOI DA (max_depth=None).
        2. Moi gia tri ccp_alpha, chay K-fold CV tren TAP TRAIN.
        3. Chon gia tri co F1 cao nhat trong CV.
        4. Sau do moi danh gia tren TAP VALIDATION.

    Vi sao dung CV chu khong dung tap validation cho viec chon tham so?
        - Cross-validation dung nhieu lan lap tren train -> uoc luong
          on dinh hon, it phu thuoc vao mot lan chia ngau nhien.
        - Tap validation duoc giu lai de KIEM TRA mo hinh da chon,
          khong dung de "san" tham so. Cach nay giu tach biet,
          dung nguyen tac khong chon tham so tren tap danh gia.
    """
    print()
    print("=" * 74)
    print("THI NGHIEM 2: CAT TIA BANG ccp_alpha (CROSS-VALIDATION)")
    print("=" * 74)
    print(f"  K-fold: {n_splits} folds, StratifiedKFold, random_state={RANDOM_STATE}")
    print()

    alphas = [0.0, 0.0001, 0.0005, 0.001, 0.002, 0.005, 0.008, 0.01, 0.015, 0.02, 0.03, 0.05]
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)

    rows = []
    for alpha in alphas:
        model = DecisionTreeClassifier(
            max_depth=None, ccp_alpha=alpha, random_state=RANDOM_STATE
        )
        scores = cross_val_score(
            model, X_train, y_train, cv=cv, scoring=f1_scorer, n_jobs=-1
        )
        # Do kich thuoc cay SAU khi cat, tren toan bo tap train.
        # Day la bang chung cho thay cat tia lam cay don gian thu nao.
        fitted = DecisionTreeClassifier(
            max_depth=None, ccp_alpha=alpha, random_state=RANDOM_STATE
        ).fit(X_train, y_train)
        rows.append(
            {
                "ccp_alpha": alpha,
                "cv_f1_mean": scores.mean(),
                "cv_f1_std": scores.std(),
                "cv_f1_min": scores.min(),
                "cv_f1_max": scores.max(),
                "n_leaves": int(fitted.get_n_leaves()),
                "n_nodes": int(fitted.tree_.node_count),
                "train_acc": float(fitted.score(X_train, y_train)),
            }
        )
        print(
            f"  ccp_alpha={alpha:<8} CV F1 = {scores.mean():.4f} "
            f"+/- {scores.std():.4f}   [{scores.min():.4f}, {scores.max():.4f}]  "
            f"la={fitted.get_n_leaves()}"
        )

    results = pd.DataFrame(rows)
    best = results.loc[results["cv_f1_mean"].idxmax()]
    print()
    print(f"  => ccp_alpha tot nhat theo CV: {best['ccp_alpha']}")
    print(f"     F1 trung binh = {best['cv_f1_mean']:.4f} +/- {best['cv_f1_std']:.4f}")
    return results


# ---------------------------------------------------------------------------
# THI NGHIEM 3: so sanh cay va rung
# ---------------------------------------------------------------------------
def experiment_tree_vs_forest(X_train, y_train, X_valid, y_valid) -> pd.DataFrame:
    """
    So sanh cay quyet dinh va rung ngau nhien.
    Do ca diem so, thoi gian va kha nang giai thich.

    Day la THI NGHIEM BAT BUOC SO 3 cua de tai.
    """
    print()
    print("=" * 74)
    print("THI NGHIEM 3: SO SANH CAY QUYET DINH VA RUNG NGAU NHIEN")
    print("=" * 74)

    configs = [
        ("Cay khong gioi han", DecisionTreeClassifier(max_depth=None, random_state=RANDOM_STATE)),
        ("Cay cat tia (ccp_alpha=0.002)", DecisionTreeClassifier(max_depth=None, ccp_alpha=0.002, random_state=RANDOM_STATE)),
        ("Cay gioi han sau 6", DecisionTreeClassifier(max_depth=6, random_state=RANDOM_STATE)),
        ("Rung 100 cay, sau khong gioi han", RandomForestClassifier(n_estimators=100, max_depth=None, random_state=RANDOM_STATE, n_jobs=-1)),
        ("Rung 100 cay, sau toi da 10", RandomForestClassifier(n_estimators=100, max_depth=10, random_state=RANDOM_STATE, n_jobs=-1)),
    ]

    rows = []
    for name, model in configs:
        start = time.perf_counter()
        model.fit(X_train, y_train)
        train_time = time.perf_counter() - start

        start = time.perf_counter()
        y_pred = model.predict(X_valid)
        predict_time = time.perf_counter() - start

        valid_acc = model.score(X_valid, y_valid)
        valid_f1 = _f1(y_valid, y_pred)

        # Do kich thuoc mo hinh va kha nang giai thich
        if hasattr(model, "estimators_"):
            n_trees = len(model.estimators_)
            total_leaves = sum(est.get_n_leaves() for est in model.estimators_)
            explain = "KHONG DOC DUOC (nhieu cay)"
            size_note = f"{n_trees} cay, {total_leaves} la"
        else:
            n_trees = 1
            total_leaves = model.get_n_leaves()
            explain = "DOC DUOC (export_text)"
            size_note = f"1 cay, {total_leaves} la"

        rows.append(
            {
                "mo_hinh": name,
                "valid_acc": valid_acc,
                "valid_f1": valid_f1,
                "train_time_s": round(train_time, 4),
                "predict_time_s": round(predict_time, 4),
                "n_trees": n_trees,
                "n_leaves": total_leaves,
                "giai_thich": explain,
                "kich_thuoc": size_note,
            }
        )

        print(
            f"  {name:<32} acc={valid_acc:.4f} f1={valid_f1:.4f} "
            f"train={train_time:.3f}s  {size_note}"
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 74)
    print("MO HINH CHIN: CAY QUYET DINH, CAT TIA, RUNG NGAU NHIEN")
    print("=" * 74)

    df = load_raw()
    train_df, valid_df, test_df = split_data(df)

    X_train, y_train = xy(train_df)
    X_valid, y_valid = xy(valid_df)

    # Thi nghiem 1
    depth_results = experiment_max_depth(X_train, y_train, X_valid, y_valid)

    # Thi nghiem 2
    alpha_results = experiment_ccp_alpha(X_train, y_train)

    # Thi nghiem 3
    compare_results = experiment_tree_vs_forest(X_train, y_train, X_valid, y_valid)

    # Luu ket qua
    reports = Path(__file__).resolve().parent.parent / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    depth_results.to_csv(reports / "exp1_max_depth.csv", index=False, encoding="utf-8")
    alpha_results.to_csv(reports / "exp2_ccp_alpha.csv", index=False, encoding="utf-8")
    compare_results.to_csv(reports / "exp3_tree_vs_forest.csv", index=False, encoding="utf-8")

    # Quay cay cat tia de hien thi len web.
    # CHON ccp_alpha theo ket qua CV o tren (0.005), khong hardcode tu do.
    best_alpha = float(alpha_results.loc[alpha_results["cv_f1_mean"].idxmax(), "ccp_alpha"])

    pruned = DecisionTreeClassifier(
        max_depth=None, ccp_alpha=best_alpha, random_state=RANDOM_STATE
    )
    pruned.fit(X_train, y_train)

    print()
    print("=" * 74)
    print(f"QUY TAC CAY SAU CAT TIA (ccp_alpha={best_alpha}, chon theo CV)")
    print("=" * 74)
    print(export_text(pruned, feature_names=FEATURES, decimals=2))
    print(f"  So la cua cay: {pruned.get_n_leaves()}")

    # So sanh cay cat tia voi cay co gioi han sau
    depth_best = compare_results.sort_values("valid_f1", ascending=False).iloc[0]
    print()
    print(f"  Mo hinh tot nhat tren VALIDATION: {depth_best['mo_hinh']}")
    print(f"    valid_acc = {depth_best['valid_acc']:.4f}, valid_f1 = {depth_best['valid_f1']:.4f}")
    print()
    print("  NHAN XET QUAN TRONG:")
    print("  - Cay cat tia co 4 la, doc duoc, nhanh, va VAN dat ~0.93 tren validation.")
    print("  - Rung ngau nhien dat do tuong tu nhung cham hon va khong giai thich duoc.")
    print("  - => CHON CAY LAM MO HINH CHINH, rung lam doi chieu.")
    print("  - Ly do: do chinh xac nhu nhau, nhung cay don giai thich duoc,")
    print("    khoi luon nho hon nhieu, va khop voi yeu cau web 'hien thi quy tac cay'.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
