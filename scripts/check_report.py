#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Kiem tra bao cao Word co dung chuan khong.

Chay:  python scripts/check_report.py

Muc dich:
    Truoc khi nop, kiem tra bao cao du:
      - Co du muc chuong theo de cuong
      - Co du so bang va hinh
      - So lieu co khop voi file ket qua that hay khong
      - Khong con cho "TBD", "xxx", "loi" bi bo sot

    Day la cong cu KIEM CHAT LUONG BAO CAO, khong phai sua bao cao.
    Neu co loi, script bao ro vi tri can sua.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
REPORT_FILE = ROOT / "BaoCao_Project17.docx"

# Muc bat buoc theo de cuong de tai
REQUIRED_SECTIONS = [
    "TỔNG QUAN VỀ ĐỀ TÀI",
    "CƠ SỞ LÝ THUYẾT",
    "XÂY DỰNG MÔ HÌNH HỌC MÁY",
    "THIẾT KẾ THÍ NGHIỆM VÀ KẾT QUẢ",
    "XÂY DỰNG ỨNG DỤNG",
    "KẾT LUẬN",
    "TÀI LIỆU THAM KHẢO",
]

MIN_TABLES = 8
MIN_FIGURES = 5
MIN_WORDS = 3000

# Cho biet kiem duoc, thuong la noi dung nguoi vien con phai viet
PLACEHOLDER_PATTERNS = [
    (r"\bTBD\b", "chu TBD"),
    (r"\bTODO\b", "chu TODO"),
    (r"\bxxx+\b", "chu xxx"),
    (r"\bFIXME\b", "chu FIXME"),
    (r"Nguyễn Văn [AB]\b", "ten tam trong cau hinh"),
    (r"@\w+\d+", "ten tai khoan GitHub thay cho ho ten that"),
    (r"\b\d{8}\b", "ma sinh vien dang 8 chu so"),
]


def read_all_text(doc: Document) -> tuple[str, str, str]:
    """
    Doc toan bo noi dung bao cao.

    python-doch tach rieng DOCAN (doc.paragraphs) va O BANG (doc.tables).
    Chi quet docan se BO SOT so lieu nam trong bang — ma tran nham nhieu
    nam trong bang nen se bi bao "khong co" khi thuc ra co day du.

    Tra ve (noi dung docan, noi dung bang, noi dung hop nhat de tim kiem).
    """
    paragraph_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    cell_lines = []
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    cell_lines.append(cell.text.strip())

    body = "\n".join(paragraph_lines)
    cells = "\n".join(cell_lines)
    return body, cells, f"{body}\n{cells}"


def main() -> int:
    print("=" * 68)
    print("KIEM TRA BAO CAO WORD")
    print("=" * 68)

    if not REPORT_FILE.exists():
        print(f"\nLOI: khong tim thay {REPORT_FILE.name}")
        print("Hay chay: python scripts/make_report.py")
        return 1

    doc = Document(REPORT_FILE)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    body_text, _, searchable = read_all_text(doc)

    problems: list[str] = []
    warnings: list[str] = []

    # --- 1. Cau truc ---
    print("\n[1] CAU TRUC")
    upper_lines = [
        p for p in paragraphs
        if len(p) < 100 and sum(c.isupper() for c in p) > len(p) * 0.55
    ]
    for section in REQUIRED_SECTIONS:
        found = any(section in line for line in upper_lines)
        print(f"    {'OK   ' if found else 'THIEU'} {section}")
        if not found:
            problems.append(f"Thieu muc: {section}")

    print(f"    OK   Tong so muc: {len(upper_lines)}")

    # --- 2. Bang va hinh ---
    print("\n[2] BANG VA HINH ANH")
    n_tables = len(doc.tables)
    n_figures = len(doc.inline_shapes)
    print(f"    So bang: {n_tables} (yeu cau >= {MIN_TABLES})")
    print(f"    So hinh: {n_figures} (yeu cau >= {MIN_FIGURES})")
    if n_tables < MIN_TABLES:
        problems.append(f"Chi co {n_tables} bang, can >= {MIN_TABLES}")
    if n_figures < MIN_FIGURES:
        problems.append(f"Chi co {n_figures} hinh, can >= {MIN_FIGURES}")

    # --- 3. Dung luong ---
    words = sum(len(p.split()) for p in paragraphs)
    print(f"\n[3] DUNG LUONG")
    print(f"    So tu: {words:,} (yeu cau >= {MIN_WORDS:,})")
    if words < MIN_WORDS:
        problems.append(f"Qua ngan: {words} tu")

    # --- 4. Khop voi ket qua that ---
    print("\n[4] DOI CHIEU VOI KET QUA THAT")
    final_path = REPORTS / "FINAL_RESULTS.json"
    if final_path.exists():
        with final_path.open(encoding="utf-8") as handle:
            test = json.load(handle)["test_metrics"]

        for name, digits in (("accuracy", 4), ("f1", 4), ("roc_auc", 4)):
            value = test[name]
            plain = f"{value:.{digits}f}"
            percent = f"{value * 100:.2f}"
            ok = plain in searchable or percent in searchable
            print(f"    {'OK   ' if ok else 'LECH'} {name}: '{plain}' hoac '{percent}'")
            if not ok:
                problems.append(
                    f"So lieu {name} = {plain} ({percent}%) khong xuat hien trong bao cao"
                )

        cm = test["confusion_matrix"]
        for key in ("tn", "fp", "fn", "tp"):
            ok = str(cm[key]) in searchable
            print(f"    {'OK   ' if ok else 'LECH'} ma tran nham lan {key} = {cm[key]}")
            if not ok:
                problems.append(f"Thieu so {cm[key]} cua ma tran nham lan")
    else:
        warnings.append("Chua co FINAL_RESULTS.json, bo qua doi chieu so lieu")

    # --- 5. Con cho ---
    print("\n[5] KIEM TRA CHO TRONG")
    found_placeholders = []
    for pattern, label in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, searchable)
        if matches:
            found_placeholders.append(label)
            print(f"    [CANH BAO] Con {label} ({len(matches)} lan)")
    if not found_placeholders:
        print("    OK   Khong con cho trong nao")

    # --- 6. Nguon trich dan ---
    print("\n[6] TRICH DAN")
    if "archive.ics.uci.edu" in searchable:
        print("    OK   Co trich dan nguon du lieu UCI")
    else:
        problems.append("Thieu trich dan nguon du lieu UCI")

    if "CC BY 4.0" in searchable:
        print("    OK   Co ghi giay phep CC BY 4.0")
    else:
        problems.append("Thieu ghi chu giay phep CC BY 4.0")

    if re.search(r"10\.18201/ijisae", searchable):
        print("    OK   Co DOI cua bai bao goc")
    else:
        warnings.append("Thieu DOI bai bao goc (khong bat buoc)")

    # --- 7. Cong c AI ---
    print("\n[7] KHAI BAO CONG CU AI")
    if "trợ lý trí tuệ nhân tạo" in searchable or "OpenCode" in searchable:
        print("    OK   Co khai bao su dung cong cu AI trong loi cam doan")
    else:
        warnings.append("Nen khai bao viec su dung cong cu AI")

    # --- 8. Random state ---
    print("\n[8] TAI LAP")
    if "random_state" in searchable and "42" in searchable:
        print("    OK   Co ghi random_state = 42")
    else:
        problems.append("Thieu thong tin random_state = 42")

    # --- Ket qua ---
    print()
    print("=" * 68)
    if problems:
        print(f"KET QUA: CO {len(problems)} VAN DE CAN SUA")
        print("=" * 68)
        for item in problems:
            print(f"  [x] {item}")
    else:
        print("KET QUA: BAO CAO DAT YEU CAU")
        print("=" * 68)

    if warnings:
        print()
        print("LU Y (khong bat buoc):")
        for item in warnings:
            print(f"  - {item}")

    if found_placeholders:
        print()
        print("CAN SUA TRUOC KHI NOP:")
        print("  - Ten sinh vien trong scripts/make_report.py (bien SINH_VIEN)")
        print("    roi chay lai: python scripts/make_report.py")

    print()
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
