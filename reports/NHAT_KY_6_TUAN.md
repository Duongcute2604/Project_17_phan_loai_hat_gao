# Nhật ký 6 tuần và phân công nhóm

> **Lưu ý:** mẫu dưới đây để tham khảo về *cách trình bày*. Thay bằng nội
> dung thật của nhóm, ghi rõ người thực hiện và giờ ước lượng. GV có thể đối
> chiếu với lịch sử Git nên nhật ký phải khớp với commit thực tế.

---

## 1. Bảng phân công

Yêu cầu của đề: *"Mỗi người phải có đóng góp đáng kể ở cả phần dữ liệu/mô hình
và phần web/báo cáo."*

| Hạng mục | Người A | Người B | Ghi chú |
|---|---|---|---|
| Thu thập & làm sạch dữ liệu | ✔ | | Có checksum, có báo cáo chất lượng |
| EDA và biểu đồ khám phá | ✔ | ✔ | Cùng review |
| Thiết kế chia tập & chống leakage | | ✔ | Phần cốt lõi nhất |
| Baseline | ✔ | | |
| Cây quyết định, cắt tỉa | ✔ | | |
| Rừng ngẫu nhiên (đối chiếu) | ✔ | | |
| Thí nghiệm & phân tích lỗi | ✔ | ✔ | Cùng thảo luận kết luận |
| API FastAPI | | ✔ | |
| Kiểm thử API | | ✔ | |
| Giao diện web | | ✔ | |
| Viết báo cáo | ✔ | ✔ | Mỗi người viết ~2 chương |
| Làm slide & rehearsal | | ✔ | |
| Model card & data card | ✔ | ✔ | |

> Cột ✔ phải phản ánh đúng lịch sử Git. Không ghi tên cho người không thực sự
> đóng góp.

---

## 2. Nhật ký theo tuần

### Tuần 1 — Chốt bài toán, tạo repo
| Việc | Người | Giờ | Kết quả | Vấn đề |
|---|---|---|---|---|
| Đọc đề, chốt câu hỏi nghiên cứu | | | | |
| Xác định nguồn dữ liệu, giấy phép | | | | |
| Tạo repo, .gitignore, requirements | | | | |

**Minh chứng:** commit `chore: khoi tao repo...`

### Tuần 2 — Tải dữ liệu, EDA, chia tập
| Việc | Người | Giờ | Kết quả | Vấn đề |
|---|---|---|---|---|
| Script tải dữ liệu + checksum | | | | |
| Báo cáo chất lượng dữ liệu | | | | |
| Chia tập stratified + kiểm tra leakage | | | | |

**Minh chứng:** commit `feat: script tai du lieu...`, `feat: chia tap...`

### Tuần 3 — Baseline và mô hình chính
| Việc | Người | Giờ | Kết quả | Vấn đề |
|---|---|---|---|---|
| 3 baseline | | | | |
| Thí nghiệm max_depth | | | | |
| Thí nghiệm ccp_alpha (CV) | | | | |

**Minh chứng:** commit `feat: 3 baseline...`

### Tuần 4 — Hoàn tất thí nghiệm, đóng băng
| Việc | Người | Giờ | Kết quả | Vấn đề |
|---|---|---|---|---|
| Thí nghiệm so sánh cây/rừng | | | | |
| Phân tích lỗi | | | | |
| Biểu đồ | | | | |
| **Đánh giá test 1 lần, đóng băng** | | | | |

**Minh chứng:** commit `feat: 4 thi nghiem...`, `feat: dong bang mo hinh...`

### Tuần 5 — API và giao diện web
| Việc | Người | Giờ | Kết quả | Vấn đề |
|---|---|---|---|---|
| API FastAPI + validation | | | | |
| Kiểm thử API | | | | |
| Giao diện 3 màn hình | | | | |

**Minh chứng:** commit `feat: API FastAPI...`, `feat: giao dien web...`

### Tuần 6 — Hoàn thiện báo cáo, rehearsal
| Việc | Người | Giờ | Kết quả | Vấn đề |
|---|---|---|---|---|
| Báo cáo + slide | | | | |
| Chạy lại trên môi trường sạch | | | | |
| Rehearsal demo | | | | |

**Minh chứng:** commit `docs: README...`

---

## 3. Cổng kiểm tra trước khi nộp

| Cổng | Đạt khi | Trạng thái |
|---|---|---|
| Dữ liệu | Nguồn truy cập được; CC BY 4.0; checksum; script tái tạo | ✔ `data/README.md`, `data/checksums.txt` |
| Đánh giá | Split hợp lệ; baseline; tách validation/test; phân tích lỗi | ✔ `reports/` |
| Kỹ thuật | Chạy được từ máy mới; không đường dẫn tuyệt đối | ✔ `README.md` |
| Web | Luồng chính + API chạy; input xấu không sập; model card rõ | ✔ `app/`, 16 test |
| Học thuật | Mọi bảng/hình có nguồn; trích dẫn; ghi công cụ AI | ☐ Làm trước khi nộp |

---

## 4. Câu hỏi vấn đáp — chuẩn bị trả lời

### "ccp_alpha làm cây thay đổi thế nào?"
`ccp_alpha` cắt các nhanh mà chi phí bỏ đi nhỏ hơn ngưỡng. Ở dữ liệu này:
`ccp_alpha = 0` → cây **190 lá**, F1 CV = 0.8757. `ccp_alpha = 0.005` →
cây **4 lá**, F1 CV = **0.9168**. Cắt tỉa không chỉ làm cây gọn mà làm
**tốt hơn**, vì các nhanh còn lại đang học nhiễu.

### "Feature importance của rừng có thiên lệch gì?"
Cây dùng gần như chỉ `Major_Axis_Length` (và `Perimeter` ở nhánh phụ). Vì hai
giống khác nhau chủ yếu về kích thước, feature importance sẽ tập trung ở
các đặc trưng hình học kích thước và bỏ qua `Extent` hoặc `Eccentricity`.
Feature importance **không nói lên quan hệ nhân quả** — nó chỉ phản ánh cách
mô hình dùng biến trong dữ liệu này.

### "Khi nào chọn cây thay vì rừng?"
Chọn cây khi: cần giải thích cho người không chuyên môn; dữ liệu nhỏ và trực
giác quan trọng hơn điểm số tối đa; đặc trưng có tương quan mạnh (rừng thì
đánh giá tầm quan trọng không đáng tin vì ngẫu nhiên chia giữa các biến
tương quan); cần triển khai nhẹ.

Chọn rừng khi: dữ liệu nhiều, nhiều nhiễu, đặc trưng yếu, chấp nhận mất khả
năng giải thích để đổi lấy độ chính xác và ổn định.

**Trong bài này:** cả hai đạt điểm gần như bằng nhau (F1 0.9199 cây vs
0.9184 rừng), rừng chậm hơn 12 lần và không giải thích được → **chọn cây**.

### "Vì sao F1 trên test thấp hơn validation?"
Không phải lỗi. Ba lý do đều được kiểm chứng:
1. Test là 572 mẫu đánh giá **một lần duy nhất**, không tinh chỉnh theo → con
   số này trung thực hơn validation.
2. Chênh lệch 0.028 nằm trong biến động tự nhiên: thử 5 seed khác nhau, F1
   dao động 0.8941–0.9293 (độ lệch chuẩn 0.0127).
3. Model cuối fit trên train+validation (3.238 mẫu) khác với model chỉ fit
   trên train (2.666 mẫu) đã dùng để đo validation.

### "Vì sao một cây 1 nhánh đã đạt 93%?"
Vì hai giống phân biệt được chủ yếu bằng kích thước. Đây là **phát hiện về
dữ liệu**, không phải về mô hình. Hệ quả: phần lớn điểm số cao đến từ tính
chất dễ của bài toán, nên báo cáo tập trung vào **thiết kế thí nghiệm và
phân tích lỗi** thay vì điểm số.

---

## 5. Tự đánh giá

| Tiêu chí | Điểm tự chấm | Ghi chú |
|---|---|---|
| Bài toán & phạm vi | | |
| Dữ liệu & EDA | | |
| Split, leakage, tái lập | | |
| Mô hình & thí nghiệm | | |
| Đánh giá & phân tích lỗi | | |
| Web/API | | |
| Mã nguồn & bàn giao | | |
| Báo cáo, trình bày | | |

**Điểm yếu đã nhận biết:**

1. Chưa thử mô hình ngoài phạm vi bài (ví dụ k-NN, SVM) để biết cây có tốt
   bằng thực sự hay không.
2. Chỉ kiểm tra 5 seed. Có thể mở rộng để ảnh hưỡng mẫu nhỏ là biến thiên.
3. Chưa thử phân tích phân lớp theo thời gian vì dữ liệu không có cột thời gian.
4. Phần lõi Git do một người nhập về; khi sửa lịch sử tên cần chạy lại toàn bộ
   pipeline và xác nhận checksum kết quả không đổi.
