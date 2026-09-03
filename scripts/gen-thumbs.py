#!/usr/bin/env python3
"""Sinh thumbnail bài viết bằng hình vẽ tự tạo, không dùng ảnh của bên thứ ba.

    python3 scripts/gen-thumbs.py content-7.json

Đọc gói nội dung, với mỗi bài có id nằm trong ICONS thì vẽ ảnh 246x180 gồm
nền gradient theo màu category và một icon line-art trắng ở giữa, xuất JPEG.
Chạy lại được nhiều lần, kết quả không đổi.

Vẽ trực tiếp bằng MVG (`magick -draw`) chứ KHÔNG qua SVG: máy không có
`rsvg-convert`, nên magick rơi về renderer MSVG nội bộ và cho ra ảnh đen.

Khác với crop-from-design.sh, script này không cần kho design của app —
sáu bài gốc vẫn dùng ảnh thật cắt từ design và không nằm trong ICONS.
"""
import json
import subprocess
import sys
from pathlib import Path

W, H, QUALITY = 246, 180, 88
ROOT = Path(__file__).resolve().parent.parent

# Icon vẽ trong khung 24x24, cùng ngôn ngữ đồ hoạ với ul.icon-list trong bài viết.
ICONS = {
    # --- 17 bài đợt trước ---
    "ong-cong-ong-tao":           "M3 12c3-4 7-5 10-5s5 2 5 5-2 5-5 5-7-1-10-5z M18 12h3 M15 10.5h.01 M8 8l-3-3 M8 16l-3 3",
    "ram-thang-gieng":            "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M12 3v18 M4 9h16 M4 15h16",
    "tet-thanh-minh-tao-mo":      "M3 20h18 M5 20a7 7 0 0 1 14 0 M9 13V9 M12 12.5V7.5 M15 13V9",
    "tet-doan-ngo":               "M4 11h16a8 8 0 0 1-8 8 8 8 0 0 1-8-8z M8 8c0-2 1-3 1-4 M12 7c0-2 1-3 1-4 M16 8c0-2 1-3 1-4",
    "ram-thang-bay-vu-lan":       "M12 21c-4-2-7-5-7-9 0 0 3 1 4 4 1-4 3-7 3-10 0 3 2 6 3 10 1-3 4-4 4-4 0 4-3 7-7 9z",
    "le-that-tich":               "M6 6l1.5 3L11 10.5 7.5 12 6 15l-1.5-3L1 10.5 4.5 9z M18 9l1.2 2.4 2.8 1.1-2.8 1.1L18 16l-1.2-2.4-2.8-1.1 2.8-1.1z M8 18c3-3 6-3 9 0",
    "gio-to-hung-vuong":          "M3 20h18 M5 20V11l7-6 7 6v9 M9 20v-5h6v5 M12 3v2",
    "phong-tuc-cuoi-hoi":         "M9.5 14a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9z M15 19a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9z",
    "day-thang-thoi-noi":         "M5 12a7 7 0 0 1 14 0 M4 12h16 M6 12v5a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3v-5 M12 5V3",
    "tang-le-va-kieng-ky":        "M12 3c1.5 2.5.5 4-.5 5.5S10 12 12 13.5c2-1.5 1.5-3.5.5-5 M8 21h8 M12 13.5V21",
    "le-nhap-trach-ve-nha-moi":   "M3 10.5 12 3l9 7.5 M5.5 9.5V20h13V9.5 M13 15a2 2 0 1 0 0-4 2 2 0 0 0 0 4z M13 15v3h2",
    "dong-tho-xay-nha":           "M4 20h16 M6 20v-4h5v4 M8.5 13V4l4 3-4 3 M15 20v-7h4v7",
    "xuat-hanh-xong-dat-dau-nam": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M15.5 8.5l-2 5-5 2 2-5z",
    "khai-truong-dau-nam":        "M4 9h16v11H4z M3 9l2-4h14l2 4 M9 20v-6h6v6 M8 9v.5a2 2 0 1 0 4 0V9 M12 9v.5a2 2 0 1 0 4 0V9",
    "chuyen-ban-tho-ve-nha-moi":  "M8 20h8 M9 20v-6a3 3 0 0 1 6 0v6 M12 11V7 M9.5 8.5h5 M4 20h16",
    "cung-mung-mot-ngay-ram":     "M5 12a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M12 12a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M12 5v7 M19 12a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M4 17h16 M6 20h12",
    "mam-ngu-qua-ba-mien":        "M3 14h18a9 9 0 0 1-18 0z M4 18h16 M8 11a2 2 0 1 0 0-4 2 2 0 0 0 0 4z M13 11a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z M17.5 12a1.8 1.8 0 1 0 0-3.6 1.8 1.8 0 0 0 0 3.6z",
    # --- 13 bài mới ---
    "tet-han-thuc":               "M3 12h18a9 9 0 0 1-18 0z M4 16h16 M8 9a1.8 1.8 0 1 0 0-3.6A1.8 1.8 0 0 0 8 9z M12 8a1.8 1.8 0 1 0 0-3.6A1.8 1.8 0 0 0 12 8z M16 9a1.8 1.8 0 1 0 0-3.6A1.8 1.8 0 0 0 16 9z",
    "le-cung-giao-thua":          "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 7v5l3.5 2 M12 3V1.5 M20.5 12H22",
    "le-tat-nien":                "M4 12h11a5.5 5.5 0 0 1-11 0z M4.5 16h10 M17.5 4 16 20 M20.5 4 19 20",
    "tho-than-tai-tho-dia":       "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 7v10 M14.5 9.5A2.5 2.5 0 0 0 12 8h-.5a2 2 0 0 0 0 4h1a2 2 0 0 1 0 4H12a2.5 2.5 0 0 1-2.5-1.5",
    "tin-nguong-tho-mau":         "M12 20c-4.5-2-7.5-5.5-7.5-9.5 0 0 3.5 1 5 4.5.5-4.5 2.5-8 2.5-11.5 0 3.5 2 7 2.5 11.5 1.5-3.5 5-4.5 5-4.5 0 4-3 7.5-7.5 9.5z M6 21h12",
    "le-cat-noc-do-mai":          "M2 12 12 4l10 8 M5 12v8h14v-8 M9 20v-5h6v5 M12 4V2",
    "le-tan-gia-hoan-cong":       "M3 10.5 12 3l9 7.5 M5.5 9.5V20h13V9.5 M12 17.5s-2.5-1.7-2.5-3.2a1.6 1.6 0 0 1 2.5-1.2 1.6 1.6 0 0 1 2.5 1.2c0 1.5-2.5 3.2-2.5 3.2z",
    "tuc-dot-via-tre-so-sinh":    "M12 3c2 3.5.5 5-1 7s-1.5 4.5 1 6.5c2.5-2 2-4.5.5-6.5 M6.5 14c0 4 2.5 7 5.5 7s5.5-3 5.5-7",
    "phong-tuc-o-cu-sau-sinh":    "M9 21v-6a3 3 0 0 1 6 0v6 M12 10a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M4 21c0-3 1.5-5 3.5-6 M20 21c0-3-1.5-5-3.5-6",
    "cai-tang-sang-cat":          "M9 21h6 M8 21v-7h8v7 M6.5 14h11 M9.5 11h5 M12 11V9 M10.5 9h3 M4 21h16",
    "phong-tuc-mua-ban-nha-dat":  "M3 11 10.5 5 18 11 M5.5 10v10h10V10 M8.5 20v-4h4v4 M19 4h3v6h-3z M19 6h3",
    "vay-muon-tra-no-dau-nam":    "M3 6h18v12H3z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M6 9h.01 M18 15h.01",
    "le-cung-xe-moi":             "M3 12h18 M5 12l1.8-4.5A2 2 0 0 1 8.7 6h6.6a2 2 0 0 1 1.9 1.5L19 12 M4 12v5h16v-5 M7 17v2 M17 17v2 M7.5 14.5h.01 M16.5 14.5h.01",
}


def darken(hex_color: str, factor: float) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(max(0, int(c * factor)) for c in (r, g, b))


ICON_SCALE = 3.6                           # khung icon 24 -> 86.4 px


def magick_args(color: str, path_d: str, out: Path) -> list:
    """Nền gradient theo màu category + vầng sáng mờ + icon trắng ở giữa."""
    tx = (W - 24 * ICON_SCALE) / 2
    ty = (H - 24 * ICON_SCALE) / 2 - 4
    return [
        "magick", "-size", f"{W}x{H}",
        f"gradient:{color}-{darken(color, 0.58)}",
        # vầng sáng nhẹ phía sau icon cho đỡ phẳng
        "-fill", "rgba(255,255,255,0.09)", "-stroke", "none",
        "-draw", f"circle {W / 2},{H / 2 - 4} {W / 2},{H / 2 - 4 + 58}",
        # icon line-art
        "-fill", "none", "-stroke", "white", "-strokewidth", "1.6",
        "-draw", f"stroke-linecap round stroke-linejoin round "
                 f"translate {tx:.2f},{ty:.2f} scale {ICON_SCALE},{ICON_SCALE} "
                 f"path '{path_d}'",
        "-quality", str(QUALITY), str(out),
    ]


def main() -> int:
    pkg_path = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "content-7.json")
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    cat = {(t["id"], c["id"]): c for t in pkg["topics"] for c in t["categories"]}

    made, skipped, failed = 0, 0, []

    for a in pkg["articles"]:
        d = ICONS.get(a["id"])
        if d is None:
            skipped += 1
            continue
        out = ROOT / a["thumbnail"]
        out.parent.mkdir(parents=True, exist_ok=True)
        color = cat[(a["topicId"], a["categoryId"])]["color"]
        r = subprocess.run(magick_args(color, d, out), capture_output=True, text=True)
        if r.returncode != 0:
            failed.append(f"{a['id']}: {r.stderr.strip()[:120]}")
        else:
            made += 1

    print(f"đã sinh {made} ảnh, bỏ qua {skipped} bài (dùng ảnh design gốc)")
    for f in failed:
        print("  LỖI:", f)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
