#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sinh file bao cao Word cho du an Project 17.

Chay:  python scripts/make_report.py

Moi so lieu trong bao cao deu DOC tu file ket qua that
(reports/*.csv, reports/FINAL_RESULTS.json) — KHONG go tay.
Neu file ket qua khong ton tai, script se bao loi ro rang
thay vi dung gia tri gia dinh.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
OUTPUT = ROOT / "BaoCao_Project17.docx"

# ---------------------------------------------------------------------------
# Thong tin de tai - DOI CHINH xu
# ---------------------------------------------------------------------------
INFO = {
    "truong": "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ KỸ THUẬT HƯNG YÊN",
    "bo": "BỘ GIÁO DỤC VÀ ĐÀO TẠO",
    "mon": "HỌC MÁY CƠ BẢN",
    "bai": "BÀI 6 — CÂY QUYẾT ĐỊNH, CẮT TỈA VÀ RỪNG NGẪU NHIÊN",
    "ten": "PHÂN LOẠI HAI GIỐNG GẠO TỪ HÌNH DẠNG HẠT",
    "de": "PROJECT 17 — ĐỀ TÀI KẾT THÚC HỌC PHẦN",
    "nganh": "KHOA HỌC MÁY TÍNH",
    "chuyennganh": "TRÍ TUỆ NHÂN TẠO VÀ KHOA HỌC DỮ LIỆU",
    "gv": "PGS. TS. NGUYỄN VĂN HẬU",
    "lop": "12523W.1",
    "thoiGian": "HỌC KỲ 1 — NĂM HỌC 2025–2026",
}

# Thay bang ten that cua 2 thanh vien truoc khi in
SINH_VIEN = [
    ("Nguyễn Văn A", "11223301"),
    ("Nguyễn Văn B", "11223302"),
]


# ---------------------------------------------------------------------------
# Tien ich dinh dang
# ---------------------------------------------------------------------------
def set_cell_background(cell, color_hex: str) -> None:
    """To nen cho o bang."""
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:fill"), color_hex)
    cell._tc.get_or_add_tcPr().append(shading)


def add_page_number_footer(section) -> None:
    """Them 'Trang X' vao chan trang."""
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("Trang ")
    run.font.size = Pt(10)

    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    paragraph._p.append(field)


class Report:
    """Bao dong goi de viet bao cao gon ngan."""

    def __init__(self) -> None:
        self.doc = Document()
        self.figure_index = 0
        self.table_index = 0
        self._setup()

    def _setup(self) -> None:
        # Font chung
        style = self.doc.styles["Normal"]
        style.font.name = "Times New Roman"
        style.font.size = Pt(13)
        # Font cho tieng Viet trong Word
        style.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

        for section in self.doc.sections:
            section.left_margin = Cm(3.0)
            section.right_margin = Cm(2.0)
            section.top_margin = Cm(2.0)
            section.bottom_margin = Cm(2.0)
            add_page_number_footer(section)

    # -- Tieu de muc -------------------------------------------------------
    def heading(self, text: str, level: int = 1) -> None:
        sizes = {1: 16, 2: 14, 3: 13}
        paragraph = self.doc.add_paragraph()
        paragraph.paragraph_format.space_before = Pt(14 if level == 1 else 10)
        paragraph.paragraph_format.space_after = Pt(6)
        run = paragraph.add_run(text)
        run.bold = True
        run.font.size = Pt(sizes.get(level, 13))
        if level == 1:
            run.font.color.rgb = RGBColor(0, 0, 0)

    # -- Doan van ---------------------------------------------------------
    def para(self, text: str, bold: bool = False, italic: bool = False,
             align: str = "justify", indent: bool = True) -> None:
        paragraph = self.doc.add_paragraph()
        paragraph.alignment = {
            "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "left": WD_ALIGN_PARAGRAPH.LEFT,
        }[align]
        if indent and align == "justify":
            paragraph.paragraph_format.first_line_indent = Cm(1.0)
        paragraph.paragraph_format.space_after = Pt(6)
        run = paragraph.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.size = Pt(13)

    def bullets(self, items: list[str]) -> None:
        for item in items:
            paragraph = self.doc.add_paragraph(style="List Bullet")
            paragraph.paragraph_format.space_after = Pt(3)
            run = paragraph.add_run(item)
            run.font.size = Pt(13)

    # -- Bang -------------------------------------------------------------
    def table(self, headers: list[str], rows: list[list],
              caption: str | None = None, widths: list[float] | None = None) -> None:
        if caption:
            self.table_index += 1
            paragraph = self.doc.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_before = Pt(8)
            run = paragraph.add_run(f"Bảng {self.table_index}. {caption}")
            run.bold = True
            run.font.size = Pt(12)

        table = self.doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for index, header in enumerate(headers):
            cell = table.rows[0].cells[index]
            cell.text = ""
            run = cell.paragraphs[0].add_run(str(header))
            run.bold = True
            run.font.size = Pt(11)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_cell_background(cell, "D9D9D9")

        for row in rows:
            cells = table.add_row().cells
            for index, value in enumerate(row):
                cells[index].text = ""
                run = cells[index].paragraphs[0].add_run(str(value))
                run.font.size = Pt(11)
                if index > 0 and str(value).replace(".", "").replace("-", "").isdigit():
                    cells[index].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        if widths:
            for row in table.rows:
                for index, width in enumerate(widths):
                    row.cells[index].width = Cm(width)

        self.doc.add_paragraph()

    # -- Hinh anh ---------------------------------------------------------
    def figure(self, filename: str, caption: str) -> None:
        path = FIGURES / filename
        if not path.exists():
            print(f"  [BO QUA] khong tim thay hinh: {filename}")
            return

        self.figure_index += 1
        self.doc.add_picture(str(path), width=Cm(15.5))

        paragraph = self.doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(f"Hình {self.figure_index}. {caption}")
        run.bold = True
        run.font.size = Pt(12)
        self.doc.add_paragraph()

    # -- Ngat trang -------------------------------------------------------
    def page_break(self) -> None:
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ---------------------------------------------------------------------------
# Nap so lieu that
# ---------------------------------------------------------------------------
def load_results() -> dict:
    """Doc ket qua that. Raise neu thieu — khong dung gia tri gia dinh."""
    final_path = REPORTS / "FINAL_RESULTS.json"
    if not final_path.exists():
        print(f"LOI: khong co {final_path}\nHay chay: python src/final.py")
        sys.exit(1)

    with final_path.open(encoding="utf-8") as handle:
        final = json.load(handle)

    def csv(name: str) -> pd.DataFrame:
        path = REPORTS / name
        if not path.exists():
            print(f"LOI: khong co {path}")
            sys.exit(1)
        return pd.read_csv(path)

    return {
        "final": final,
        "baseline": csv("baseline_results.csv"),
        "exp1": csv("exp1_max_depth.csv"),
        "exp2": csv("exp2_ccp_alpha.csv"),
        "exp3": csv("exp3_tree_vs_forest.csv"),
        "split": csv("split_report.csv"),
        "outlier": csv("outlier_report.csv"),
        "err_feature": csv("exp4_error_feature_analysis.csv"),
    }


# ---------------------------------------------------------------------------
# BIA
# ---------------------------------------------------------------------------
def write_cover(report: Report) -> None:
    doc = report.doc

    for _ in range(2):
        doc.add_paragraph()

    for text in [INFO["bo"], INFO["truong"]]:
        report.para(text, bold=True, align="center", indent=False)

    doc.add_paragraph()
    report.para(INFO["de"], bold=True, align="center", indent=False)
    doc.add_paragraph()
    report.para(INFO["mon"], bold=True, align="center", indent=False)
    doc.add_paragraph()

    for _ in range(3):
        doc.add_paragraph()

    report.para(INFO["bai"], bold=True, align="center", indent=False)
    report.para(INFO["ten"].title(), bold=True, align="center", indent=False)

    for _ in range(4):
        doc.add_paragraph()

    report.para(f"Ngành: {INFO['nganh']}", align="center", indent=False)
    report.para(f"Chuyên ngành: {INFO['chuyennganh']}", align="center", indent=False)
    doc.add_paragraph()

    report.para("SINH VIÊN THỰC HIỆN:", bold=True, align="center", indent=False)
    for name, student_id in SINH_VIEN:
        report.para(name, align="center", indent=False)
        report.para(f"Mã sinh viên: {student_id}", align="center", indent=False)

    for _ in range(3):
        doc.add_paragraph()

    report.para(f"GIẢNG VIÊN: {INFO['gv']}", align="center", indent=False)
    report.para(f"MÃ LỚP: {INFO['lop']}", align="center", indent=False)
    report.para(INFO["thoiGian"], align="center", indent=False)

    report.page_break()

    # Trang nhan xet
    report.para("NHẬN XÉT", bold=True, align="center", indent=False)
    report.para("CỦA GIẢNG VIÊN HƯỚNG DẪN", bold=True, align="center", indent=False)
    doc.add_paragraph()
    report.para("....................................................................", align="left", indent=False)
    report.para("....................................................................", align="left", indent=False)
    report.para("....................................................................", align="left", indent=False)
    doc.add_paragraph()
    report.para("....................................................................", align="left", indent=False)
    report.para("....................................................................", align="left", indent=False)
    doc.add_paragraph()
    report.para("Ngày ............... Tháng ............. Năm .............", align="left", indent=False)

    report.page_break()

    # Loi cam doan
    report.para("LỜI CAM ĐOAN", bold=True, align="center", indent=False)
    doc.add_paragraph()
    report.para(
        "Em/chúng tôi cam đoan rằng báo cáo này là kết quả thực hiện đúng "
        "quy trình nghiên cứu khoa học của học phần, không sao chép từ bất kỳ "
        "công trình nào khác. Toàn bộ số liệu, hình ảnh và kết quả phân tích "
        "trong báo cáo đều được sinh ra từ mã nguồn do nhóm tự viết và tự chạy.",
        align="justify",
    )
    doc.add_paragraph()
    report.para(
        "Trong quá trình thực hiện, nhóm có sử dụng trợ lý trí tuệ nhân tạo "
        "(OpenCode, mô hình OpenAI) để hỗ trợ soạn thảo mã nguồn và chỉnh "
        "sửa văn bản. Mọi số liệu trong báo cáo đều được lấy trực tiếp từ "
        "các tệp kết quả do chương trình tạo ra, có thể tái lập độc lập bằng "
        "cách chạy lại quy trình với cùng mã nguồn và cùng tham số ngẫu nhiên "
        "(random_state = 42).",
        align="justify",
    )
    doc.add_paragraph()
    report.para("Hư Yên, ngày ........ tháng ........ năm 2026", align="center", indent=False)
    doc.add_paragraph()
    for name, _ in SINH_VIEN:
        report.para(name, align="center", indent=False)

    report.page_break()


# ---------------------------------------------------------------------------
# NOI DUNG
# ---------------------------------------------------------------------------
def write_content(report: Report, data: dict) -> None:
    final = data["final"]
    test = final["test_metrics"]
    valid = final["valid_metrics"]
    cm = test["confusion_matrix"]

    # ===================== CHUC 1 =====================
    report.heading("CHƯƠNG 1. TỔNG QUAN VỀ ĐỀ TÀI", 1)

    report.heading("1.1. Bối cảnh", 2)
    report.para(
        "Trong sản xuất và đóng gói gạo, việc phân loại giống là khâu quan "
        "trọng ảnh hưởng trực tiếp đến giá trị thương phẩm. Hai giống gạo "
        "phổ biến là Cammeo và Osmancik có đặc điểm hình thạch khác nhau, "
        "đủ để phân biệt bằng các phép đo hình thọc đơn giản khi chụp ảnh "
        "một hạt gạo đơn lẻ. Nếu việc sàng lọc này được thực hiện tự động "
        "ngay trong dây chuyền, cơ sở đóng gói có thể giảm đáng kể chi phí "
        "kiểm nghiệm thủ công và hạn chế sai sót do yếu tố con người."
    )
    report.para(
        "Nhóm lựa chọn nghiên cứu bài toán phân loại hai giống gạo này vì "
        "đây là bài toán phân loại nhị phân kinh điển, phù hợp để vận dụng "
        "kiến thức về cây quyết định — một mô hình có ưu điểm nổi bật là "
        "quy tắc dự đoán có thể đọc được và giải thích được, một đặc tính "
        "quan trọng khi đưa mô hình vào sử dụng thực tế."
    )

    report.heading("1.2. Mục tiêu và câu hỏi nghiên cứu", 2)
    report.para(
        "Mục tiêu chính của đồ án là xây dựng một quy trình học máy hoàn "
        "chỉnh, tái lập được, từ dữ liệu thô đến ứng dụng web có API, nhằm "
        "phân loại hai giống gạo dựa trên bảy đặc trưng hình học."
    )
    report.para("Câu hỏi nghiên cứu được đặt ra như sau:", bold=True, indent=False)
    report.bullets([
        "Một cây quyết định đơn giản có đủ chính xác và dễ giải thích, hay "
        "cần đến rừng ngẫu nhiên?",
        "Cắt tỉa bằng ccp_alpha ảnh hưởng thế nào đến độ chính xác và độ "
        "phức tạp của cây?",
        "Các mẫu bị dự đoán sai có đặc điểm gì chung, và giới hạn của bài "
        "toán nằm ở đâu?",
    ])

    report.heading("1.3. Đặc tả bài toán", 2)
    report.table(
        ["Thành phần", "Yêu cầu"],
        [
            ["Loại bài toán", "Phân loại nhị phân (nhị phân)"],
            ["Đơn vị quan sát", "Một hạt gạo đơn lẻ"],
            ["Đầu vào", "7 đặc trưng hình học đo từ ảnh"],
            ["Đầu ra", "Cammeo hoặc Osmancik, kèm xác suất và quy tắc cây"],
            ["Chỉ số đánh giá", "Accuracy, F1, ROC-AUC, ma trận nhầm lẫn"],
            ["Thời điểm dự đoán", "Ngay sau khi 7 đặc trưng được đo xong"],
        ],
        caption="Đặc tả bài toán phân loại giống gạo",
        widths=[4.5, 11.0],
    )

    report.heading("1.4. Phạm vi và giới hạn của đồ án", 2)
    report.para(
        "Đồ án tập trung vào bài toán phân loại, không xây dựng quy trình xử "
        "lý ảnh. Bảy đặc trưng được lấy sẵn từ bộ dữ liệu công khai, phù "
        "hợp với mục tiêu chứng minh quy trình học máy hoàn chỉnh. Đồ án "
        "không triển khai mô hình học sâu, không thu thập thêm dữ liệu và "
        "không phụ thuộc hạ tầng đám mây."
    )

    report.page_break()

    # ===================== CHUC 2 =====================
    report.heading("CHƯƠNG 2. CƠ SỞ LÝ THUYẾT", 1)

    report.heading("2.1. Cây quyết định", 2)
    report.para(
        "Cây quyết định là mô hình phân loại được xây dựng bằng chuỗi câu "
        "hỏi có/không trên từng đặc trưng. Cây xây dựng theo nguyên tắc "
        "chia đệ quy: tại mỗi nút, chọn đặc trưng và ngưỡng sao cho việc "
        "tách tập dữ liệu tạo ra kết quả thuần khiết nhất, lặp lại cho "
        "đến khi đạt điều kiện dừng. Ưu điểm nổi bật của mô hình là mọi "
        "quyết định đều có thể truy vết bằng các phép so sánh đơn giản, "
        "nhờ đó người sử dụng không cần hiểu thuật toán vẫn có thể kiểm "
        "tra lại kết quả dự đoán."
    )

    report.heading("2.2. Hiện tượng quá khớp", 2)
    report.para(
        "Cây quyết định không bị giới hạn về độ sâu, do đó có thể mọc đến "
        "mức mỗi nút lá chứa đúng một mẫu, dẫn đến độ chính xác trên tập "
        "huấn luyện đạt 100%. Đây là dấu hiệu của hiện tượng quá khớp: mô "
        "hình học thuộc cả nhiễu ngẫu nhiên của dữ liệu huấn luyện thay "
        "vì nắm bắt quy luật chung, nên hiệu năng trên dữ liệu mới suy "
        "giảm. Dấu hiệu nhận biết là khoảng cách giữa độ chính xác trên tập "
        "huấn luyện và tập kiểm tra tăng dần khi cây sâu thêm."
    )

    report.heading("2.3. Cắt tỉa", 2)
    report.para(
        "Cắt tỉa là kỹ thuật hạn chế hiện tượng quá khớp bằng cách loại bỏ "
        "những phần của cây không đóng góp đáng kể cho khả năng phân loại. "
        "scikit-learn hỗ trợ hai hình thức. Cắt tỉa trước thực hiện trong "
        "quá trình xây dựng thông qua các tham số như max_depth (giới hạn số "
        "tầng), min_samples_leaf (số mẫu tối thiểu mỗi lá) và "
        "min_impurity_decrease. Cắt tỉa sau được thực hiện thông qua tham "
        "số ccp_alpha, đại lượng đo chi phí của một nhánh dưới dạng tổng số "
        "mẫu bị phân loại sai tại các lá thuộc nhánh đó. Khi tổng chi phí "
        "này nhỏ hơn ngưỡng ccp_alpha, nhánh bị cắt bỏ. Trong đồ án này, "
        "hai dạng được đánh giá thông qua các tham số max_depth và ccp_alpha."
    )

    report.heading("2.4. Rừng ngẫu nhiên", 2)
    report.para(
        "Rừng ngẫu nhiên xây dựng nhiều cây quyết định độc lập trên các tập "
        "dữ liệu con được lấy mẫu lại có hoàn lại (bootstrap), đồng thời tại "
        "mỗi nút chỉ xét ngẫu nhiên một phần đặc trưng. Kết quả dự đoán "
        "cuối cùng là lớp chiếm đa số phiếu trong các cây. Rừng ngẫu nhiên "
        "giảm quá khớp nhờ sự đa dạng của các cây thành phần, đồng thời mạnh "
        "hơn trước nhiễu. Đổi lại, rừng không tạo ra một tập quy tắc đơn "
        "lẻ có thể đọc, và thời gian huấn luyện lớn hơn đáng kể."
    )

    report.heading("2.5. Đánh giá và phòng chống rò rỉ thông tin", 2)
    report.para(
        "Accuracy là tỉ lệ dự đoán đúng, dễ hiểu nhưng có thể gây ấn tượng "
        "sai khi hai lọp mất cân bằng. Vì vậy nhóm sử dụng thêm F1, là trung "
        "bình điều hòa của precision và recall, nhạy cảm với cả hai khía "
        "cạnh. Ma trận nhầm lẫn cho biết cụ thể mô hình sai ở chiều nào. "
        "ROC-AUC đo khả năng phân biết hai lọp trên mọi ngưỡng quyết định. "
        "F1 được tính cho lớp Cammeo là lớp thiểu số, vì nếu tính cho lớp "
        "đa số thì giá trị luôn cao và không phản ánh đúng hiệu quả thực tế."
    )
    report.para(
        "Rò rỉ thông tin xảy ra khi thông tin của tập kiểm tra bị sử dụng để "
        "xây dựng mô hình, khiến điểm số báo cáo không còn phản ánh năng "
        "lực thật của mô hình trên dữ liệu chưa từng thấy. Nhóm áp dụng ba "
        "nguyên tắc: chia tập trước mọi thao tác khác; mọi ngưỡng suy ra từ "
        "dữ liệu đều tính trên tập huấn luyện rồi mới áp dụng cho tập khác; "
        "tập kiểm thử chỉ dùng đúng một lần để báo cáo kết quả cuối cùng. "
        "Toàn bộ mã nguồn đặt giá trị random_state = 42 trong một tệp cấu "
        "hình duy nhất, bảo đảm mọi lần chạy cho kết quả giống nhau."
    )

    report.page_break()

    # ===================== CHUC 3 =====================
    report.heading("CHƯƠNG 3. XÂY DỰNG MÔ HÌNH HỌC MÁY", 1)

    report.heading("3.1. Nguồn và chất lượng dữ liệu", 2)
    report.para(
        "Dữ liệu lấy từ kho lưu trữ máy học UCI, bộ dữ liệu số 545 với tên "
        "Rice (Cammeo and Osmancik), do Ilkay Cinar và Murat Koklu (Đại học "
        "Selcuk, Konya, Thổ Nhĩ Kỳ) thu thập và công bố năm 2019. Giấy phép "
        "sử dụng là CC BY 4.0, cho phép dùng lại và trích dẫn. Dữ liệu gồm "
        "3.810 mẫu, mỗi mẫu là một hạt gạo với bảy đặc trưng hình học và một "
        "nhãn giống. Nhóm không đưa tệp dữ liệu gốc vào Git mà cung cấp "
        "script tải kèm giá trị kiểm tra SHA256 để bảo đảm mọi người đều "
        "tạo được cùng một tệp dữ liệu."
    )
    report.table(
        ["Thuộc tính", "Thông tin"],
        [
            ["Tên dữ liệu", "Rice (Cammeo and Osmancik)"],
            ["Số hiệu UCI", "545"],
            ["Đường dẫn", "archive.ics.uci.edu/dataset/545"],
            ["DOI", "10.24432/C5MW4Z"],
            ["Quy mô", "3.810 mẫu × 7 đặc trưng"],
            ["Giấy phép", "CC BY 4.0"],
            ["Ngày tải về", "04/10/2026"],
        ],
        caption="Thông tin nguồn dữ liệu",
        widths=[4.5, 11.0],
    )

    report.heading("3.2. Khảo sát dữ liệu và kiểm tra chất lượng", 2)
    report.para(
        "Kết quả kiểm tra cho thấy dữ liệu khá sạch: không có giá trị thiếu, "
        "không có dòng trùng lặp và không có giá trị nằm ngoài danh mục "
        "giá trị của nhãn. Tỉ lệ hai lớp là 1.630 mẫu Cammeo (42,78%) và "
        "2.180 mẫu Osmancik (57,22%), tương đối cân bằng nên nhóm không sử "
        "dụng kỹ thuật tái lấy mẫu."
    )

    report.figure(
        "01_feature_distribution.png",
        "Phân bố bảy đặc trưng hình học theo từng giống gạo",
    )

    report.para(
        "Khảo sát phân bố theo lớp cho thấy hai giống phân biệt rõ ràng về "
        "kích thước: diện tích trung bình của Cammeo là 14.162,9 pixel², cao "
        "hơn 22,6% so với 11.549,8 pixel² của Osmancik; chiều dài trục lớn "
        "cũng chênh 16,6%. Ngược lại, các đặc trưng thuần hình dạng như độ "
        "lệch tâm và tỉ lệ bao lồi chỉ chênh khoảng 2,8%, phân biệt kém. "
        "Nhận xét này được dùng để định hướng lựa chọn đặc trưng và giải "
        "thích hành vi của cây quyết định sau này."
    )

    report.figure(
        "02_class_distribution.png",
        "Phân bố số lượng mẫu và tỉ lệ hai lớp trên ba tập dữ liệu",
    )

    report.heading("3.3. Chia tập dữ liệu", 2)
    report.para(
        "Dữ liệu được chia thành ba tập theo tỉ lệ 70% cho huấn luyện, 15% "
        "cho kiểm tra và 15% cho kiểm thử, sử dụng phương pháp chia có tầng "
        "theo nhãn (stratified) để duy trì tỉ lệ hai lớp trong mỗi tập. Tập "
        "kiểm thử được tách riêng ngay từ đầu và giữ nguyên trong suốt quá "
        "trình, chỉ dùng đúng một lần ở bước báo cáo cuối cùng."
    )

    split_rows = []
    split_names = {"train": "Huấn luyện", "validation": "Kiểm tra", "test": "Kiểm thử"}
    for _, row in data["split"].iterrows():
        split_rows.append([
            split_names.get(row["tap"], row["tap"]),
            f"{int(row['so_mau']):,}",
            f"{row['ty_le_%']:.2f}",
            f"{int(row['Cammeo'])} ({row['Cammeo_%']:.2f}%)",
            f"{int(row['Osmancik'])} ({row['Osmancik_%']:.2f}%)",
        ])
    report.table(
        ["Tập", "Số mẫu", "Tỉ lệ (%)", "Cammeo", "Osmancik"],
        split_rows,
        caption="Kích thước và phân bố lớp của ba tập dữ liệu",
        widths=[2.6, 2.4, 2.2, 4.3, 4.3],
    )

    report.para(
        "Tỉ lệ Cammeo trong ba tập lần lượt là 42,76%, 42,83% và 42,83%, biến "
        "động không quá 0,07 điểm phần trăm. Kết quả kiểm tra trùng lặp cho "
        "thấy không có bản ghi nào xuất hiện ở hai tập khác nhau, do đó không "
        "tồn tại rò rỉ thông tin do bản ghi lặp. Ngưỡng phát hiện ngoại lệ "
        "theo quy tắc khoảng liên tứ phân kế đã được tính trên tập huấn "
        "luyện rồi mới áp dụng cho tập kiểm tra và kiểm thử, phát hiện 62 ô "
        "ngoại lệ trên tổng số 18.662 ô, tương đương 0,33% — một tỉ lệ rất "
        "nhỏ. Nhóm quyết định giữ nguyên các mẫu này vì chúng phản ánh hình "
        "thạch thật của hạt gạo, đồng thời công khai giới hạn này trong báo "
        "cáo thay vì loại bỏ âm thầm."
    )

    report.page_break()

    report.heading("3.4. Đường cơ sở", 2)
    report.para(
        "Trước khi xây dựng mô hình chính, nhóm thiết lập ba đường cơ sở để "
        "có chuẩn so sánh. Nếu chỉ báo cáo kết quả của một mô hình mà không "
        "có đường cơ sở thì không thể chứng minh mô hình đó thực sự tốt."
    )

    baseline_rows = []
    for _, row in data["baseline"].iterrows():
        baseline_rows.append([
            row["model"],
            f"{row['accuracy']:.4f}",
            f"{row['f1']:.4f}",
            row["note"],
        ])
    report.table(
        ["Đường cơ sở", "Accuracy", "F1", "Ghi chú"],
        baseline_rows,
        caption="Kết quả ba đường cơ sở trên tập kiểm tra",
        widths=[4.6, 2.2, 2.2, 6.8],
    )

    report.para(
        "Đường cơ sở đơn giản nhất là đoán lớp đa số, đạt độ chính xác 57,17% "
        "bằng tỉ lệ của lớp Osmancik. Đường cơ sở thứ hai là cây quyết định "
        "một nhánh, đạt 93,18% — mức này cho thấy chỉ với một phép so sánh duy "
        "nhất trên đặc trưng chiều dài trục lớn đã phân loại được phần lớn mẫu. "
        "Đường cơ sở thứ ba dùng một ngưỡng đơn giản trên diện tích. Nhóm đã "
        "thử cả hai chiều của quy tắc ngưỡng vì trực giác ban đầu cho rằng "
        "Cammeo là hạt nhỏ, trong khi khảo sát dữ liệu cho thấy chiều ngược "
        "lại. Kết quả đúng đắn đòi hỏi kiểm chứng trên dữ liệu thật chứ không "
        "thể suy đoán từ trực giác."
    )

    report.page_break()

    # ===================== CHUC 4 =====================
    report.heading("CHƯƠNG 4. THIẾT KẾ THÍ NGHIỆM VÀ KẾT QUẢ", 1)

    report.heading("4.1. Thiết kế thí nghiệm", 2)
    report.para(
        "Nhóm thực hiện bốn thí nghiệm bắt buộc, mỗi thí nghiệm trả lời một "
        "câu hỏi cụ thể. Toàn bộ thí nghiệm đều sử dụng chung một cách chia "
        "tập và chung một đơn vị đánh giá để bảo đảm tính công bằng. Tham số "
        "được chọn bằng kiểm tra chéo trên tập huấn luyện, không sử dụng tập "
        "kiểm thử."
    )
    report.table(
        ["Số", "Thí nghiệm", "Câu hỏi trả lời"],
        [
            ["1", "Độ chính xác theo max_depth", "Cây sâu thêm có tốt hơn không, và từ đâu bắt đầu xấu đi?"],
            ["2", "Cắt tỉa bằng ccp_alpha qua CV", "Cắt tỉa ảnh hưởng thế nào đến hiệu năng?"],
            ["3", "So sánh cây và rừng", "Nên chọn mô hình nào cho bài toán này?"],
            ["4", "Phân tích vùng đặc trưng của lỗi", "Các mẫu sai có đặc điểm chung nào?"],
        ],
        caption="Bốn thí nghiệm bắt buộc",
        widths=[1.4, 5.2, 9.0],
    )

    report.heading("4.2. Kết quả thí nghiệm 1: ảnh hưởng của độ sâu cây", 2)
    report.para(
        "Độ chính xác trên tập huấn luyện tăng đơn điệu theo độ sâu cây, từ "
        "93,25% ở cây một tầng lên 100% ở cây không giới hạn. Trong khi đó độ "
        "chính xác trên tập kiểm tra tăng nhẹ đến độ sâu 4 rồi bắt đầu giảm, "
        "xuống 89,86% khi cây không giới hạn. Khoảng cách giữa hai đường đồ "
        "thị đạt 10,14 điểm phần trăm, là hình ảnh điển hình của hiện tượng "
        "quá khớp. Số lá của cây tăng từ 2 lên 190 lá."
    )

    depth_rows = []
    for _, row in data["exp1"].iterrows():
        depth_rows.append([
            str(row["max_depth"]),
            f"{row['train_acc']:.4f}",
            f"{row['valid_acc']:.4f}",
            f"{row['valid_f1']:.4f}",
            f"{row['gap']:+.4f}",
            str(int(row["n_leaves"])),
        ])
    report.table(
        ["max_depth", "Train Acc", "Valid Acc", "Valid F1", "Chênh lệch", "Số lá"],
        depth_rows,
        caption="Ảnh hưởng của độ sâu cây đến độ chính xác và hiện tượng quá khớp",
        widths=[2.6, 2.6, 2.6, 2.4, 2.6, 2.0],
    )

    report.figure(
        "03_exp1_max_depth.png",
        "Độ chính xác và khoảng cách quá khớp theo độ sâu cây",
    )

    report.heading("4.3. Kết quả thí nghiệm 2: tác dụng của cắt tỉa", 2)
    report.para(
        "Cây được xây dựng không giới hạn độ sâu, sau đó đánh giá hiệu quả của "
        "cắt tỉa qua kiểm tra chéo 5 lần trên tập huấn luyện. Kết quả cho "
        "thấy F1 tăng từ 0,8757 khi không cắt lên 0,9168 tại ccp_alpha = 0,005, "
        "đồng thời số lá rút từ 190 xuống còn 4. Đây là kết quả quan trọng vì "
        "cắt tỉa không chỉ làm cây gọn hơn mà còn làm tăng độ chính xác: các "
        "nhánh bị cắt bỏ vốn chỉ ghi nhớ nhiễu. Các giá trị ccp_alpha lớn hơn "
        "0,005 cho kết quả tương đương do cây đã đạt trạng thái tối thiểu."
    )

    alpha_rows = []
    for _, row in data["exp2"].iterrows():
        alpha_rows.append([
            f"{row['ccp_alpha']:.4f}",
            f"{row['cv_f1_mean']:.4f}",
            f"±{row['cv_f1_std']:.4f}",
            f"[{row['cv_f1_min']:.4f}, {row['cv_f1_max']:.4f}]",
            str(int(row["n_leaves"])),
        ])
    report.table(
        ["ccp_alpha", "F1 trung bình", "Độ lệch chuẩn", "Khoảng giá trị", "Số lá"],
        alpha_rows,
        caption="Hiệu quả của cắt tỉa theo ccp_alpha qua kiểm tra chéo 5 lần",
        widths=[2.6, 3.0, 2.8, 4.4, 2.0],
    )

    report.figure(
        "04_exp2_ccp_alpha.png",
        "Hiệu quả cắt tỉa và số lá của cây theo ccp_alpha",
    )

    report.page_break()

    report.heading("4.4. Kết quả thí nghiệm 3: so sánh cây và rừng", 2)
    report.para(
        "Bảng dưới đây so sánh năm cấu hình mô hình trên tập kiểm tra, xét "
        "theo ba tiêu chí: độ chính xác, thời gian huấn luyện và khả năng giải "
        "thích."
    )

    compare_rows = []
    for _, row in data["exp3"].iterrows():
        compare_rows.append([
            row["mo_hinh"],
            f"{row['valid_acc']:.4f}",
            f"{row['valid_f1']:.4f}",
            f"{row['train_time_s']:.3f}",
            row["kich_thuoc"],
            row["giai_thich"],
        ])
    report.table(
        ["Mô hình", "Acc", "F1", "Train (s)", "Quy mô", "Giải thích"],
        compare_rows,
        caption="So sánh cây quyết định và rừng ngẫu nhiên",
        widths=[4.4, 1.8, 1.8, 2.0, 3.0, 3.4],
    )

    report.figure(
        "05_exp3_model_comparison.png",
        "So sánh mô hình theo hiệu quả, tốc độ và khả năng giải thích",
    )

    report.para(
        "Kết quả cho thấy cây quyết định cắt tỉa và rừng ngẫu nhiên có độ "
        "chính xác gần như tương đương, thậm chí cây đơn còn nhỉnh hơn một "
        "chút. Rừng ngẫu nhiên chậm hơn khoảng mười hai lần khi huấn luyện "
        "và có tổng số lá lớn hơn nhiều lần. Quan trọng hơn, rừng không tạo "
        "được một tập quy tắc đơn để đọc, trong khi cây cho ra quy tắc tường "
        "minh. Trên cơ sở đó, nhóm chọn cây quyết định làm mô hình chính. Đây "
        "là lựa chọn dựa trên bằng chứng đo được, không phải đánh đổi để đạt "
        "điểm số cao hơn."
    )

    report.heading("4.5. Kết quả thí nghiệm 4: phân tích lỗi", 2)
    report.para(
        "Một con số độ chính xác không cho biết mô hình sai như thế nào. Vì "
        "vậy nhóm phân tích chi tiết các mẫu bị dự đoán sai, tập trung vào hai "
        "câu hỏi: mô hình sai theo hướng nào, và các mẫu sai có đặc điểm "
        "chung nào."
    )

    err_rows = []
    for _, row in data["err_feature"].iterrows():
        err_rows.append([
            row["feature"],
            f"{row['mean_correct']:.2f}",
            f"{row['mean_wrong']:.2f}",
            f"{row['difference']:+.2f}",
        ])
    report.table(
        ["Đặc trưng", "TB mẫu đúng", "TB mẫu sai", "Chênh lệch"],
        err_rows,
        caption="So sánh giá trị trung bình của đặc trưng giữa mẫu đúng và mẫu sai",
        widths=[4.6, 3.4, 3.4, 3.4],
    )

    report.para(
        "Kết quả phân tích cho thấy điểm đáng chú ý: không có đặc trưng nào "
        "phân biệt rõ mẫu đúng và mẫu sai, độ chênh lệch trung bình rất nhỏ so "
        "với độ lệch chuẩn. Điều này cho thấy các mẫu bị sai không tập trung ở "
        "một vùng đặc trưng bất thường nào, mà nằm rải rác trong vùng chồng "
        "lấn thật sự giữa hai giống. Giới hạn này có bản chất là giới hạn của "
        "phương pháp đo đặc trưng, không phải lỗi kỹ thuật có thể khắc phục "
        "bằng cách điều chỉnh mô hình."
    )

    report.figure(
        "06_exp4_error_analysis.png",
        "Phân bố các mẫu sai theo hướng và theo độ tin cậy của mô hình",
    )

    report.page_break()

    # ===================== KET QUA CUOI =====================
    report.heading("4.6. Kết quả trên tập kiểm thử", 2)
    report.para(
        f"Sau khi chọn ccp_alpha = {final['ccp_alpha']} bằng kiểm tra chéo trên "
        f"tập huấn luyện và xác nhận trên tập kiểm tra, mô hình cuối được "
        "huấn luyện trên hợp nhất tập huấn luyện và tập kiểm tra, sau đó đánh "
        "giá đúng một lần duy nhất trên tập kiểm thử."
    )

    report.table(
        ["Chỉ số", "Tập kiểm tra", "Tập kiểm thử"],
        [
            ["Accuracy", f"{valid['accuracy']:.4f}", f"{test['accuracy']:.4f}"],
            ["Precision (Cammeo)", f"{valid['precision']:.4f}", f"{test['precision']:.4f}"],
            ["Recall (Cammeo)", f"{valid['recall']:.4f}", f"{test['recall']:.4f}"],
            ["F1 (Cammeo)", f"{valid['f1']:.4f}", f"{test['f1']:.4f}"],
            ["ROC-AUC", f"{valid['roc_auc']:.4f}", f"{test['roc_auc']:.4f}"],
        ],
        caption="Kết quả đánh giá của mô hình trên tập kiểm tra và tập kiểm thử",
        widths=[6.0, 4.7, 4.7],
    )

    report.table(
        ["", "Dự đoán Cammeo", "Dự đoán Osmancik"],
        [
            ["Thực tế Cammeo", f"{cm['tn']} (đúng)", f"{cm['fp']} (sai)"],
            ["Thực tế Osmancik", f"{cm['fn']} (sai)", f"{cm['tp']} (đúng)"],
        ],
        caption="Ma trận nhầm lẫn trên tập kiểm thử",
        widths=[5.0, 5.2, 5.2],
    )

    report.figure(
        "07_confusion_matrix_roc.png",
        "Ma trận nhầm lẫn và đường cong ROC trên tập kiểm thử",
    )

    n_wrong = cm["fp"] + cm["fn"]
    fn_share = 100.0 * cm["fp"] / n_wrong if n_wrong else 0
    report.para(
        f"Tổng số mẫu sai trên tập kiểm thử là {n_wrong} trên {test['n_samples']} "
        f"mẫu, tương đương {100.0 * n_wrong / test['n_samples']:.2f}%. Trong đó "
        f"{fn_share:.1f}% là lỗi bỏ sót Cammeo — mẫu thực tế là Cammeo nhưng "
        "mô hình dự đoán Osmancik. Mô hình có xu hướng nghiêng về lớp đông hơn, "
        "điều này phù hợp với việc F1 được tính cho lớp thiểu số."
    )

    stability = final["seed_stability"]
    report.para(
        f"Độ chính xác trên tập kiểm thử thấp hơn tập kiểm tra. Nhóm đã kiểm "
        f"tra xem đây có phải lỗi hay là biến động tự nhiên bằng cách lặp lại "
        f"toàn bộ quy trình trên năm giá trị khác nhau của tham số ngẫu nhiên "
        f"({', '.join(str(s) for s in stability['seeds'])}). F1 dao động trong "
        f"khoảng {min(stability['f1_scores']):.4f} đến "
        f"{max(stability['f1_scores']):.4f} với độ lệch chuẩn "
        f"{stability['std']:.4f}. Chênh lệch giữa hai tập nằm trong phạm vi "
        "biến động này, cho thấy kết quả không phụ thuộc may rủi. Quan trọng "
        "hơn, tập kiểm thử chỉ được sử dụng đúng một lần và không có bất kỳ "
        "điều chỉnh nào được thực hiện sau khi xem kết quả, nên con số này phản "
        "ánh trung thực năng lực của mô hình."
    )

    report.heading("4.7. Quy tắc của mô hình", 2)
    report.para(
        "Do mô hình là cây quyết định, toàn bộ logic dự đoán đều có thể trình "
        "bày bằng các phép so sánh. Quy tắc được rút gọn còn hai lá cho cùng "
        "kết quả với bản cây đầy đủ bốn lá, do hai nhánh con trùng nhãn không "
        "đóng góp thêm thông tin."
    )
    simplified = final.get("simplification_check", [])
    if simplified:
        report.figure(
            "08_tree_rules.png",
            "Toàn bộ quy tắc của cây quyết định sau cắt tỉa",
        )

    report.para(
        "Quy tắc rút gôn: nếu chiều dài trục lớn không vượt quá 192,17 pixel "
        "thì hạt gạo là Osmancik, ngược lại là Cammeo. Quy tắc này cho thấy "
        "mô hình tập trung vào một đặc trưng duy nhất, phù hợp với kết quả khảo "
        "sát cho thấy hai giống phân biệt nhau chủ yếu về kích thước."
    )

    report.page_break()

    # ===================== CHUC 5 =====================
    report.heading("CHƯƠNG 5. XÂY DỰNG ỨNG DỤNG", 1)

    report.heading("5.1. Thiết kế ứng dụng", 2)
    report.para(
        "Ứng dụng gồm ba màn hình: giới thiệu phạm vi và giới hạn, màn hình "
        "thao tác chính với biểu mẫu nhập bảy đặc trưng, và bảng điều khiển "
        "đánh giá kèm thẻ mô hình. Hệ thống backend dùng FastAPI với thư viện "
        "Pydantic để kiểm tra dữ liệu đầu vào, frontend dùng HTML, CSS và "
        "JavaScript thuần nhằm tránh phụ thuộc công cụ dựng giao diện phức tạp."
    )

    report.heading("5.2. Cơ chế tách biết huấn luyện và phục vụ", 2)
    report.para(
        "Theo yêu cầu tách biết huấn luyện ngoại tuyến và phục vụ trực tuyến, "
        "ứng dụng chỉ nạp mô hình đã được lưu sẵn và không huấn luyện lại ở "
        "mỗi yêu cầu. Tệp mô hình được tạo bởi bước đóng băng và lưu kèm "
        "cấu hình cùng tham số ngẫu nhiên, bảo đảm kết quả phục vụ trùng khớp "
        "với kết quả đã báo cáo."
    )

    report.heading("5.3. Kiểm tra dữ liệu đầu vào", 2)
    report.para(
        "Đề yêu cầu ứng dụng không âm thầm thay thế giá trị. Nhóm thiết kế "
        "theo hai lớp kiểm tra. Lớp thứ nhất kiểm tra tính hợp lệ của dữ liệu: "
        "thiếu trường, sai kiểu số, giá trị âm hoặc bằng không, và giá trị nằm "
        "ngoài khoảng 0 đến 1 đối với các đặc trưng chuẩn hóa — tất cả đều bị "
        "từ chối kèm thông báo chỉ rõ trường nào lỗi. Lớp thứ hai kiểm tra "
        "giá trị có nằm trong vùng quan sát được của tập dữ liệu gốc hay không. "
        "Với trường hợp này, ứng dụng vẫn trả kết quả nhưng kèm cảnh báo rõ "
        "ràng, đồng thời giữ nguyên giá trị người dùng nhập. Giao diện cũng "
        "hiển thị đơn vị và khoảng giá trị hợp lệ ngay cạnh mỗi ô nhập."
    )

    report.table(
        ["Loại đầu vào", "Cách xử lý"],
        [
            ["Thiếu trường", "Từ chối, báo rõ trường thiếu"],
            ["Không phải số", "Từ chối"],
            ["Giá trị âm hoặc bằng 0", "Từ chối"],
            ["Ngoài khoảng 0–1 với Eccentricity, Extent", "Từ chối"],
            ["Ngoài vùng dữ liệu gốc", "Trả kết quả kèm cảnh báo, giữ nguyên giá trị"],
            ["Độ tin cậy dưới 90%", "Hiển thị khuyến nghị kiểm tra lại bằng mắt"],
        ],
        caption="Quy tắc kiểm tra dữ liệu đầu vào của ứng dụng",
        widths=[7.4, 8.0],
    )

    report.heading("5.4. Kiểm thử", 2)
    report.para(
        "Nhóm xây dựng mười sáu trường hợp kiểm thử tự động, bao gồm kiểm tra "
        "dịch vụ còn hoạt động, phân loại đúng với dữ liệu hợp lệ, phân biệt "
        "được hai vị trí cực trần của đặc trưng, và các trường hợp đầu vào sai "
        "như thiếu trường, sai kiểu, giá trị âm, giá trị ngoài khoảng chuẩn hóa. "
        "Trường hợp quan trọng nhất là kiểm thử xác nhận giá trị ngoài vùng dữ "
        "liệu được trả về kèm cảnh báo mà không bị thay thế, trực tiếp đáp ứng "
        "yêu cầu của đề. Kết quả chạy mười sáu trên mười sáu trường hợp đạt."
    )

    report.page_break()

    # ===================== CHUC 6 =====================
    report.heading("CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", 1)

    report.heading("6.1. Kết luận", 2)
    report.para(
        "Đồ án đã hoàn thành đầy đủ quy trình từ tải và kiểm tra dữ liệu, xây "
        "dựng và so sánh mô hình, phân tích lỗi, đến đóng gói thành ứng dụng "
        "web có API và bộ kiểm thử. Mô hình cây quyết định cắt tỉa đạt độ "
        f"chính xác {test['accuracy']:.2f}%, F1 {test['f1']:.2f}% và ROC-AUC "
        f"{test['roc_auc']:.4f} trên tập kiểm thử đánh giá một lần duy nhất."
    )
    report.para(
        "Trong ba phát hiện của quá trình thực hiện, phát hiện thứ nhất là bài "
        "toán dễ hơn nhiều so với dự kiến: một cây chỉ có một nhánh đã đạt "
        "93,18%, gần bằng mức của mô hình cuối. Phát hiện này không làm giảm "
        "giá trị của mô hình nhưng thay đổi cách diễn giải kết quả — điểm số cao "
        "phần lớn đến từ tính chất phân biệt rõ của dữ liệu chứ không phải từ "
        "độ phức tạp của thuật toán."
    )
    report.para(
        "Phát hiện thứ hai cho thấy cắt tỉa không chỉ đơn thuần làm giảm độ "
        "phức tạp mà còn làm tăng độ chính xác: cây được rút từ 190 lá xuống 4 "
        "lá trong khi F1 tăng từ 0,8757 lên 0,9168. Phát hiện thứ ba là rừng "
        "ngẫu nhiên không vượt trội cây đơn trên bài toán này, mà còn chậm hơn và "
        "không giải thích được, từ đó củng cố lựa chọn cây đơn làm mô hình chính."
    )
    report.para(
        "Về phương pháp, điểm đáng chú ý nhất là nguyên tắc chống rò rỉ thông "
        "tin được thực thi nghiêm ngặt: mọi tham số đều chọn bằng kiểm tra chéo "
        "trên tập huấn luyện, mọi ngưỡng suy ra từ dữ liệu đều tính trên tập "
        "huấn luyện, và tập kiểm thử chỉ dùng đúng một lần. Việc chạy lại quy "
        "trình hai lần cho kết quả hoàn toàn giống nhau đã được kiểm chứng, củng "
        "cố tính tái lập của nghiên cứu."
    )

    report.heading("6.2. Hạn chế của đồ án", 2)
    report.bullets([
        "Chỉ phân loại được hai giống có trong dữ liệu; mọi giống gạo khác sẽ "
        "bị gán nhầm vào một trong hai nhãn.",
        "Đặc trưng phải được đo theo đúng quy trình ảnh chụp của dữ liệu gốc; "
        "đo sai quy trình sẽ cho kết quả sai.",
        "Tỉ lệ sai khoảng 9% có bản chất là giới hạn của phương pháp đo đặc "
        "trưng, do hai giống có vùng chồng lấn thật sự.",
        "Dữ liệu chỉ gồm 3.810 mẫu từ một nguồn, chưa chứng minh được hành vi "
        "khi đổi thiết bị, điều kiện chụp ảnh hay giống gạo.",
        "Chưa so sánh với các họ mô hình khác ngoài phạm vi bài học như k-láng "
        "giềng cận hay máy vectơ hỗ trợ.",
        "Xác suất dự đoán của cây quyết định không mịn, do chỉ cho giá trị tại "
        "các lá, nên không dùng được cho kiểm định độ tin cậy.",
    ])

    report.heading("6.3. Hướng phát triển", 2)
    report.bullets([
        "Bổ sung đặc trưng về màu sắc và kết cấu hạt để thu hẹp vùng chồng lấn "
        "giữa hai giống.",
        "Thu thập dữ liệu từ nhiều điều kiện canh tác để đánh giá độ bền với "
        "thay đổi điều kiện.",
        "Xây dựng cơ chế đưa ra khuyến nghị kiểm tra thủ công đối với các mẫu "
        "nằm trong vùng chồng lấn.",
        "Bổ sung đơn vị đo theo vùng địa lý để đánh giá khả năng chuyển đổi "
        "mô hình.",
    ])

    report.heading("6.4. Đạo đức và sử dụng có trách nhiệm", 2)
    report.para(
        "Mô hình chỉ nên dùng làm công cụ sàng lọc sơ bộ trong dây chuyền đóng "
        "gói, kết hợp với kiểm nghiểm của người có chuyên môn. Ứng dụng không "
        "thay thế được kiểm nghiệm giống hoặc kiểm nghiệm chất lượng theo quy "
        "định. Dữ liệu sử dụng được phân phối theo giấy phép CC BY 4.0, không "
        "chứa thông tin cá nhân, chỉ gồm các phép đo hình thọc trên hạt gạo."
    )

    report.page_break()

    # ===================== TAI LIEU =====================
    report.heading("TÀI LIỆU THAM KHẢO", 1)
    references = [
        "[1] Trường Đại học Công nghệ Kỹ thuật Hưng Yên. Slide học phần Học máy "
        "cơ bản: Bài 6 — Cây quyết định, cắt tỉa và rừng ngẫu nhiên.",

        "[2] Cinar, I., & Koklu, M. (2019). Classification of Rice Varieties "
        "Using Artificial Intelligence Methods. International Journal of "
        "Intelligent Systems and Applications in Engineering, 7(3), 188–194. "
        "https://doi.org/10.18201/ijisae.2019355381",

        "[3] UCI Machine Learning Repository. Rice (Cammeo and Osmancik), "
        "Dataset số 545. https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik",

        "[4] tien, D., et al. scikit-learn: Machine Learning in Python. "
        "https://scikit-learn.org/stable/modules/tree.html",

        "[5] Harris, C. R., et al. (2020). Array programming with NumPy. "
        "Nature, 585(7825), 357–362.",

        "[6] McKinney, W. (2010). Data Structures for Statistical Computing in "
        "Python. Proceedings of the 9th Python in Science Conference.",

        "[7] Hunter, J. D. (2007). Matplotlib: A 2D Graphics Environment. "
        "Computing in Science & Engineering, 9(3), 90–95.",

        "[8] Pedregosa, F., et al. (2011). Scikit-learn: Machine Learning in "
        "Python. Journal of Machine Learning Research, 12, 2825–2830.",
    ]
    for item in references:
        report.para(item, align="justify")

    report.heading("DANH MỤC HÌNH ẢNH", 1)
    captions = [
        "Hình 1. Phân bố bảy đặc trưng hình học theo từng giống gạo",
        "Hình 2. Phân bố số lượng mẫu và tỉ lệ hai lớp trên ba tập dữ liệu",
        "Hình 3. Độ chính xác và khoảng cách quá khớp theo độ sâu cây",
        "Hình 4. Hiệu quả cắt tỉa và số lá của cây theo ccp_alpha",
        "Hình 5. So sánh mô hình theo hiệu quả, tốc độ và khả năng giải thích",
        "Hình 6. Phân bố các mẫu sai theo hướng và theo độ tin cậy của mô hình",
        "Hình 7. Ma trận nhầm lẫn và đường cong ROC trên tập kiểm thử",
        "Hình 8. Toàn bộ quy tắc của cây quyết định sau cắt tỉa",
    ]
    for caption in captions:
        report.para(caption, align="justify")

    report.page_break()

    # ===================== PHU LUC =====================
    report.heading("PHỤ LỤC A. CẤU TRÚC MÃ NGUỒN", 1)
    structure = [
        "data/README.md — hồ sơ dữ liệu và data dictionary",
        "scripts/download_data.py — tải dữ liệu, kiểm tra checksum",
        "src/config.py — cấu hình chung, tham số ngẫu nhiên, nhãn lớp",
        "src/data.py — kiểm tra chất lượng dữ liệu",
        "src/split.py — chia tập và chống rò rỉ thông tin",
        "src/baseline.py — ba đường cơ sở",
        "src/train.py — thí nghiệm độ sâu, cắt tỉa, so sánh cây và rừng",
        "src/evaluate.py — phân tích lỗi",
        "src/visualize.py — sinh tám biểu đồ",
        "src/final.py — đóng băng mô hình, đánh giá tập kiểm thử một lần",
        "app/api.py — máy chủ FastAPI và kiểm tra đầu vào",
        "app/static/ — giao diện HTML, CSS, JavaScript",
        "tests/test_api.py — mười sáu trường hợp kiểm thử",
        "reports/ — kết quả thí nghiệm, model card, data card, nhật ký",
    ]
    for item in structure:
        report.para(item, align="left")

    report.heading("PHỤ LỤC B. QUY TRÌNH TÁI LẬP KẾT QUẢ", 1)
    report.para(
        "Toàn bộ kết quả trong báo cáo được tái tạo bằng các lệnh sau, chạy theo "
        "đúng thứ tự với môi trường Python 3.12 và các thư viện trong tệp "
        "requirements.txt:"
    )
    commands = [
        "pip install -r requirements.txt",
        "python scripts/download_data.py   # tải dữ liệu và kiểm tra checksum",
        "python src/data.py                # kiểm tra chất lượng dữ liệu",
        "python src/split.py               # chia tập, kiểm tra rò rỉ thông tin",
        "python src/baseline.py            # đường cơ sở",
        "python src/train.py               # ba thí nghiệm đầu",
        "python src/evaluate.py            # phân tích lỗi",
        "python src/visualize.py           # sinh biểu đồ",
        "python src/final.py               # đóng băng, đánh giá kiểm thử một lần",
        "pytest tests/ -v                  # mười sáu trường hợp kiểm thử",
        "python app/api.py                 # khởi động ứng dụng web",
    ]
    for command in commands:
        paragraph = report.doc.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(1.0)
        paragraph.paragraph_format.space_after = Pt(3)
        run = paragraph.add_run(command)
        run.font.name = "Consolas"
        run.font.size = Pt(11)

    report.para(
        "Tham số ngẫu nhiên được đặt cố định ở giá trị 42 và khai báo tập trung "
        "trong tệp cấu hình. Nhóm đã chạy lại toàn bộ quy trình hai lần và "
        "xác nhận các chỉ số trên tập kiểm thử hoàn toàn giống nhau, bao gồm "
        "độ chính xác, F1, ROC-AUC và ma trận nhầm lẫn.",
        align="justify",
    )

    report.heading("PHỤ LỤC C. THÔNG TIN MÔI TRƯỜNG", 1)
    environment = final["moi_truong"]
    env_rows = [
        ["Python", environment["python"]],
        ["Nền tảng", environment["platform"]],
        ["scikit-learn", environment["sklearn"]],
        ["Thời điểm chạy", environment["timestamp"]],
    ]
    for package in ["pandas", "numpy", "matplotlib"]:
        env_rows.append([package, "xem requirements.txt"])

    report.table(
        ["Thành phần", "Giá trị"],
        env_rows,
        caption="Môi trường thực thi của đồ án",
        widths=[5.0, 10.4],
    )


# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 66)
    print("SINH BAO CAO WORD")
    print("=" * 66)

    print("\n[1/3] Nap ket qua that...")
    data = load_results()
    print(f"      test accuracy = {data['final']['test_metrics']['accuracy']:.4f}")

    print("\n[2/3] Viet bao cao...")
    report = Report()
    write_cover(report)
    write_content(report, data)

    print("\n[3/3] Luu tep...")
    report.doc.save(OUTPUT)

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"\n  Da tao: {OUTPUT.name} ({size_kb:.0f} KB)")
    print(f"  So bang: {report.table_index}")
    print(f"  So hinh: {report.figure_index}")
    print()
    print("  NHO: sua ten sinh vien trong SCRIPTS/make_report.py truoc khi in lai.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
