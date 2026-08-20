/* Cầu nối giữa app Lịch Pro và trang bài viết.
 *
 * GitHub Pages là hosting tĩnh, không chạy được mã phía máy chủ, nên bốn tham
 * số app gắn vào URL phải do chính trang đọc và tự áp vào giao diện.
 * Xem wiki/specs/kham-pha-chu-de-va-bai-viet/PRODUCT.md §6.3.1 và §6.5.1.1.
 *
 * Mở trang này thẳng trên trình duyệt (không qua app) thì không có tham số nào —
 * khi đó mọi giá trị rơi về mặc định và trang vẫn đọc được bình thường.
 */
(function () {
  var p = new URLSearchParams(window.location.search);
  var root = document.documentElement;

  // theme: light | dark. App quyết theo AppearanceMode của nó, KHÔNG theo hệ
  // điều hành — nên không được dùng prefers-color-scheme thay cho tham số này.
  var theme = p.get('theme');
  root.setAttribute('data-theme', theme === 'dark' ? 'dark' : 'light');

  // accent: mã màu 6 ký tự, không có dấu #.
  var accent = (p.get('accent') || '').replace(/[^0-9a-fA-F]/g, '');
  if (accent.length === 6) {
    root.style.setProperty('--accent', '#' + accent);
  }

  // top / bottom: số pt trang phải chừa để thanh công cụ nổi của app và thanh
  // tab không đè lên nội dung. Bỏ qua hai cái này là lỗi hay gặp nhất.
  var top = parseInt(p.get('top'), 10);
  var bottom = parseInt(p.get('bottom'), 10);
  root.style.setProperty('--inset-top', (isNaN(top) ? 24 : top) + 'px');
  root.style.setProperty('--inset-bottom', (isNaN(bottom) ? 24 : bottom) + 'px');
})();
