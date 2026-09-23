# ⚡️ SnapAll - iOS Shortcuts & Web Downloader

**SnapAll** là giải pháp tải video đa nền tảng tối ưu cho **iPhone (iOS Shortcuts)** và **Web**, hỗ trợ:
- 🎬 **TikTok:** Tải video chất lượng cao **xóa sạch logo / watermark** (nguồn TikWM API).
- 📹 **Facebook:** Tải video Reels, Watch, bài viết công khai độ phân giải **HD / SD**.
- 🎵 **Trích xuất âm thanh (Audio):** Tải file MP3 studio gốc (TikTok) hoặc tách âm thanh sang M4A trực tiếp trên iPhone.

---

## 📱 Cài Đặt Phím Tắt (Shortcuts) Trên iPhone

Bạn có thể tải file phím tắt đã ký số sẵn của Apple:
* File phím tắt: [`SnapAll.shortcut`](./SnapAll.shortcut)

### Cách thêm vào iPhone:
1. **Trên Mac:** Nhấp đúp vào `SnapAll.shortcut` ➔ Chọn **Thêm phím tắt**. Phím tắt sẽ tự động đồng bộ sang iPhone qua iCloud.
2. **Trên iPhone:** Tải file về qua Safari hoặc AirDrop từ Mac ➔ Bấm mở và chọn **Thêm phím tắt**.

### Cách sử dụng trên iPhone:
1. Mở app **TikTok** hoặc **Facebook**.
2. Nhấn nút **Chia sẻ (Share)** ➔ Chọn **SnapAll**.
3. Chọn:
   - **🎬 Tải Video HD (Không Logo):** Tự động tải và lưu thẳng vào ứng dụng **Ảnh (Cuộn Camera)**.
   - **🎵 Trích Xuất Âm Thanh (MP3):** Tự động tải và mở menu lưu vào ứng dụng **Tệp (Files)**.

Xem hướng dẫn chi tiết từng khối lệnh tại: [HUONG_DAN_TAO_SHORTCUT.md](./HUONG_DAN_TAO_SHORTCUT.md).

---

## 🌐 Triển Khai Web & API Miễn Phí

### 1. Triển khai lên Vercel (Khuyên dùng - Full tính năng cả TikTok & Facebook)
Repo đã được cấu hình sẵn Serverless Function [api/parse.js](./api/parse.js) và [vercel.json](./vercel.json):
1. Đăng nhập [Vercel](https://vercel.com) bằng tài khoản GitHub.
2. Bấm **Add New...** ➔ **Project** ➔ Chọn repo `angiangvnc/snapall`.
3. Bấm **Deploy**. Bạn sẽ có ngay một website HTTPS miễn phí trọn đời (ví dụ: `snapall.vercel.app`).

### 2. Triển khai lên GitHub Pages (Dành cho web tĩnh & tải file shortcut)
1. Vào mục **Settings** của repo trên GitHub ➔ **Pages**.
2. Tại **Branch**, chọn `main` ➔ Thư mục `/(root)` ➔ Bấm **Save**.
3. Trang web sẽ trực tiếp tải được video TikTok không logo qua CORS và cho phép tải file `SnapAll.shortcut`.

### 3. Chạy trên máy chủ PHP (Local hoặc Cpanel/VPS)
Yêu cầu: PHP 8.0+ có cài cURL extension.
```bash
# Chạy local test
php -S localhost:8000
```
Mở trình duyệt truy cập: `http://localhost:8000`.

---

## 🔌 API Endpoint

### `GET /api.php` hoặc `GET /api/parse`
Truyền tham số `url` cần bóc tách:
```bash
curl "https://your-domain.com/api/parse?url=https://vt.tiktok.com/ZSb1j83qS/"
```

**Response JSON mẫu:**
```json
{
  "status": "success",
  "platform": "tiktok",
  "title": "Video TikTok của @heokhoua1983",
  "author": "Tài khoản bạn đã bị chặn",
  "thumbnail": "https://...",
  "video": "https://...mp4",
  "video_hd": "https://...mp4",
  "video_sd": "https://...mp4",
  "audio": "https://...mp3"
}
```

---

## 📄 License
Phát hành theo giấy phép MIT. Sử dụng cho mục đích cá nhân và học tập.
