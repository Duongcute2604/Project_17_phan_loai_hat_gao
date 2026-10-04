# Hồ sơ dữ liệu — Rice (Cammeo and Osmancik)

## 1. Nguồn

| Mục | Nội dung |
|---|---|
| Tên | Rice (Cammeo and Osmancik) |
| Cơ sở dữ liệu | UCI Machine Learning Repository |
| Số hiệu | 545 |
| Trang dữ liệu | https://archive.ics.uci.edu/dataset/545/rice+cammeo+and+osmancik |
| DOI | https://doi.org/10.24432/C5MW4Z |
| Giấy phép | CC BY 4.0 (được phép dùng lại và trích dẫn) |
| Ngày tải về | 04/10/2026 |
| File tải về | `data/raw/rice+cammeo+and+osmancik.zip` |
| Người tạo dữ liệu | Ilkay CINAR, Murat KOKLU — Trường Đại học Selcuk, Konya, Thổ Nhĩ Kỳ |

### Trích dẫn

> Cinar, I., & Koklu, M. (2019). Classification of Rice Varieties Using Artificial
> Intelligence Methods. *International Journal of Intelligent Systems and
> Applications in Engineering*, 7(3), 188–194.
> https://doi.org/10.18201/ijisae.2019355381

## 2. Cách tái tạo dữ liệu

```bash
python scripts/download_data.py
```

Script tải file zip gốc từ UCI, giải nén, chuyển `.arff` → `.csv`,
rồi ghi SHA256 của từng file vào `data/checksums.txt`.

**Không commit dữ liệu vào Git.** Dữ liệu được tải lại bằng script mỗi khi
cần, nhờ vậy repo luôn nhỏ và ai cũng tạo ra cùng một kết quả.

## 3. Checksum (SHA256)

Xem `data/checksums.txt`. Giá trị mong đợi:

```
fe94e42046b829de21b92b0ffb6a22774fde021328cae799faa802a14e8dbed9  data/raw/rice+cammeo+and+osmancik.zip
1af97883100c89de...                                            data/raw/uci_545/Rice_Cammeo_Osmancik.arff
c55797972f68f7e5...                                            data/rice.csv
```

Kiểm tra lại sau khi tải:

```bash
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('data/rice.csv').read_bytes()).hexdigest())"
```

## 4. Data dictionary

| Tên biến | Kiểu | Đơn vị | Vai trò | Mô tả |
|---|---|---|---|---|
| `Area` | int | pixel² | feature | Diện tích hạt gạo |
| `Perimeter` | float | pixel | feature | Chu vi hình thuộc bao hạt |
| `Major_Axis_Length` | float | pixel | feature | Chiều dài trục lớn (hướng chính) |
| `Minor_Axis_Length` | float | pixel | feature | Chiều dài trục nhỏ (hướng vuông góc) |
| `Eccentricity` | float | — (0–1) | feature | Độ lệch tâm; càng gần 1 càng dẹt |
| `Convex_Area` | int | pixel² | feature | Diện tích bao lồi |
| `Extent` | float | — (0–1) | feature | Diện tích hạt ÷ diện tích bao lồi |
| `Class` | str | — | target | Nhãn: `Cammeo` hoặc `Osmancik` |

**Không có cột ID** trong dataset gốc — mỗi dòng là một hạt gạo riêng biệt.

## 5. Quy mô

- **3.810 mẫu**, **7 đặc trưng**, **1 biến nhãn**
- Nhiệm vụ: phân loại nhị phân
- Đơn vị quan sát: một hạt gạo
- Mốc thời gian dự đoán: ngay sau khi 7 đặc trưng hình học được đo xong
  (tức là không cần chờ thêm thông tin nào khác)

## 6. Thời điểm đặc trưng trở nên có sẵn

Cả 7 đặc trưng đều được tính từ **ảnh chụp một hạt gạo đơn lẻ**, thực hiện trước
khi bán ra thị trường. Nói cách khác: đội ngũ nhà sản xuất có thể thu được đủ
thông tin này ngay ở khâu phân loại trong dây chuyền đóng gói — đúng với bối cảnh
ứng dụng của đề tài.

## 7. Chất lượng dữ liệu

Chạy `python src/data.py` để xem báo cáo đầy đủ. Tóm tắt:

- **Thiếu giá trị (missing):** 0
- **Dòng trùng lặp:** 0
- **Ngoại lệ (outlier):** có, ghi nhận bằng IQR trên tập train, **không loại bỏ**
- **Phân bố lớp:** xem `reports/figures/class_distribution.png`

> **Lưu ý về nguyên tắc không rò rỉ thông tin:** mọi phép kiểm tra (kiểm tra
> trùng lặp, phát hiện ngoại lệ, thống kê phân bố) đều được thực hiện **trên
> tập train sau khi đã chia**. Quyết định loại bỏ dòng — nếu có — chỉ được dựa
> trên tập train và chỉ dùng tính chất của biến, **tuyệt đối không dùng nhãn**.

## 8. Chia tập

```
train      70%  -> 2667 mẫu   (dùng để dạy mô hình)
validation 15%  ->  571 mẫu   (dùng để chọn mô hình / tham số)
test       15%  ->  572 mẫu   (chỉ dùng MỘT LẦN để báo cáo cuối)
```

Chia theo kiểu **stratified** (giữ nguyên tỉ lệ Cammeo/Osmancik trong mỗi tập),
`random_state = 42`. Cài đặt chi tiết trong `src/split.py`.
