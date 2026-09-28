// Vercel Serverless Function: /api/parse
// Hỗ trợ bóc tách link TikTok, Douyin, Facebook và đa nền tảng cho Apple Shortcut & Web
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  let inputUrl = '';

  // 1. Nhận từ tham số b64 (tương thích cơ chế base64 của Snap Video gốc)
  if (req.query.b64) {
    try {
      inputUrl = Buffer.from(req.query.b64, 'base64').toString('utf-8').trim();
    } catch (e) {
      inputUrl = '';
    }
  }

  // 2. Nhận từ tham số url
  if (!inputUrl && req.query.url) {
    inputUrl = String(req.query.url).trim();
  }

  // 3. Xử lý trường hợp URL bị cắt do chứa nhiều tham số query ? và &
  if (!inputUrl && req.url && req.url.includes('url=')) {
    const rawUrlPart = req.url.substring(req.url.indexOf('url=') + 4);
    if (rawUrlPart) {
      try {
        inputUrl = decodeURIComponent(rawUrlPart).trim();
      } catch (e) {
        inputUrl = rawUrlPart.trim();
      }
    }
  }

  // Tách URL sạch từ văn bản nếu người dùng dán cả đoạn văn bản
  if (inputUrl) {
    const match = inputUrl.match(/https?:\/\/[^\s]+/i);
    if (match) {
      inputUrl = match[0];
    }
  }

  if (!inputUrl) {
    return res.status(400).json({
      status: 'error',
      message: 'Vui lòng cung cấp liên kết (url hoặc b64) video hợp lệ.'
    });
  }

  // Hàm dọn dẹp tiêu đề file sạch
  function cleanTitle(str) {
    if (!str) return 'video';
    return str
      .replace(/[\r\n\t]+/g, ' ')
      .replace(/[\\\/:\*\?"<>\|#%&{}<>\\$\!'`@\+~]+/g, '')
      .replace(/\s+/g, ' ')
      .trim()
      .substring(0, 60) || 'video';
  }

  try {
    // -------------------------------------------------------------
    // 1. TIKTOK & DOUYIN
    // -------------------------------------------------------------
    if (/tiktok\.com|douyin\.com/i.test(inputUrl)) {
      const response = await fetch(`https://www.tikwm.com/api/?url=${encodeURIComponent(inputUrl)}`, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        }
      });
      const data = await response.json();

      if (data && data.code === 0 && data.data) {
        const item = data.data;
        const author = item.author?.nickname || item.author?.unique_id || 'TikTok Creator';
        const titleText = cleanTitle(item.title ? item.title.trim() : `TikTok by ${author}`);
        const videoHd = item.hdplay || item.play || '';
        const videoSd = item.play || '';
        const audioUrl = item.music || '';
        const images = item.images || [];

        const labels = [];
        const medias = {};

        // Phân loại: Ảnh Slideshow hay Video
        if (images && images.length > 0) {
          images.forEach((img, idx) => {
            const lbl = `🖼️ Tải Ảnh ${idx + 1} jpg`;
            labels.push(lbl);
            medias[lbl] = img;
          });
        } else {
          if (videoHd) {
            labels.push('🎬 Tải Video HD (Không logo) mp4');
            medias['🎬 Tải Video HD (Không logo) mp4'] = videoHd;
          }
          if (videoSd && videoSd !== videoHd) {
            labels.push('🎬 Tải Video SD mp4');
            medias['🎬 Tải Video SD mp4'] = videoSd;
          }
        }

        // Âm thanh MP3
        if (audioUrl) {
          labels.push('🎵 Trích xuất Âm thanh mp3');
          medias['🎵 Trích xuất Âm thanh mp3'] = audioUrl;
        }

        return res.status(200).json({
          status: 'success',
          platform: 'tiktok',
          title: titleText,
          author,
          thumbnail: item.cover || '',
          video: videoHd || videoSd,
          video_hd: videoHd,
          video_sd: videoSd,
          audio: audioUrl,
          menu_title: `⚡️ Chọn định dạng (${titleText}):`,
          labels,
          medias
        });
      }

      return res.status(400).json({
        status: 'error',
        message: 'Không thể phân giải video TikTok. Vui lòng kiểm tra lại liên kết.'
      });
    }

    // -------------------------------------------------------------
    // 2. FACEBOOK (Reels, Watch, Post, Video)
    // -------------------------------------------------------------
    if (/facebook\.com|fb\.watch|fb\.me/i.test(inputUrl)) {
      const fbRes = await fetch(inputUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.9',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'none'
        }
      });
      const html = await fbRes.text();
      const cleanHtml = html.replace(/&quot;/g, '"').replace(/&amp;/g, '&');

      function extractPattern(regex) {
        const m = cleanHtml.match(regex);
        if (m && m[1]) {
          try {
            return JSON.parse(`"${m[1]}"`);
          } catch (e) {
            return m[1].replace(/\\\//g, '/');
          }
        }
        return '';
      }

      const hd = extractPattern(/"browser_native_hd_url":"(.*?)"/) ||
                 extractPattern(/"playable_url_quality_hd":"(.*?)"/) ||
                 extractPattern(/hd_src:"(.*?)"/) ||
                 extractPattern(/hd_src_no_ratelimit:"(.*?)"/);

      const sd = extractPattern(/"browser_native_sd_url":"(.*?)"/) ||
                 extractPattern(/"playable_url":"(.*?)"/) ||
                 extractPattern(/sd_src:"(.*?)"/) ||
                 extractPattern(/sd_src_no_ratelimit:"(.*?)"/);

      const finalVideo = hd || sd;

      if (finalVideo) {
        const titleMatch = cleanHtml.match(/<meta\s+property="og:title"\s+content="([^"]*)"/i) ||
                           cleanHtml.match(/<title>(.*?)<\/title>/i);
        const thumbMatch = cleanHtml.match(/<meta\s+property="og:image"\s+content="([^"]*)"/i);
        const titleText = cleanTitle(titleMatch ? titleMatch[1] : 'Facebook Video');

        const labels = [];
        const medias = {};

        if (hd) {
          labels.push('🎬 Tải Video Facebook HD mp4');
          medias['🎬 Tải Video Facebook HD mp4'] = hd;
        }
        if (sd && (!hd || sd !== hd)) {
          labels.push('🎬 Tải Video Facebook SD mp4');
          medias['🎬 Tải Video Facebook SD mp4'] = sd;
        }
        labels.push('🎵 Trích xuất Âm thanh từ Video mp3');
        medias['🎵 Trích xuất Âm thanh từ Video mp3'] = finalVideo;

        return res.status(200).json({
          status: 'success',
          platform: 'facebook',
          title: titleText,
          thumbnail: thumbMatch ? thumbMatch[1] : '',
          video: finalVideo,
          video_hd: hd || sd,
          video_sd: sd || hd,
          audio: finalVideo,
          menu_title: `⚡️ Chọn định dạng (${titleText}):`,
          labels,
          medias
        });
      }

      return res.status(400).json({
        status: 'error',
        message: 'Không tìm thấy video Facebook công khai hoặc video yêu cầu đăng nhập.'
      });
    }

    // -------------------------------------------------------------
    // 3. LINK FILE TRỰC TIẾP (Direct Media URL)
    // -------------------------------------------------------------
    if (/\.(mp4|mov|mp3|m4a|jpg|jpeg|png|webp)(\?.*)?$/i.test(inputUrl)) {
      const extMatch = inputUrl.match(/\.(mp4|mov|mp3|m4a|jpg|jpeg|png|webp)/i);
      const ext = extMatch ? extMatch[1].toLowerCase() : 'mp4';
      const isAudio = /mp3|m4a/i.test(ext);
      const isImage = /jpg|jpeg|png|webp/i.test(ext);
      const icon = isAudio ? '🎵' : (isImage ? '🖼️' : '🎬');
      const labelName = `${icon} Tải file gốc ${ext}`;

      return res.status(200).json({
        status: 'success',
        platform: 'direct',
        title: `media_file_${Date.now()}`,
        menu_title: '⚡️ Tải tệp tin media trực tiếp:',
        labels: [labelName],
        medias: {
          [labelName]: inputUrl
        },
        video: isAudio ? '' : inputUrl,
        audio: isAudio ? inputUrl : '',
        thumbnail: ''
      });
    }

    // -------------------------------------------------------------
    // 4. FALLBACK: Cố gắng cào og:video từ trang web bất kỳ
    // -------------------------------------------------------------
    try {
      const pageRes = await fetch(inputUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
        }
      });
      const html = await pageRes.text();
      const ogVideo = html.match(/<meta\s+property="og:video(?::secure_url)?"\s+content="([^"]*)"/i);
      const ogTitle = html.match(/<meta\s+property="og:title"\s+content="([^"]*)"/i) || html.match(/<title>(.*?)<\/title>/i);
      const ogImage = html.match(/<meta\s+property="og:image"\s+content="([^"]*)"/i);

      if (ogVideo && ogVideo[1]) {
        const videoUrl = ogVideo[1].replace(/&amp;/g, '&');
        const titleText = cleanTitle(ogTitle ? ogTitle[1] : 'Web Video');
        const labels = ['🎬 Tải Video mp4', '🎵 Trích xuất Âm thanh mp3'];
        const medias = {
          '🎬 Tải Video mp4': videoUrl,
          '🎵 Trích xuất Âm thanh mp3': videoUrl
        };

        return res.status(200).json({
          status: 'success',
          platform: 'generic',
          title: titleText,
          thumbnail: ogImage ? ogImage[1] : '',
          video: videoUrl,
          audio: videoUrl,
          menu_title: `⚡️ Tải video (${titleText}):`,
          labels,
          medias
        });
      }
    } catch (fallbackErr) {
      // Ignored
    }

    return res.status(400).json({
      status: 'error',
      message: 'Nền tảng này chưa được hỗ trợ hoặc liên kết không chứa video công khai.'
    });
  } catch (err) {
    return res.status(500).json({
      status: 'error',
      message: `Lỗi máy chủ khi xử lý: ${err.message}`
    });
  }
}
