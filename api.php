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
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: SAMEORIGIN');
}

$requestMethod = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($requestMethod === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// -------------------------------------------------------------
// 0. Bảo mật chống SSRF / Local File Read / Open Proxy & Hỗ trợ Proxy Tải Xuống
// -------------------------------------------------------------
function isAllowedMediaOrSocialHost($host) {
    $host = strtolower(trim($host, '.'));
    return (bool) preg_match(
        '/(?:^|\.)(tiktok\.com|tiktokv\.com|tiktokv\.us|tiktokv\.eu|tiktokcdn\.com|tiktokcdn-us\.com|tiktokcdn-eu\.com|tiktokcdn-in\.com|byteoversea\.com|ByteOversea\.net|ibytedtos\.com|ibyteimg\.com|muscdn\.com|musical\.ly|douyin\.com|douyinvod\.com|douyinpic\.com|iesdouyin\.com|tikwm\.com|facebook\.com|fb\.com|fb\.watch|fb\.me|fbcdn\.net|fbsbx\.com|instagram\.com|cdninstagram\.com|akamaized\.net|akamaihd\.net|cloudfront\.net)$/i',
        $host
    );
}

function isSafeRemoteUrl($url, $requireAllowedMediaHost = false) {
    if (!is_string($url) || empty($url)) return false;
    $url = trim($url);
    if (!filter_var($url, FILTER_VALIDATE_URL)) return false;

    $parts = parse_url($url);
    if (!$parts || empty($parts['scheme']) || empty($parts['host'])) return false;

    $scheme = strtolower($parts['scheme']);
    if (!in_array($scheme, ['http', 'https'], true)) return false;

    $host = strtolower(trim($parts['host'], '[]'));
    if (in_array($host, ['localhost', '127.0.0.1', '0.0.0.0', '::1', '169.254.169.254'], true)) return false;
    if (preg_match('/(\.local|\.internal|\.localhost|\.lan|\.arpa)$/i', $host)) return false;

    if (filter_var($host, FILTER_VALIDATE_IP)) {
        if ($requireAllowedMediaHost) return false;
        return (bool) filter_var($host, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE);
    }

    if ($requireAllowedMediaHost && !isAllowedMediaOrSocialHost($host)) {
        return false;
    }

    // Cho phép nhanh các tên miền CDN công khai của TikTok / Douyin / Facebook để tránh lỗi timeout DNS trên VPS
    if (isAllowedMediaOrSocialHost($host)) {
        return true;
    }

    $ips = @gethostbynamel($host);
    if (empty($ips) || !is_array($ips)) {
        // Fallback sang dns_get_record (hỗ trợ cả A và AAAA) nếu gethostbynamel bị lỗi tạm thời
        $records = @dns_get_record($host, DNS_A + DNS_AAAA);
        if (!empty($records) && is_array($records)) {
            $ips = [];
            foreach ($records as $rec) {
                if (!empty($rec['ip'])) $ips[] = $rec['ip'];
                elseif (!empty($rec['ipv6'])) $ips[] = $rec['ipv6'];
            }
        }
    }
    if (empty($ips) || !is_array($ips)) return false;
    foreach ($ips as $ip) {
        if (!filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE)) {
            return false;
        }
    }
    return true;
}

function getBaseApiUrl() {
    $rawHost = $_SERVER['HTTP_HOST'] ?? 'snapall.giaiphap.pro';
    // Chống Host Header Injection: chỉ chấp nhận tên miền hợp lệ
    if (!preg_match('/^[a-zA-Z0-9.\-]+(?::\d{1,5})?$/', $rawHost)) {
        $host = 'snapall.giaiphap.pro';
    } else {
        $host = $rawHost;
    }
    $isHttps = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https')
        || (!empty($_SERVER['HTTP_CF_VISITOR']) && strpos($_SERVER['HTTP_CF_VISITOR'], 'https') !== false)
        || (strpos($host, 'giaiphap.pro') !== false);
    $scheme = $isHttps ? 'https' : 'http';
    return $scheme . '://' . $host . '/api.php';
}

function toAsciiFilename($filename) {
    $map = [
        'à'=>'a','á'=>'a','ạ'=>'a','ả'=>'a','ã'=>'a','â'=>'a','ầ'=>'a','ấ'=>'a','ậ'=>'a','ẩ'=>'a','ẫ'=>'a','ă'=>'a','ằ'=>'a','ắ'=>'a','ặ'=>'a','ẳ'=>'a','ẵ'=>'a',
        'è'=>'e','é'=>'e','ẹ'=>'e','ẻ'=>'e','ẽ'=>'e','ê'=>'e','ề'=>'e','ế'=>'e','ệ'=>'e','ể'=>'e','ễ'=>'e',
        'ì'=>'i','í'=>'i','ị'=>'i','ỉ'=>'i','ĩ'=>'i',
        'ò'=>'o','ó'=>'o','ọ'=>'o','ỏ'=>'o','õ'=>'o','ô'=>'o','ồ'=>'o','ố'=>'o','ộ'=>'o','ổ'=>'o','ỗ'=>'o','ơ'=>'o','ờ'=>'o','ớ'=>'o','ợ'=>'o','ở'=>'o','ỡ'=>'o',
        'ù'=>'u','ú'=>'u','ụ'=>'u','ủ'=>'u','ũ'=>'u','ư'=>'u','ừ'=>'u','ứ'=>'u','ự'=>'u','ử'=>'u','ữ'=>'u',
        'ỳ'=>'y','ý'=>'y','ỵ'=>'y','ỷ'=>'y','ỹ'=>'y','đ'=>'d',
        'À'=>'A','Á'=>'A','Ạ'=>'A','Ả'=>'A','Ã'=>'A','Â'=>'A','Ầ'=>'A','Ấ'=>'A','Ậ'=>'A','Ẩ'=>'A','Ẫ'=>'A','Ă'=>'A','Ằ'=>'A','Ắ'=>'A','Ặ'=>'A','Ẳ'=>'A','Ẵ'=>'A',
        'È'=>'E','É'=>'E','Ẹ'=>'E','Ẻ'=>'E','Ẽ'=>'E','Ê'=>'E','Ề'=>'E','Ế'=>'E','Ệ'=>'E','Ể'=>'E','Ễ'=>'E',
        'Ì'=>'I','Í'=>'I','Ị'=>'I','Ỉ'=>'I','Ĩ'=>'I',
        'Ò'=>'O','Ó'=>'O','Ọ'=>'O','Ỏ'=>'O','Õ'=>'O','Ô'=>'O','Ồ'=>'O','Ố'=>'O','Ộ'=>'O','Ổ'=>'O','Ỗ'=>'O','Ơ'=>'O','Ờ'=>'O','Ớ'=>'O','Ợ'=>'O','Ở'=>'O','Ỡ'=>'O',
        'Ù'=>'U','Ú'=>'U','Ụ'=>'U','Ủ'=>'U','Ũ'=>'U','Ư'=>'U','Ừ'=>'U','Ứ'=>'U','Ự'=>'U','Ử'=>'U','Ữ'=>'U',
        'Ỳ'=>'Y','Ý'=>'Y','Ỵ'=>'Y','Ỷ'=>'Y','Ỹ'=>'Y','Đ'=>'D'
    ];
    $s = strtr($filename, $map);
    $ext = strtolower(pathinfo($s, PATHINFO_EXTENSION));
    $base = pathinfo($s, PATHINFO_FILENAME);
    $base = preg_replace('/[^a-zA-Z0-9_\-]+/', '_', $base);
    $base = trim($base, '_-');
    if ($base === '') $base = 'snapall_media';
    return $ext !== '' ? ($base . '.' . $ext) : $base;
}

// Hàm dọn dẹp tiêu đề file sạch (dùng chung cho cả đầu trang và bên dưới)
function cleanTitle($str) {
    if (!$str) return 'video';
    $clean = preg_replace('/[\r\n\t]+/', ' ', $str);
    $clean = preg_replace('/[\\\\\\/:\\*\\?"<>\\|#%&{}<>\\$\\!\'`@\\+~]+/', '', $clean);
    $clean = preg_replace('/\\s+/', ' ', $clean);
    $clean = trim($clean);
    $clean = $clean ?: 'video';
    if (function_exists('mb_substr')) {
        return mb_substr($clean, 0, 42, 'UTF-8');
    }
    return preg_match('/^.{0,42}/us', $clean, $cut) ? $cut[0] : substr($clean, 0, 42);
}

function buildProxyDownloadUrl($rawUrl, $filename, $convertMp3 = false) {
    if (empty($rawUrl)) return '';
    $safeName = toAsciiFilename($filename);

    // 1. Lưu cache tạm trên server theo ID ngắn (12 ký tự hex) để phản hồi tức thì
    $dlId = substr(md5($rawUrl), 0, 12);
    $cacheDir = sys_get_temp_dir();
    if (!empty($cacheDir) && @is_writable($cacheDir)) {
        @file_put_contents($cacheDir . '/snapall_dl_' . $dlId . '.txt', $rawUrl);
        if (mt_rand(1, 50) === 1) {
            $now = time();
            foreach ((array) @glob($cacheDir . '/snapall_dl_*.txt') as $f) {
                if (@is_file($f) && ($now - (int) @filemtime($f)) > 21600) {
                    @unlink($f);
                }
            }
        }
    }

    // 2. Chia nhỏ chuỗi Base64 thành các đoạn <= 180 ký tự (b0, b1, b2...)
    // QUAN TRỌNG: Bộ nhận diện URL của iOS Shortcuts (Apple NSDataDetector / WFURLContentItem)
    // sẽ tự động cắt cụt mọi giá trị query param dài quá 511 ký tự (làm mất sạch dữ liệu sau '&b64').
    // Việc chia nhỏ mỗi param <= 180 ký tự giúp NSDataDetector giữ nguyên 100% URL trên mọi phiên bản iOS!
    $b64 = rtrim(strtr(base64_encode($rawUrl), '+/', '-~'), '=');
    $chunks = str_split($b64, 180);
    $bParams = [];
    foreach ($chunks as $idx => $chunk) {
        $bParams[] = 'b' . $idx . '=' . rawurlencode($chunk);
    }

    $url = getBaseApiUrl()
        . '?action=download'
        . '&id=' . $dlId
        . '&filename=' . rawurlencode($safeName)
        . '&' . implode('&', $bParams);
    if ($convertMp3) {
        $url .= '&convert=mp3';
    }
    return $url;
}

$action = $_GET['action'] ?? '';
if (empty($action) && !empty($_SERVER['QUERY_STRING']) && strpos($_SERVER['QUERY_STRING'], 'action=download') !== false) {
    $action = 'download';
}
if ($action === 'download' && (!empty($_GET['url']) || !empty($_GET['b64']) || !empty($_GET['id']) || !empty($_GET['b0']) || !empty($_SERVER['QUERY_STRING']))) {
    $fileUrl = '';

    // A. Khôi phục nhanh từ cache ID trên máy chủ (nếu có)
    $dlId = preg_replace('/[^a-f0-9]/i', '', $_GET['id'] ?? '');
    if (!empty($dlId)) {
        $cacheFile = sys_get_temp_dir() . '/snapall_dl_' . $dlId . '.txt';
        if (@is_file($cacheFile)) {
            $cachedUrl = trim((string) @file_get_contents($cacheFile));
            if (preg_match('/^https?:\/\//i', $cachedUrl)) {
                $fileUrl = $cachedUrl;
            }
        }
    }

    // B. Ghép các đoạn Base64 đã chia nhỏ (b0, b1, b2...) hoặc lấy từ b64 truyền thống
    $b64Param = $_GET['b64'] ?? '';
    if (empty($b64Param) && isset($_GET['b0'])) {
        $joined = '';
        for ($i = 0; $i < 20; $i++) {
            if (!isset($_GET['b' . $i])) break;
            $joined .= (string) $_GET['b' . $i];
        }
        $b64Param = $joined;
    }
    if (empty($b64Param) && !empty($_SERVER['QUERY_STRING']) && preg_match('/(?:^|[?&]|&amp;)b64=([^&]+)/', $_SERVER['QUERY_STRING'], $bm)) {
        $b64Param = rawurldecode($bm[1]);
    }
    if (empty($fileUrl) && !empty($b64Param)) {
        $tryDecode = function ($rawB64) {
            $b = strtr(trim($rawB64), '-~_ ', '+//+');
            $b = preg_replace('/[^A-Za-z0-9+\/]/', '', $b);
            $pad = strlen($b) % 4;
            if ($pad === 1) return '';
            if ($pad > 0) $b .= str_repeat('=', 4 - $pad);
            $dec = base64_decode($b, true);
            return ($dec !== false && preg_match('/^https?:\/\//i', trim($dec))) ? trim($dec) : '';
        };

        $fileUrl = $tryDecode($b64Param);

        // Khôi phục tự động nếu phím tắt trên iPhone dùng bản cũ làm mất dấu '_' ở vị trí '?_a=0' ('/_YT0' -> '/YT0')
        if (empty($fileUrl) || !filter_var($fileUrl, FILTER_VALIDATE_URL)) {
            $repairedB64 = preg_replace('/(Qy8|di8|NS8|dC8|MC8|MS8|Mi8|My8|NC8|Ni8|Ny8|OC8|OS8)(YT0[A-Za-z0-9])/', '$1_$2', $b64Param);
            if ($repairedB64 !== $b64Param) {
                $candidate = $tryDecode($repairedB64);
                if (!empty($candidate) && filter_var($candidate, FILTER_VALIDATE_URL)) {
                    $fileUrl = $candidate;
                }
            }
        }
    }
    if (empty($fileUrl) && !empty($_GET['url'])) {
        $fileUrl = trim($_GET['url']);
    }

    if (!isSafeRemoteUrl($fileUrl, true)) {
        http_response_code(403);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode([
            'status' => 'error',
            'message' => 'Liên kết tải xuống không hợp lệ hoặc bị chặn vì lý do bảo mật.'
        ], JSON_UNESCAPED_UNICODE);
        exit;
    }

    $rawFilename = $_GET['filename'] ?? '';
    if (empty($rawFilename) && !empty($_SERVER['QUERY_STRING']) && preg_match('/(?:^|[?&]|&amp;)filename=([^&]+)/', $_SERVER['QUERY_STRING'], $fm)) {
        $rawFilename = rawurldecode($fm[1]);
    }
    $filename = preg_replace('/[^a-zA-Z0-9_\-\.]/', '_', $rawFilename ?: 'file');
    $ext = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
    $contentType = 'application/octet-stream';
    if ($ext === 'mp4') $contentType = 'video/mp4';
    elseif ($ext === 'mp3') $contentType = 'audio/mpeg';
    elseif ($ext === 'm4a') $contentType = 'audio/mp4';
    elseif (in_array($ext, ['jpg', 'jpeg'])) $contentType = 'image/jpeg';
    elseif ($ext === 'png') $contentType = 'image/png';
    elseif ($ext === 'webp') $contentType = 'image/webp';

    header('Content-Description: File Transfer');
    header('Content-Type: ' . $contentType);
    header('Content-Disposition: attachment; filename="' . $filename . '"');
    header('Expires: 0');
    header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
    header('Pragma: public');

    // Nếu yêu cầu tải file .mp3 và máy chủ có sẵn ffmpeg, tự động chuyển đổi định dạng chuẩn MP3 128kbps
    // (Xử lý triệt để trường hợp video Facebook MP4 hoặc âm thanh TikTok M4A/MP4 bị lỗi không phát được khi đổi tên .mp3)
    $needConvertMp3 = ($ext === 'mp3') && (
        !empty($_GET['convert']) ||
        preg_match('/(mime_type=audio_mp4|mime_type=video_mp4|tos-alisg-ve-2774|\.mp4|\.m4a|fbcdn\.net)/i', $fileUrl)
    );
    if ($needConvertMp3 && function_exists('passthru')) {
        $ffmpegBin = '';
        foreach (['/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg', '/opt/homebrew/bin/ffmpeg'] as $candidate) {
            if (@is_executable($candidate)) {
                $ffmpegBin = $candidate;
                break;
            }
        }
        if ($ffmpegBin !== '') {
            $ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
            $cmd = escapeshellcmd($ffmpegBin)
                . ' -loglevel error -protocol_whitelist https,http,tcp,tls,crypto -user_agent ' . escapeshellarg($ua)
                . ' -i ' . escapeshellarg($fileUrl)
                . ' -vn -acodec libmp3lame -ab 128k -ar 44100 -f mp3 pipe:1';
            @passthru($cmd, $retCode);
            if ($retCode === 0) {
                exit;
            }
        }
    }

    $ch = curl_init($fileUrl);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_MAXREDIRS, 5);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 90);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1');
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Referer: https://www.tiktok.com/'
    ]);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
    if (defined('CURLOPT_PROTOCOLS')) {
        curl_setopt($ch, CURLOPT_PROTOCOLS, CURLPROTO_HTTP | CURLPROTO_HTTPS);
        curl_setopt($ch, CURLOPT_REDIR_PROTOCOLS, CURLPROTO_HTTP | CURLPROTO_HTTPS);
    }
    curl_exec($ch);
    if (PHP_VERSION_ID < 80500) {
        @curl_close($ch);
    }
    exit;
}

if (!headers_sent()) {
    header('Content-Type: application/json; charset=utf-8');
}

// -------------------------------------------------------------
// Versioning & Auto-Update Configuration
// -------------------------------------------------------------
$CURRENT_VERSION = '12.5';
$UPDATE_URL = 'https://www.icloud.com/shortcuts/507b7dcf64004b47865103b8f63541b5';

function sendJsonResponse(array $payload) {
    global $CURRENT_VERSION, $UPDATE_URL;
    $clientVersion = $_GET['v'] ?? $_GET['version'] ?? '';
    $hasUpdate = (!empty($clientVersion) && version_compare($clientVersion, $CURRENT_VERSION, '<'));
    
    $payload['version'] = $CURRENT_VERSION;
    $payload['has_update'] = $hasUpdate ? 'true' : 'false';
    $payload['latest_version'] = $CURRENT_VERSION;
    $payload['update_url'] = $UPDATE_URL;

    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    exit;
}

if (isset($_GET['action']) && $_GET['action'] === 'check_update') {
    $clientVersion = $_GET['v'] ?? $_GET['version'] ?? '1.0';
    $hasUpdate = version_compare($clientVersion, $CURRENT_VERSION, '<');
    sendJsonResponse([
        'status' => 'success',
        'has_update' => $hasUpdate ? 'true' : 'false',
        'message' => $hasUpdate 
            ? "Đã có bản cập nhật mới SnapAll v{$CURRENT_VERSION}!" 
            : "Bạn đang sử dụng phiên bản mới nhất SnapAll v{$CURRENT_VERSION}."
    ]);
}

// -------------------------------------------------------------
// 1. Nhận & Làm sạch URL
// -------------------------------------------------------------
$inputUrl = '';

// A. Hỗ trợ tham số b64 (hỗ trợ cả chuẩn Base64 thường, URL-safe Base64 và dấu '+' bị đổi thành khoảng trắng trên URL)
if (!empty($_GET['b64'])) {
    $b64Clean = strtr(trim($_GET['b64']), '-_ ', '+/+');
    $b64Clean = preg_replace('/[^A-Za-z0-9+\/=]/', '', $b64Clean);
    $pad = strlen($b64Clean) % 4;
    if ($pad > 0) $b64Clean .= str_repeat('=', 4 - $pad);
    $decoded = base64_decode($b64Clean);
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
if (!empty($inputUrl) && preg_match('/https?:\/\/[^\s"\'<>]+/i', $inputUrl, $matchUrl)) {
    $inputUrl = rtrim($matchUrl[0], '.,;!?)]}\'"');
}

if (empty($inputUrl) || !isSafeRemoteUrl($inputUrl)) {
    sendJsonResponse([
        'status' => 'error',
        'message' => 'Vui lòng cung cấp liên kết hợp lệ (url hoặc b64) video TikTok hoặc Facebook.'
    ]);
}

// Hàm gửi request cURL
function fetchCurl($url, $customHeaders = [], $followRedirect = true) {
    if (!isSafeRemoteUrl($url)) {
        return ['code' => 403, 'body' => '', 'url' => $url];
    }
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
    if (defined('CURLOPT_PROTOCOLS')) {
        curl_setopt($ch, CURLOPT_PROTOCOLS, CURLPROTO_HTTP | CURLPROTO_HTTPS);
        curl_setopt($ch, CURLOPT_REDIR_PROTOCOLS, CURLPROTO_HTTP | CURLPROTO_HTTPS);
    }

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $effectiveUrl = curl_getinfo($ch, CURLINFO_EFFECTIVE_URL);
    if (PHP_VERSION_ID < 80500) {
        @curl_close($ch);
    }

    if (!empty($effectiveUrl) && $effectiveUrl !== $url && !isSafeRemoteUrl($effectiveUrl)) {
        return ['code' => 403, 'body' => '', 'url' => $effectiveUrl];
    }

    return [
        'code' => $httpCode,
        'body' => $response,
        'url'  => $effectiveUrl
    ];
}

// -------------------------------------------------------------
// 2. Xử lý TIKTOK & DOUYIN
// -------------------------------------------------------------
if (preg_match('/(tiktok\.com|douyin\.com)/i', $inputUrl)) {
    $apiUrl = 'https://www.tikwm.com/api/?hd=1&url=' . urlencode($inputUrl);
    $res = fetchCurl($apiUrl);
    $item = null;
    $tiktokErrorReason = '';

    if ($res['code'] === 200 && !empty($res['body'])) {
        $data = json_decode($res['body'], true);
        if (isset($data['code']) && $data['code'] === 0 && isset($data['data'])) {
            $item = $data['data'];
        }
    }

    // Fallback: Bóc tách trực tiếp từ trang TikTok (__UNIVERSAL_DATA_FOR_REHYDRATION__)
    // hoặc phát hiện chính xác nếu tài khoản / bài viết đang để chế độ Riêng tư (Private)
    if (!$item) {
        $directRes = fetchCurl($inputUrl);
        if (!empty($directRes['body']) && preg_match('/<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)<\/script>/s', $directRes['body'], $mRehy)) {
            $rehy = json_decode($mRehy[1], true);
            $scope = $rehy['__DEFAULT_SCOPE__'] ?? [];
            $detail = $scope['webapp.reflow.video.detail'] ?? ($scope['webapp.video-detail'] ?? []);
            $statusCode = (int) ($detail['statusCode'] ?? 0);
            $shareUser = $scope['webapp.reflow.global.shareUser']['shareUser'] ?? [];
            $isPrivateUser = !empty($shareUser['privateAccount']) || !empty($shareUser['secret']);
            $uName = !empty($shareUser['uniqueId']) ? ('@' . $shareUser['uniqueId']) : '';

            if (!empty($detail['itemInfo']['itemStruct'])) {
                $st = $detail['itemInfo']['itemStruct'];
                $imgs = [];
                if (!empty($st['imagePost']['images']) && is_array($st['imagePost']['images'])) {
                    foreach ($st['imagePost']['images'] as $im) {
                        if (!empty($im['imageURL']['urlList'][0])) {
                            $imgs[] = $im['imageURL']['urlList'][0];
                        }
                    }
                }
                $playUrl = $st['video']['playAddr'] ?? ($st['video']['downloadAddr'] ?? '');
                $item = [
                    'title' => $st['desc'] ?? '',
                    'author' => [
                        'nickname' => $st['author']['nickname'] ?? ($shareUser['nickname'] ?? 'TikTok Creator'),
                        'unique_id' => $st['author']['uniqueId'] ?? ($shareUser['uniqueId'] ?? '')
                    ],
                    'images' => $imgs,
                    'music' => $st['music']['playUrl'] ?? '',
                    'hdplay' => $playUrl,
                    'play' => $playUrl,
                    'wmplay' => $st['video']['downloadAddr'] ?? $playUrl,
                    'cover' => $st['video']['cover'] ?? (!empty($imgs) ? $imgs[0] : '')
                ];
            } elseif (in_array($statusCode, [10222, 10216, 10204], true) || $isPrivateUser) {
                $tiktokErrorReason = 'Bài đăng này thuộc tài khoản Riêng tư' . ($uName ? " ({$uName})" : '') . ' hoặc đang để chế độ "Chỉ bạn bè / Chỉ mình tôi" nên TikTok chặn tải từ bên ngoài. Vui lòng chuyển tài khoản/bài viết sang Công khai (Mọi người) rồi thử lại!';
            }
        }
    }

    if ($item) {
        if (true) {
            
            $author = $item['author']['nickname'] ?? ($item['author']['unique_id'] ?? 'TikTok Creator');
            $rawTitle = !empty($item['title']) ? $item['title'] : ('TikTok by ' . $author);
            $titleText = cleanTitle($rawTitle);
            
            $images = $item['images'] ?? [];
            $isSlideshow = (!empty($images) && is_array($images) && count($images) > 0);

            $audioUrl = $item['music'] ?? '';
            if (empty($audioUrl) && !empty($item['music_info']['play'])) {
                $audioUrl = $item['music_info']['play'];
            }
            if (empty($audioUrl)) {
                $audioUrl = $item['play'] ?? $item['hdplay'] ?? '';
            }

            // Nếu là album ảnh slideshow, tikwm trả play/hdplay là file audio chứ không phải video
            if ($isSlideshow) {
                $videoHd = '';
                $videoSd = '';
                $videoWm = '';
            } else {
                $videoHd = !empty($item['hdplay']) ? $item['hdplay'] : ($item['play'] ?? '');
                $videoSd = $item['play'] ?? '';
                $videoWm = $item['wmplay'] ?? '';
            }

            $labels = [];
            $medias = [];
            // Đồng nhất 100% link tải trong medias qua cùng domain proxy (snapall.giaiphap.pro)
            // để iOS Shortcuts chỉ hỏi quyền Lưu vào Album Ảnh đúng 1 lần duy nhất ("Always Allow")!
            $add = function ($lbl, $link, $fname, $convertMp3 = false) use (&$labels, &$medias) {
                if (!empty($link)) {
                    $labels[] = $lbl;
                    $medias[$lbl] = buildProxyDownloadUrl($link, $fname, $convertMp3);
                }
            };

            // Nếu là album ảnh slideshow
            if ($isSlideshow) {
                foreach ($images as $idx => $img) {
                    $num = $idx + 1;
                    $add('🖼️ JPG HD ' . $num, $img, $titleText . '_anh_' . $num . '.jpg');
                }
            } else {
                $add('🎬 MP4 HD', $videoSd ?: $videoHd, $titleText . '_HD.mp4');
                if (!empty($videoHd) && $videoHd !== $videoSd) {
                    $add('🎬 MP4 FULL HD', $videoHd, $titleText . '_FullHD.mp4');
                }
                $add('🎬 MP4 WATERMARK', $videoWm, $titleText . '_Watermark.mp4');
            }

            // Âm thanh MP3
            if (!empty($audioUrl)) {
                $add('🎵 MP3 128KBPS', $audioUrl, $titleText . '_audio.mp3', true);
            }

            $downloadProxy = [];
            if (!empty($audioUrl)) {
                $downloadProxy['audio'] = buildProxyDownloadUrl($audioUrl, $titleText . '_audio.mp3', true);
            }
            if (!$isSlideshow && (!empty($videoHd) || !empty($videoSd))) {
                $downloadProxy['video'] = buildProxyDownloadUrl($videoHd ?: $videoSd, $titleText . '_video.mp4');
            }

            sendJsonResponse([
                'status' => 'success',
                'platform' => 'tiktok',
                'type' => $isSlideshow ? 'slideshow' : 'video',
                'is_slideshow' => $isSlideshow,
                'title' => $titleText,
                'author' => $author,
                'thumbnail' => $item['cover'] ?? (!empty($images) ? $images[0] : ''),
                'video' => $videoHd ?: $videoSd,
                'video_hd' => $videoHd,
                'video_sd' => $videoSd,
                'audio' => $audioUrl,
                'images' => $images,
                'image_count' => count($images),
                'menu_title' => 'Choose media:',
                'labels' => $labels,
                'medias' => $medias,
                'download_proxy' => $downloadProxy
            ]);
        }
    }

    sendJsonResponse([
        'status' => 'error',
        'message' => $tiktokErrorReason ?: 'Không thể lấy video TikTok. Vui lòng kiểm tra lại liên kết hoặc thử lại sau.'
    ]);
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

        // Lấy ID video từ URL cuối (share/v/... redirect sang /reel/{id})
        $videoId = '';
        if (preg_match('~/(?:reel|videos)/(\d{8,})|[?&]v=(\d{8,})~', ($res['url'] ?? '') . ' ' . $inputUrl, $idm)) {
            $videoId = !empty($idm[1]) ? $idm[1] : ($idm[2] ?? '');
        }

        // Ưu tiên link nằm gần ID video (trang reel chứa cả các reel gợi ý)
        $pickFbUrl = function (array $keys) use ($cleanHtml, $videoId) {
            $first = '';
            foreach ($keys as $key) {
                if (!preg_match_all('/"?' . preg_quote($key, '/') . '"?:"((?:[^"\\\\]|\\\\.)+)"/', $cleanHtml, $all, PREG_OFFSET_CAPTURE)) {
                    continue;
                }
                foreach ($all[1] as $hit) {
                    $url = json_decode('"' . $hit[0] . '"');
                    if (!$url) $url = str_replace('\\/', '/', $hit[0]);
                    if (!preg_match('~^https?://~', $url)) continue;
                    if ($first === '') $first = $url;
                    if ($videoId === '') return $url;
                    $seg = substr($cleanHtml, max(0, $hit[1] - 3000), 6000);
                    if (strpos($seg, $videoId) !== false) return $url;
                }
            }
            return $first;
        };

        $hd = $pickFbUrl(['browser_native_hd_url', 'playable_url_quality_hd', 'hd_src_no_ratelimit', 'hd_src']);
        $sd = $pickFbUrl(['browser_native_sd_url', 'playable_url', 'sd_src_no_ratelimit', 'sd_src']);

        $finalVideo = $hd ?: $sd;

        if (!empty($finalVideo)) {
            $titleText = 'Facebook Video';
            if (preg_match('/<meta\s+property="og:title"\s+content="([^"]*)"/i', $cleanHtml, $tm)) {
                $titleText = $tm[1];
            } elseif (preg_match('/<title>(.*?)<\/title>/i', $cleanHtml, $tm)) {
                $titleText = $tm[1];
            }
            $titleText = html_entity_decode($titleText, ENT_QUOTES | ENT_HTML5, 'UTF-8');
            $titleText = preg_replace('/^[^|]*\b(views|reactions|lượt xem)\b[^|]*\|\s*/iu', '', $titleText);
            $titleClean = cleanTitle($titleText);

            $thumb = '';
            if (preg_match('/<meta\s+property="og:image"\s+content="([^"]*)"/i', $cleanHtml, $im)) {
                $thumb = $im[1];
            }

            $labels = [];
            $medias = [];

            if (!empty($hd)) {
                $labels[] = '🎬 MP4 HD';
                $medias['🎬 MP4 HD'] = buildProxyDownloadUrl($hd, $titleClean . '_HD.mp4');
            }
            if (!empty($sd) && (empty($hd) || $sd !== $hd)) {
                $labels[] = '🎬 MP4 SD';
                $medias['🎬 MP4 SD'] = buildProxyDownloadUrl($sd, $titleClean . '_SD.mp4');
            }
            $labels[] = '🎵 MP3 AUDIO';
            $medias['🎵 MP3 AUDIO'] = buildProxyDownloadUrl($finalVideo, $titleClean . '_audio.mp3', true);

            sendJsonResponse([
                'status' => 'success',
                'platform' => 'facebook',
                'type' => 'video',
                'is_slideshow' => false,
                'title' => $titleClean,
                'thumbnail' => $thumb,
                'video' => $finalVideo,
                'video_hd' => $hd ?: $sd,
                'video_sd' => $sd ?: $hd,
                'audio' => $finalVideo,
                'menu_title' => 'Choose media:',
                'labels' => $labels,
                'medias' => $medias,
                'download_proxy' => [
                    'video' => buildProxyDownloadUrl($finalVideo, $titleClean . '_video.mp4'),
                    'audio' => buildProxyDownloadUrl($finalVideo, $titleClean . '_audio.mp3', true)
                ]
            ]);
        }
    }

    sendJsonResponse([
        'status' => 'error',
        'message' => 'Không tìm thấy video Facebook công khai hoặc video yêu cầu đăng nhập.'
    ]);
}

// -------------------------------------------------------------
// 4. Link Tệp Media Trực Tiếp (Direct File URL)
// -------------------------------------------------------------
if (preg_match('/\.(mp4|mov|mp3|m4a|jpg|jpeg|png|webp)(\?.*)?$/i', $inputUrl, $extM)) {
    $ext = strtolower($extM[1]);
    $isAudio = in_array($ext, ['mp3', 'm4a']);
    $isImage = in_array($ext, ['jpg', 'jpeg', 'png', 'webp']);
    $icon = $isAudio ? '🎵' : ($isImage ? '🖼️' : '🎬');
    $lbl = $icon . ' ' . strtoupper($ext) . ' ORIGINAL';
    $titleDirect = 'media_file_' . time();

    sendJsonResponse([
        'status' => 'success',
        'platform' => 'direct',
        'type' => $isImage ? 'slideshow' : 'video',
        'is_slideshow' => $isImage,
        'title' => $titleDirect,
        'menu_title' => 'Choose media:',
        'labels' => [$lbl],
        'medias' => [$lbl => buildProxyDownloadUrl($inputUrl, $titleDirect . '.' . $ext)],
        'video' => $isAudio ? '' : $inputUrl,
        'audio' => $isAudio ? $inputUrl : '',
        'thumbnail' => ''
    ]);
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

    sendJsonResponse([
        'status' => 'success',
        'platform' => 'generic',
        'type' => 'video',
        'is_slideshow' => false,
        'title' => $titleClean,
        'thumbnail' => '',
        'video' => $videoUrl,
        'audio' => $videoUrl,
        'menu_title' => 'Choose media:',
        'labels' => ['🎬 MP4 VIDEO', '🎵 MP3 AUDIO'],
        'medias' => [
            '🎬 MP4 VIDEO' => buildProxyDownloadUrl($videoUrl, $titleClean . '.mp4'),
            '🎵 MP3 AUDIO' => buildProxyDownloadUrl($videoUrl, $titleClean . '.mp3', true)
        ]
    ]);
}

sendJsonResponse([
    'status' => 'error',
    'message' => 'Nền tảng này chưa được hỗ trợ hoặc liên kết không chứa video công khai.'
]);
