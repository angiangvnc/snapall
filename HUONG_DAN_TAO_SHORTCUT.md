# Hướng Dẫn Kiến Trúc & Cài Đặt Phím Tắt SnapAll v5.0 Pro (Học Hỏi Từ Snap Video)

Tài liệu này phân tích chi tiết cách thức hoạt động của phím tắt **Snap Video** nổi tiếng, và cách **SnapAll Pro v5.0** đã học hỏi, kế thừa những ưu điểm vượt trội đồng thời khắc phục các nhược điểm (quảng cáo, link chuyển hướng bên thứ 3) để trở thành công cụ tải video chuyên nghiệp nhất cho iPhone.

---

## 🔬 PHÂN TÍCH KIẾN TRÚC PHÍM TẮT SNAP VIDEO (BẢN GỐC TRÊN PHIMTAT.VN)

Qua phân tích trực tiếp file phím tắt gốc `Snap Video` (87 khối lệnh) được lưu trên iCloud của cộng đồng Phím tắt VN, chúng ta rút ra được các điểm mấu chốt:

### 1. Điểm mạnh cần học hỏi từ Snap Video:
* **Cơ chế nhận link 3 lớp (Không bao giờ báo lỗi URL rỗng):**
  1. *Lớp 1:* Lấy trực tiếp từ `Đầu vào phím tắt` (ExtensionInput) khi bấm nút **Chia sẻ** trong app.
  2. *Lớp 2:* Nếu mở phím tắt độc lập, tự động kiểm tra `Bảng nhớ tạm` (Clipboard).
  3. *Lớp 3:* Nếu cả hai đều trống, phím tắt dùng khối **Hỏi đầu vào** (`Ask for Input`) để hiện ô: *"Vui lòng dán liên kết video TikTok/Facebook vào đây"* (tự điền sẵn Clipboard). Nhờ đó, người dùng bấm chạy lúc nào cũng hoạt động trơn tru.
* **Menu lựa chọn đa năng (`Choose from List`):**
  - Sau khi gọi API bóc tách, phím tắt đọc danh sách `labels` và hiện menu trực quan:
    - 🎬 Tải Video HD (Không logo)
    - 🎵 Trích xuất Âm thanh (Audio MP3)
* **Tự động phân loại nơi lưu trữ:**
  - Nếu mục người dùng chọn là **Âm thanh (`🎵`)** ➔ Tự động lưu vào ứng dụng **Tệp (Files)**.
  - Nếu là **Video** ➔ Tự động lưu thẳng vào **Cuộn Camera (Album Ảnh)**.

### 2. Điểm yếu của Snap Video đã được SnapAll khắc phục:
* **Gắn mã độc / Quảng cáo:** Snap Video chạy mã JavaScript ngầm `data:text/html,...` để chuyển hướng người dùng sang `snapvideo.co`, ép người dùng xem quảng cáo và bấm mở link tài trợ.
* **Phụ thuộc API bên thứ 3:** Khi máy chủ `api.phimtat.vn` chết hoặc bị chặn, toàn bộ phím tắt Snap Video bị liệt hoàn toàn.
* **SnapAll Pro v5.0:** Hoàn toàn sạch 100%, sử dụng Serverless API riêng trên Vercel tốc độ cao, không quảng cáo, mã nguồn mở minh bạch.

---

## 🚀 CÁCH CÀI ĐẶT SNAPALL PRO V5.0 (KHUYÊN DÙNG)

Trong thư mục dự án đã có sẵn file **`SnapAll.shortcut`** (bản v5.0 Pro) được ký số Apple hợp lệ:

1. **Trên iPhone:**
   - Mở Safari truy cập: **[https://snapall.vercel.app](https://snapall.vercel.app)**
   - Nhấn nút **Cài Đặt File Phím Tắt v5.0 Pro (SnapAll.shortcut)**.
   - Khi iPhone hỏi, chọn **Thêm phím tắt** (hoặc **Thay thế** nếu đã có bản cũ).
2. **Trên Mac:**
   - Nhấp đúp vào file [SnapAll.shortcut](file:///Users/hoduylinh/Documents/Sites/shortcut/snapall/SnapAll.shortcut) để thêm vào app Phím tắt. Nhờ iCloud Sync, nó sẽ tự xuất hiện trên iPhone.

---

## 🛠️ CẤU TRÚC 27 KHỐI LỆNH CHUẨN CỦA SNAPALL PRO V5.0

Nếu bạn muốn tự xây dựng bằng tay trên iPhone:

| STT | Tên khối lệnh (Tiếng Việt) | Action Identifier (iOS) | Chi tiết thiết lập |
| :--- | :--- | :--- | :--- |
| **0** | **Ghi chú** | `is.workflow.actions.comment` | Thông tin bản quyền & hướng dẫn SnapAll v5.0 Pro |
| **1** | **Lấy URL từ đầu vào** | `is.workflow.actions.detect.link` | Lấy từ `Đầu vào phím tắt` (ExtensionInput) |
| **2** | **Lấy bảng nhớ tạm** | `is.workflow.actions.getclipboard` | Đọc clipboard máy |
| **3** | **Lấy URL từ đầu vào** | `is.workflow.actions.detect.link` | Lấy từ kết quả `Bảng nhớ tạm` |
| **4** | **Văn bản (Gộp URL)** | `is.workflow.actions.gettext` | Ghép `[URLs Chia sẻ]` xuống dòng `[URLs Clipboard]` |
| **5** | **Lấy URL từ đầu vào** | `is.workflow.actions.detect.link` | Lấy danh sách URL chuẩn từ Văn bản trên |
| **6** | **Lấy mục từ danh sách** | `is.workflow.actions.getitemfromlist` | Lấy `Mục đầu tiên` (First Item) |
| **7** | **Nếu (If)** | `is.workflow.actions.conditional` | `Nếu [Mục đầu tiên] có bất kỳ giá trị nào` (Condition: 100) |
| **8** | **Lấy URL từ đầu vào** | `is.workflow.actions.detect.link` | Giữ nguyên URL đã có |
| **9** | **Nếu không (Otherwise)** | `is.workflow.actions.conditional` | Xử lý khi người dùng chưa có link |
| **10**| **Yêu cầu đầu vào (Ask)**| `is.workflow.actions.ask` | Hiện bảng: *"⚡️ SnapAll: Vui lòng dán link video:"*, mặc định điền `Bảng nhớ tạm` |
| **11**| **Lấy URL từ đầu vào** | `is.workflow.actions.detect.link` | Lấy URL từ `Đầu vào đã cung cấp` |
| **12**| **Lấy mục từ danh sách** | `is.workflow.actions.getitemfromlist` | Lấy `Mục đầu tiên` |
| **13**| **Kết thúc điều kiện** | `is.workflow.actions.conditional` | Output: `Kết quả nếu` (If Result) |
| **14**| **Lấy nội dung của URL** | `is.workflow.actions.downloadurl` | URL: `https://snapall.vercel.app/api/parse?url=[Kết quả nếu]`, ép kiểu `WFURLContentItem` |
| **15**| **Lấy giá trị từ từ điển**| `is.workflow.actions.getvalueforkey` | Từ điển: `Nội dung của URL`, Khóa: `menu_title` |
| **16**| **Lấy giá trị từ từ điển**| `is.workflow.actions.getvalueforkey` | Từ điển: `Nội dung của URL`, Khóa: `labels` |
| **17**| **Lấy giá trị từ từ điển**| `is.workflow.actions.getvalueforkey` | Từ điển: `Nội dung của URL`, Khóa: `medias` |
| **18**| **Chọn từ danh sách** | `is.workflow.actions.choosefromlist` | Danh sách: `labels`, Lời nhắc: `menu_title` |
| **19**| **Lấy giá trị từ từ điển**| `is.workflow.actions.getvalueforkey` | Từ điển: `medias`, Khóa: `Mục đã chọn` (Chosen Item) |
| **20**| **Lấy nội dung của URL** | `is.workflow.actions.downloadurl` | URL: `[download_url]` (ép kiểu `WFURLContentItem`), tải file MP4/MP3 |
| **21**| **Nếu (If)** | `is.workflow.actions.conditional` | `Nếu [Mục đã chọn] chứa 🎵` |
| **22**| **Lưu tệp** | `is.workflow.actions.documentpicker.save`| Lưu file âm thanh vào ứng dụng Tệp |
| **23**| **Hiển thị thông báo** | `is.workflow.actions.notification` | Báo *"🎵 Đã trích xuất & lưu file âm thanh vào Tệp!"* |
| **24**| **Nếu không (Otherwise)** | `is.workflow.actions.conditional` | Xử lý khi chọn Video |
| **25**| **Lưu vào album ảnh** | `is.workflow.actions.savetocameraroll` | Lưu video sạch logo vào Cuộn Camera (Recents) |
| **26**| **Hiển thị thông báo** | `is.workflow.actions.notification` | Báo *"🎬 Đã lưu video vào Thư viện Ảnh!"* |
| **27**| **Kết thúc điều kiện** | `is.workflow.actions.conditional` | Hoàn tất |

---

## 🎯 CÁCH SỬ DỤNG HÀNG NGÀY TRÊN IPHONE

1. **Cách 1 (Nhanh nhất - 1 chạm qua Share Sheet):**
   * Trong app **TikTok** hoặc **Facebook**, nhấn biểu tượng **Chia sẻ (Share)**.
   * Chọn **SnapAll**.
   * Menu xuất hiện hỏi bạn muốn tải **Video HD** hay **Âm thanh MP3**. Chạm vào mục bạn thích ➔ File sẽ tự tải và lưu vào đúng nơi!
2. **Cách 2 (Mở trực tiếp phím tắt):**
   * Bạn có thể bấm mở phím tắt **SnapAll** từ Màn hình chính, Widget hoặc bên trong app Phím tắt.
   * Nếu bạn đã sao chép link trước đó, phím tắt sẽ tự động nhận và tải.
   * Nếu chưa sao chép link, phím tắt sẽ mở ô popup lịch sự hỏi: *"⚡️ SnapAll: Vui lòng dán link video TikTok hoặc Facebook"* để bạn dán link vào mà không bao giờ gặp lỗi!
