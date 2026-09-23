# Hướng Dẫn Tạo & Cài Đặt Phím Tắt (Shortcuts) Tải Video TikTok, Facebook & Tách Nhạc Trên iPhone

Tài liệu này hướng dẫn chi tiết cách sở hữu phím tắt **SnapAll** trên iPhone để:
- Tự động nhận link khi bấm nút **Chia sẻ (Share)** trên app TikTok hoặc Facebook.
- Tải video chất lượng cao **xóa sạch logo / watermark**.
- Tùy chọn **Trích xuất âm thanh (Audio MP3/M4A)** trực tiếp trên iPhone.

---

## CÁCH 1: Cài đặt nhanh bằng File có sẵn (Khuyên dùng - 1 Chạm)

Trong thư mục này đã có sẵn file **`SnapAll.shortcut`** được ký số chuẩn bởi Apple:

1. **Nếu bạn đang ở trên máy Mac:**
   - Chỉ cần nhấp đúp (Double-click) vào file [SnapAll.shortcut](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/SnapAll.shortcut).
   - Ứng dụng **Phím tắt (Shortcuts)** trên Mac sẽ mở ra và hỏi bạn có muốn thêm phím tắt không. Nhấn **Thêm phím tắt (Add Shortcut)**.
   - Nhờ tính năng đồng bộ iCloud, phím tắt sẽ tự động xuất hiện ngay trên iPhone của bạn!

2. **Nếu muốn chuyển trực tiếp sang iPhone:**
   - Dùng **AirDrop** gửi file `SnapAll.shortcut` sang iPhone.
   - Hoặc gửi qua ứng dụng **Files (Tệp) / iCloud Drive / Zalo / Telegram**, sau đó chạm vào file để mở và chọn **Thêm phím tắt**.

---

## CÁCH 2: Tự tạo từng khối lệnh bằng tay trên iPhone (Từng bước chi tiết)

Nếu bạn muốn tự xây dựng hoặc tùy biến theo ý thích, hãy mở ứng dụng **Phím tắt (Shortcuts)** trên iPhone và làm theo các bước dưới đây:

### Bước 1: Tạo Phím tắt mới và bật Bảng chia sẻ (Share Sheet)
1. Trong ứng dụng **Phím tắt**, nhấn dấu **`+`** ở góc trên bên phải để tạo phím tắt mới.
2. Đổi tên phím tắt thành: **`SnapAll`** (hoặc tên bạn thích).
3. Nhấn vào biểu tượng thông tin **(i)** ở thanh công cụ dưới cùng:
   - Bật công tắc: **Hiển thị trong Bảng chia sẻ** *(Show in Share Sheet)*.
   - Ở mục **"Nhận các loại"**, chọn: **URL**, **Văn bản** *(Text)*, **Trang web Safari** *(Safari web pages)*.

---

### Bước 2: Thiết lập nhận link (Từ Nút Chia sẻ hoặc Bảng nhớ tạm)
Khi bạn bấm nút "Chia sẻ" trong app, link sẽ đi vào biến `Đầu vào phím tắt`. Nếu bạn mở phím tắt trực tiếp, nó sẽ tự động lấy link bạn vừa sao chép.

Thêm các khối lệnh sau (tìm kiếm trong ô tìm kiếm ở dưới):

1. **Khối: Nếu *(If)***
   - Thiết lập: `Nếu [Đầu vào phím tắt]` `không có bất kỳ giá trị nào` *(has no value)*
2. **Khối: Lấy bảng nhớ tạm *(Get Clipboard)***
   - Kéo khối này đặt vào bên trong khối `Nếu`.
3. **Khối: Kết thúc điều kiện *(End If)***
4. **Khối: Lấy URL từ đầu vào *(Get URLs from Input)***
   - Đầu vào: Chọn kết quả từ bước trên để đảm bảo bóc tách sạch sẽ đường dẫn `https://...`.
   - Đặt biến: **`URL_Goc`**.

---

### Bước 3: Nhận diện nền tảng (TikTok hay Facebook)

#### Trường hợp A: Video TIKTOK (Xóa Logo Watermark)
1. **Khối: Nếu *(If)***:
   - Điều kiện: `Nếu [URL_Goc]` `chứa` `tiktok.com`
2. **Khối: Lấy nội dung của URL *(Get Contents of URL)***:
   - URL điền vào: `https://www.tikwm.com/api/?url=` gắn kèm biến `[URL_Goc]`.
   - Phương thức: **GET**.
   *(TikWM là API mở miễn phí chuyên bóc tách TikTok, trả về video sạch logo chất lượng HD và file MP3 riêng biệt)*.
3. **Khối: Lấy giá trị từ từ điển *(Get Dictionary Value)***:
   - Nhận từ: `Nội dung của URL`.
   - Lấy giá trị cho khóa: **`data`**.
   - Đặt tên biến là: **`TikTok_Data`**.
4. **Khối: Chọn từ menu *(Choose from Menu)***:
   - Nhập lời nhắc: `Bạn muốn tải gì?`
   - Mục 1: **🎬 Tải Video HD (Không Logo)**
   - Mục 2: **🎵 Trích xuất Âm thanh (Audio MP3)**

   *Xử lý trong Mục 1 (Video HD Không Logo):*
   - **Lấy giá trị từ từ điển**: Nhận từ `[TikTok_Data]`, khóa: **`play`** (hoặc `hdplay`).
   - **Lấy nội dung của URL**: Nhận đường dẫn video vừa lấy để tải file về.
   - **Lưu vào album ảnh *(Save to Photo Album)***: Lưu vào `Gần đây (Recents)`.
   - **Hiển thị thông báo *(Show Notification)***: *"✅ Đã lưu video TikTok không logo vào Thư viện ảnh!"*.

   *Xử lý trong Mục 2 (Trích xuất Âm thanh):*
   - **Lấy giá trị từ từ điển**: Nhận từ `[TikTok_Data]`, khóa: **`music`**.
   - **Lấy nội dung của URL**: Nhận đường dẫn audio để tải về.
   - **Đặt tên *(Set Name)***: `TikTok_Audio.mp3`.
   - **Lưu tệp *(Save File)*** (hoặc khối **Chia sẻ**): Để lưu vào ứng dụng Tệp (Files / iCloud Drive).
   - **Hiển thị thông báo**: *"🎵 Đã trích xuất và lưu âm thanh thành công!"*.

5. **Khối: Kết thúc điều kiện *(End If)*** của TikTok.

---

#### Trường hợp B: Video FACEBOOK (Reels / Watch / Post HD)
1. **Khối: Nếu *(If)***:
   - Điều kiện: `Nếu [URL_Goc]` `chứa` `facebook.com` hoặc `fb.watch`.
2. **Khối: Lấy nội dung của URL *(Get Contents of URL)***:
   - Bạn có thể trỏ về API của server SnapAll:
     `http://<dia-chi-ip-may-chu>:8000/api.php?url=` gắn kèm `[URL_Goc]`.
3. **Khối: Lấy giá trị từ từ điển *(Get Dictionary Value)***:
   - Lấy giá trị cho khóa: **`video`** (hoặc `video_hd`).
4. **Khối: Lấy nội dung của URL**:
   - Tải file video MP4 về máy.
   - Đặt biến: **`Video_FB`**.
5. **Khối: Chọn từ menu *(Choose from Menu)***:
   - Mục 1: **🎬 Tải Video Facebook HD**
     - **Lưu vào album ảnh**: Lưu `[Video_FB]` vào cuộn Camera.
     - **Hiển thị thông báo**: *"✅ Đã lưu video Facebook vào Thư viện ảnh!"*.
   - Mục 2: **🎵 Trích xuất Âm thanh từ Video**
     - Dùng khối lệnh cực mạnh có sẵn của iOS: **Mã hoá phương tiện *(Encode Media)***:
       - Đầu vào: `[Video_FB]`.
       - Nhấn vào mũi tên mở rộng: Bật công tắc **Chỉ âm thanh *(Audio Only)*** = **BẬT**.
       - Định dạng: **M4A** (hoặc AIFF).
     - **Lưu tệp *(Save File)***: Lưu vào ứng dụng Tệp.
     - **Hiển thị thông báo**: *"🎵 Đã tách âm thanh từ video Facebook thành công!"*.
6. **Khối: Kết thúc điều kiện *(End If)***.

---

## BẢNG TRA CỨU HÀNH ĐỘNG (TIẾNG VIỆT & TIẾNG ANH TRÊN IOS)

| Tiếng Việt (iOS) | Tiếng Anh (iOS) | Chức năng |
| :--- | :--- | :--- |
| **Nếu / Nếu không / Kết thúc điều kiện** | `If / Otherwise / End If` | Rẽ nhánh điều kiện |
| **Lấy bảng nhớ tạm** | `Get Clipboard` | Đọc link đã copy |
| **Lấy URL từ đầu vào** | `Get URLs from Input` | Bóc link web chuẩn |
| **Lấy nội dung của URL** | `Get Contents of URL` | Gọi API hoặc tải file MP4/MP3 |
| **Lấy giá trị từ từ điển** | `Get Dictionary Value` | Bóc trường JSON (`data`, `play`, `music`) |
| **Chọn từ menu** | `Choose from Menu` | Hiện bảng hỏi Tải Video hay Tách Âm thanh |
| **Mã hoá tệp phương tiện** | `Encode Media` | Tách nhạc từ video MP4 sang M4A trực tiếp trên iPhone |
| **Lưu vào album ảnh** | `Save to Photo Album` | Đưa video vào ứng dụng Ảnh (Cuộn Camera) |
| **Lưu tệp** | `Save File` | Lưu vào ứng dụng Tệp (Files / Thư mục trên iPhone) |
| **Hiển thị thông báo** | `Show Notification` | Báo hoàn tất kèm âm thanh nhẹ |

---

## HƯỚNG DẪN SỬ DỤNG HÀNG NGÀY TRÊN IPHONE

1. Mở ứng dụng **TikTok** hoặc **Facebook**.
2. Tìm video hoặc Reel bạn thích.
3. Nhấn vào biểu tượng nút **Chia sẻ (Share)**:
   - Trong menu chia sẻ của iPhone, cuộn sang và chọn **SnapAll** (nếu chưa thấy, nhấn nút **Thêm / More** rồi chọn SnapAll).
4. Phím tắt sẽ hiện menu hỏi:
   - **🎬 Tải Video HD (Không Logo)**: Video tải xong sẽ nằm ngay trong ứng dụng **Ảnh (Photos)**.
   - **🎵 Trích xuất Âm thanh**: File nhạc tải xong sẽ được lưu vào ứng dụng **Tệp (Files)** để làm nhạc chuông, ghép video CapCut, v.v.

> [!TIP]
> **Cấp quyền lần đầu:** Trong lần chạy đầu tiên, iPhone sẽ hỏi: *"Cho phép SnapAll kết nối đến website và truy cập Ảnh của bạn?"* Hãy chọn **Luôn cho phép (Always Allow)** để các lần sau phím tắt tự động chạy ngầm siêu nhanh mà không hỏi lại.
