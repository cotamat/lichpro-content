#!/usr/bin/env bash
#
# Sinh lại toàn bộ ảnh trong images/ bằng cách cắt từ file design của app.
#
#   ./scripts/crop-from-design.sh [đường-dẫn-kho-app]
#
# Mặc định kho app ở ../../Utilities/LichPro so với kho này.
#
# Vì sao cần script này thay vì cắt tay một lần rồi thôi: toạ độ dưới đây đo
# bằng cách quét pixel trên chính file mock (biên dải hero, khung thumbnail,
# khung ảnh bìa). Không ghi lại thì vài tháng nữa không ai biết `853x422+0+60`
# ở đâu ra, và khi designer giao mock mới thì phải đo lại từ đầu.
#
# Nguồn: wiki/uiux/03.tab-kham-pha/cate/*.png — cả 5 file đều 853 × 1844 px.
# Quy đổi: 853 px ↔ 393 pt ⇒ ảnh cắt ra ở khoảng 2,17× cho máy 393 pt.

set -euo pipefail

APP_REPO="${1:-$(cd "$(dirname "$0")/../../../Utilities/LichPro" && pwd)}"
OUT="$(cd "$(dirname "$0")/.." && pwd)"
MOCK="$APP_REPO/wiki/uiux/03.tab-kham-pha/cate"

[ -d "$MOCK" ] || { echo "Không thấy thư mục mock: $MOCK" >&2; exit 1; }

Q=88

# Hậu tố phiên bản gắn vào TÊN FILE ảnh. Bắt buộc, không phải trang trí:
# app cache ảnh theo URL với hạn 30 ngày (`RemoteImage.maxDiskAge`), nên ghi đè
# cùng tên là vô hình với máy đã tải ảnh cũ. Đổi ảnh ⇒ đổi hậu tố ⇒ lên gói mới.
# Ảnh tên cũ **giữ nguyên trong kho**, vì máy còn ở gói cũ vẫn trỏ vào chúng.
V=v2

# ---------------------------------------------------------------- hero chủ đề
#
# CẠM BẪY: mock vẽ cả thanh trạng thái giả "9:41 / sóng / pin", nét của nó nằm
# ở y = 30..56. Cắt từ y = 0 là nướng chữ "9:41" vào ảnh. Mọi crop hero vì thế
# bắt đầu ở y = 60. Phần nền phía trên chỉ là màu kem phẳng nên không mất gì.
#
# Chiều cao khác nhau giữa 4 chủ đề vì mô tả dài ngắn khác nhau; biên dưới đo
# bằng chỗ hiệu R-B tụt từ ~10 xuống ~3 (nền kem của hero → nền trang).
#
# Phải xoá hai thứ khỏi ảnh vì app tự vẽ lại chúng:
#
# 1. CHỮ ở nửa trái (tiêu đề, mô tả, viên đếm bài) và nút Back góc trên–trái.
#    Đã đo mật độ nét theo cột: chữ và minh hoạ chồng lấn nhau ~20 px, nên lớp
#    che phải **mờ dần** ở mép phải — cắt thẳng sẽ để lại một đường dọc rõ giữa
#    cụm hoa của mock Lễ Tết.
#    Màu che lấy từ cột x = 4: nằm ngoài cả chữ lẫn minh hoạ, và giữ đúng
#    chuyển sắc dọc của nền.
#
# 2. NÚT tròn góc trên–phải (kính lúp / chia sẻ), khung x = 753..814. Nút này
#    nằm **đè lên minh hoạ** nên không che bằng màu phẳng được — vá bằng chính
#    vùng ảnh cách đó 95 px về bên trái, qua một mặt nạ elip đã làm mờ biên.
#
# Bề rộng lớp che chữ đặt riêng từng mock: mép phải của chữ và mép trái của
# minh hoạ cách nhau khác nhau ở mỗi bức. Che thiếu thì còn vệt chữ mờ, che thừa
# thì ăn vào minh hoạ.
FEATHER=20        # nửa bề rộng dải mờ dần ở mép phải lớp che
BTN_CX=783        # tâm ngang của nút tròn
BTN_RX=48         # bán trục vùng vá — rộng hơn nút để trùm cả bóng đổ
BTN_RY=46
PATCH_DX=95       # lấy ảnh vá từ bao xa về bên trái

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

hero() { # $1 mock  $2 cao  $3 tâm dọc nút  $4 bề rộng che chữ  $5 vá thêm  $6 tên
  local src="$MOCK/$1" h="$2" bcy="$3" text_w="$4" extra="$5" name="$6"
  local dst="$OUT/images/topics/$name-hero-$V.jpg"
  local cy=$((bcy - 60))          # đổi sang toạ độ sau khi đã cắt bỏ 60px đầu

  # Làm từng bước qua file tạm, và **gắn mặt nạ vào kênh alpha của lớp phủ**
  # (`-compose CopyOpacity`) rồi mới chồng lên bằng `-compose Over`.
  # Dạng ba ảnh `magick nền phủ mặt-nạ -composite` KHÔNG dùng được ở đây: nó
  # bỏ qua ảnh mặt nạ và chồng nguyên lớp phủ lên — sai âm thầm, lệnh vẫn báo
  # thành công còn ảnh thì lệch cả bố cục.
  magick "$src" -crop "853x${h}+0+60" +repage "$TMP/base.png"

  # 1a. dải màu nền: nhân bản cột x = 4 ra hết bề ngang, giữ đúng chuyển sắc dọc
  magick "$TMP/base.png" -crop "1x${h}+4+0" +repage -resize "853x${h}!" "$TMP/bg.png"

  # 1b. mặt nạ: đục tới TEXT_W - FEATHER, mờ dần thành trong suốt ở TEXT_W
  magick -size "853x${h}" xc:black \
    -fill white -draw "rectangle 0,0 $((text_w + FEATHER)),${h}" \
    -blur 0x${FEATHER} "$TMP/mask_text.png"

  magick "$TMP/bg.png" "$TMP/mask_text.png" -alpha off -compose CopyOpacity -composite \
    "$TMP/bg_rgba.png"
  magick "$TMP/base.png" "$TMP/bg_rgba.png" -compose Over -composite "$TMP/step1.png"

  # 2a. ảnh vá cho nút tròn: chính bức trên, dịch sang phải PATCH_DX
  magick "$TMP/step1.png" -roll "+${PATCH_DX}+0" "$TMP/patch.png"

  # 2b. mặt nạ elip làm mờ biên để chỗ vá không lộ đường ghép
  magick -size "853x${h}" xc:black -fill white \
    -draw "ellipse ${BTN_CX},${cy} ${BTN_RX},${BTN_RY} 0,360" -blur 0x9 "$TMP/mask_btn.png"

  magick "$TMP/patch.png" "$TMP/mask_btn.png" -alpha off -compose CopyOpacity -composite \
    "$TMP/patch_rgba.png"
  magick "$TMP/step1.png" "$TMP/patch_rgba.png" -compose Over -composite \
    -alpha remove -alpha off "$TMP/step2.png"

  # 3. vá thêm một ô chữ nhật (tuỳ chọn, dạng "x0,y0,x1,y1" theo toạ độ sau cắt)
  #
  #    Cần cho mock Tiết khí: đuôi dòng mô tả chạy tới x ≈ 428, trong khi hai
  #    con chim của minh hoạ nằm ở x ≈ 400..475. Nới lớp che chữ ở bước 1 cho
  #    đủ rộng sẽ xoá mất chim, nên vá riêng đúng ô chứa chữ — chim ở dải y
  #    khác nên không đụng tới.
  if [ "$extra" != "-" ]; then
    IFS=, read -r ex0 ey0 ex1 ey1 <<< "$extra"
    magick -size "853x${h}" xc:black -fill white \
      -draw "rectangle ${ex0},${ey0} ${ex1},${ey1}" -blur 0x14 "$TMP/mask_extra.png"
    magick "$TMP/bg.png" "$TMP/mask_extra.png" -alpha off -compose CopyOpacity -composite \
      "$TMP/extra_rgba.png"
    magick "$TMP/step2.png" "$TMP/extra_rgba.png" -compose Over -composite \
      -alpha remove -alpha off "$TMP/step2.png"
  fi

  magick "$TMP/step2.png" -strip -quality $Q "$dst"
  echo "  hero  $name  $(magick identify -format '%wx%h %b' "$dst")"
}

# tâm dọc của nút đo riêng từng mock (nút trôi theo chiều cao khối chữ)
echo "Hero chủ đề:"
#    mock                                     cao  tâm-nút  che-chữ  vá-thêm          tên
hero 03.topic-cate-le-tet.png                422  111      382      -                tet
hero 03.topic-cate-nha-cua.png               426  105      388      -                fengshui
hero 03.topic-cate-tiet-khi.png              434  114      390      365,225,440,320  season
hero 03.topic-cate-van-hoa-truyen-thong.png  442  121      405      -                culture

# ---------------------------------------------------------------- card chủ đề
#
# KHÔNG sinh ở đây. Ảnh thẻ chủ đề (`images/topics/*-card-v2.jpg`) là hình minh
# hoạ thật do người khác cung cấp, không cắt từ mock — mock chỉ vẽ thẻ ở cỡ rất
# nhỏ và phần dưới đã bị chữ phủ mờ. Đừng thêm bước sinh card vào script này.

# ------------------------------------------------------- thumbnail bài viết
#
# Khung thumbnail trong mock đồng nhất: x = 46, rộng 254. Chiều dọc đo riêng
# từng thẻ. Thumbnail có bo góc nên thu vào 4 px mỗi cạnh, nếu không bốn góc
# trắng của thẻ sẽ dính vào ảnh — app tự bo góc lại theo TopicMetrics.
INSET=4

thumb() { # $1 file mock  $2 y  $3 chiều cao  $4 tên file đích
  local src="$MOCK/$1" y="$2" h="$3" name="$4"
  local dst="$OUT/images/articles/$name-thumb-$V.jpg"
  magick "$src" \
    -crop "$((254 - 2*INSET))x$((h - 2*INSET))+$((46 + INSET))+$((y + INSET))" +repage \
    -strip -quality $Q "$dst"
  echo "  thumb $name  $(magick identify -format '%wx%h %b' "$dst")"
}

echo "Thumbnail bài viết:"
thumb 03.topic-cate-van-hoa-truyen-thong.png  618 198 tet-nguyen-dan
thumb 03.topic-cate-van-hoa-truyen-thong.png  846 194 tho-cung
thumb 03.topic-cate-nha-cua.png               592 188 huong-nha
thumb 03.topic-cate-tiet-khi.png              599 178 lap-xuan
thumb 03.topic-cate-le-tet.png                998 184 trung-thu
thumb 03.topic-cate-le-tet.png               1203 172 le-chua

# --------------------------------------------------------- ảnh bìa bài viết
#
# Mock chỉ có ĐÚNG MỘT ảnh bìa: bánh chưng trong 03.chi-tiet-bai-viet.png,
# khung x = 43..809, y = 545..954. Thu 6 px mỗi cạnh để bỏ bo góc.
# Năm bài còn lại không có ảnh bìa nào trong design nên không có ảnh bìa —
# đó là chủ ý, đừng sinh ảnh thay thế.
echo "Ảnh bìa bài viết:"
magick "$MOCK/03.chi-tiet-bai-viet.png" -crop "755x397+49+551" +repage \
  -strip -quality $Q "$OUT/images/articles/tet-nguyen-dan-hero-$V.jpg"
echo "  cover tet-nguyen-dan  $(magick identify -format '%wx%h %b' "$OUT/images/articles/tet-nguyen-dan-hero-$V.jpg")"

echo
echo "Xong. Tổng: $(du -sh "$OUT/images" | cut -f1)"
