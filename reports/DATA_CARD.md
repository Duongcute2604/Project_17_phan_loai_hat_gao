# Data Card — Rice (Cammeo and Osmancik)

Phiên bản 1.0 · Ngày 04/10/2026

---

## 1. Tổng quan

| Mục | Nội dung |
|---|---|
| **Tên** | Rice (Cammeo and Osmancik) |
| **Cơ sở** | UCI Machine Learning Repository, số hiệu 545 |
| **Trang** | https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik |
| **DOI** | https://doi.org/10.24432/C5MW4Z |
| **Giấy phép** | **CC BY 4.0** — cho phép dùng lại và trích dẫn |
| **Kích thước** | 3.810 mẫu × 7 đặc trưng + 1 nhãn |
| **Ngôn ngữ** | Không có (dữ liệu số) |
| **Người tạo** | Ilkay Cinar, Murat Koklu — Đại học Selcuk, Konya, Thổ Nhĩ Kỳ |
| **Ngày tải về** | 04/10/2026 |

### Trích dẫn

> Cinar, I., & Koklu, M. (2019). Classification of Rice Varieties Using
> Artificial Intelligence Methods. *International Journal of Intelligent
> Systems and Applications in Engineering*, 7(3), 188–194.
> https://doi.org/10.18201/ijisae.2019355381

---

## 2. Cách dữ liệu được tạo ra

1. Chụp ảnh **3.810 hạt gạo đơn lẻ**, mỗi hạt một ảnh.
2. Tách nền ảnh.
3. Đo 7 đặc trưng hình học cho từng hạt.

Hai giống: **Cammeo** (hạt lớn hơn) và **Osmancik** (hạt nhỏ hơn).

> **Giới hạn quan trọng:** quy trình tách nền và đo đặc trưng **không được mô
> tả chi tiết** trong tài liệu gốc. Vì vậy đặc trưng có thể khác nhau đáng kể
> nếu dùng phần mềm khác. Đây là lý do mô hình chỉ được dùng khi đặc trưng
> đo theo **cùng quy trình** với dữ liệu gốc.

---

## 3. Schema

| Tên biến | Kiểu | Đơn vị | Vai trò | Mô tả |
|---|---|---|---|---|
| `Area` | int | pixel² | feature | Diện tích hạt |
| `Perimeter` | float | pixel | feature | Chu vi hình thuộc bao |
| `Major_Axis_Length` | float | pixel | feature | Chiều dài trục lớn nhất |
| `Minor_Axis_Length` | float | pixel | feature | Chiều dài trục nhỏ nhất |
| `Eccentricity` | float | 0–1 | feature | Độ lệch tâm |
| `Convex_Area` | int | pixel² | feature | Diện tích bao lồi |
| `Extent` | float | 0–1 | feature | Diện tích thật ÷ bao lồi |
| `Class` | str | — | target | `Cammeo` hoặc `Osmancik` |

**Không có cột định danh.** Mỗi dòng là một hạt gạo độc lập.

### Kiểu nội dung dạng chuỗi (categorical)

| Giá trị | Ý nghĩa |
|---|---|
| `Cammeo` | Giống Cammeo |
| `Osmancik` | Giống Osmancik |

### Khoảng giá trị quan sát

| Đặc trưng | Nhỏ nhất | Lớn nhất | Trung vị | Trung bình | Độ lệch chuẩn |
|---|---|---|---|---|---|
| `Area` | 7.551 | 18.913 | 12.421,5 | 12.667,7 | 1.732,4 |
| *(khoảng của Cammeo riêng)* | 9.908 | 18.913 | | 14.162,9 | |
| `Perimeter` | 359,10 | 548,45 | 448,85 | 454,24 | 35,60 |
| `Major_Axis_Length` | 145,26 | 239,01 | 185,81 | 188,78 | 17,45 |
| `Minor_Axis_Length` | 59,53 | 107,54 | 86,43 | 86,31 | 5,73 |
| `Eccentricity` | 0,7772 | 0,9480 | 0,8891 | 0,8869 | 0,0208 |
| `Convex_Area` | 7.723 | 19.099 | 12.706,5 | 12.952,5 | 1.777,0 |
| `Extent` | 0,4974 | 0,8610 | 0,6454 | 0,6619 | 0,0772 |

---

## 4. Phân bố lớp

| Lớp | Số mẫu | Tỉ lệ |
|---|---|---|
| Cammeo | 1.630 | 42,78% |
| Osmancik | 2.180 | 57,22% |

**Tỉ lệ 1,34 : 1 — cân bằng vừa phải.** Không dùng resampling.

Sau khi chia tập stratified, tỉ lệ giữ nguyên trong cả 3 tập:

| Tập | Số mẫu | Cammeo | Osmancik | Biến động tỉ lệ |
|---|---|---|---|---|
| train | 2.666 (69,97%) | 42,76% | 57,24% | 0,07 pp |
| validation | 572 (15,01%) | 42,83% | 57,17% | |
| test | 572 (15,01%) | 42,83% | 57,17% | |

### Phân bố đặc trưng theo lớp

| Đặc trưng | Cammeo (TB) | Osmancik (TB) | Chênh lệch |
|---|---|---|---|
| `Area` | 14.162,9 | 11.549,8 | +2.613 (**+22,6%**) |
| `Major_Axis_Length` | 205,48 | 176,29 | +29,19 (**+16,6%**) |
| `Perimeter` | 487,44 | 429,42 | +58,02 (+13,5%) |
| `Minor_Axis_Length` | 88,77 | 84,48 | +4,29 (+5,1%) |
| `Eccentricity` | 0,8993 | 0,8745 | +0,0248 (+2,8%) |
| `Extent` | 0,6689 | 0,6505 | +0,0184 (+2,8%) |

So sánh tương đối: `Area` chênh **22,6%** còn `Eccentricity` và `Extent` chỉ
chênh **2,8%**.

**Phát hiện:** hai giống phân biệt được rõ qua **kích thước** (`Area`,
`Major_Axis_Length`). Các đặc trưng hình dạng (`Eccentricity`, `Extent`) phân
biệt rất kém. Đây là lý do cây quyết định chọn `Major_Axis_Length` làm điều
kiện tách đầu tiên.

---

## 5. Chất lượng dữ liệu

Kết quả kiểm tra bằng `python src/data.py`:

| Kiểm tra | Kết quả |
|---|---|
| **Giá trị thiếu** | **0** trên cả 8 cột |
| **Dòng trùng lặp** | **0** |
| **Nhãn ngoài danh sách** | Không có |
| **Giá trị không hợp lệ** | Không có |

### Phát hiện ngoại lệ (IQR, tính trên tập train)

Tính trên **tập train** (2.666 mẫu × 7 đặc trưng = 18.662 ô):

| Đặc trưng | Số ô ngoại lệ | Tỉ lệ | Khoảng hợp lệ (tính trên train) |
|---|---|---|---|
| `Area` | 2 | 0,075% | [7.431,9; 17.892,9] |
| `Minor_Axis_Length` | 47 | 1,763% | [71,93; 101,08] |
| `Eccentricity` | 12 | 0,450% | [0,8258; 0,9484] |
| `Convex_Area` | 1 | 0,038% | [7.580,5; 18.344,5] |
| `Perimeter`, `Major_Axis_Length`, `Extent` | 0 | 0% | — |

**Tổng: 62 ô trên 18.662 ô (0,33%).**

> **Khác biệt giữa hai cách báo cáo:** chạy `src/data.py` báo cáo trên **toàn bộ
> 3.810 mẫu** (93 ô), còn `src/split.py` báo cáo trên **tập train** (62 ô).
> Con số chính thức dùng để xử lý là **62 ô** vì ngưỡng phải suy ra từ tập
> train rồi mới áp dụng cho tập khác. Hai cách cho thấy ngưỡng IQR phụ thuộc
> tập dữ liệu — đó chính là lý do tính trên toàn bộ dữ liệu là sai.

### Quyết định xử lý: **không loại bỏ dòng nào**

1. Tỉ lệ ngoại lệ rất nhỏ (0,33% tổng số ô).
2. Loại bỏ sẽ làm mất thông tin hình học thật của hạt gạo.
3. Giữ nguyên để báo cáo minh bạch và công khai ràng buộc.
4. Định nghĩa "ngoại lệ" ở đây chỉ là **thông báo**, không phải mắc lỗi dữ liệu.

> **Nguyên tắc:** ngưỡng ngoại lệ tính trên **tập train**, rồi áp dụng cho tập
> khác. Tính trên toàn bộ dữ liệu sẽ làm ngưỡng "biết" thông tin của tập test.

---

## 6. Chia tập

| Tập | Số mẫu | Mục đích |
|---|---|---|
| **train** | 2.666 | Dạy mô hình, chọn tham số bằng CV |
| **validation** | 572 | Kiểm tra cấu hình chọn được |
| **test** | 572 | **Một lần duy nhất** để báo cáo cuối |

Phương pháp: `train_test_split(stratify=y, random_state=42)`.

**Kiểm tra trùng lặp giữa các tập:** 0 dòng trùng trong cả 3 cặp.
→ Không tồn tại rò rỉ thông tin do bản ghi lặp.

---

## 7. Tính tái lập

### Cách tải lại

```bash
python scripts/download_data.py
```

### Checksum SHA256

| Tệp | SHA256 (rút gọn) |
|---|---|
| `rice+cammeo+and+osmancik.zip` | `fe94e42046b829de21b92b0ffb6a22774fde021328cae799faa802a14e8dbed9` |
| `Rice_Cammeo_Osmancik.arff` | `1af97883100c89de...` |
| `rice.csv` | `c55797972f68f7e5...` |

Giá trị đầy đủ: `data/checksums.txt`.

### Quy trình chuyển đổi

Tệp gốc từ UCI là định dạng **ARFF** (`@RELATION`, `@ATTRIBUTE`, `@DATA`).
Script chuyển sang CSV để pandas đọc thuận tiện. Không có thao tác làm sạch
hay thay đổi giá trị nào — **chỉ chuyển đổi định dạng**.

---

## 8. Xử lý ở mức dữ liệu

| Vấn đề | Xử lý |
|---|---|
| Thiếu giá trị | Không có — không cần imputer |
| Trùng lặp | Không có — không cần loại |
| Ngoại lệ | Có (12 ô) — giữ nguyên, chỉ báo cáo |
| Mất cân bằng lớp | Không (1,34:1) — không cần resampling |
| Chuẩn hóa | Không dùng — cây quyết định không nhạy với thang đo |

> Không dùng `StandardScaler` là có chủ ý: cây quyết định so sánh thứ tự
> (`≤` hoặc `>`), không so sánh khoảng cách. Chuẩn hóa không làm thay đổi
> cây tìm được.

---

## 9. Đạo đức và rủi ro

| Mục | Đánh giá |
|---|---|
| **Dữ liệu cá nhân** | Không có. Chỉ đặc trưng hình học của hạt gạo. |
| **Thành kiến** | Không liên quan đến con người. |
| **Rủi ro gây hại** | Thấp. Nhãn sai dẫn tới phân loại nhầm giống gạo — hậu quả là kinh tế, không phải an toàn. |
| **Sai lệch chọn mẫu** | Có thể: 3.810 hạt từ một lứa thu hoạch, một nơi, một thiết bị chụp ảnh. Không biết đại diện cho bao nhiêu điều kiện. |
| **Sử dụng được phép** | Có — CC BY 4.0, kèm trích dẫn. |
