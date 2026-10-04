# -*- coding: utf-8 -*-
"""
KIEM THU API.

=====================================================================
TAI SAO CAN KIEM THU?
=====================================================================
    De tai yeu cau: "API tra JSON, co schema/validation, ma loi hop ly,
    vi du request/response va KIEM THU TOI THIEU."

    Va mot cam bao quan trong: "input xau khong lam sap".

    Kiem thu la tu dong kiem tra phan do. Chay lai nhieu lan deu
    cho cung ket qua -> chung minh API khong hong.

    Nguoi dung khong lo test API bang tay. Cau hoi luon la "co bi
    hong khong?" - test la cau tra loi.

=====================================================================
CAC TRUONG HOP KIEM THU
=====================================================================
    1. Server con song
    2. Du lieu dung -> ket qua dung
    3. Thieu truong          -> 422
    4. Gia tri khong phai so -> 422
    5. Gia tri am / = 0      -> 422  (Area khong the am)
    6. Gia tri > 1 khi phai 0..1 -> 422  (Extent, Eccentricity)
    7. Gia tri ngoai vung du lieu -> 200 NHUNG kem canh bao
       (khong phai loi: mo hinh van chay, nguoi dung can xem ket qua
        va canh bao. Cam bao khong "am tham thay the gia tri")
    8. Batch nhieu mau
    9. Batch rong           -> 400
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.api import app  # noqa: E402

client = TestClient(app)


# Mau goc: gia tri tu chính du lieu thuc te
VALID_SAMPLE = {
    "Area": 15231,
    "Perimeter": 525.5789794921875,
    "Major_Axis_Length": 229.7498779296875,
    "Minor_Axis_Length": 85.09378814697266,
    "Eccentricity": 0.9288820028305054,
    "Convex_Area": 15617,
    "Extent": 0.5728955268859863,
}


# ---------------------------------------------------------------------------
# 1. Server con song
# ---------------------------------------------------------------------------
def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["classes"] == ["Cammeo", "Osmancik"]
    assert len(data["features"]) == 7


# ---------------------------------------------------------------------------
# 2. Du lieu dung -> ket qua dung
# ---------------------------------------------------------------------------
def test_classify_valid_sample():
    response = client.post("/api/rice-classify", json=VALID_SAMPLE)
    assert response.status_code == 200

    data = response.json()
    assert data["prediction"] in ("Cammeo", "Osmancik")
    assert 0.0 <= data["confidence"] <= 1.0
    assert abs(sum(data["probabilities"].values()) - 1.0) < 1e-6
    # Phai co quy tac cay de giai thich
    assert len(data["rule_applied"]) >= 2
    assert data["inputs"]["Area"] == 15231


def test_classify_grain_nho_va_grain_lon():
    """
    Kiem tra mo hinh phan biet duoc hai viet cuc.
    Cammeo la hat lon, Osmancik la hat nho (xem EDA).
    """
    # Hat nho -> ky vong Osmancik
    small = {
        "Area": 7551, "Perimeter": 359.10, "Major_Axis_Length": 145.26,
        "Minor_Axis_Length": 59.53, "Eccentricity": 0.843,
        "Convex_Area": 7723, "Extent": 0.4974,
    }
    # Hat lon -> ky vong Cammeo
    large = {
        "Area": 18913, "Perimeter": 548.45, "Major_Axis_Length": 239.01,
        "Minor_Axis_Length": 107.54, "Eccentricity": 0.931,
        "Convex_Area": 19099, "Extent": 0.861,
    }

    assert client.post("/api/rice-classify", json=small).json()["prediction"] == "Osmancik"
    assert client.post("/api/rice-classify", json=large).json()["prediction"] == "Cammeo"


# ---------------------------------------------------------------------------
# 3-6. Input sai phai bi TU CHOI (khong duoc am tham sua)
# ---------------------------------------------------------------------------
def test_missing_field_rejected():
    """Thieu mot truong -> 422, khong duoc tu dien gia tri."""
    incomplete = dict(VALID_SAMPLE)
    del incomplete["Area"]

    response = client.post("/api/rice-classify", json=incomplete)
    assert response.status_code == 422
    # Loi phai chi ro truong nao
    assert "Area" in response.text


def test_non_numeric_rejected():
    """Gia tri khong phai so -> 422."""
    bad = dict(VALID_SAMPLE, Area="khong phai so")
    assert client.post("/api/rice-classify", json=bad).status_code == 422


def test_negative_area_rejected():
    """Dien tich khong the am -> 422."""
    bad = dict(VALID_SAMPLE, Area=-5000)
    response = client.post("/api/rice-classify", json=bad)
    assert response.status_code == 422
    assert "Area" in response.text


def test_zero_area_rejected():
    """Dien tich phai > 0, khong chap nhan 0."""
    bad = dict(VALID_SAMPLE, Area=0)
    assert client.post("/api/rice-classify", json=bad).status_code == 422


def test_extent_out_of_unit_range_rejected():
    """Extent phai tu 0 den 1; gia tri 5.0 vo nghia -> 422."""
    bad = dict(VALID_SAMPLE, Extent=5.0)
    assert client.post("/api/rice-classify", json=bad).status_code == 422


def test_eccentricity_negative_rejected():
    """Eccentricity khong the am -> 422."""
    bad = dict(VALID_SAMPLE, Eccentricity=-0.5)
    assert client.post("/api/rice-classify", json=bad).status_code == 422


# ---------------------------------------------------------------------------
# 7. Gia tri ngoai vung du lieu -> 200 NHUNG kem canh bao
# ---------------------------------------------------------------------------
def test_out_of_domain_returns_warning_not_silent_fix():
    """
    Gia tri trong mieng (lon nhu 5000 pixel^2) van hop le ve kieu,
    nhung ngoai vung du lieu goc.
    => API van tra ket qua (200) NHUNG kem canh bao.

    Dieu khoan: khong tu thay the gia tri. Do la de tai yeu cau.
    """
    weird = dict(VALID_SAMPLE, Area=5000)
    response = client.post("/api/rice-classify", json=weird)

    assert response.status_code == 200
    data = response.json()
    assert data["in_domain"] is False
    assert len(data["warnings"]) > 0
    # Gia tri phai giu nguyen, khong bi sua
    assert data["inputs"]["Area"] == 5000


def test_in_domain_sample_has_no_warning():
    """Mau binh thuong khong duoc canh bao gia."""
    data = client.post("/api/rice-classify", json=VALID_SAMPLE).json()
    assert data["in_domain"] is True
    assert data["warnings"] == []
    assert data["low_confidence"] is False


# ---------------------------------------------------------------------------
# 8-9. Batch
# ---------------------------------------------------------------------------
def test_batch_classify():
    response = client.post("/api/batch-classify", json=[VALID_SAMPLE] * 3)
    assert response.status_code == 200

    data = response.json()
    assert data["n_samples"] == 3
    assert len(data["results"]) == 3
    total = data["summary"]["Cammeo"] + data["summary"]["Osmancik"]
    assert total == 3


def test_batch_empty_rejected():
    """Danh sach rong -> 400."""
    response = client.post("/api/batch-classify", json=[])
    assert response.status_code == 400


def test_batch_with_one_invalid_entire_request_rejected():
    """
    Neu 1 trong 100 mau sai, ca request bi tu choi.
    => Nguoi dung biet ngay, khong nhan ket qua "nua chung".
    """
    rows = [VALID_SAMPLE, dict(VALID_SAMPLE, Area=-1)]
    assert client.post("/api/batch-classify", json=rows).status_code == 422


# ---------------------------------------------------------------------------
# Model card
# ---------------------------------------------------------------------------
def test_model_card_has_metrics_and_limitations():
    response = client.get("/api/model-card")
    assert response.status_code == 200

    data = response.json()
    assert "metrics_test" in data
    assert data["metrics_test"]["accuracy"] > 0
    # De tai yeu cau phai co gioi han -> bat buoc co, va phai nhieu
    assert len(data["limitations"]) >= 3
    assert len(data["not_intended_use"]) >= 1
    assert data["dataset"]["license"] == "CC BY 4.0"


def test_value_help_covers_all_features():
    data = client.get("/api/value-help").json()
    for feature in (
        "Area", "Perimeter", "Major_Axis_Length", "Minor_Axis_Length",
        "Eccentricity", "Convex_Area", "Extent",
    ):
        assert feature in data
        assert "min" in data[feature]
        assert "max" in data[feature]
        assert "unit" in data[feature]
