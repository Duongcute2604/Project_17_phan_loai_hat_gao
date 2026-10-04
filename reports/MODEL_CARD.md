# Model Card — Phân loại giống gạo Cammeo / Osmancik

Phiên bản 1.0 · Ngày 04/10/2026

---

## 1. Tóm tắt

| Mục | Nội dung |
|---|---|
| **Tên** | Bộ phân loại 2 giống gạo (cây quyết định cắt tỉa) |
| **Nhiệm vụ** | Phân loại nhị phân, đơn vị quan sát = 1 hạt gạo |
| **Mô hình** | `DecisionTreeClassifier(max_depth=None, ccp_alpha=0.005)` |
| **Số lá** | 4 |
| **Đặc trưng đầu vào** | 7 (xem mục 3) |
| **Lớp đầu ra** | `Cammeo` (245 mẫu) · `Osmancik` (327 mẫu) trong tập kiểm thử |
| **Dữ liệu huấn luyện** | UCI ML Repository #545, CC BY 4.0 |
| **`random_state`** | 42 |

---

## 2. Cách sử dụng

### Ý định thiết kế
- Sàng lọc sơ bộ hai giống gạo trong dây chuyền đóng gói.
- Kiểm nhanh, có người trực để quyết định cuối.

### KHÔNG dùng khi
- Thay thế kiểm nghiệm giống hoặc kiểm nghiệm chất lượng.
- Quyết định giá re, pháp lý, hay phân loại biế thể.
- Khi đặc trưng được đo bằng quy trình khác với dữ liệu gốc.

### Yêu cầu đầu vào
7 số đúng đơn vị, đo theo quy trình ảnh chụp chuẩn. Giá trị ngoài vùng dữ
liệu gốc vẫn được xử lý nhưng **kèm cảnh báo**, không tự sửa.

---

## 3. Đặc trưng

| Tên | Ý nghĩa | Đơn vị | Khoảng dữ liệu |
|---|---|---|---|
| `Area` | Diện tích hạt gạo | pixel² | 7.551 – 18.913 |
| `Perimeter` | Chu vi hạt gạo | pixel | 359,1 – 548,4 |
| `Major_Axis_Length` | Chiều dài trục lớn | pixel | 145,3 – 239,0 |
| `Minor_Axis_Length` | Chiều dài trục nhỏ | pixel | 59,5 – 107,5 |
| `Eccentricity` | Độ lệch tâm | 0 – 1 | 0,777 – 0,948 |
| `Convex_Area` | Diện tích bao lồi | pixel² | 7.723 – 19.099 |
| `Extent` | Diện tích thật ÷ bao lồi | 0 – 1 | 0,497 – 0,861 |

Mốc thời gian: đặc trưng có sẵn **ngay sau khi đo xong ảnh một hạt gạo đơn lẻ**,
tức là dùng được trong khâu phân loại trước khi đóng gói.

---

## 4. Quy trình huấn luyện

```
3.810 mẫu gốc
    ├── train      2.666 mẫu (69,97%)  dùng dạy mô hình
    │                                   và chọn tham số (5-fold CV)
    ├── validation   572 mẫu (15,01%)  dùng kiểm tra lựa chọn
    └── test         572 mẫu (15,01%)  dùng MỘT LẦN để báo cáo
```

Các bước:
1. Chia tập **stratified** với `random_state=42`, trước mọi thao tác khác.
2. Chọn `ccp_alpha` bằng **5-fold cross-validation trên tập train**
   (F1 của lớp `Cammeo`).
3. Kiểm tra cấu hình chọn được trên tập validation.
4. Fit mô hình cuối trên **train + validation** (3.238 mẫu).
5. Đánh giá trên tập test **đúng một lần**.

---

## 5. Kết quả đánh giá

### Tập validation (572 mẫu)

| Chỉ số | Giá trị |
|---|---|
| Accuracy | 0.9318 |
| Precision (Cammeo) | 0.9256 |
| Recall (Cammeo) | 0.9143 |
| F1 (Cammeo) | 0.9199 |
| ROC-AUC | 0.9630 |

### Tập kiểm thử (572 mẫu) — đánh giá một lần

| Chỉ số | Giá trị |
|---|---|
| **Accuracy** | **0.9091** |
| Precision (Cammeo) | 0.9106 |
| Recall (Cammeo) | 0.8735 |
| **F1 (Cammeo)** | **0.8917** |
| **ROC-AUC** | **0.9480** |

### Ma trận nhầm lẫn (test)

|  | Dự đoán Cammeo | Dự đoán Osmancik |
|---|---|---|
| **Thực tế Cammeo** | 214 (đúng) | 31 (sai) |
| **Thực tế Osmancik** | 21 (sai) | 306 (đúng) |

Tổng sai: **52 / 572 = 9,09%**. Trong đó 31/52 = 59,6% là lỗi **bỏ sót
Cammeo** — mô hình nghiêng về lớp đông hơn.

### Đối chiếu baseline (validation)

| Mô hình | Accuracy | F1 |
|---|---|---|
| Đoán lớp phổ biến | 0.5717 | 0.0000 |
| Cây 1 nhánh | 0.9318 | 0.9199 |
| Ngưỡng `Area` | 0.8794 | 0.8577 |
| **Cây cắt tỉa (mô hình cuối)** | **0.9318** | **0.9199** |

> **Cần nói thẳng khi trình bày:** cây một nhánh đã đạt 93,18%. Mô hình cắt tỉa
> không vượt baseline — **cùng điểm số nhưng đơn giản hơn nhiều** (1 lá so
> với 4 lá) và giải thích được bằng một quy tắc duy nhất. Cải thiện thật sự so
> với baseline đến từ việc hiểu bài toán, không phải từ độ phức tạp mô hình.

### Độ ổn định

| Seed | F1 trên tập kiểm tra riêng |
|---|---|
| 42 | 0.9199 |
| 7 | 0.9293 |
| 2024 | 0.8941 |
| 123 | 0.9250 |
| 99 | 0.9083 |

Độ lệch chuẩn **0.0127**. Chênh lệch giữa validation và test (0,028) nằm
trong biến động này.

---

## 6. Quy tắc mô hình

Toàn bộ logic của mô hình — không có phần nào ẩn:

```
Major_Axis_Length <= 192.17  →  Osmancik
Major_Axis_Length >  192.17  →  Cammeo
```

Do `ccp_alpha` chưa cắt hết các nhánh con trùng nhãn, cây lưu trữ có 4 lá
nhưng sau khi rút gọn về 2 lá cho **cùng kết quả**. Ứng dụng dùng bản rút gọn
này.

---

## 7. Giới hạn

1. **Chỉ phân loại 2 giống.** Giống khác bị gán nhầm một trong hai.
2. **Phụ thuộc quy trình đo đặc trưng.** Đo sai cách thì kết quả sai.
3. **Vùng chồng lấn thật sự.** Không đặc trưng nào phân biệt rõ mẫu sai với
   mẫu đúng → ~9% sai là giới hạn thực, không phải lỗi kỹ thuật.
4. **Một nguồn dữ liệu, 3.810 mẫu.** Chưa chứng minh được hành vi khi đổi điều
   kiện chụp ảnh, giống gạo, hay thiết bị đo.
5. **Không đánh giá chất lượng, độ chín, hay phân loại biến thể.**
6. **Xác suất không mịn.** Cây quyết định chỉ cho giá trị xác suất tại lá, nên
   không dùng được cho kiểm định xác suất (calibration).

---

## 8. Công cụ khai thác

```bash
python scripts/download_data.py     # tải + checksum
python src/final.py                 # đóng băng + đánh giá test
python app/api.py                   # chạy API
```

Phiên bản môi trường: Python 3.12.10 · scikit-learn 1.9.1 · pandas 3.0.6 ·
numpy 2.5.3 · matplotlib 3.11.2. Ghi trong `reports/FINAL_RESULTS.json`.

---

## 9. Công cụ AI đã dùng

Mã nguồn và báo cáo được hỗ trợ soạn thảo bằng trợ lý AI (OpenCode, mô hình
OpenAI). Cách kiểm chứng:

- **Mọi số liệu trong model card này được lấy từ file kết quả thật**
  (`reports/FINAL_RESULTS.json`), không nhập tay.
- Chạy lại toàn bộ pipeline với `random_state=42` sẽ cho kết quả giống hệt.
- Kiểm thử API: `pytest tests/ -v` → 16/16 đạt.
- Bảng dữ liệu, ma trận nhầm lẫn và quy tắc cây đều in ra từ mô hình đã lưu,
  không viết tay trong báo cáo.
