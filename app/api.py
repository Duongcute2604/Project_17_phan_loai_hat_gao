# -*- coding: utf-8 -*-
"""
API phan loai gao bang cay quyet dinh.

=====================================================================
API LA GI?
=====================================================================
    API (Application Programming Interface) la "cong giao tiep" de
    phan mem gui du lieu cho nhau.

    Vi du: nguoi dung dien thoai gui 7 so -> may chu nhan -> mo hinh
    du doan -> tra ve "Cammeo, xac suat 97%".

    Trong du an nay: UNG DUNG WEB goi API. Khong co web thi API van
    chay doc lap bang cach goi truc tiep (xem tests/).

=====================================================================
BAI TOAN KIEM TRA DAU VAO (VALIDATION) - PHAN QUAN TRONG NHAT
=====================================================================
    Mo hinh chi hoat dong tren du lieu co 7 so, moi so co MIEN hop le.

    Neu nguoi dung nhap:
        Area = -5000           -> vo nghia, khong phai kich thuoc that
        Perimeter = "abc"       -> khong phai so
        Extent = 5.0            > 1, khong co y nghia
        Thi truong thieu        -> khong doan duoc

    THIET KE SAI (can tranh):
        Tu dong thay the = 0. Neu lam vay, nguoi dung go -5000 se
        duoc ket qua cho nhan khong bi bao loi -> im lang lam sai.
        De tai yeu cau ro: "khong am tham thay the gia tri".

    THIET KE DUNG:
        Tu choi request, tra ve 422 kem ly do cu the. Nguoi dung
        biet ngay minh nhap sai o dau.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODEL_PATH = ROOT / "models" / "tree_pruned.joblib"
RESULTS_PATH = ROOT / "reports" / "FINAL_RESULTS.json"
STATIC_DIR = ROOT / "app" / "static"

# Ngung do tin cay: xac suat du doan thap -> can nguoi kiem tra lai
LOW_CONFIDENCE_THRESHOLD = 0.90


# ---------------------------------------------------------------------------
# Tai mo hinh MOT LAN khi khoi dong server
# ---------------------------------------------------------------------------
def load_model() -> dict:
    """
    Nap mo hinh da huan luyen san.

    NGUYEN TAC: chi NAP, khong HUAN LUYEN LAI.
    De tai yeu cau: "Ung dung chi nap model/pipeline da luu,
    khong huan luyen lai o moi request."

    Huan luyen lai moi request se:
      - rat cham
      - lam ket qua thay doi khong kiem soat duoc
      - khong tao lap
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Khong tim thay mo hinh tai {MODEL_PATH}\n"
            f"Hay chay: python src/final.py"
        )
    return joblib.load(MODEL_PATH)


BUNDLE = load_model()
MODEL = BUNDLE["model"]
FEATURES = BUNDLE["features"]
CLASSES = BUNDLE["classes"]
POS_LABEL = BUNDLE["pos_label"]

# Ket qua danh gia, de hien thi tren trang "model card"
METRICS: dict = {}
if RESULTS_PATH.exists():
    with RESULTS_PATH.open(encoding="utf-8") as handle:
        METRICS = json.load(handle)


# ---------------------------------------------------------------------------
# Mo ta mieng gia tri cho nguoi dung
# ---------------------------------------------------------------------------
# Khoang giap trong tap train (nhac toi co so khong viet chu)
# Khoi dong lai app bang lenh moi de lay lai. Day chi la thong bao.
VALUE_HELP: dict[str, dict] = {
    "Area": {"min": 7000, "max": 19500, "unit": "pixel²", "desc": "Dien tich hat gao"},
    "Perimeter": {"min": 340, "max": 570, "unit": "pixel", "desc": "Chu vi hat gao"},
    "Major_Axis_Length": {"min": 125, "max": 255, "unit": "pixel", "desc": "Chieu dai truc lon"},
    "Minor_Axis_Length": {"min": 55, "max": 112, "unit": "pixel", "desc": "Chieu dai truc nho"},
    "Eccentricity": {"min": 0.77, "max": 0.96, "unit": "(0-1)", "desc": "Do lech tam"},
    "Convex_Area": {"min": 7000, "max": 19500, "unit": "pixel²", "desc": "Dien tich bao loi"},
    "Extent": {"min": 0.40, "max": 0.94, "unit": "(0-1)", "desc": "Ti le dien tich that / bao loi"},
}


# ---------------------------------------------------------------------------
# Kiem tra du lieu dau vao (Pydantic)
# ---------------------------------------------------------------------------
class RiceFeatures(BaseModel):
    """
    Schema dau vao: 7 dac trung cua mot hat gao.

    Field(...) gan rong buoc:
      - gt:  cho phep gia tri
      - ge/le: gioi han duoi / tren
      - mo ta: hien thi cho nguoi dung trong giao dien

    Neu vi pham, FastAPI tra ve 422 AUTOMATIC, kem ten truong va
    ly do. Nguoi dung khong the bo qua.
    """

    Area: float = Field(
        gt=0, le=30000,
        description="Dien tich hat gao, don vi pixel^2 (vuong)",
    )
    Perimeter: float = Field(
        gt=0, le=1000,
        description="Chu vi hat gao, don vi pixel",
    )
    Major_Axis_Length: float = Field(
        gt=0, le=400,
        description="Chieu dai theo truc lon nhat, don vi pixel",
    )
    Minor_Axis_Length: float = Field(
        gt=0, le=300,
        description="Chieu dai theo truc nho nhat, don vi pixel",
    )
    Eccentricity: float = Field(
        ge=0.0, le=1.0,
        description="Do lech tam, gia tri tu 0 den 1",
    )
    Convex_Area: float = Field(
        gt=0, le=30000,
        description="Dien tich bao loi cua hat gao, don vi pixel^2",
    )
    Extent: float = Field(
        ge=0.0, le=1.0,
        description="Ti le dien tich that tren dien tich bao loi, tu 0 den 1",
    )


# ---------------------------------------------------------------------------
# Kiem tra ngoai mieng (ngoai ra tap train)
# ---------------------------------------------------------------------------
def out_of_domain_check(sample: pd.DataFrame) -> dict:
    """
    Phat hien gia tri nam NGOAI vung da thay trong tap train.

    Y nghia: mo hinh chi duoc xac nhan trong vung du lieu goc.
    Mot hat gao co dien tich 500 pixel^2 thi khong phai la gao
    thuong -> ket qua du doan khong co y nghia.

    Tra ve danh sach cac truong bi canh bao.
    """
    warnings = []
    for feature in FEATURES:
        help_info = VALUE_HELP.get(feature)
        if not help_info:
            continue
        value = float(sample[feature].iloc[0])
        if value < help_info["min"] or value > help_info["max"]:
            warnings.append(
                {
                    "feature": feature,
                    "value": value,
                    "expected_range": [help_info["min"], help_info["max"]],
                    "message": (
                        f"{feature} = {value:.2f} nam ngoai khoang da thay "
                        f"[{help_info['min']}, {help_info['max']}]. "
                        f"Ket qua du doan co the khong chinh xac."
                    ),
                }
            )
    return {
        "in_domain": len(warnings) == 0,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Ung dung FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Rice Classification API",
    description=(
        "Phan loai hai giong gao (Cammeo / Osmancik) tu 7 dac trung hinh hoc.\n\n"
        "**Cach dung:** nhap JSON vao POST /api/rice-classify, hoac mo "
        "/docs de xem tu dong sinh giao dien.\n\n"
        "Mien hop le cua moi dac trung duoc mo ta trong phan Schema cua /docs."
    ),
    version="1.0.0",
)


@app.get("/api/health", summary="Kiem tra dich vu con song")
def health() -> dict:
    """Dung de kiem tra server da len chua."""
    return {
        "status": "ok",
        "model": type(MODEL).__name__,
        "n_leaves": int(MODEL.get_n_leaves()),
        "features": FEATURES,
        "classes": CLASSES,
    }


@app.get("/api/value-help", summary="Mo ta khoang gia tri hop le cua 7 dac trung")
def value_help() -> dict:
    """Frontend dung de hien thi don vi va khoang gia tri can nhap."""
    return VALUE_HELP


@app.get("/api/model-card", summary="Thong tin mo hinh va gioi han")
def model_card() -> dict:
    """
    Tra ve thong tin mo hinh cho trang "Model card".

    Bao gom ca gioi han - phan nay de tai yeu cau bat buoc
    ("model card va canh bao").
    """
    if not METRICS:
        return {"error": "Chay python src/final.py truoc de co ket qua danh gia"}

    test = METRICS["test_metrics"]
    valid = METRICS["valid_metrics"]
    return {
        "model": {
            "type": METRICS["mo_hinh"],
            "ccp_alpha": METRICS["ccp_alpha"],
            "random_state": METRICS["random_state"],
            "n_leaves": METRICS["n_leaves"],
            "features": METRICS["features"],
        },
        "dataset": {
            "name": "Rice (Cammeo and Osmancik) - UCI ML Repository",
            "url": "https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik",
            "license": "CC BY 4.0",
            "n_samples": test["n_samples"],
        },
        "metrics_validation": {
            "accuracy": valid["accuracy"],
            "precision": valid["precision"],
            "recall": valid["recall"],
            "f1": valid["f1"],
            "roc_auc": valid["roc_auc"],
        },
        "metrics_test": {
            "accuracy": test["accuracy"],
            "precision": test["precision"],
            "recall": test["recall"],
            "f1": test["f1"],
            "roc_auc": test["roc_auc"],
        },
        "confusion_matrix_test": test["confusion_matrix"],
        "seed_stability": METRICS.get("seed_stability"),
        "tree_rules": METRICS.get("tree_rules"),
        "limitations": [
            "Chi dung tren 7 dac trung hinh hoc. Khong xac dinh chat luong, "
            "dinh chat, hay phan loai bien the.",
            "Chi co 2 giong trong du lieu (Cammeo va Osmancik). "
            "Giong khac se duoc gan nham mot trong hai.",
            "Dac trung phai duoc do theo CUNG quy trinh anh chup cua tap goc. "
            "Do sai quy trinh lam ket qua sai.",
            "Du lieu chi co 3810 mau, tu mot nguon. Chua chung minh duoc "
            "khi nao mo hinh chuyen sang dieu kien khac.",
            "Vung chong lap giua hai lop khong the tach hoan toan bang dac "
            "trung hinh hoc. Ty le sai ~9% la gi han nghe.",
            "Mo hinh CHI phuc vu sang loc so bo. KHONG thay the kiem nghiem "
            "chat luong chinh thuc.",
        ],
        "intended_use": [
            "Sang loc so bo hai giong gao trong day chuyen dong goi.",
            "Kiem nhan nhanh tren day chuyen, co nguoi trucc.",
        ],
        "not_intended_use": [
            "Khong dung thay the kiem nghiem giong hoac chat luong.",
            "Khong dung quyet dinh gia re, khong dung phap ly.",
        ],
    }


@app.post("/api/rice-classify", response_model=None, summary="Phan loai mot hat gao")
def classify(payload: RiceFeatures) -> dict:
    """
    Phan loai hat gao tu 7 dac trung.

    Tra ve: nhan du doan, xac suat, quy tac cay da ap dung,
    va canh bao neu input nam ngoai vung du lieu.
    """
    # Chuyen sang DataFrame dung thu tu cot mo hinh da hoc
    sample = pd.DataFrame([payload.model_dump()])[FEATURES]

    # --- Kiem tra ngoai mieng truoc khi du doan ---
    # Khong tu choi request: nguoi dung van muon xem ket qua, va
    # canh bao duoc tra ve kem de giao dien hien thi. NHUNG phai
    # canh bao ro rang - khong de im lang ket qua sai.
    domain = out_of_domain_check(sample)

    # --- Du doan ---
    prediction = MODEL.predict(sample)[0]
    proba = MODEL.predict_proba(sample)[0]
    proba_map = {label: float(p) for label, p in zip(MODEL.classes_, proba)}
    confidence = proba_map[prediction]

    # --- Lay duong dan toi la cay da dung ---
    rule_path = explain(sample)

    result = {
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "probabilities": {k: round(v, 4) for k, v in proba_map.items()},
        "rule_applied": rule_path,
        "in_domain": domain["in_domain"],
        "warnings": domain["warnings"],
        "low_confidence": confidence < LOW_CONFIDENCE_THRESHOLD,
        "note": (
            f"Ket qua nay co do tin cay {confidence:.1%}, thap hon nguong "
            f"{LOW_CONFIDENCE_THRESHOLD:.0%}. Nen kiem tra lai bang mat hoac "
            f"do lai dac trung."
            if confidence < LOW_CONFIDENCE_THRESHOLD
            else "Do tin cay cao."
        ),
        "inputs": payload.model_dump(),
    }
    return result


def explain(sample: pd.DataFrame) -> list[str]:
    """
    Doc quy tac cay cho MOT mau cu the.

    Di tu goc cay xuong, moi nut so sanh gia tri dac trung voi nguong.
    Neu nhanh phu "trái" thi ghi lai, giu xuong nhanh phai.

    Ket qua: danh sach cac dieu kien, doc theo thu tu phai ra quyet dinh.
    """
    tree = MODEL.tree_
    conditions = []
    node = 0

    while tree.children_left[node] != -1:  # chua toi la
        feature_name = FEATURES[tree.feature[node]]
        threshold = tree.threshold[node]
        value = float(sample[feature_name].iloc[0])

        if value <= threshold:
            direction = "<="
            node = tree.children_left[node]
        else:
            direction = ">"
            node = tree.children_right[node]

        conditions.append(f"{feature_name} ({value:.2f}) {direction} {threshold:.2f}")

    leaf_class = MODEL.classes_[tree.value[node].argmax()]
    conditions.append(f"=> {leaf_class}")
    return conditions


@app.post("/api/batch-classify", summary="Phan loai nhieu hat gao (CSV batch)")
def batch_classify(rows: list[RiceFeatures]) -> dict:
    """
    Phan loai nhieu mau mot luc - cho nhu cau "CSV batch" cua de tai.

    Nhan mot danh sach cac mau, tra ve ket qua cho tung mau.
    """
    if not rows:
        raise HTTPException(status_code=400, detail="Danh sach rong")

    if len(rows) > 1000:
        raise HTTPException(
            status_code=400,
            detail=f"Toi da 1000 mau moi request, nhan {len(rows)}",
        )

    frame = pd.DataFrame([row.model_dump() for row in rows])[FEATURES]
    predictions = MODEL.predict(frame)
    proba = MODEL.predict_proba(frame)

    results = []
    for index, prediction in enumerate(predictions):
        proba_map = {c: float(p) for c, p in zip(MODEL.classes_, proba[index])}
        confidence = proba_map[prediction]
        domain = out_of_domain_check(frame.iloc[[index]])
        results.append(
            {
                "index": index,
                "prediction": prediction,
                "confidence": round(confidence, 4),
                "in_domain": domain["in_domain"],
                "warnings": domain["warnings"],
            }
        )

    summary = {}
    for label in CLASSES:
        summary[label] = sum(1 for r in results if r["prediction"] == label)
    summary["n_out_of_domain"] = sum(1 for r in results if not r["in_domain"])

    return {
        "n_samples": len(results),
        "summary": summary,
        "results": results,
    }


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> HTMLResponse:
    """Trang chu ung dung web."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse(
            "<h1>Rice Classification API</h1>"
            "<p>Giao dien web chua duoc them. Xem <a href='/docs'>API docs</a>.</p>"
        )
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.exception_handler(FileNotFoundError)
def handle_missing_model(request, exc: FileNotFoundError):
    """Tra ve loi 503 ro rang thay vi loi 500 mo hinh."""
    return JSONResponse(
        status_code=503,
        content={
            "error": "Model chua san sang",
            "detail": str(exc),
            "huong_dan": "Chay: python src/final.py",
        },
    )


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("Khoi dong API tai http://127.0.0.1:8000")
    print("  Giao dien web : http://127.0.0.1:8000/")
    print("  API docs      : http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)
