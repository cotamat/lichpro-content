# lichpro-content

Kho nội dung tĩnh cho tab **Khám phá** của app Lịch Pro, phục vụ qua GitHub Pages tại:

```
https://cotamat.github.io/lichpro-content/
```

App đọc kho này ở hai chỗ và **chỉ hai chỗ**:

| App đọc gì | Khi nào |
|---|---|
| `version.json` | Mỗi lần người dùng vào tab Khám phá, nhiều nhất 6 giờ một lần |
| `content-<n>.json` | Chỉ khi `version` trong `version.json` khác version app đang có |
| `articles/*.html` | Khi người dùng mở một bài viết cụ thể |

Đặc tả đầy đủ nằm ở kho app: `wiki/specs/kham-pha-chu-de-va-bai-viet/PRODUCT.md`.

## Cấu trúc

```
version.json            → { version, url } — file duy nhất app kiểm định kỳ
content-1.json          → gói nội dung: chủ đề, danh mục con, danh sách bài viết
articles/*.html         → mỗi bài viết là một trang HTML đầy đủ
assets/article.css      → khuôn trình bày dùng chung cho mọi bài
assets/article.js       → đọc tham số app truyền vào URL (bắt buộc)
images/                 → ảnh chủ đề và ảnh bài viết
scripts/validate.py     → kiểm gói trước khi đẩy
```

## Thêm một bài viết

1. Tạo `articles/<slug>.html`, chép từ một bài có sẵn. **Bắt buộc** giữ hai dòng
   `<link rel="stylesheet" href="../assets/article.css">` và
   `<script src="../assets/article.js"></script>`.
2. Thêm ảnh bìa và thumbnail vào `images/articles/`.
3. Thêm một mục vào mảng `articles` trong `content-1.json`. `categoryId` phải là
   một danh mục **của đúng chủ đề** ghi ở `topicId`, nếu không app từ chối **cả gói**.
4. **Tăng `version`** ở cả `content-1.json` lẫn `version.json`. Quên bước này thì
   không máy nào thấy bài mới.
5. Chạy `python3 scripts/validate.py content-1.json` — phải sạch lỗi.

## Sửa một bài viết đã xuất bản

Sửa file HTML **và tăng `pageRevision`** của bài đó trong gói, rồi tăng `version`
của gói. Không tăng `pageRevision` thì máy đã cache bản cũ sẽ không bao giờ thấy
bản mới — app không có cách nào tự phát hiện.

## Bốn tham số app truyền vào URL

App mở bài bằng URL dạng:

```
articles/tet-nguyen-dan-net-dep.html?theme=dark&accent=D32412&top=64&bottom=96&v=1
```

| Tham số | Nghĩa | Bỏ qua thì sao |
|---|---|---|
| `theme` | `light` / `dark` theo cài đặt **của app**, không theo hệ điều hành | Bài nền sáng chói giữa app đang ở chế độ Tối |
| `accent` | Màu chủ đạo người dùng chọn, 6 ký tự hex không có `#` | Màu nhấn trong bài lệch với phần còn lại của app |
| `top` | Số pt phải chừa ở đỉnh trang | Bốn nút nổi của app đè lên đầu bài |
| `bottom` | Số pt phải chừa ở đáy trang | Đoạn cuối bài bị thanh tab che |

`assets/article.js` đã xử lý sẵn cả bốn. **Đừng viết trang không nạp file này.**

## Ràng buộc bắt buộc

- **Chỉ dùng tài nguyên trên chính host này.** App chặn mọi yêu cầu ra host khác —
  không font Google, không thư viện CDN, không ảnh dẫn từ nơi khác.
- **Chỉ `https`.** GitHub Pages không phục vụ `http`.
- **Không để trang cuộn ngang** trên bề rộng 393 pt. Bảng rộng phải bọc trong
  `<div class="table-wrap">` để tự cuộn bên trong khung của nó.
- Kiểm bài mới ở **393 pt**, cả `theme=light` lẫn `theme=dark`, trước khi đẩy.

## Ảnh cắt từ file design

Ảnh **hero chủ đề**, **thumbnail bài viết** và **ảnh bìa** sinh bằng
`scripts/crop-from-design.sh`, cắt từ mock trong kho app
(`wiki/uiux/03.tab-kham-pha/cate/`). Chạy lại khi designer giao mock mới:

```bash
./scripts/crop-from-design.sh /đường/dẫn/tới/kho/LichPro
```

Toạ độ cắt nằm trong chính script, kèm ghi chú vì sao chọn từng con số. Ba điều
script phải xử lý mà cắt tay rất dễ quên:

- **Thanh trạng thái giả** của mock (`9:41`, sóng, pin) nằm ở `y = 30..56` —
  cắt từ `y = 0` là nướng luôn chữ "9:41" vào ảnh hero.
- **Chữ ở nửa trái** dải hero (tiêu đề, mô tả, viên đếm bài) do app tự vẽ, phải
  che đi bằng chính màu nền, biên phải mờ dần để không lộ đường cắt.
- **Nút tròn góc trên–phải** (kính lúp / chia sẻ) nằm đè lên minh hoạ, phải vá
  bằng vùng ảnh bên cạnh chứ không che bằng màu phẳng được.

Độ phân giải: mock rộng 853 px ứng với màn 393 pt, nên ảnh ra khoảng **2,17×** —
đủ nét cho máy 2×, hơi mềm trên máy 3×. Đây là giới hạn của nguồn, chờ designer
giao asset gốc chất lượng cao.

Ảnh **thẻ chủ đề** (`*-card-*.jpg`) **không** do script này sinh — đó là hình
minh hoạ thật cấp riêng, mock chỉ vẽ thẻ ở cỡ rất nhỏ và phần dưới đã bị chữ phủ mờ.

Chỉ bài **Tết Nguyên Đán** có ảnh bìa, vì design chỉ vẽ đúng một ảnh bìa. Năm
bài còn lại vào thẳng nội dung sau phần mô tả.

## Đổi ảnh thì phải đổi TÊN FILE

App cache ảnh theo URL, hạn 30 ngày (`RemoteImage.maxDiskAge`). **Ghi đè cùng
tên là vô hình** với mọi máy đã tải ảnh cũ — URL không đổi thì không có lý do
tải lại. Vì vậy:

1. Ảnh mới đặt tên có hậu tố phiên bản: `tet-hero-v2.jpg`, `tet-hero-v3.jpg`…
   (biến `V` ở đầu `scripts/crop-from-design.sh`).
2. Trỏ gói mới sang tên mới, **tăng `version`**, cập nhật `version.json`.
3. **Giữ lại ảnh tên cũ và gói cũ.** Máy còn ở gói cũ vẫn trỏ vào chúng cho tới
   lần kiểm định kỳ kế tiếp — xoá đi là làm hỏng màn hình của họ ngay lập tức.

Hệ quả: `images/` chỉ phình thêm, không bao giờ co lại. Dọn được khi chắc chắn
không còn máy nào ở gói cũ.
