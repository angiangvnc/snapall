<?php
/**
 * SnapAll API - Bộ bóc tách và phân giải video TikTok & Facebook
 * Hỗ trợ:
 * - TikTok: Video HD không logo / watermark + Âm thanh MP3 chất lượng cao
 * - Facebook: Video Reels, Watch, Post (HD & SD) + Trích xuất âm thanh
 */

if (!headers_sent()) {
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
}

$requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($requestMethod === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Xử lý tải trực tiếp (Proxy download với header Attachment)
$action = $_GET['action'] ?? '';
if ($action === 'download' && !empty($_GET['url'])) {
    $fileUrl = filter_var($_GET['url'], FILTER_VALIDATE_URL);
    $filename = preg_replace('/[^a-zA-Z0-9_\-\.]/', '_', $_GET['filename'] ?? 'video.mp4');
    if ($fileUrl) {
        header('Content-Description: File Transfer');
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="' . $filename . '"');
        header('Expires: 0');
        header('Cache-Control: must-revalidate');
        header('Pragma: public');
        
        $ch = curl_init($fileUrl);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1');
        curl_exec($ch);
        curl_close($ch);
        exit;
    }
}

if (!headers_sent()) {
    header('Content-Type: application/json; charset=utf-8');
}

$inputUrl = trim($_GET['url'] ?? $_POST['url'] ?? '');

if (empty($inputUrl)) {
    echo json_encode([
        'status' => 'error',
        'message' => 'Vui lòng cung cấp liên kết (url) TikTok hoặc Facebook.'
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// Tách URL sạch từ văn bản nếu người dùng dán cả đoạn văn có chứa URL
if (preg_match('/https?:\/\/[^\s]+/', $inputUrl, $matchUrl)) {
    $inputUrl = $matchUrl[0];
}

// Hàm gửi request cURL chuẩn
function fetchUrl($url, $customHeaders = [], $followRedirect = true) {
    $ch = curl_init();
    $defaultHeaders = [
        'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
    $finalUrl = curl_getinfo($ch, CURLINFO_EFFECTIVE_URL);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    // In PHP 8.0+, curl handles close automatically; in older versions curl_close($ch)
    if (PHP_VERSION_ID < 80500) {
        @curl_close($ch);
    }

    return [
        'code' => $httpCode,
        'final_url' => $finalUrl,
        'body' => $response
    ];
}

// 1. Xử lý TIKTOK
if (preg_match('/(tiktok\.com|douyin\.com)/i', $inputUrl)) {
    $apiUrl = 'https://www.tikwm.com/api/?url=' . urlencode($inputUrl);
    $res = fetchUrl($apiUrl);

    if ($res['code'] === 200 && !empty($res['body'])) {
        $data = json_decode($res['body'], true);
        if (isset($data['code']) && $data['code'] === 0 && isset($data['data'])) {
            $item = $data['data'];
            
            $videoHd = !empty($item['hdplay']) ? $item['hdplay'] : $item['play'];
            $videoSd = $item['play'] ?? '';
            $audio = $item['music'] ?? '';
            $author = $item['author']['nickname'] ?? ($item['author']['unique_id'] ?? 'TikTok Creator');
            $title = !empty($item['title']) ? $item['title'] : ('Video TikTok của @' . $author);
            $cover = $item['cover'] ?? '';

            echo json_encode([
                'status' => 'success',
                'platform' => 'tiktok',
                'title' => $title,
                'author' => $author,
                'thumbnail' => $cover,
                'duration' => $item['duration'] ?? 0,
                'video' => $videoHd ?: $videoSd,
                'video_hd' => $videoHd,
                'video_sd' => $videoSd,
                'audio' => $audio,
                'download_proxy' => [
                    'video' => 'api.php?action=download&filename=tiktok_video.mp4&url=' . urlencode($videoHd ?: $videoSd),
                    'audio' => 'api.php?action=download&filename=tiktok_audio.mp3&url=' . urlencode($audio)
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

// 2. Xử lý FACEBOOK
if (preg_match('/(facebook\.com|fb\.watch)/i', $inputUrl)) {
    // Request bằng desktop User-Agent để lấy HTML đầy đủ chứa browser_native_hd_url
    $desktopHeaders = [
        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language: en-US,en;q=0.9',
        'Sec-Fetch-Dest: document',
        'Sec-Fetch-Mode: navigate',
        'Sec-Fetch-Site: none',
        'Upgrade-Insecure-Requests: 1'
    ];

    $res = fetchUrl($inputUrl, $desktopHeaders);
    $html = $res['body'] ?? '';

    // Thay thế ký tự escaped phổ biến trong script FB
    $htmlClean = str_replace(['&quot;', '&amp;'], ['"', '&'], $html);

    // Tìm HD URL
    $hdUrl = '';
    if (preg_match('/"browser_native_hd_url":"(.*?)"/', $htmlClean, $m) ||
        preg_match('/"playable_url_quality_hd":"(.*?)"/', $htmlClean, $m) ||
        preg_match('/hd_src\s*:\s*"([^"]*)"/', $htmlClean, $m)) {
        $hdUrl = json_decode('"' . $m[1] . '"');
    }

    // Tìm SD URL
    $sdUrl = '';
    if (preg_match('/"browser_native_sd_url":"(.*?)"/', $htmlClean, $m) ||
        preg_match('/"playable_url":"(.*?)"/', $htmlClean, $m) ||
        preg_match('/sd_src\s*:\s*"([^"]*)"/', $htmlClean, $m)) {
        $sdUrl = json_decode('"' . $m[1] . '"');
    }

    // Tìm tiêu đề và ảnh bìa
    $title = 'Facebook Video';
    if (preg_match('/<meta\s+property="og:title"\s+content="([^"]*)"/i', $htmlClean, $m)) {
        $title = html_entity_decode($m[1], ENT_QUOTES, 'UTF-8');
    } elseif (preg_match('/<title>(.*?)<\/title>/i', $htmlClean, $m)) {
        $title = html_entity_decode($m[1], ENT_QUOTES, 'UTF-8');
    }

    $thumbnail = '';
    if (preg_match('/<meta\s+property="og:image"\s+content="([^"]*)"/i', $htmlClean, $m)) {
        $thumbnail = html_entity_decode($m[1], ENT_QUOTES, 'UTF-8');
    }

    $finalVideo = $hdUrl ?: $sdUrl;

    if (!empty($finalVideo)) {
        echo json_encode([
            'status' => 'success',
            'platform' => 'facebook',
            'title' => $title,
            'thumbnail' => $thumbnail,
            'video' => $finalVideo,
            'video_hd' => $hdUrl ?: $sdUrl,
            'video_sd' => $sdUrl ?: $hdUrl,
            'audio' => $finalVideo, // Facebook audio nằm chung trong luồng MP4 (iOS Shortcut có hành động Encode Media bóc riêng M4A)
            'download_proxy' => [
                'video' => 'api.php?action=download&filename=facebook_video.mp4&url=' . urlencode($finalVideo)
            ]
        ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        exit;
    }

    echo json_encode([
        'status' => 'error',
        'message' => 'Không tìm thấy video Facebook công khai từ liên kết này. Vui lòng đảm bảo bài viết ở chế độ Công khai (Public).'
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// Không thuộc nền tảng hỗ trợ
echo json_encode([
    'status' => 'error',
    'message' => 'Nền tảng chưa được hỗ trợ. Hiện SnapAll hỗ trợ liên kết từ TikTok và Facebook.'
], JSON_UNESCAPED_UNICODE);
