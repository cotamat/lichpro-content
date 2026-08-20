#!/usr/bin/env python3
"""Kiểm tra gói nội dung trước khi đẩy lên GitHub Pages.

Cài đúng các điều kiện hợp lệ ở PRODUCT.md §1.9 của app, cộng thêm vài kiểm
tra chỉ làm được ở phía nội dung (file trang có tồn tại không, ảnh có tồn tại
không). App từ chối *toàn bộ* gói không hợp lệ, nên một lỗi ở đây là lỗi chặn.

    python3 scripts/validate.py content-1.json
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def need(obj: dict, key: str, where: str):
    value = obj.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        err(f"{where}: thiếu trường bắt buộc '{key}'")
        return None
    return value


def local_file(rel: str, where: str, kind: str) -> None:
    """Đường dẫn tương đối phải trỏ tới file có thật trong kho."""
    if rel.startswith("http://"):
        err(f"{where}: '{rel}' dùng http — GitHub Pages chỉ phục vụ https (§6.5.1.2)")
        return
    if rel.startswith("https://"):
        return  # URL tuyệt đối, không kiểm được ở đây
    if not (ROOT / rel).exists():
        (err if kind == "trang" else warn)(f"{where}: không tìm thấy {kind} '{rel}'")


def main(path: str) -> int:
    pack = json.loads(Path(path).read_text(encoding="utf-8"))

    version = pack.get("version")
    if not isinstance(version, int) or version <= 0:
        err("gói: 'version' phải là số nguyên dương")
    if not str(pack.get("imageBaseURL", "")).startswith("https://"):
        err("gói: 'imageBaseURL' phải là URL https")

    topics = pack.get("topics") or []
    articles = pack.get("articles") or []
    if not topics:
        err("gói: không có chủ đề nào")

    # id chủ đề duy nhất; danh mục con duy nhất trong phạm vi từng chủ đề
    cats_by_topic: dict[str, set[str]] = {}
    seen_topics: set[str] = set()
    for t in topics:
        where = f"chủ đề '{t.get('id', '?')}'"
        tid = need(t, "id", where)
        for key in ("name", "heroTitle", "summary", "cardImage", "heroImage"):
            need(t, key, where)
        if tid:
            if tid in seen_topics:
                err(f"{where}: id trùng")
            seen_topics.add(tid)
        for key in ("cardImage", "heroImage"):
            if t.get(key):
                local_file(t[key], where, "ảnh")

        cats = t.get("categories") or []
        if not cats:
            err(f"{where}: phải có ít nhất một danh mục con")
        ids: set[str] = set()
        for c in cats:
            cw = f"{where} / danh mục '{c.get('id', '?')}'"
            cid = need(c, "id", cw)
            need(c, "name", cw)
            color = c.get("color")
            if color is not None and not HEX.fullmatch(str(color)):
                err(f"{cw}: 'color' phải dạng #RRGGBB, đang là {color!r}")
            if cid:
                if cid in ids:
                    err(f"{cw}: id danh mục trùng trong cùng chủ đề")
                ids.add(cid)
        cats_by_topic[tid or "?"] = ids

    # bài viết: id duy nhất, topicId/categoryId trỏ đúng
    seen_articles: set[str] = set()
    for a in articles:
        where = f"bài viết '{a.get('id', '?')}'"
        aid = need(a, "id", where)
        for key in ("title", "summary", "thumbnail", "publishedAt", "pageURL"):
            need(a, key, where)
        if aid:
            if aid in seen_articles:
                err(f"{where}: id trùng")
            seen_articles.add(aid)

        if a.get("publishedAt") and not DATE.fullmatch(a["publishedAt"]):
            err(f"{where}: 'publishedAt' phải dạng YYYY-MM-DD")

        rev = a.get("pageRevision")
        if not isinstance(rev, int) or rev <= 0:
            err(f"{where}: 'pageRevision' phải là số nguyên dương")

        tid = a.get("topicId")
        if tid not in cats_by_topic:
            err(f"{where}: 'topicId' = {tid!r} không có chủ đề tương ứng")
        else:
            cid = a.get("categoryId")
            if cid not in cats_by_topic[tid]:
                err(f"{where}: 'categoryId' = {cid!r} không thuộc chủ đề '{tid}'")

        if a.get("thumbnail"):
            local_file(a["thumbnail"], where, "ảnh")
        if a.get("pageURL"):
            local_file(a["pageURL"], where, "trang")

    # featuredRank: không bắt buộc, nhưng trùng nhau thì thứ tự hiển thị bấp bênh
    ranks = [a["featuredRank"] for a in articles if a.get("featuredRank") is not None]
    if len(ranks) != len(set(ranks)):
        warn("có 'featuredRank' trùng nhau — thứ tự Bài viết nổi bật sẽ không xác định")
    if not ranks:
        warn("không bài nào có 'featuredRank' — mục Bài viết nổi bật sẽ biến mất khỏi trang gốc")

    for w in warnings:
        print(f"  cảnh báo: {w}")
    for e in errors:
        print(f"  LỖI: {e}")

    if errors:
        print(f"\n✗ {len(errors)} lỗi — KHÔNG được đẩy gói này lên.")
        return 1
    print(f"\n✓ Gói hợp lệ: {len(topics)} chủ đề, {len(articles)} bài viết, version {version}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "content-1.json"))
