// Vercel Serverless Function: /api/download
export default async function handler(req, res) {
  const fileUrl = req.query.url;
  const filename = (req.query.filename || 'media.mp4').replace(/[^a-zA-Z0-9_\-\.]/g, '_');

  if (!fileUrl) {
    return res.status(400).send('Missing url parameter');
  }

  try {
    const upstreamRes = await fetch(fileUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Referer': 'https://www.tiktok.com/'
      }
    });

    if (!upstreamRes.ok) {
      // Nếu upstream lỗi, redirect trực tiếp về URL gốc
      return res.redirect(302, fileUrl);
    }

    const contentType = upstreamRes.headers.get('content-type') || (filename.endsWith('.mp3') ? 'audio/mpeg' : 'video/mp4');
    const contentLength = upstreamRes.headers.get('content-length');

    res.setHeader('Content-Type', contentType);
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    if (contentLength) {
      res.setHeader('Content-Length', contentLength);
    }
    res.setHeader('Cache-Control', 'public, max-age=3600');

    const arrayBuffer = await upstreamRes.arrayBuffer();
    return res.status(200).send(Buffer.from(arrayBuffer));
  } catch (err) {
    // Nếu có lỗi proxy, redirect trực tiếp người dùng đến URL gốc
    return res.redirect(302, fileUrl);
  }
}
