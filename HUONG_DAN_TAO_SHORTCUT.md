# Hướng Dẫn Kiến Trúc & Cài Đặt Phím Tắt SnapAll v8.0 Pro (Kế Thừa 100% Snap Video + API Riêng)

Phím tắt **SnapAll Pro v8.0** được chuyển đổi trực tiếp từ 100% mã nguồn và luồng lệnh của phím tắt **Snap Video** nổi tiếng (từ các ảnh chụp màn hình thực tế), nhưng được trỏ sang **API riêng của bạn** (`https://snapall.vercel.app/api/parse` hoặc `api.php`), hoàn toàn loại bỏ quảng cáo độc hại và không còn phụ thuộc vào bên thứ 3.

---

## 🔬 TOÀN BỘ CẤU TRÚC SNAPALL V8.0 ĐÃ ĐƯỢC CHUYỂN ĐỔI

1. **Cơ chế nhận link 3 lớp (Share Sheet / Clipboard / Ask Prompt):**
   - Tự động nhận link từ ExtensionInput khi bấm **Chia sẻ** trong TikTok/Facebook.
   - Nếu chạy trực tiếp: tự động quét **Clipboard**.
   - Nếu cả 2 đều trống: bật hộp thoại nhập link an toàn.

2. **Xử lý link điều hướng đặc biệt (`{{open-url}}` - Ảnh 4):**
   - Loại bỏ tag `{{open-url}}` và mở URL an toàn bằng trình duyệt nếu có chỉ định.

3. **Vòng lặp xử lý & Tải đa lựa chọn (Repeat Loop):**
   - Lọc format và đuôi mở rộng file qua **Regex** (`mp4|mov|jpg|jpeg|heic|png|webp|mp3|m4a` - Ảnh 4).
   - Ép kiểu về chữ thường (`lowercase`) ➔ biến `ext`.
   - Sinh số ngẫu nhiên `1 đến 9999999` ➔ biến `Random Number`.
   - Đổi tên file chuẩn hóa: `snapall--[title] - [Random Number].[ext]` (Ảnh 3).

4. **Tự động phân loại nơi lưu trữ (Ảnh 3):**
   - Nếu nhãn chọn chứa **Âm thanh (`🎵`)** ➔ Tự động lưu vào ứng dụng **Tệp (Documents)** & gán cờ `m_file`.
   - Nếu là **Video** ➔ Tự động lưu thẳng vào **Cuộn Camera (Recents / Photos)** & gán cờ `m_album`.

5. **Thông báo kiểu Snap Video (menu thay cho hộp thông báo):**
   - **Chọn định dạng:** `Choose media:` ➔ `🎬 MP4 HD`, `🎬 MP4 FULL HD`, `🎬 MP4 WATERMARK`, `🎵 MP3 128KBPS` (ảnh: `🖼️ PHOTO n`).
   - **Tải xong:** `🥳 Download successful!!`
     - `🖼️ Open Photos` ➔ Mở ứng dụng **Photos**.
     - `📁 Open Files` ➔ Mở ứng dụng **Tệp** (chỉ hiện khi có tải MP3).
     - `❌ Close` ➔ Dừng phím tắt.
   - **Lỗi:** `😢 Download failed!!` + nội dung lỗi từ API ➔ `📖 User guide` / `❌ Close`.

---

## 🚀 CÁCH CÀI ĐẶT & SỬ DỤNG

### 1. Cài đặt trực tiếp file đã ký số Apple hợp lệ:
* **Cách nhanh nhất (iCloud):** mở link [https://www.icloud.com/shortcuts/6e6f9bd8cf874f3db43d753fcea81669](https://www.icloud.com/shortcuts/6e6f9bd8cf874f3db43d753fcea81669) trên iPhone ➔ **Thêm phím tắt**.
  - ⚠️ Mỗi lần build lại phím tắt cần tạo link iCloud mới (Phím tắt ➔ Chia sẻ ➔ Sao chép liên kết iCloud) và cập nhật vào `index.html`.
* **Trên iPhone/iPad:**
  - Truy cập web của bạn hoặc tải trực tiếp file [SnapAll.shortcut](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/SnapAll.shortcut).
  - Nhấn **Thêm phím tắt** (hoặc **Thay thế**).
* **Trên Mac:**
  - Nhấp đúp vào file [SnapAll.shortcut](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/SnapAll.shortcut) để thêm ngay vào ứng dụng Phím tắt.

### 2. Tự cấu hình API theo tên miền riêng của bạn:
Trong file [build_shortcut.py](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/build_shortcut.py), bạn có thể đổi địa chỉ API ở ngay đầu file:
```python
# CẤU HÌNH API RIÊNG CỦA BẠN:
DEFAULT_API_URL = "https://your-domain.com/api/parse?url="
# Hoặc hosting PHP:
# DEFAULT_API_URL = "https://your-domain.com/api.php?url="
```
Sau đó chỉ cần chạy:
```bash
python3 build_shortcut.py
```
Script sẽ tự động sinh và ký số ra file `SnapAll.shortcut` mới ngay lập tức!
