document.addEventListener('DOMContentLoaded', () => {
    const inputUrl = document.getElementById('videoUrl');
    const btnPaste = document.getElementById('btnPaste');
    const btnSubmit = document.getElementById('btnSubmit');
    const btnText = btnSubmit.querySelector('.btn-text');
    const btnLoader = btnSubmit.querySelector('.btn-loader');
    
    const resultCard = document.getElementById('resultCard');
    const resThumbnail = document.getElementById('resThumbnail');
    const resPlatformBadge = document.getElementById('resPlatformBadge');
    const resTitle = document.getElementById('resTitle');
    const resAuthor = document.getElementById('resAuthor');
    const btnDownloadHd = document.getElementById('btnDownloadHd');
    const btnDownloadSd = document.getElementById('btnDownloadSd');
    const btnDownloadAudio = document.getElementById('btnDownloadAudio');
    const errorAlert = document.getElementById('errorAlert');

    // Nút Dán (Paste)
    btnPaste.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                inputUrl.value = text.trim();
                triggerParse();
            }
        } catch (err) {
            inputUrl.focus();
        }
    });

    // Enter để submit
    inputUrl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            triggerParse();
        }
    });

    btnSubmit.addEventListener('click', () => {
        triggerParse();
    });

    async function triggerParse() {
        const url = inputUrl.value.trim();
        if (!url) {
            showError('Vui lòng dán liên kết video TikTok hoặc Facebook!');
            return;
        }

        hideError();
        hideResult();
        setLoading(true);

        try {
            // Thử gọi backend (Vercel serverless /api/parse hoặc PHP api.php)
            let data = null;
            try {
                // Thử endpoint Vercel
                let response = await fetch(`api/parse?url=${encodeURIComponent(url)}`);
                if (!response.ok) {
                    // Thử endpoint PHP
                    response = await fetch(`api.php?url=${encodeURIComponent(url)}`);
                }
                if (response.ok) {
                    data = await response.json();
                }
            } catch (backendErr) {
                console.log('Backend not reachable, attempting client-side fallback...');
            }

            // Fallback trực tiếp cho TikTok nếu chạy trên GitHub Pages (hoàn toàn không cần backend)
            if ((!data || data.status !== 'success') && (url.includes('tiktok.com') || url.includes('douyin.com'))) {
                const directRes = await fetch(`https://www.tikwm.com/api/?url=${encodeURIComponent(url)}`);
                const directData = await directRes.json();
                if (directData && directData.code === 0 && directData.data) {
                    const item = directData.data;
                    data = {
                        status: 'success',
                        platform: 'tiktok',
                        title: item.title || ('Video TikTok của @' + (item.author?.nickname || item.author?.unique_id || 'user')),
                        author: item.author?.nickname || item.author?.unique_id || 'TikTok Creator',
                        thumbnail: item.cover || '',
                        video_hd: item.hdplay || item.play,
                        video_sd: item.play,
                        audio: item.music
                    };
                }
            }

            if (data && data.status === 'success') {
                showResult(data);
            } else {
                showError((data && data.message) || 'Không thể phân giải video. Vui lòng kiểm tra lại liên kết hoặc thử lại sau.');
            }
        } catch (err) {
            showError('Đã xảy ra lỗi kết nối. Vui lòng thử lại sau.');
        } finally {
            setLoading(false);
        }
    }

    function showResult(data) {
        const displayTitle = data.title && data.title.trim() ? data.title : ('Video TikTok của @' + (data.author || 'người dùng'));
        resTitle.textContent = displayTitle;
        resPlatformBadge.textContent = (data.platform || 'VIDEO').toUpperCase();
        resPlatformBadge.style.backgroundColor = data.platform === 'tiktok' ? '#f43f5e' : '#2563eb';

        if (data.author) {
            resAuthor.style.display = 'block';
            resAuthor.querySelector('span').textContent = data.author;
        } else {
            resAuthor.style.display = 'none';
        }

        if (data.thumbnail) {
            resThumbnail.src = data.thumbnail;
            resThumbnail.style.display = 'block';
        } else {
            resThumbnail.style.display = 'none';
        }

        // Kiểm tra xem có máy chủ PHP không hay đang chạy static
        const isHttp = window.location.protocol.startsWith('http');

        // Setup nút tải HD
        if (data.video_hd || data.video) {
            const videoUrl = data.video_hd || data.video;
            btnDownloadHd.href = isHttp 
                ? `/api/download?filename=${data.platform}_video_hd.mp4&url=${encodeURIComponent(videoUrl)}` 
                : videoUrl;
            btnDownloadHd.setAttribute('download', `${data.platform}_video_hd.mp4`);
            btnDownloadHd.style.display = 'inline-flex';
        } else {
            btnDownloadHd.style.display = 'none';
        }

        // Setup nút tải SD
        if (data.video_sd && data.video_sd !== data.video_hd) {
            btnDownloadSd.href = isHttp 
                ? `/api/download?filename=${data.platform}_video_sd.mp4&url=${encodeURIComponent(data.video_sd)}` 
                : data.video_sd;
            btnDownloadSd.setAttribute('download', `${data.platform}_video_sd.mp4`);
            btnDownloadSd.style.display = 'inline-flex';
        } else {
            btnDownloadSd.style.display = 'none';
        }

        // Setup nút tải Audio
        if (data.audio) {
            btnDownloadAudio.href = isHttp 
                ? `/api/download?filename=${data.platform}_audio.mp3&url=${encodeURIComponent(data.audio)}` 
                : data.audio;
            btnDownloadAudio.setAttribute('download', `${data.platform}_audio.mp3`);
            btnDownloadAudio.style.display = 'inline-flex';
        } else {
            btnDownloadAudio.style.display = 'none';
        }

        resultCard.style.display = 'block';
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function hideResult() {
        resultCard.style.display = 'none';
    }

    function showError(msg) {
        errorAlert.textContent = msg;
        errorAlert.style.display = 'block';
    }

    function hideError() {
        errorAlert.style.display = 'none';
    }

    function setLoading(isLoading) {
        if (isLoading) {
            btnSubmit.disabled = true;
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline-block';
        } else {
            btnSubmit.disabled = false;
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
        }
    }
});
