<?php
/**
 * SnapAll & Snap Video PHP API
 * Bộ bóc tách và phân giải video TikTok, Douyin, Facebook và đa nền tảng
 * Tương thích chuẩn 100% với Apple Shortcuts (Phím tắt iOS/macOS) và Web Interface
 */

if (!headers_sent()) {
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');
}

$requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($requestMethod === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// -------------------------------------------------------------
// 0. Xử lý Proxy Tải Xuống (Stream Attachment)
// -------------------------------------------------------------
$action = $_GET['action'] ?? '';
if ($action === 'download' && !empty($_GET['url'])) {
    $fileUrl = filter_var($_GET['url'], FILTER_VALIDATE_URL);
    $filename = preg_replace('/[^a-zA-Z0-9_\-\.]/', '_', $_GET['filename'] ?? 'video.mp4');
    if ($fileUrl) {
        header('Content-Description: File Transfer');
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="' . $filename . '"');
        header('Expires: 0');
        header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
        header('Pragma: public');
        
        $ch = curl_init($fileUrl);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, false);
        curl_setopt($ch, CURLOPT_TIMEOUT, 60);
        curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1');
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        curl_exec($ch);
        curl_close($ch);
        exit;
    }
}

if (!headers_sent()) {
    header('Content-Type: application/json; charset=utf-8');
}

// -------------------------------------------------------------
// 1. Nhận & Làm sạch URL
// -------------------------------------------------------------
$inputUrl = '';

// A. Hỗ trợ tham số b64 (từ Snap Video gốc)
if (!empty($_GET['b64'])) {
    $decoded = base64_decode($_GET['b64'], true);
    if ($decoded !== false) {
        $inputUrl = trim($decoded);
    }
}

// B. Hỗ trợ tham số url
if (empty($inputUrl)) {
    $inputUrl = trim($_GET['url'] ?? $_POST['url'] ?? '');
}

// C. Xử lý nếu url nằm trong chuỗi query string có nhiều dấu ? và &
if (empty($inputUrl) && !empty($_SERVER['QUERY_STRING']) && strpos($_SERVER['QUERY_STRING'], 'url=') !== false) {
    $rawPart = substr($_SERVER['QUERY_STRING'], strpos($_SERVER['QUERY_STRING'], 'url=') + 4);
    $inputUrl = trim(urldecode($rawPart));
}

// D. Tách URL sạch từ văn bản nếu người dùng dán cả đoạn caption dài
if (!empty($inputUrl) && preg_match('/https?:\/\/[^\s]+/i', $inputUrl, $matchUrl)) {
    $inputUrl = $matchUrl[0];
}

if (empty($inputUrl)) {
    echo json_encode([
        'status' => 'error',
        'message' => 'Vui lòng cung cấp liên kết (url hoặc b64) video TikTok hoặc Facebook.'
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// Hàm dọn dẹp tiêu đề file sạch
function cleanTitle($str) {
    if (!$str) return 'video';
    $clean = preg_replace('/[\r\n\t]+/', ' ', $str);
    $clean = preg_replace('/[\\\\\\/:\\*\\?"<>\\|#%&{}<>\\$\\!\'`@\\+~]+/', '', $clean);
    $clean = preg_replace('/\\s+/', ' ', $clean);
    $clean = trim($clean);
    return mb_substr($clean ?: 'video', 0, 60, 'UTF-8');
}

// Hàm gửi request cURL
function fetchCurl($url, $customHeaders = [], $followRedirect = true) {
    $ch = curl_init();
    $defaultHeaders = [
        'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language: vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    ];
    $headers = array_merge($defaultHeaders, $customHeaders);

    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, $followRedirect);
    curl_setopt($ch, CURLOPT_MAXREDIRS, 10);
    curl_setopt($ch, CURLOPT_TIMEOUT, 15);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    if (PHP_VERSION_ID < 80500) {
        @curl_close($ch);
    }

    return [
        'code' => $httpCode,
        'body' => $response
    ];
}

// -------------------------------------------------------------
// 2. Xử lý TIKTOK & DOUYIN
// -------------------------------------------------------------
if (preg_match('/(tiktok\.com|douyin\.com)/i', $inputUrl)) {
    $apiUrl = 'https://www.tikwm.com/api/?url=' . urlencode($inputUrl);
    $res = fetchCurl($apiUrl);

    if ($res['code'] === 200 && !empty($res['body'])) {
        $data = json_decode($res['body'], true);
        if (isset($data['code']) && $data['code'] === 0 && isset($data['data'])) {
            $item = $data['data'];
            
            $author = $item['author']['nickname'] ?? ($item['author']['unique_id'] ?? 'TikTok Creator');
            $rawTitle = !empty($item['title']) ? $item['title'] : ('TikTok by ' . $author);
            $titleText = cleanTitle($rawTitle);
            
            $videoHd = !empty($item['hdplay']) ? $item['hdplay'] : ($item['play'] ?? '');
            $videoSd = $item['play'] ?? '';
            $audioUrl = $item['music'] ?? '';
            $images = $item['images'] ?? [];

            $labels = [];
            $medias = [];

            // Nếu là album ảnh slideshow
            if (!empty($images) && is_array($images)) {
                foreach ($images as $idx => $img) {
                    $lbl = "🖼️ Tải Ảnh " . ($idx + 1) . " jpg";
                    $labels[] = $lbl;
                    $medias[$lbl] = $img;
                }
            } else {
                if (!empty($videoHd)) {
                    $labels[] = '🎬 Tải Video HD (Không logo) mp4';
                    $medias['🎬 Tải Video HD (Không logo) mp4'] = $videoHd;
                }
                if (!empty($videoSd) && $videoSd !== $videoHd) {
                    $labels[] = '🎬 Tải Video SD mp4';
                    $medias['🎬 Tải Video SD mp4'] = $videoSd;
                }
            }

            // Âm thanh MP3
            if (!empty($audioUrl)) {
                $labels[] = '🎵 Trích xuất Âm thanh mp3';
                $medias['🎵 Trích xuất Âm thanh mp3'] = $audioUrl;
            }

            echo json_encode([
                'status' => 'success',
                'platform' => 'tiktok',
                'title' => $titleText,
                'author' => $author,
                'thumbnail' => $item['cover'] ?? '',
                'video' => $videoHd ?: $videoSd,
                'video_hd' => $videoHd,
                'video_sd' => $videoSd,
                'audio' => $audioUrl,
                'menu_title' => "⚡️ Chọn định dạng (" . $titleText . "):",
                'labels' => $labels,
                'medias' => $medias,
                'download_proxy' => [
                    'video' => 'api.php?action=download&filename=tiktok_video.mp4&url=' . urlencode($videoHd ?: $videoSd),
                    'audio' => 'api.php?action=download&filename=tiktok_audio.mp3&url=' . urlencode($audioUrl)
                ]
            ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
            exit;
        }
    }

    echo json_encode([
        'status' => 'error',
        'message' => 'Không thể lấy video TikTok. Vui lòng kiểm tra lại liên kết hoặc thử lại sau.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// -------------------------------------------------------------
// 3. Xử lý FACEBOOK (Reels, Watch, Video Posts)
// -------------------------------------------------------------
if (preg_match('/(facebook\.com|fb\.watch|fb\.me)/i', $inputUrl)) {
    $desktopHeaders = [
        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language: en-US,en;q=0.9',
        'Sec-Fetch-Dest: document',
        'Sec-Fetch-Mode: navigate',
        'Sec-Fetch-Site: none',
        'Upgrade-Insecure-Requests: 1'
    ];

    $res = fetchCurl($inputUrl, $desktopHeaders);
    $html = $res['body'] ?? '';

    if (!empty($html)) {
        $cleanHtml = str_replace(['&quot;', '&amp;'], ['"', '&'], $html);

        function matchPattern($regex, $content) {
            if (preg_match($regex, $content, $m)) {
                $val = str_replace('\\/', '/', $m[1]);
                $decoded = json_decode('"' . $m[1] . '"');
                return $decoded ?: $val;
            }
            return '';
        }

        $hd = matchPattern('/"browser_native_hd_url":"(.*?)"/', $cleanHtml);
        if (!$hd) $hd = matchPattern('/"playable_url_quality_hd":"(.*?)"/', $cleanHtml);
        if (!$hd) $hd = matchPattern('/hd_src:"(.*?)"/', $cleanHtml);
        if (!$hd) $hd = matchPattern('/hd_src_no_ratelimit:"(.*?)"/', $cleanHtml);

        $sd = matchPattern('/"browser_native_sd_url":"(.*?)"/', $cleanHtml);
        if (!$sd) $sd = matchPattern('/"playable_url":"(.*?)"/', $cleanHtml);
        if (!$sd) $sd = matchPattern('/sd_src:"(.*?)"/', $cleanHtml);
        if (!$sd) $sd = matchPattern('/sd_src_no_ratelimit:"(.*?)"/', $cleanHtml);

        $finalVideo = $hd ?: $sd;

        if (!empty($finalVideo)) {
            $titleText = 'Facebook Video';
            if (preg_match('/<meta\s+property="og:title"\s+content="([^"]*)"/i', $cleanHtml, $tm)) {
                $titleText = $tm[1];
            } elseif (preg_match('/<title>(.*?)<\/title>/i', $cleanHtml, $tm)) {
                $titleText = $tm[1];
            }
            $titleClean = cleanTitle($titleText);

            $thumb = '';
            if (preg_match('/<meta\s+property="og:image"\s+content="([^"]*)"/i', $cleanHtml, $im)) {
                $thumb = $im[1];
            }

            $labels = [];
            $medias = [];

            if (!empty($hd)) {
                $labels[] = '🎬 Tải Video Facebook HD mp4';
                $medias['🎬 Tải Video Facebook HD mp4'] = $hd;
            }
            if (!empty($sd) && (empty($hd) || $sd !== $hd)) {
                $labels[] = '🎬 Tải Video Facebook SD mp4';
                $medias['🎬 Tải Video Facebook SD mp4'] = $sd;
            }
            $labels[] = '🎵 Trích xuất Âm thanh từ Video mp3';
            $medias['🎵 Trích xuất Âm thanh từ Video mp3'] = $finalVideo;

            echo json_encode([
                'status' => 'success',
                'platform' => 'facebook',
                'title' => $titleClean,
                'thumbnail' => $thumb,
                'video' => $finalVideo,
                'video_hd' => $hd ?: $sd,
                'video_sd' => $sd ?: $hd,
                'audio' => $finalVideo,
                'menu_title' => "⚡️ Chọn định dạng (" . $titleClean . "):",
                'labels' => $labels,
                'medias' => $medias,
                'download_proxy' => [
                    'video' => 'api.php?action=download&filename=facebook_video.mp4&url=' . urlencode($finalVideo),
                    'audio' => 'api.php?action=download&filename=facebook_audio.mp3&url=' . urlencode($finalVideo)
                ]
            ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
            exit;
        }
    }

    echo json_encode([
        'status' => 'error',
        'message' => 'Không tìm thấy video Facebook công khai hoặc video yêu cầu đăng nhập.'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// -------------------------------------------------------------
// 4. Link Tệp Media Trực Tiếp (Direct File URL)
// -------------------------------------------------------------
if (preg_match('/\.(mp4|mov|mp3|m4a|jpg|jpeg|png|webp)(\?.*)?$/i', $inputUrl, $extM)) {
    $ext = strtolower($extM[1]);
    $isAudio = in_array($ext, ['mp3', 'm4a']);
    $isImage = in_array($ext, ['jpg', 'jpeg', 'png', 'webp']);
    $icon = $isAudio ? '🎵' : ($isImage ? '🖼️' : '🎬');
    $lbl = "{$icon} Tải file gốc {$ext}";

    echo json_encode([
        'status' => 'success',
        'platform' => 'direct',
        'title' => 'media_file_' . time(),
        'menu_title' => '⚡️ Tải tệp tin media trực tiếp:',
        'labels' => [$lbl],
        'medias' => [$lbl => $inputUrl],
        'video' => $isAudio ? '' : $inputUrl,
        'audio' => $isAudio ? $inputUrl : '',
        'thumbnail' => ''
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}

// -------------------------------------------------------------
// 5. Fallback og:video Web
// -------------------------------------------------------------
$res = fetchCurl($inputUrl);
$html = $res['body'] ?? '';
if (!empty($html) && preg_match('/<meta\s+property="og:video(?::secure_url)?"\s+content="([^"]*)"/i', $html, $vm)) {
    $videoUrl = str_replace('&amp;', '&', $vm[1]);
    $titleText = 'Web Video';
    if (preg_match('/<meta\s+property="og:title"\s+content="([^"]*)"/i', $html, $tm)) {
        $titleText = $tm[1];
    }
    $titleClean = cleanTitle($titleText);

    echo json_encode([
        'status' => 'success',
        'platform' => 'generic',
        'title' => $titleClean,
        'thumbnail' => '',
        'video' => $videoUrl,
        'audio' => $videoUrl,
        'menu_title' => "⚡️ Tải video (" . $titleClean . "):",
        'labels' => ['🎬 Tải Video mp4', '🎵 Trích xuất Âm thanh mp3'],
        'medias' => [
            '🎬 Tải Video mp4' => $videoUrl,
            '🎵 Trích xuất Âm thanh mp3' => $videoUrl
        ]
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}

echo json_encode([
    'status' => 'error',
    'message' => 'Nền tảng này chưa được hỗ trợ hoặc liên kết không chứa video công khai.'
], JSON_UNESCAPED_UNICODE);
