// Vercel Serverless Function: /api/parse
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  let inputUrl = (req.query.url || '').trim();
  // Trích xuất toàn bộ URL nguyên bản sau 'url=' nếu link có chứa nhiều dấu ? hoặc &
  if (req.url && req.url.includes('url=')) {
    const rawUrlPart = req.url.substring(req.url.indexOf('url=') + 4);
    if (rawUrlPart) {
      try {
        inputUrl = decodeURIComponent(rawUrlPart).trim();
      } catch (e) {
        inputUrl = rawUrlPart.trim();
      }
    }
  }

  if (!inputUrl) {
    return res.status(400).json({ status: 'error', message: 'Vui lòng cung cấp URL.' });
  }

  try {
    // 1. TikTok
    if (/tiktok\.com|douyin\.com/i.test(inputUrl)) {
      const response = await fetch(`https://www.tikwm.com/api/?url=${encodeURIComponent(inputUrl)}`, {
        headers: { 'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)' }
      });
      const data = await response.json();
      if (data && data.code === 0 && data.data) {
        const item = data.data;
        const author = item.author?.nickname || item.author?.unique_id || 'TikTok Creator';
        const videoUrl = item.hdplay || item.play;
        const audioUrl = item.music || '';
        const labels = ['🎬 Tải Video HD (Không logo)'];
        const medias = {
          '🎬 Tải Video HD (Không logo)': videoUrl
        };
        if (audioUrl) {
          labels.push('🎵 Trích xuất Âm thanh (Audio MP3)');
          medias['🎵 Trích xuất Âm thanh (Audio MP3)'] = audioUrl;
        }

        return res.status(200).json({
          status: 'success',
          platform: 'tiktok',
          title,
          author,
          thumbnail: item.cover || '',
          video: videoUrl,
          video_hd: item.hdplay || item.play,
          video_sd: item.play,
          audio: audioUrl,
          menu_title: `${title} (@${author})`,
          labels,
          medias
        });
      }
      return res.status(400).json({ status: 'error', message: 'Không thể phân giải video TikTok.' });
    }

    // 2. Facebook
    if (/facebook\.com|fb\.watch/i.test(inputUrl)) {
      const fbRes = await fetch(inputUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'none'
        }
      });
      const html = await fbRes.text();
      const cleanHtml = html.replace(/&quot;/g, '"').replace(/&amp;/g, '&');

      const hdMatch = cleanHtml.match(/"browser_native_hd_url":"(.*?)"/) || cleanHtml.match(/"playable_url_quality_hd":"(.*?)"/) || cleanHtml.match(/hd_src\s*:\s*"([^"]*)"/);
      const sdMatch = cleanHtml.match(/"browser_native_sd_url":"(.*?)"/) || cleanHtml.match(/"playable_url":"(.*?)"/) || cleanHtml.match(/sd_src\s*:\s*"([^"]*)"/);

      const hd = hdMatch ? JSON.parse(`"${hdMatch[1]}"`) : '';
      const sd = sdMatch ? JSON.parse(`"${sdMatch[1]}"`) : '';
      const finalVideo = hd || sd;

      if (finalVideo) {
        const titleMatch = cleanHtml.match(/<meta\s+property="og:title"\s+content="([^"]*)"/i) || cleanHtml.match(/<title>(.*?)<\/title>/i);
        const thumbMatch = cleanHtml.match(/<meta\s+property="og:image"\s+content="([^"]*)"/i);
        const titleText = titleMatch ? titleMatch[1] : 'Facebook Video';

        const labels = ['🎬 Tải Video Facebook HD'];
        const medias = {
          '🎬 Tải Video Facebook HD': finalVideo
        };
        if (sd && hd && sd !== hd) {
          labels.push('🎬 Tải Video Facebook SD');
          medias['🎬 Tải Video Facebook SD'] = sd;
        }
        labels.push('🎵 Trích xuất Âm thanh từ Video');
        medias['🎵 Trích xuất Âm thanh từ Video'] = finalVideo;

        return res.status(200).json({
          status: 'success',
          platform: 'facebook',
          title: titleText,
          thumbnail: thumbMatch ? thumbMatch[1] : '',
          video: finalVideo,
          video_hd: hd || sd,
          video_sd: sd || hd,
          audio: finalVideo,
          menu_title: titleText,
          labels,
          medias
        });
      }
      return res.status(400).json({ status: 'error', message: 'Không tìm thấy video Facebook công khai.' });
    }

    return res.status(400).json({ status: 'error', message: 'Nền tảng chưa được hỗ trợ.' });
  } catch (err) {
    return res.status(500).json({ status: 'error', message: err.message });
  }
}
