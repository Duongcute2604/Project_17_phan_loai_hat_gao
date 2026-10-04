# Hướng dẫn bàn giao

Tài liệu này dành cho người nhận bàn giao dự án (giảng viên hoặc nhóm khác).
Đọc theo thứ tự dưới đây là chạy được toàn bộ hệ thống trong khoảng 15 phút.

---

## 1. Thông tin tổng quan

| Mục | Nội dung |
|---|---|
| Đề tài | Phân loại hai giống gạo (Cammeo / Osmancik) từ hình dạng hạt |
| Chủ đề học phần | Bài 6 — Cây quyết định, cắt tỉa và rừng ngẫu nhiên |
| Mô hình chính | `DecisionTreeClassifier(ccp_alpha=0.005)`, 4 lá |
| Kết quả kiểm thử | Accuracy 0.9091 · F1 0.8917 · ROC-AUC 0.9480 |
| Dữ liệu | UCI ML Repository #545, CC BY 4.0 |
| Môi trường | Python 3.12.10 |

---

## 2. Chạy toàn bộ hệ thống

### Bước 1 — Môi trường

```bash
python -m venv .venv
.venv\Scripts\activate              # Windows
pip install -r requirements.txt
```

### Bước 2 — Tải dữ liệu

```bash
python scripts/download_data.py
```

Script tải file gốc từ UCI, chuyển đổi sang CSV và ghi SHA256 checksum.
Kiểm tra tính toàn vẹn:

```bash
python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('data/rice.csv').read_bytes()).hexdigest())"
```

Kết quả phải khớp với dòng tương ứng trong `data/checksums.txt`.

### Bước 3 — Chạy toàn bộ pipeline

```bash
python src/data.py          # kiểm tra chất lượng dữ liệu
python src/split.py         # chia tập + kiểm tra rò rỉ thông tin
python src/baseline.py      # 3 đường cơ sở
python src/train.py         # thí nghiệm 1, 2, 3
python src/evaluate.py      # thí nghiệm 4: phân tích lỗi
python src/visualize.py     # sinh 8 biểu đồ
```

### Bước 4 — Đóng băng mô hình

```bash
python src/final.py
```

> **Lưu ý quan trọng.** Lệnh này đánh giá trên tập kiểm thử **đúng một lần
> duy nhất**. Kết quả được ghi vào `reports/FINAL_RESULTS.json` và file này sẽ
> chặn các lần chạy sau, trừ khi truyền tham số `--force`. Cơ chế bảo vệ này
> nhằm bảo đảm nguyên tắc *"test chỉ dùng một lần để báo cáo"* — một yêu
> cầu bắt buộc của đề tài. Nếu cần chạy lại vì sửa lỗi code, dùng `--force`
> và ghi rõ lý do trong báo cáo.

### Bước 5 — Kiểm thử

```bash
pytest tests/ -v
```

Kết quả mong đợi: **36 trường hợp đạt**, gồm 16 test API và 20 test mô hình.

### Bước 6 — Chạy ứng dụng

```bash
python app/api.py
```

| Địa chỉ | Nội dung |
|---|---|
| <http://127.0.0.1:8000/> | Giao diện web 3 màn hình |
| <http://127.0.0.1:8000/docs> | Tài liệu API tự sinh kèm ví dụ request |
| <http://127.0.0.1:8000/api/model-card> | Thông tin mô hình và giới hạn |

---

## 3. Kiểm tra nhanh sau khi bàn giao

Dùng bảng này để xác nhận hệ thống hoạt động đúng:

| Kiểm tra | Kết quả mong đợi |
|---|---|
| `python src/split.py` | train 2666 · validation 572 · test 572 |
| Tỉ lệ Cammeo trong 3 tập | Chênh lệch ≤ 0,07 điểm phần trăm |
| Kiểm tra trùng lặp giữa các tập | 0 dòng trùng |
| `python src/baseline.py` | Cây 1 nhánh đạt 0.9318 trên validation |
| `python src/final.py` | Accuracy 0.9091, F1 0.8917, ROC-AUC 0.9480 |
| `pytest tests/ -v` | 36 passed |
| Gõ trường hợp rỗng vào form | Hiện thông báo lỗi, không gửi đi |
| Gõ `Extent = 5.0` | Từ chối với lý do giá trị phải trong khoảng 0–1 |

---

## 4. Cấu trúc mã nguồn

```
data/          Hồ sơ dữ liệu, CSV sinh ra, checksum
scripts/       Tải dữ liệu, sinh báo cáo, kiểm tra báo cáo
src/           Pipeline: config, data, split, baseline, train, evaluate, visualize, final
app/           Máy chủ FastAPI và giao diện tĩnh
tests/         Kiểm thử API và kiểm thử mô hình
models/        Mô hình đã lưu (sinh ra khi chạy)
reports/       Kết quả thí nghiệm, biểu đồ, model card, data card, nhật ký
```

---

## 5. Những điểm cần lưu ý khi đọc mã nguồn

### 5.1. Chia tập diễn ra trước mọi thao tác khác

Đây là yêu cầu nghiêm ngặt nhất của đề tài, liên quan trực tiếp đến điều kiện
giới hạn điểm. Trong `src/split.py`, hàm `split_data()` chia tập với
`stratify` theo nhãn và `random_state=42`. Mọi phép tính sau đó — ngưỡng ngoại
lệ, chọn tham số — đều chỉ dựa trên tập huấn luyện.

### 5.2. Tham số ngẫu nhiên khai báo tập trung

Toàn bộ giá trị `RANDOM_STATE` nằm trong `src/config.py`. Nhóm không hardcode
số 42 rải rác nhiều chỗ, nhằm đảm bảo khi đổi giá trị thì toàn bộ pipeline
đổi theo. Đây là điểm cần chứng minh khi vấn đáp về khả năng tái lập.

### 5.3. Nhãn lớp thiểu số được chọn trước

`POS_LABEL = "Cammeo"` trong `src/config.py`. F1 luôn được tính cho lớp này.
Lý do: nếu tính F1 cho lớp đa số thì giá trị luôn cao và không phản ánh hiệu
quả thực tế. Việc chọn lớp cố định một chỗ tránh tình trạng F1 không nhất
quán giữa các báo cáo.

### 5.4. Ứng dụng chỉ nạp mô hình, không huấn luyện lại

`app/api.py` nạp `models/tree_pruned.joblib` một lần khi khởi động máy chủ.
Không có lệnh `fit()` nào trong mã ứng dụng. Đây là yêu cầu tách biết huấn
luyện ngoại tuyến và phục vụ trực tuyến.

### 5.5. Không thay thế giá trị đầu vào

Đề yêu cầu *"không âm thầm thay thế giá trị"*. Vì vậy:

- Giá trị sai kiểu hoặc ngoài miền hợp lệ → **từ chối** (mã 422)
- Giá trị hợp lệ về kiểu nhưng nằm ngoài vùng dữ liệu gốc → **trả kết quả kèm
  cảnh báo**, giữ nguyên giá trị gửi lên

Có trường hợp kiểm thử riêng
(`test_out_of_domain_returns_warning_not_silent_fix`) bảo đảm điều này không
bị vi phạm trong tương lai.

---

## 6. Vì sao chọn cây quyết định chứ không phải rừng ngẫu nhiên

Đây là câu hỏi vấn đáp trọng tâm. Trả lời dựa trên số liệu đo được:

| Tiêu chí | Cây cắt tỉa | Rừng 100 cây |
|---|---|---|
| F1 trên validation | 0.9199 | 0.9184 |
| Thời gian huấn luyện | 0,019 giây | 0,227 giây |
| Số lá | 4 | 15.631 |
| Quy tắc đọc được | Có | Không |

Rừng không vượt trội cây đơn mà chậm hơn khoảng mười hai lần và không tạo
được một tập quy tắc đơn để giải thích. Với điểm số gần như tương đương,
chọn cây là quyết định dựa trên bằng chứng, đồng thời khớp với yêu cầu của đề
là ứng dụng phải *"hiển thị quy tắc cây ngắn"*.

---

## 7. Điểm yếu đã biết

Nhóm ghi nhận các hạn chế sau, đã nêu đầy đủ trong báo cáo:

1. Tỉ lệ sai khoảng 9% có bản chất là giới hạn của phương pháp đo đặc trưng,
   do hai giống có vùng chồng lấn thật sự — không phải lỗi kỹ thuật.
2. Chưa so sánh với các họ mô hình ngoài phạm vi bài học.
3. Dữ liệu chỉ từ một nguồn, chưa đánh giá được độ bền khi đổi điều kiện chụp ảnh.
4. Xác suất dự đoán của cây không mịn nên không dùng được cho kiểm định độ
   tin cậy.

---

## 8. Tài liệu liên quan

| Tệp | Nội dung |
|---|---|
| `README.md` | Tổng quan và hướng dẫn chạy |
| `data/README.md` | Hồ sơ dữ liệu, data dictionary, checksum |
| `reports/MODEL_CARD.md` | Thông tin mô hình, kết quả, giới hạn |
| `reports/DATA_CARD.md` | Thông tin dữ liệu, phân bố, chất lượng |
| `reports/FINAL_RESULTS.json` | Kết quả đánh giá đóng băng |
| `reports/NHAT_KY_6_TUAN.md` | Nhật ký và phân công nhóm |
