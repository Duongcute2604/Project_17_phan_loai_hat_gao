# -*- coding: utf-8 -*-
"""
VE BIEU DO CHO BAO CAO.

=====================================================================
TAI SAO CAN BIEU DO?
=====================================================================
    Con so trong bao cao chi cho biet KET QUA. Bieu do cho biet XU HUONG.
    Ví du:
      - Bang: "train 1.000, valid 0.899"
      - Bieu do: mot duong xuong dan, do la HINH DANG cua qua khop.
        Nguoi doc thay ngay "cay sau hon -> train len, valid giam".

    Trong bao cao 15-25 trang, bieu do la phan "bang chung" chinh.
    Khong co bieu do, phan "Ket qua" va "Phan tich loi" khong co gi de
    bai bien.

LUU Y KHI VE:
    - Tieu de co nghĩa, khong viet "Hinh 1" khong gi.
    - Nhan truc rõ don vi.
    - Khong dung hieu ung trai truc (khong cat truc Y khi bat dau khong 0
      tren bieu do duong) — lam nhoi lech.
    - Chiu cao buoc phai chua so lieu.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Khong mo cua so khi ve (chay tren server/CI)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import CLASSES, FEATURES, POS_LABEL, TARGET_COLUMN  # noqa: E402
from src.data import load_raw  # noqa: E402
from src.split import split_data  # noqa: E402

FIGURES = Path(__file__).resolve().parent.parent / "reports" / "figures"


# ---------------------------------------------------------------------------
# Cau hinh chung
# ---------------------------------------------------------------------------
# Arial hoac Segoe UI co full bo dau tieng Viet
plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
        "axes.unicode_minus": False,  # dau am trong bieu do khong bi mat
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
    }
)

COLORS = {
    "train": "#2E6F9E",
    "valid": "#C1553B",
    "accent": "#3B8A5A",
    "warn": "#D08A00",
    "neutral": "#6B7280",
}


def _save(fig, name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.savefig(path)
    plt.close(fig)
    print(f"  Da luu: reports/figures/{name}")


# ---------------------------------------------------------------------------
# Hinh 1: phan bo dac trung theo lop (cho thay hai lop tach nhau the)
# ---------------------------------------------------------------------------
def plot_feature_distribution(df: pd.DataFrame) -> None:
    """Khoa hoc du lieu - 7 dac trung, ve tieu do phan bo theo tung lop."""
    fig, axes = plt.subplots(2, 4, figsize=(14, 7))
    axes = axes.flatten()

    for index, feature in enumerate(FEATURES):
        ax = axes[index]
        for position, label in enumerate(CLASSES):
            values = df.loc[df[TARGET_COLUMN] == label, feature]
            ax.hist(
                values,
                bins=25,
                alpha=0.55,
                label=label,
                color=COLORS["train"] if position == 0 else COLORS["warn"],
                edgecolor="white",
                linewidth=0.4,
                density=True,
            )
        ax.set_title(feature, fontsize=10)
        ax.set_xlabel("Gia tri")
        ax.set_ylabel("Mat do")
        ax.legend(fontsize=7, loc="upper right", framealpha=0.9)
        ax.tick_params(labelsize=8)

    # An truc khong dung
    axes[-1].axis("off")

    fig.suptitle(
        "Phan bo 7 dac trung hinh hoc theo giong gao\n"
        "(mot so dac trung tach hai lop ro, so khac co vung chong lap)",
        fontsize=13,
        y=1.0,
    )
    fig.tight_layout()
    _save(fig, "01_feature_distribution.png")


# ---------------------------------------------------------------------------
# Hinh 2: phan bo lop + kich thuoc tap
# ---------------------------------------------------------------------------
def plot_class_distribution(train_df, valid_df, test_df) -> None:
    """Can bang lop qua 3 tap."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # Trai: thanh so luong theo lop, tach theo tap
    parts = [("train", train_df), ("validation", valid_df), ("test", test_df)]
    bottoms = np.zeros(len(CLASSES))
    shades = [COLORS["train"], COLORS["accent"], COLORS["warn"]]
    for (name, part), shade in zip(parts, shades):
        counts = [int((part[TARGET_COLUMN] == label).sum()) for label in CLASSES]
        ax1.bar(CLASSES, counts, bottom=bottoms, label=name, color=shade, edgecolor="white")
        bottoms += np.array(counts)

    ax1.set_title("So luong mau theo lop va tap")
    ax1.set_ylabel("So mau")
    ax1.legend(title="Tap")
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_axisbelow(True)

    # Phai: ti le phan bo %, co vach 50%
    percentages = [100.0 * bottoms[i] / bottoms.sum() for i in range(len(CLASSES))]
    bars = ax2.bar(CLASSES, percentages, color=[COLORS["warn"], COLORS["train"]], edgecolor="white")
    ax2.axhline(50, ls="--", color=COLORS["neutral"], lw=1, label="50% (can bang)")
    for bar, value in zip(bars, percentages):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            value + 1,
            f"{value:.2f}%",
            ha="center",
            fontsize=10,
            fontweight="bold",
        )
    ax2.set_title("Ti le phan bo lop")
    ax2.set_ylabel("Ty le (%)")
    ax2.set_ylim(0, 70)
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)
    ax2.set_axisbelow(True)

    fig.tight_layout()
    _save(fig, "02_class_distribution.png")


# ---------------------------------------------------------------------------
# Hinh 3: THI NGHIEM 1 - do chinh xac theo max_depth
# ---------------------------------------------------------------------------
def plot_max_depth(results: pd.DataFrame) -> None:
    """
    Hinh quan trong nhat cua bao cao: minh hoa qua khop.

    Hai duong:
      - train accuracy luon TANG theo do sau
      - valid accuracy TANG nhung sau do BI GIAM
    - Khoang cach giua hai duong = do qua khop (gap).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Chuyen nhan "khong gioi han" thanh so de ve duoc
    depths = list(range(len(results)))
    labels = results["max_depth"].tolist()

    # Trai: so sanh train / valid
    ax1.plot(depths, results["train_acc"], "o-", label="Train", color=COLORS["train"], lw=2)
    ax1.plot(depths, results["valid_acc"], "s-", label="Validation", color=COLORS["valid"], lw=2)
    ax1.fill_between(
        depths,
        results["train_acc"],
        results["valid_acc"],
        color=COLORS["warn"],
        alpha=0.18,
        label="Khoang qua khop (gap)",
    )
    ax1.set_xticks(depths)
    ax1.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax1.set_xlabel("max_depth")
    ax1.set_ylabel("Do chinh xac")
    ax1.set_title("Do chinh xac theo do sau cay\n(Train luon tang, Validation tang roi giam)")
    ax1.legend(loc="lower left", fontsize=9)
    ax1.grid(alpha=0.3)
    ax1.set_axisbelow(True)

    # Phai: khoang qua khop
    bars = ax2.bar(depths, results["gap"], color=COLORS["warn"], edgecolor="white")
    ax2.set_xticks(depths)
    ax2.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax2.set_xlabel("max_depth")
    ax2.set_ylabel("train - validation")
    ax2.set_title("Khoang qua khop tang dan\n(Cay sau hon -> hoc nho nhieu hon)")
    bars[-1].set_color("#B03A2E")
    ax2.grid(axis="y", alpha=0.3)
    ax2.set_axisbelow(True)

    # Chu thich dinh vi tri, giu trong khung do thi
    ax2.annotate(
        f"Cay khong gioi han:\ntrain = 100%, valid = {results['valid_acc'].iloc[-1]:.1%}",
        xy=(len(depths) - 1, results["gap"].iloc[-1]),
        xytext=(-8, 38),
        textcoords="offset points",
        fontsize=9,
        color="#B03A2E",
        ha="right",
        arrowprops=dict(arrowstyle="->", color="#B03A2E"),
    )
    ax2.set_ylim(0, results["gap"].max() * 1.28)

    fig.tight_layout()
    _save(fig, "03_exp1_max_depth.png")


# ---------------------------------------------------------------------------
# Hinh 4: THI NGHIEM 2 - ccp_alpha tren CV
# ---------------------------------------------------------------------------
def plot_ccp_alpha(results: pd.DataFrame) -> None:
    """Tac dung cua cat tia, kem thanh loi chuan cua CV."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    alphas = results["ccp_alpha"].tolist()
    positions = list(range(len(alphas)))

    # Trai: duong F1 + vung loi
    mean = results["cv_f1_mean"].to_numpy()
    std = results["cv_f1_std"].to_numpy()
    ax1.plot(positions, mean, "o-", color=COLORS["train"], lw=2, label="F1 trung binh (CV)")
    ax1.fill_between(
        positions,
        mean - std,
        mean + std,
        color=COLORS["train"],
        alpha=0.18,
        label=r"$\pm$ 1 do lech chuan",
    )
    best = int(np.argmax(mean))
    ax1.plot(best, mean[best], "*", ms=18, color="#B03A2E", label=f"tot nhat: {alphas[best]}")

    ax1.set_xticks(positions)
    ax1.set_xticklabels([str(a) for a in alphas], rotation=45, ha="right", fontsize=8)
    ax1.set_xlabel("ccp_alpha")
    ax1.set_ylabel("F1 (5-fold CV tren tap train)")
    ax1.set_title("Cat tia bang ccp_alpha\n(Cat nhanh it gop y nhat -> F1 tang)")
    ax1.legend(fontsize=8)
    ax1.grid(alpha=0.3)
    ax1.set_axisbelow(True)

    # Phai: so la cua cay sau khi cat
    ax2.plot(positions, results.get("n_leaves", pd.Series(dtype=float)), "s-", color=COLORS["accent"], lw=2)
    ax2.set_xticks(positions)
    ax2.set_xticklabels([str(a) for a in alphas], rotation=45, ha="right", fontsize=8)
    ax2.set_xlabel("ccp_alpha")
    ax2.set_ylabel("So la")
    ax2.set_title("Cay don gian hon khi cat tia")
    ax2.grid(alpha=0.3)
    ax2.set_axisbelow(True)

    fig.tight_layout()
    _save(fig, "04_exp2_ccp_alpha.png")


# ---------------------------------------------------------------------------
# Hinh 5: THI NGHIEM 3 - so sanh mo hinh
# ---------------------------------------------------------------------------
def plot_model_comparison(results: pd.DataFrame) -> None:
    """Ba tieu chi de so sanh cay va rung: hieu qua, toc do, giai thich."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    names = results["mo_hinh"].tolist()
    positions = np.arange(len(names))

    # 1. Do chinh xac va F1
    ax = axes[0]
    width = 0.38
    ax.barh(positions - width / 2, results["valid_acc"], height=width, label="Accuracy", color=COLORS["train"])
    ax.barh(positions + width / 2, results["valid_f1"], height=width, label="F1", color=COLORS["accent"])
    ax.set_yticks(positions)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("Diem so tren validation")
    ax.set_xlim(0.85, 1.0)
    ax.set_title("1. Hieu qua\n(Tren validation)")
    ax.legend(fontsize=8)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    # 2. Thoi gian train
    ax = axes[1]
    bars = ax.barh(positions, results["train_time_s"], color=COLORS["warn"])
    ax.set_yticks(positions)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel("Giay")
    ax.set_title("2. Toc do khi train\n(Rung cham hon cay nhieu)")
    for bar, value in zip(bars, results["train_time_s"]):
        ax.text(value, bar.get_y() + bar.get_height() / 2, f" {value:.3f}s", va="center", fontsize=8)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    # 3. Kha nang giai thich
    ax = axes[2]
    explainable = results["giai_thich"].str.contains("DOC DUOC")
    colors = [COLORS["accent"] if e else "#B03A2E" for e in explainable]
    ax.barh(positions, explainable.astype(int), color=colors)
    ax.set_yticks(positions)
    ax.set_yticklabels([n[:34] for n in results["kich_thuoc"]], fontsize=8)
    ax.set_xlabel("1 = doc duoc quy tac, 0 = khong doc duoc")
    ax.set_title("3. Kha nang giai thich\n(Cay co quy tac, rung khong)")
    ax.set_xticks([0, 1])
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    fig.suptitle("So sanh cay quyet dinh va rung ngau nhien", fontsize=13, y=1.02)
    fig.tight_layout()
    _save(fig, "05_exp3_model_comparison.png")


# ---------------------------------------------------------------------------
# Hinh 6: THI NGHIEM 4 - phan bo loi
# ---------------------------------------------------------------------------
def plot_error_analysis(frame: pd.DataFrame) -> None:
    """Tinh hinh loi: so loi theo huong va theo do tin cay."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Trai: so mau sai theo loai
    counts = frame["error_type"].value_counts()
    fn = int(counts.get("false_negative", 0))
    fp = int(counts.get("false_positive", 0))
    correct = int(counts.get("correct", 0))

    ax1.bar(["Dung", "Cammeo -> duoi sai", "Osmancik -> duoi sai"], [correct, fn, fp],
            color=[COLORS["accent"], "#B03A2E", COLORS["warn"]], edgecolor="white")
    ax1.set_ylabel("So mau")
    ax1.set_title("Phan bo mau dung/sai")
    for i, (value, label) in enumerate(zip([correct, fn, fp], [correct, fn, fp])):
        ax1.text(i, value + max(correct, fn, fp) * 0.01, f"{label}", ha="center", fontweight="bold")
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_axisbelow(True)

    # Phai: ty le sai theo do tin cay
    if "prob_pos" in frame.columns:
        bins = [0.0, 0.5, 0.7, 0.8, 0.9, 1.0]
        labels = ["<0.5", "0.5-0.7", "0.7-0.8", "0.8-0.9", ">=0.9"]
        buckets = pd.cut(frame["prob_pos"], bins=bins, labels=labels)
        grouped = frame.groupby(buckets, observed=False)["correct"].apply(
            lambda s: 100.0 * (~s).mean()
        )
        bars = ax2.bar(labels, grouped.to_numpy(), color=COLORS["warn"], edgecolor="white")
        ax2.set_xlabel("Xac suat mo hinh du doan lop Cammeo")
        ax2.set_ylabel("Ty le sai (%)")
        ax2.set_title("Ty le sai theo do tin cay\n(Xac suat cao -> it sai hon)")
        for bar, value in zip(bars, grouped.to_numpy()):
            if value > 0:
                ax2.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.1f}%",
                         ha="center", va="bottom", fontsize=9)
        ax2.grid(axis="y", alpha=0.3)
        ax2.set_axisbelow(True)

    fig.tight_layout()
    _save(fig, "06_exp4_error_analysis.png")


# ---------------------------------------------------------------------------
# Hinh 7: ma tran nham nhieu + duong ROC
# ---------------------------------------------------------------------------
def plot_confusion_and_roc(y_true, y_pred, proba_pos, classes=CLASSES) -> None:
    """Hai hinh kinh dien: ma tran nham nhieu va duong ROC."""
    from sklearn.metrics import confusion_matrix, roc_curve

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Ma tran nham nhieu
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    image = ax1.imshow(cm, cmap="Blues")

    ax1.set_xticks(range(len(classes)))
    ax1.set_xticklabels(classes)
    ax1.set_yticks(range(len(classes)))
    ax1.set_yticklabels(classes)
    ax1.set_xlabel("Du doan")
    ax1.set_ylabel("Thuc te")
    ax1.set_title("Ma tran nham nhieu")

    # Ghi so vao o
    threshold = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax1.text(
                j,
                i,
                f"{cm[i, j]}",
                ha="center",
                va="center",
                fontsize=16,
                fontweight="bold",
                color="white" if cm[i, j] > threshold else "black",
            )

    # Ghi chu dinh nghia
    ax1.text(
        0.5,
        -0.16,
        "Tren: duoi Osmancik sai   Duoi: duoi Cammeo sai",
        transform=ax1.transAxes,
        ha="center",
        fontsize=9,
        color="#555555",
    )

    # Duong ROC
    binary = (pd.Series(y_true).to_numpy() == POS_LABEL).astype(int)
    fpr, tpr, _ = roc_curve(binary, proba_pos)
    from sklearn.metrics import auc

    roc_auc = auc(fpr, tpr)
    ax2.plot(fpr, tpr, color=COLORS["train"], lw=2, label=f"Cay quyet dinh (AUC = {roc_auc:.4f})")
    ax2.plot([0, 1], [0, 1], "--", color=COLORS["neutral"], lw=1, label="Ngau nhien (AUC = 0.5)")
    ax2.set_xlabel("Ty le bao loi (False Positive Rate)")
    ax2.set_ylabel("Ty le bat dung (True Positive Rate)")
    ax2.set_title("Duong cong ROC")
    ax2.legend(loc="lower right", fontsize=9)
    ax2.grid(alpha=0.3)
    ax2.set_axisbelow(True)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1.02)

    fig.tight_layout()
    _save(fig, "07_confusion_matrix_roc.png")


# ---------------------------------------------------------------------------
# Hinh 8: quy tac cay quyet dinh
# ---------------------------------------------------------------------------
def plot_tree_text(tree_text: str) -> None:
    """In quy tac cay ra hinh de dan vao bao cao."""
    fig = plt.figure(figsize=(11, max(4, 0.32 * len(tree_text.splitlines()))))
    fig.text(0.02, 0.98, tree_text, family="monospace", fontsize=8.5, va="top", wrap=True)
    fig.suptitle("Quy tac cay quyet dinh sau cat tia (doc duoc duoc)", fontsize=12, y=0.99)
    _save(fig, "08_tree_rules.png")


# ---------------------------------------------------------------------------
def main() -> int:
    from sklearn.tree import DecisionTreeClassifier, export_text

    print("=" * 70)
    print("VE BIEU DO")
    print("=" * 70)

    reports = Path(__file__).resolve().parent.parent / "reports"
    FIGURES.mkdir(parents=True, exist_ok=True)

    # Nap ket qua da tinh o cac buoc truoc
    df = load_raw()
    train_df, valid_df, test_df = split_data(df)

    print("\n[1/8] Phan bo dac trung")
    plot_feature_distribution(df)

    print("[2/8] Phan bo lop")
    plot_class_distribution(train_df, valid_df, test_df)

    print("[3/8] Thi nghiem 1: max_depth")
    depth = pd.read_csv(reports / "exp1_max_depth.csv")
    plot_max_depth(depth)

    print("[4/8] Thi nghiem 2: ccp_alpha")
    alpha = pd.read_csv(reports / "exp2_ccp_alpha.csv")
    plot_ccp_alpha(alpha)

    print("[5/8] Thi nghiem 3: so sanh mo hinh")
    compare = pd.read_csv(reports / "exp3_tree_vs_forest.csv")
    plot_model_comparison(compare)

    print("[6/8] Thi nghiem 4: phan tich loi")
    errors = pd.read_csv(reports / "exp4_error_rows.csv")
    plot_error_analysis(errors)

    print("[7/8] Ma tran nham nhieu + ROC")
    model = DecisionTreeClassifier(max_depth=None, ccp_alpha=0.005, random_state=42)
    model.fit(train_df[FEATURES], train_df[TARGET_COLUMN])
    y_pred = model.predict(valid_df[FEATURES])
    proba_pos = model.predict_proba(valid_df[FEATURES])[:, list(model.classes_).index(POS_LABEL)]
    plot_confusion_and_roc(valid_df[TARGET_COLUMN], y_pred, proba_pos)

    print("[8/8] Quy tac cay")
    tree_text = export_text(model, feature_names=FEATURES, decimals=2)
    plot_tree_text(tree_text)

    print(f"\nHoan tat. Xem thu muc: reports/figures/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
