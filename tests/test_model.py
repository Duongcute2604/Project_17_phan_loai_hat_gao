# -*- coding: utf-8 -*-
"""
KIEM THU MO HINH (khong can API).

=====================================================================
KIEM THU MO HINH KHAC KIEM THU API O THAY NAO?
=====================================================================
    tests/test_api.py kiem tra TANG DUONG: du lieu gui len co hop
    le khong, ket qua tra ve dung dinh dang khong.

    File nay kiem tra TINH DUNG cua mo hinh:
      - Du lieu co hieu luc khong? (co mau trung lap khong?)
      - Mo hinh co phan loai dung hai viet cuc khong?
      - Cay co qua khop khong? (train khong vuot qua validation qua nhieu)
      - Ccp alpha co cat tia that khong?
      - Quy tac cay co giai thich duoc mau sai khong?
      - Xac suat co hop le khong?

    Hai lop kiem thu nay bo sung nhau. Chi kiem tra API thi co the
    co mot mo hinh sai ma API van tra ket qua dep.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import FEATURES, POS_LABEL, RANDOM_STATE, TARGET_COLUMN  # noqa: E402
from src.data import load_raw  # noqa: E402
from src.split import split_data  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def data() -> dict:
    """Nap du lieu va chia tap mot lan cho ca file test."""
    df = load_raw()
    train_df, valid_df, test_df = split_data(df)
    return {
        "raw": df,
        "train": train_df,
        "valid": valid_df,
        "test": test_df,
    }


@pytest.fixture(scope="module")
def fitted(data) -> DecisionTreeClassifier:
    """Mo hinh cay da cat tia, huan luyen tren tap train."""
    model = DecisionTreeClassifier(
        max_depth=None, ccp_alpha=0.005, random_state=RANDOM_STATE
    )
    model.fit(data["train"][FEATURES], data["train"][TARGET_COLUMN])
    return model


# ---------------------------------------------------------------------------
# 1. Du lieu dung khong
# ---------------------------------------------------------------------------
def test_no_missing_values(data):
    """Dữ liệu goc khong co gia tri thieu."""
    missing = data["raw"].isna().sum().sum()
    assert missing == 0, f"Co {missing} gia tri thieu trong du lieu"


def test_no_duplicate_rows(data):
    """Khong co dong trung lap trong du lieu goc."""
    duplicated = data["raw"].duplicated().sum()
    assert duplicated == 0, f"Co {duplicated} dong trung lap"


def test_label_values_valid(data):
    """Chi co hai gia tri nhan, dung nhu bai toan."""
    labels = set(data["raw"][TARGET_COLUMN].unique())
    assert labels == {"Cammeo", "Osmancik"}, f"Nhan khong mong doi: {labels}"


def test_all_features_numeric(data):
    """Ca 7 dac trung deu la so - dung de tinh cac chi so."""
    for feature in FEATURES:
        assert pd.api.types.is_numeric_dtype(data["raw"][feature]), (
            f"{feature} khong phai kieu so"
        )


# ---------------------------------------------------------------------------
# 2. Chia tap dung khong
# ---------------------------------------------------------------------------
def test_split_sizes_add_up(data):
    """Tong so mau cua ba tap bang tong so mau goc."""
    total = len(data["train"]) + len(data["valid"]) + len(data["test"])
    assert total == len(data["raw"])


def test_split_sizes_ordered(data):
    """Tap train phai lon nhat - truong hop nguoi cung nham bien se fail day."""
    assert len(data["train"]) > len(data["valid"]), "Train phai lon hon validation"
    assert len(data["train"]) > len(data["test"]), "Train phai lon hon test"
    assert abs(len(data["valid"]) - len(data["test"])) <= 1


def test_stratified_class_ratio(data):
    """Ti le Cammeo phai nhat quan giua ba tap."""
    ratios = [
        (data[part][TARGET_COLUMN] == POS_LABEL).mean() * 100
        for part in ("train", "valid", "test")
    ]
    spread = max(ratios) - min(ratios)
    assert spread <= 1.0, f"Ti le lop lech {spread:.2f} diem phan tram giua cac tap"


def test_no_row_overlap_between_splits(data):
    """
    Khong duoc co ban ghi xuat hien o ca hai tap.
    Neu co -> ro ri thong tin, diem bi cham nang.
    """
    def keys(frame):
        return set(map(tuple, frame[FEATURES + [TARGET_COLUMN]].to_numpy()))

    train_keys = keys(data["train"])
    assert not (train_keys & keys(data["valid"])), "Co ban ghi trung train <-> validation"
    assert not (train_keys & keys(data["test"])), "Co ban ghi trung train <-> test"


def test_split_is_deterministic(data):
    """Chia lai voi cung seed phai ra cung ket qua."""
    _, valid_again, _ = split_data(data["raw"], random_state=RANDOM_STATE)
    pd.testing.assert_frame_equal(data["valid"], valid_again)


# ---------------------------------------------------------------------------
# 3. Hanh vi mo hinh
# ---------------------------------------------------------------------------
def test_model_separates_two_extremes(fitted, data):
    """
    Hat nho nhat phai Osmancik, hat lon nhat phai Cammeo.
    Do hai giong phan biet nhau ve kich thuoc, cau nay phai dung.
    """
    frame = data["raw"]
    smallest = frame.loc[frame["Area"].idxmin()]
    largest = frame.loc[frame["Area"].idxmax()]

    assert fitted.predict(pd.DataFrame([smallest[FEATURES]]))[0] == "Osmancik"
    assert fitted.predict(pd.DataFrame([largest[FEATURES]]))[0] == "Cammeo"


def test_probabilities_sum_to_one(fitted, data):
    """Xac suat hai lop luong cong don mot."""
    proba = fitted.predict_proba(data["valid"][FEATURES])
    sums = proba.sum(axis=1)
    assert np.allclose(sums, 1.0), f"Xac suat khong cong bang 1 (max lech {abs(sums - 1).max()})"


def test_predict_matches_argmax(fitted, data):
    """Nhan du doan phai la lop co xac suat cao nhat."""
    frame = data["valid"]
    predictions = fitted.predict(frame[FEATURES])
    proba = fitted.predict_proba(frame[FEATURES])
    argmax = fitted.classes_[proba.argmax(axis=1)]
    assert np.array_equal(predictions, argmax)


def test_accuracy_above_baseline(fitted, data):
    """
    Mo hinh phai tot hon duong co so "doan lop da so".
    Neu khong, co nghia mo hinh khong hoc duoc gi ca.
    """
    y_true = data["valid"][TARGET_COLUMN]
    y_pred = fitted.predict(data["valid"][FEATURES])
    accuracy = (y_true == y_pred).mean()

    majority = y_true.value_counts(normalize=True).max()
    assert accuracy > majority, (
        f"Mo hinh {accuracy:.4f} khong tot hon duong co so {majority:.4f}"
    )
    # Nguong thuc te: mot cay rat don gien da duoc ~0.93
    assert accuracy > 0.85, f"Do chinh xac {accuracy:.4f} qua thap cho bai nay"


def test_training_never_far_exceeds_validation(fitted, data):
    """
    Do qua khop khong duoc qua lon.
    Cay cat tia phai giu khoang cach nho giua hai tap.
    """
    train_score = fitted.score(data["train"][FEATURES], data["train"][TARGET_COLUMN])
    valid_score = fitted.score(data["valid"][FEATURES], data["valid"][TARGET_COLUMN])
    gap = train_score - valid_score

    assert gap < 0.05, (
        f"Qua khop qua lon: train={train_score:.4f}, valid={valid_score:.4f}, "
        f"chenh {gap:.4f}. Kiem tra lai tham so cat tia."
    )


# ---------------------------------------------------------------------------
# 4. Cat tia
# ---------------------------------------------------------------------------
def test_pruning_reduces_leaves(data):
    """
    Cat tia phai lam cay nho hon cay khong cat.
    Day la dinh nghia cua cat tia - fail o day nghia tham so sai.
    """
    train = data["train"]

    unpruned = DecisionTreeClassifier(
        max_depth=None, random_state=RANDOM_STATE
    ).fit(train[FEATURES], train[TARGET_COLUMN])

    pruned = DecisionTreeClassifier(
        max_depth=None, ccp_alpha=0.005, random_state=RANDOM_STATE
    ).fit(train[FEATURES], train[TARGET_COLUMN])

    assert pruned.get_n_leaves() < unpruned.get_n_leaves(), (
        f"Cat tia khong lam cay nho hon: "
        f"{unpruned.get_n_leaves()} -> {pruned.get_n_leaves()}"
    )


def test_pruning_does_not_hurt_accuracy(data):
    """Cat tia khong duoc lam giam do chinh xac nhieu tren tap kiem tra."""
    train = data["train"]

    unpruned = DecisionTreeClassifier(
        max_depth=None, random_state=RANDOM_STATE
    ).fit(train[FEATURES], train[TARGET_COLUMN])
    pruned = DecisionTreeClassifier(
        max_depth=None, ccp_alpha=0.005, random_state=RANDOM_STATE
    ).fit(train[FEATURES], train[TARGET_COLUMN])

    valid = data["valid"]
    gap = (
        unpruned.score(valid[FEATURES], valid[TARGET_COLUMN])
        - pruned.score(valid[FEATURES], valid[TARGET_COLUMN])
    )
    # Cho phep cat tia hao mot chut, nhung khong duoc hao nhieu
    assert gap < 0.05, f"Cat tia giam do chinh xac {gap:.4f} qua nhieu tren tap kiem tra"


# ---------------------------------------------------------------------------
# 5. Khai ngoac mo hinh
# ---------------------------------------------------------------------------
def test_tree_uses_known_features(fitted):
    """
    Cay chi duoc dung cac dac trung da khai bao.

    LUU Y: fitted.tree_.feature luu CHI SO COT (0, 1, 2...), khong phai
    ten cot. Gia tri -2 danh dau nut la (khong dung dac trung nao).
    Vi vay phai doi chi so sang ten truoc khi so sanh.
    """
    indices = set(fitted.tree_.feature)
    indices.discard(-2)  # -2 la nut la, khong dung dac trung

    n_features = fitted.n_features_in_
    assert indices, "Cay khong dung dac trung nao - co the model chua hoc gi"
    assert min(indices) >= 0, f"Chi so cot am: {sorted(indices)}"
    assert max(indices) < n_features, (
        f"Chi so cot {max(indices)} vuot qua so dac trung {n_features}"
    )

    # Doi chi so sang ten de bao cao cho de doc
    used_names = {FEATURES[i] for i in indices}
    assert used_names <= set(FEATURES), f"Dac trung la: {used_names - set(FEATURES)}"
    print(f"\n  Cay dung cac dac trung: {', '.join(sorted(used_names))}")


def test_tree_is_not_single_leaf(fitted):
    """Cay phai co it nhat hai la - neu khong thi khong phan loai duoc gi."""
    assert fitted.get_n_leaves() >= 2, "Cay chi co mot la, khong phan loai duoc"


def test_predictions_are_explainable(fitted, data):
    """
    Moi du doan deu phai truy vet duoc bang quy tac kiem tra du lieu.
    Neu khong, mo hinh khong con "giai thich duoc" nhu nhom tuy chon.
    """
    tree = fitted.tree_
    sample = data["valid"][FEATURES].head(20)

    for _, row in sample.iterrows():
        node = 0
        while tree.children_left[node] != -1:
            feature = FEATURES[tree.feature[node]]
            node = (
                tree.children_left[node]
                if row[feature] <= tree.threshold[node]
                else tree.children_right[node]
            )
        # Phai toi duoc mot la co gia tri
        assert tree.value[node].sum() > 0, "Truot toi la rong"


def test_deterministic_predictions(fitted, data):
    """Goi predict nhieu lan phai cho cung ket qua."""
    frame = data["valid"][FEATURES].head(30)
    first = fitted.predict(frame)
    for _ in range(3):
        assert np.array_equal(fitted.predict(frame), first)
