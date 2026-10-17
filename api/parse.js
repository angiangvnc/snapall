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
    if (/facebook\.com|fb\.watch|fb\.com/i.test(inputUrl)) {
      const fbRes = await fetch(inputUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept-Language': 'en-US,en;q=0.9'
        }
      });
      const html = await fbRes.text();

      const sdMatch = html.match(/"sd_src_no_ratelimit":"([^"]+)"|"sd_src":"([^"]+)"/);
      const hdMatch = html.match(/"hd_src_no_ratelimit":"([^"]+)"|"hd_src":"([^"]+)"/);
      const thumbMatch = html.match(/og:image" content="([^"]+)"/);
      const titleMatch = html.match(/og:title" content="([^"]+)"/);

      const sd = sdMatch ? (sdMatch[1] || sdMatch[2]).replace(/\\/g, '') : '';
      const hd = hdMatch ? (hdMatch[1] || hdMatch[2]).replace(/\\/g, '') : '';

      if (sd || hd) {
        const finalVideo = hd || sd;
        const titleText = cleanTitle(titleMatch ? titleMatch[1] : 'Facebook Video');
        const labels = [];
        const medias = {};

        if (hd) { labels.push('🎬 MP4 HD'); medias['🎬 MP4 HD'] = hd; }
        if (sd && sd !== hd) { labels.push('🎬 MP4 SD'); medias['🎬 MP4 SD'] = sd; }
        labels.push('🎵 MP3 AUDIO');
        medias['🎵 MP3 AUDIO'] = finalVideo;

        return res.status(200).json(makeResponse({
          platform: 'facebook',
          title: titleText,
          menu_title: 'Choose media:',
          labels, medias,
          thumbnail: thumbMatch ? thumbMatch[1] : '',
          video: finalVideo, audio: finalVideo
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
