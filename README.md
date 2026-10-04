# Phân loại hai giống gạo từ hình dạng hạt

**Học máy cơ bản — Bài 6: Cây quyết định, cắt tỉa và rừng ngẫu nhiên**

Phân loại nhị phân hai giống gạo **Cammeo** và **Osmancik** từ 7 đặc trưng
hình học, kèm ứng dụng web có API.

---

## Kết quả chính

| Chỉ số | Validation | Test |
|---|---|---|
| Accuracy | 93.18% | **90.91%** |
| Precision (Cammeo) | 92.56% | 91.06% |
| Recall (Cammeo) | 91.43% | 87.35% |
| F1 (Cammeo) | 91.99% | **89.17%** |
| ROC-AUC | 0.9630 | **0.9480** |

**Baseline** để so sánh (trên validation):

| Baseline | Accuracy | F1 |
|---|---|---|
| Đoán lớp phổ biến | 57.17% | 0.0000 |
| Cây 1 nhánh (`max_depth=1`) | 93.18% | 0.9199 |
| Ngưỡng đơn giản trên `Area` | 87.94% | 0.8577 |

**Mô hình cuối:** `DecisionTreeClassifier(ccp_alpha=0.005)` — cây 4 lá,
accuracy **90.91%** trên tập kiểm thử.

### Ba phát hiện đáng chú ý

1. **Bài toán dễ hơn nhiều so với dự kiến.** Một cây chỉ có **một nhánh**
   (`Major_Axis_Length ≤ 192.17`) đã đạt 93.18%. Mọi điểm số cao hơn phải
   được giải thích cẩn thận, không được coi là hiệu quả vượt trội.

2. **Cắt tỉa cải thiện rõ rệt.** Rút cây từ **190 lá xuống 4 lá** mà F1
   tăng từ 0.8757 lên 0.9168. Đây là bằng chứng mạnh nhất cho cắt tỉa.

3. **Chọn cây đơn thay vì rừng.** Rừng 100 cây cho F1 0.9184 — *thấp hơn*
   cây đơn (0.9199), chậm hơn 12 lần, và không có quy tắc đơn để giải thích.
   Chọn cây là quyết định có bằng chứng, không phải tự hy sinh.

---

## Chạy dự án

### Yêu cầu
- Python 3.10 trở lên (đã kiểm thử với 3.12.10)

### Các bước

```bash
# 1. Tạo môi trường ảo
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. Cài thư viện
pip install -r requirements.txt

# 3. Tải dữ liệu (tự động kiểm tra checksum)
python scripts/download_data.py

# 4. Kiểm tra chất lượng dữ liệu
python src/data.py

# 5. Chia tập + chống rò rỉ thông tin
python src/split.py

# 6. Chạy baseline
python src/baseline.py

# 7. Chạy 4 thí nghiệm bắt buộc
python src/train.py

# 8. Phân tích lỗi
python src/evaluate.py

# 9. Vẽ biểu đồ
python src/visualize.py

# 10. Đóng băng mô hình + đánh giá MỘT LẦN trên test
python src/final.py

# 11. Chạy kiểm thử API
pytest tests/ -v

# 12. Khởi động ứng dụng web
python app/api.py
```

Mở trình duyệt:
- Ứng dụng: <http://127.0.0.1:8000/>
- API docs (tự sinh): <http://127.0.0.1:8000/docs>

> **Lưu ý về bước 10.** `src/final.py` chỉ chạy được **một lần**. Kết quả
> được ghi vào `reports/FINAL_RESULTS.json`; chạy lại sẽ bị chặn. Đây là cơ
> chế bảo vệ nguyên tắc *"test chỉ dùng một lần"*. Nếu thật sự cần chạy lại
> (sửa lỗi code), dùng `--force` và ghi rõ trong báo cáo.

---

## Cấu trúc dự án

```
.
├── data/
│   ├── README.md              Hồ sơ dữ liệu + data dictionary
│   ├── rice.csv               (sinh ra khi chạy script — không commit raw)
│   └── checksums.txt          SHA256 chứng minh dữ liệu gốc
├── scripts/
│   └── download_data.py       Tải + chuyển ARFF → CSV + checksum
├── src/
│   ├── config.py              random_state, pos_label, đường dẫn
│   ├── data.py                Kiểm tra chất lượng dữ liệu
│   ├── split.py               Chia tập + chống rò rỉ thông tin
│   ├── baseline.py            3 đường cơ sở
│   ├── train.py               3 thí nghiệm đầu (max_depth, ccp_alpha, cây vs rừng)
│   ├── evaluate.py            Thí nghiệm 4: phân tích lỗi
│   ├── visualize.py           8 biểu đồ
│   └── final.py               Đóng băng + đánh giá test 1 lần
├── app/
│   ├── api.py                 FastAPI
│   └── static/                HTML + CSS + JS thuần
├── tests/
│   └── test_api.py            16 test
├── models/                    tree_pruned.joblib
└── reports/
    ├── FINAL_RESULTS.json     Kết quả đóng băng
    ├── *.csv                  Bảng số liệu từng thí nghiệm
    └── figures/               8 biểu đồ PNG
```

---

## Phòng chống rò rỉ thông tin

Đây là yêu cầu nghiêm ngặt nhất của đề. Cách thực hiện:

| Nguyên tắc | Cài đặt |
|---|---|
| Chia tập trước mọi thao tác | `src/split.py` chạy đầu tiên, không làm gì với dữ liệu trước đó |
| Giữ nguyên tỉ lệ lớp | `stratify=y`, biến động ≤ 0.07 điểm phần trăm giữa 3 tập |
| Ngưỡng ngoại lệ tính trên train | `find_outliers_iqr(train_df)` rồi áp dụng cho tập khác |
| Chọn tham số bằng CV trên train | `cross_val_score` trong `StratifiedKFold`, không dùng validation |
| Test chỉ dùng 1 lần | `src/final.py` chặn chạy lại trừ khi có `--force` |
| Kiểm tra trùng lặp giữa các tập | `check_overlap()` — 0 dòng trùng |

**Bằng chứng trong báo cáo:** bảng kích thước và tỉ lệ lớp của 3 tập
(`reports/split_report.csv`), kết quả kiểm tra trùng lặp, và so sánh
validation ↔ test.

---

## Kiểm thử

```bash
pytest tests/ -v
```

16 test, bao gồm các trường hợp input xấu:

| Test | Kiểm tra |
|---|---|
| `test_missing_field_rejected` | Thiếu trường → 422 |
| `test_negative_area_rejected` | Diện tích âm → 422 |
| `test_extent_out_of_unit_range_rejected` | `Extent = 5.0` → 422 |
| `test_out_of_domain_returns_warning_not_silent_fix` | Giá trị lạ → 200 **kèm cảnh báo**, không tự sửa |

---

## API

| Endpoint | Mô tả |
|---|---|
| `GET /api/health` | Kiểm tra dịch vụ còn sống |
| `GET /api/value-help` | Khoảng giá trị hợp lệ + đơn vị của 7 đặc trưng |
| `GET /api/model-card` | Chỉ số, quy tắc cây, giới hạn, điều kiện sử dụng |
| `POST /api/rice-classify` | Phân loại một hạt |
| `POST /api/batch-classify` | Phân loại nhiều hạt (tối đa 1000) |

**Ví dụ:**

```bash
curl -X POST http://127.0.0.1:8000/api/rice-classify \
  -H "Content-Type: application/json" \
  -d '{
    "Area": 15231,
    "Perimeter": 525.579,
    "Major_Axis_Length": 229.750,
    "Minor_Axis_Length": 85.094,
    "Eccentricity": 0.9289,
    "Convex_Area": 15617,
    "Extent": 0.5729
  }'
```

**Trả về:**

```json
{
  "prediction": "Cammeo",
  "confidence": 0.968,
  "probabilities": { "Cammeo": 0.968, "Osmancik": 0.032 },
  "rule_applied": [
    "Major_Axis_Length (229.75) > 192.17",
    "Perimeter (525.58) > 467.86",
    "=> Cammeo"
  ],
  "in_domain": true,
  "warnings": [],
  "low_confidence": false
}
```

### Kiểm tra đầu vào

Đề yêu cầu *"không âm thầm thay thế giá trị"*. Vì vậy:

| Loại input | Xử lý |
|---|---|
| Thiếu trường | **Từ chối** (422) |
| Không phải số | **Từ chối** (422) |
| Giá trị âm / bằng 0 khi phải > 0 | **Từ chối** (422) |
| Ngoài khoảng [0, 1] với `Eccentricity`, `Extent` | **Từ chối** (422) |
| Hợp lệ về kiểu nhưng ngoài vùng dữ liệu gốc | Trả kết quả **kèm cảnh báo**, giữ nguyên giá trị |

Không có trường hợp nào bị tự thay thế giá trị.

---

## Đạo đức và giới hạn

- Mô hình là **công cụ sàng lọc sơ bộ**, không thay thế kiểm nghiệm
  chất lượng hay kiểm nghiệm giống chính thức.
- Chỉ nhận diện được 2 giống trong dữ liệu. Giống khác sẽ bị gán nhầm.
- Đặc trưng phải đo theo **cùng quy trình ảnh chụp** như dữ liệu gốc.
- Vùng chồng lấn giữa hai giống không thể tách hoàn toàn bằng đặc trưng
  hình học; ~9% sai là giới hạn thực, không phải lỗi cần sửa.
- Ứng dụng hiển thị cảnh báo khi xác suất dự đoán < 90%, khuyến nghị
  người dùng kiểm tra lại bằng mắt.

---

## Dữ liệu

Rice (Cammeo and Osmancik) — UCI ML Repository #545, giấy phép CC BY 4.0.
3.810 mẫu, 7 đặc trưng, không có giá trị thiếu hoặc dòng trùng.

Chi tiết, checksum và data dictionary: [`data/README.md`](data/README.md)

---

## Tái lập

Mọi kết quả trong báo cáo được tái tạo bằng `random_state = 42` khai báo
tập trung trong `src/config.py`. Kiểm tra độ ổn định qua 5 cách chia tập
(42, 7, 2024, 123, 99) cho F1 dao động 0.8941–0.9293, độ lệch chuẩn 0.0127.
