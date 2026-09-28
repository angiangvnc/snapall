# 📱 Phân Tích & Hướng Dẫn Chi Tiết Cấu Trúc Phím Tắt Theo Ảnh Chụp

Tài liệu này ghi chú chi tiết toàn bộ logic và cấu trúc các khối lệnh của phím tắt được đối chiếu trực tiếp từ **4 bức ảnh chụp màn hình ứng dụng Phím tắt (Apple Shortcuts)**.

---

## 📸 1. Phân Tích Chi Tiết Từng Ảnh Chụp Màn Hình

### 🖼️ Ảnh 4 (Phần 1: Xử lý link mở ngoài & Trích xuất đuôi mở rộng)
1. **Kiểm tra liên kết điều hướng ngoài `{{open-url}}`:**
   - **`If [url_fetch] contains {{open-url}}`**: Kiểm tra nếu URL trả về chứa cờ chỉ định mở trình duyệt ngoài.
   - **`Replace [{{open-url}}] with [] in [url_fetch]`**: Loại bỏ cờ để lấy link web đích (`Updated Text`).
   - **`If [Updated Text] is not anything`**: Kiểm tra link hợp lệ.
   - **`Open [Updated Text]`**: Mở link bằng Safari/trình duyệt.
   - **`Stop this shortcut`**: Dừng ngay phím tắt sau khi mở.
   - **`End If`**.
2. **Khối chuẩn bị tên file & định dạng:**
   - **`If [Repeat Index] is not 1`**: Đảm bảo từ lượt lặp thứ 2 (hoặc khi xử lý từng file đã tải) mới thực thi khối này.
   - **`Match [mp4|mov|jpg|jpeg|heic|png|webp|mp3|m4a] in [label_now]`**: Dùng biểu thức chính quy (Regex) quét qua tên nhãn lựa chọn (`label_now`) để tìm đuôi định dạng file.
   - **`Change [Matches] to [lowercase]`**: Ép kiểu đuôi mở rộng thành chữ thường (lưu vào biến `ext`).
   - **`Random number between 1 and 9999999`**: Sinh một số nguyên ngẫu nhiên từ 1 đến 9.999.999 (biến `Random Number`) để chống trùng lặp tên file khi tải nhiều lần.

---

### 🖼️ Ảnh 4 (Phần 2: Cơ chế Hỏi đầu vào & Đệ quy)
- **`Otherwise`** / **`If [Item from List] contains 💬`**: Khi người dùng chưa dán link hoặc API yêu cầu nhập thêm thông tin.
- **`Ask for [Text] with [url_fetch]`**: Hiện popup hỏi người dùng nhập link/văn bản.
- **`Text: [Shortcut Input] [Provided Input]`**: Nối đầu vào phím tắt và nội dung vừa nhập.
- **`Run [Snap Video]`**: Gọi lại chính phím tắt đệ quy với tham số mới.
- **`Stop this shortcut`**: Dừng luồng phím tắt hiện tại.
- **`End If`**.

---

### 🖼️ Ảnh 3: Đổi Tên File Chuẩn & Phân Loại Lưu Trữ Tự Động
1. **Đổi tên file chuẩn hóa:**
   - **`Set name of [fetch_result] to snapvideo--[title] - [Random Number].[ext]`**:
     - Đầu vào là file vừa tải về (`fetch_result`).
     - Tên file được cấu trúc: tiền tố `snapvideo--` + tiêu đề video `[title]` + dấu gạch nối + số ngẫu nhiên `[Random Number]` + đuôi `.[ext]`.
     - Đầu ra được đặt tên là `media_loaded`.
2. **Phân loại lưu trữ theo loại nội dung:**
   - **`If [label_now] contains 🎵`**: Nếu nhãn chứa biểu tượng nốt nhạc (Âm thanh MP3):
     - **`Save [media_loaded] to [Documents]`**: Lưu file âm thanh vào thư mục Tệp (`Documents`) ➔ Xuất ra `Saved File`.
     - **`Set variable [m_file] to [open_file]`**: Gán cờ mở file (`📁 Mở ứng dụng Tệp`).
   - **`Otherwise`**: Nếu là Video (MP4/MOV):
     - **`Save [media_loaded] to [Recents]`**: Lưu video trực tiếp vào Cuộn Camera (Album Gần đây).
     - **`Set variable [m_album] to [open_album]`**: Gán cờ mở album (`📸 Mở Album Ảnh`).
   - **`End If`**.
3. **`End If`**: Kết thúc khối điều kiện lặp tải file.
4. **Kiểm tra hoàn thành số lượng đã chọn:**
   - **`If [Repeat Index] is greater than [count_select]`**: Kiểm tra xem số vòng lặp đã vượt quá số mục người dùng chọn tải chưa.

---

### 🖼️ Ảnh 2: Menu Điều Hướng Hoàn Tất (Completion Menu)
Khối này nằm ngay bên trong điều kiện `Repeat Index > count_select`:
1. **Tạo danh sách menu hoàn tất:**
   - **`Add [m_album] to [menu_done]`**: Thêm mục mở Ảnh (nếu có tải video).
   - **`Add [m_file] to [menu_done]`**: Thêm mục mở Tệp (nếu có tải âm thanh).
   - **`Add [close] to [menu_done]`**: Thêm nút Đóng (`❌ Đóng`).
2. **Hiển thị menu tương tác:**
   - **`Choose from [menu_done]`**: Hiện menu gồm các hành động khả dụng (đầu ra: `menu_done_select`).
3. **Xử lý lựa chọn của người dùng:**
   - **`If [menu_done_select] is [open_album]`**:
     - **`Open [Photos]`**: Mở ứng dụng Ảnh trên iPhone/Mac.
     - **`End If`**.
   - **`If [menu_done_select] is [open_file]`**:
     - **`Open [Saved File] in [Finder]`**: Mở file âm thanh vừa lưu trong Finder (Mac) hoặc ứng dụng Tệp (iPhone). Tùy chọn `Show Open In Menu: false`.
     - **`End If`**.

---

### 🖼️ Ảnh 1: Dừng & Kết Thúc Vòng Lặp
1. **`Stop this shortcut`**: Dừng toàn bộ tiến trình sau khi người dùng tương tác xong menu điều hướng.
2. **`End If`**: Kết thúc điều kiện `If Repeat Index is greater than count_select`.
3. **`End Repeat`**: Kết thúc toàn bộ vòng lặp lớn (Repeat Loop).

---

## 📂 2. Các File Đã Được Tạo Trong Dự Án

| Tên File | Định Dạng | Mô Tả |
| :--- | :--- | :--- |
| [build_shortcut.py](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/build_shortcut.py) | Python Script | Script tự động biên dịch toàn bộ cây khối lệnh sang chuẩn `plist` và tự gọi `shortcuts sign` để ký số Apple |
| [SnapVideo_Source.shortcut](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/SnapVideo_Source.shortcut) | Plist (Apple) | File mã nguồn thô của `Snap Video` chuẩn 100% theo các ảnh chụp |
| [SnapVideo.shortcut](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/SnapVideo.shortcut) | Apple Shortcut | File phím tắt `Snap Video` đã được Apple ký số hợp lệ (`AEA1`), có thể cài đặt ngay |
| [SnapAll_Source.shortcut](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/SnapAll_Source.shortcut) | Plist (Apple) | File mã nguồn thô của `SnapAll v8.0 Pro` kế thừa trọn vẹn kiến trúc này |
| [SnapAll.shortcut](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/SnapAll.shortcut) | Apple Shortcut | File phím tắt `SnapAll v8.0 Pro` đã được ký số Apple, dùng API serverless riêng sạch sẽ không quảng cáo |

---

## 🚀 3. Cách Sử Dụng & Biên Dịch Lại

Nếu bạn muốn thay đổi tham số hoặc tạo lại file `.shortcut`:
```bash
cd /Users/hoduylinh/Documents/Sites/shortcut/snapall
python3 build_shortcut.py
```
Lệnh trên sẽ tự động:
1. Tạo 2 file source `.shortcut` plist (`SnapAll_Source.shortcut`, `SnapVideo_Source.shortcut`).
2. Chạy lệnh hệ thống `shortcuts sign --mode anyone` để tạo ra các file phím tắt đã ký sẵn sàng cài trên iPhone/iPad/Mac.
