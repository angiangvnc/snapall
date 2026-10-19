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

  // 3. Xử lý trường hợp URL bị cắt do chứa nhiều tham số query
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
    if (match) inputUrl = match[0];
  }

  if (!inputUrl) {
    return res.status(400).json({
      status: 'error',
      message: 'Vui lòng cung cấp liên kết (url hoặc b64) video hợp lệ.'
    });
  }

  function cleanTitle(str) {
    if (!str) return 'video';
    return str
      .replace(/[\r\n\t]+/g, ' ')
      .replace(/[\\\/:\*\?"<>\|#%&{}<>\\$\!'`@\+~]+/g, '')
      .replace(/\s+/g, ' ')
      .trim()
      .substring(0, 60) || 'video';
  }

  // Helper: tạo response schema đầy đủ tương thích Snap Video clone
  function makeResponse({ status = 'success', platform, title, menu_title, labels, medias, thumbnail = '', video = '', audio = '' }) {
    return {
      status,
      platform,
      title,
      thumbnail,
      video,
      audio,
      menu_title: menu_title || 'Choose media:',
      labels,
      medias,
      select_multiple: 'true',    // string 'true' → iOS Shortcuts đọc đúng
      skip_select: '',             // empty = hiện menu; 'true' = bỏ qua menu (tự chọn hết)
      open_album: '🖼️ Open Photos',
      open_file: '📁 Open Files',
      close: '❌ Close',
      menu_done_title: '🥳 Download successful!!'
    };
  }

  try {
    // ------------------------------------------------------------------
    // 1. TIKTOK & DOUYIN
    // ------------------------------------------------------------------
    if (/tiktok\.com|douyin\.com/i.test(inputUrl)) {
      const response = await fetch(`https://www.tikwm.com/api/?hd=1&url=${encodeURIComponent(inputUrl)}`, {
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
        const videoWm = item.wmplay || '';
        const audioUrl = item.music || '';
        const images = item.images || [];

        const labels = [];
        const medias = {};
        const add = (lbl, link) => { if (link) { labels.push(lbl); medias[lbl] = link; } };

        if (images && images.length > 0) {
          images.forEach((img, idx) => add(`🖼️ PHOTO ${idx + 1}`, img));
        } else {
          add('🎬 MP4 HD', videoSd || videoHd);
          if (videoHd && videoHd !== videoSd) add('🎬 MP4 FULL HD', videoHd);
          add('🎬 MP4 WATERMARK', videoWm);
        }

        add('🎵 MP3 128KBPS', audioUrl);

        if (labels.length > 0) {
          return res.status(200).json(makeResponse({
            platform: 'tiktok',
            title: titleText,
            menu_title: 'Choose media:',
            labels, medias,
            thumbnail: item.cover || '',
            video: videoHd || videoSd,
            audio: audioUrl
          }));
        }
      }

      return res.status(400).json({
        status: 'error',
        message: 'Không tìm thấy video TikTok. Video có thể riêng tư hoặc đã bị xóa.'
      });
    }

    // ------------------------------------------------------------------
    // 2. FACEBOOK
    // ------------------------------------------------------------------
    if (/facebook\.com|fb\.watch|fb\.com|fb\.me/i.test(inputUrl)) {
      const DESKTOP_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
      const IPHONE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';

      const fetchFb = async (ua) => {
        const r = await fetch(inputUrl, {
          redirect: 'follow',
          headers: {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1'
          }
        });
        return { html: await r.text(), finalUrl: r.url || inputUrl };
      };

      // Giải mã chuỗi JSON escape (\/ , \u0026 ...)
      const unJson = (s) => {
        try { return JSON.parse(`"${s}"`); } catch (e) { return s.replace(/\\\//g, '/'); }
      };
      // Giải mã HTML entity (&#x1edd; &amp; ...)
      const unHtml = (s) => s
        .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
        .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(parseInt(d, 10)))
        .replace(/&quot;/g, '"').replace(/&#039;|&apos;/g, "'")
        .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');

      // Lấy URL theo danh sách key, ưu tiên lần xuất hiện gần ID video (trang reel chứa cả reel gợi ý)
      const pickUrl = (html, keys, videoId) => {
        let first = '';
        for (const key of keys) {
          const re = new RegExp(`"${key}":"((?:[^"\\\\]|\\\\.)+)"`, 'g');
          let m;
          while ((m = re.exec(html)) !== null) {
            const url = unJson(m[1]);
            if (!/^https?:\/\//.test(url)) continue;
            if (!first) first = url;
            if (!videoId) return url;
            const seg = html.slice(Math.max(0, m.index - 3000), m.index + 3000);
            if (seg.includes(videoId)) return url;
          }
        }
        return first;
      };

      let { html, finalUrl } = await fetchFb(DESKTOP_UA);
      const idMatch = (finalUrl + ' ' + inputUrl).match(/\/(?:reel|videos|watch\/?\?v=)\/?(\d{8,})|[?&]v=(\d{8,})/);
      const videoId = idMatch ? (idMatch[1] || idMatch[2]) : '';

      let hd = pickUrl(html, ['browser_native_hd_url', 'playable_url_quality_hd', 'hd_src_no_ratelimit', 'hd_src'], videoId);
      let sd = pickUrl(html, ['browser_native_sd_url', 'playable_url', 'sd_src_no_ratelimit', 'sd_src'], videoId);

      let thumbMatch = html.match(/og:image" content="([^"]+)"/);
      let titleMatch = html.match(/og:title" content="([^"]+)"/);

      // Fallback: giao diện mobile thường có og:video
      if (!hd && !sd) {
        const mob = await fetchFb(IPHONE_UA);
        const og = mob.html.match(/property="og:video(?::secure_url|:url)?"\s+content="([^"]+)"/i);
        if (og) sd = unHtml(og[1]);
        thumbMatch = thumbMatch || mob.html.match(/og:image" content="([^"]+)"/);
        titleMatch = titleMatch || mob.html.match(/og:title" content="([^"]+)"/);
      }

      if (sd || hd) {
        const finalVideo = hd || sd;
        // Bỏ tiền tố "293K views · 2.5K reactions | "
        const rawTitle = titleMatch ? unHtml(titleMatch[1]).replace(/^[^|]*\b(views|reactions|lượt xem)\b[^|]*\|\s*/i, '') : 'Facebook Video';
        const titleText = cleanTitle(rawTitle);
        const labels = [];
        const medias = {};

        if (hd) { labels.push('🎬 MP4 HD'); medias['🎬 MP4 HD'] = hd; }
        if (sd && sd !== hd) { labels.push('🎬 MP4 SD'); medias['🎬 MP4 SD'] = sd; }
        labels.push('🎵 MP3 AUDIO');
        medias['🎵 MP3 AUDIO'] = sd || finalVideo;

        return res.status(200).json(makeResponse({
          platform: 'facebook',
          title: titleText,
          menu_title: 'Choose media:',
          labels, medias,
          thumbnail: thumbMatch ? unHtml(thumbMatch[1]) : '',
          video: finalVideo, audio: sd || finalVideo
        }));
      }

      return res.status(400).json({
        status: 'error',
        message: 'Không tìm thấy video Facebook công khai hoặc video yêu cầu đăng nhập.'
      });
    }

    // ------------------------------------------------------------------
    // 3. LINK FILE TRỰC TIẾP
    // ------------------------------------------------------------------
    if (/\.(mp4|mov|mp3|m4a|jpg|jpeg|png|webp)(\?.*)?$/i.test(inputUrl)) {
      const extMatch = inputUrl.match(/\.(mp4|mov|mp3|m4a|jpg|jpeg|png|webp)/i);
      const ext = extMatch ? extMatch[1].toLowerCase() : 'mp4';
      const isAudio = /mp3|m4a/i.test(ext);
      const isImage = /jpg|jpeg|png|webp/i.test(ext);
      const icon = isAudio ? '🎵' : (isImage ? '🖼️' : '🎬');
      const labelName = `${icon} ${ext.toUpperCase()} ORIGINAL`;

      return res.status(200).json(makeResponse({
        platform: 'direct',
        title: `media_file_${Date.now()}`,
        menu_title: 'Choose media:',
        labels: [labelName],
        medias: { [labelName]: inputUrl },
        video: isAudio ? '' : inputUrl,
        audio: isAudio ? inputUrl : ''
      }));
    }

    // ------------------------------------------------------------------
    // 4. FALLBACK: og:video
    // ------------------------------------------------------------------
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
        const labels = ['🎬 MP4 VIDEO', '🎵 MP3 AUDIO'];
        const medias = { '🎬 MP4 VIDEO': videoUrl, '🎵 MP3 AUDIO': videoUrl };

        return res.status(200).json(makeResponse({
          platform: 'generic',
          title: titleText,
          menu_title: 'Choose media:',
          labels, medias,
          thumbnail: ogImage ? ogImage[1] : '',
          video: videoUrl, audio: videoUrl
        }));
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
