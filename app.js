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
    
    // Video section buttons
    const videoActionsSection = document.getElementById('videoActionsSection');
    const btnDownloadHd = document.getElementById('btnDownloadHd');
    const btnDownloadSd = document.getElementById('btnDownloadSd');
    const btnDownloadAudio = document.getElementById('btnDownloadAudio');
    
    // Slideshow section elements
    const slideshowSection = document.getElementById('slideshowSection');
    const slideshowBadgeText = document.getElementById('slideshowBadgeText');
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const selectedCountBadge = document.getElementById('selectedCountBadge');
    const btnDownloadZip = document.getElementById('btnDownloadZip');
    const btnDownloadDirect = document.getElementById('btnDownloadDirect');
    const zipProgressWrapper = document.getElementById('zipProgressWrapper');
    const zipProgressText = document.getElementById('zipProgressText');
    const zipProgressPercent = document.getElementById('zipProgressPercent');
    const zipProgressBar = document.getElementById('zipProgressBar');
    const mediaItemsContainer = document.getElementById('mediaItemsContainer');
    
    // Lightbox modal elements
    const imageLightbox = document.getElementById('imageLightbox');
    const lightboxImg = document.getElementById('lightboxImg');
    const lightboxCaption = document.getElementById('lightboxCaption');
    const lightboxDownloadBtn = document.getElementById('lightboxDownloadBtn');
    const lightboxClose = document.getElementById('lightboxClose');
    const lightboxOverlay = document.getElementById('lightboxOverlay');
    
    const errorAlert = document.getElementById('errorAlert');

    let currentParsedData = null;

    // Helper: dọn dẹp tên tệp an toàn
    function sanitizeFilename(str, fallback = 'file') {
        if (!str) return fallback;
        const clean = str.replace(/[\r\n\t]+/g, ' ')
                         .replace(/[\\/:*?"<>|#%&{}$!`'@+~]+/g, '')
                         .replace(/\s+/g, '_')
                         .trim();
        return clean.substring(0, 50) || fallback;
    }

    // Helper: Tải xuống file bằng Blob (CORS) hoặc proxy fallback
    async function downloadMediaFile(url, filename) {
        if (!url) return;
        try {
            // Thử fetch trực tiếp qua CORS blob
            const res = await fetch(url, { mode: 'cors' });
            if (res.ok) {
                const blob = await res.blob();
                const blobUrl = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = blobUrl;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
                return;
            }
        } catch (fetchErr) {
            console.log('Direct fetch not possible, falling back to proxy/direct link:', fetchErr);
        }

        // Fallback qua proxy PHP nếu khả dụng
        const isHttp = window.location.protocol.startsWith('http');
        if (isHttp) {
            const proxyUrl = `api.php?action=download&filename=${encodeURIComponent(filename)}&url=${encodeURIComponent(url)}`;
            const a = document.createElement('a');
            a.href = proxyUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } else {
            // Static link
            window.open(url, '_blank');
        }
    }

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
            let data = null;
            // Gọi backend PHP
            try {
                const response = await fetch(`api.php?url=${encodeURIComponent(url)}`);
                if (response.ok) {
                    data = await response.json();
                }
            } catch (backendErr) {
                console.log('Backend not reachable, attempting client-side fallback...');
            }

            // Fallback trực tiếp cho TikTok nếu chạy static / không có backend PHP
            if ((!data || data.status !== 'success') && (url.includes('tiktok.com') || url.includes('douyin.com'))) {
                const directRes = await fetch(`https://www.tikwm.com/api/?hd=1&url=${encodeURIComponent(url)}`);
                const directData = await directRes.json();
                if (directData && directData.code === 0 && directData.data) {
                    const item = directData.data;
                    const images = item.images || [];
                    const isSlideshow = (images.length > 0);
                    const author = item.author?.nickname || item.author?.unique_id || 'TikTok Creator';
                    const rawTitle = item.title || ('TikTok by ' + author);
                    const musicUrl = item.music || item.music_info?.play || '';

                    data = {
                        status: 'success',
                        platform: 'tiktok',
                        type: isSlideshow ? 'slideshow' : 'video',
                        is_slideshow: isSlideshow,
                        title: rawTitle,
                        author: author,
                        thumbnail: item.cover || (images.length > 0 ? images[0] : ''),
                        video_hd: isSlideshow ? '' : (item.hdplay || item.play),
                        video_sd: isSlideshow ? '' : item.play,
                        audio: musicUrl,
                        images: images,
                        image_count: images.length
                    };
                }
            }

            if (data && data.status === 'success') {
                currentParsedData = data;
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
        const displayTitle = data.title && data.title.trim() ? data.title : ('TikTok của @' + (data.author || 'người dùng'));
        const safeBaseName = sanitizeFilename(displayTitle, 'tiktok_media');
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

        const isSlideshow = data.is_slideshow || (data.images && data.images.length > 0);

        if (isSlideshow) {
            // Ẩn khối video, hiện khối Slideshow Album
            videoActionsSection.style.display = 'none';
            slideshowSection.style.display = 'block';
            renderSlideshowSection(data, safeBaseName);
        } else {
            // Hiện khối Video thông thường
            slideshowSection.style.display = 'none';
            videoActionsSection.style.display = 'flex';
            setupVideoActions(data, safeBaseName);
        }

        resultCard.style.display = 'block';
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Xử lý khối Video thông thường
    function setupVideoActions(data, safeBaseName) {
        // Nút HD
        if (data.video_hd || data.video) {
            const videoUrl = data.video_hd || data.video;
            btnDownloadHd.onclick = (e) => {
                e.preventDefault();
                downloadMediaFile(videoUrl, `${safeBaseName}_HD.mp4`);
            };
            btnDownloadHd.style.display = 'inline-flex';
        } else {
            btnDownloadHd.style.display = 'none';
        }

        // Nút SD
        if (data.video_sd && data.video_sd !== data.video_hd) {
            btnDownloadSd.onclick = (e) => {
                e.preventDefault();
                downloadMediaFile(data.video_sd, `${safeBaseName}_SD.mp4`);
            };
            btnDownloadSd.style.display = 'inline-flex';
        } else {
            btnDownloadSd.style.display = 'none';
        }

        // Nút Audio
        if (data.audio) {
            btnDownloadAudio.onclick = (e) => {
                e.preventDefault();
                downloadMediaFile(data.audio, `${safeBaseName}_audio.mp3`);
            };
            btnDownloadAudio.style.display = 'inline-flex';
        } else {
            btnDownloadAudio.style.display = 'none';
        }
    }

    // Xử lý khối Album Slideshow với Checkbox ở phần đầu mỗi tệp
    function renderSlideshowSection(data, safeBaseName) {
        const images = data.images || [];
        const hasAudio = !!data.audio;

        slideshowBadgeText.textContent = `Album Ảnh TikTok (${images.length} Ảnh${hasAudio ? ' + 1 Âm Thanh' : ''})`;
        
        mediaItemsContainer.innerHTML = '';
        zipProgressWrapper.style.display = 'none';

        // 1. Tạo các thẻ Ảnh
        images.forEach((imgUrl, index) => {
            const itemNum = index + 1;
            const itemFilename = `${safeBaseName}_anh_${itemNum}.jpg`;

            const card = document.createElement('div');
            card.className = 'media-file-item selected';
            card.dataset.type = 'image';
            card.dataset.url = imgUrl;
            card.dataset.filename = itemFilename;

            card.innerHTML = `
                <div class="item-checkbox-col">
                    <input type="checkbox" class="file-checkbox-input" id="chk_img_${index}" checked title="Chọn tệp này">
                </div>
                <div class="item-preview-col" title="Nhấn để xem ảnh phóng to">
                    <img src="${imgUrl}" alt="Ảnh ${itemNum}" class="item-thumb-img" loading="lazy">
                    <div class="item-zoom-badge">🔍</div>
                </div>
                <div class="item-details-col">
                    <div class="item-file-title">Ảnh #${itemNum} (JPG HD)</div>
                    <div class="item-file-desc">
                        <span class="quality-tag">JPG HD</span>
                        <span>Độ phân giải gốc &bull; Không watermark</span>
                    </div>
                </div>
                <div class="item-actions-col">
                    <button type="button" class="btn-item-download btn-single-dl" title="Tải ảnh #${itemNum} về máy">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                        <span>Tải ảnh</span>
                    </button>
                </div>
            `;

            // Bấm xem preview phóng to
            const previewEl = card.querySelector('.item-preview-col');
            previewEl.addEventListener('click', () => {
                openLightbox(imgUrl, `Ảnh #${itemNum} - ${data.title || 'TikTok'}`, itemFilename);
            });

            // Nút tải ảnh đơn lẻ
            const dlBtn = card.querySelector('.btn-single-dl');
            dlBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                downloadMediaFile(imgUrl, itemFilename);
            });

            mediaItemsContainer.appendChild(card);
        });

        // 2. Tạo thẻ Âm Thanh MP3
        if (hasAudio) {
            const audioFilename = `${safeBaseName}_audio.mp3`;
            const audioCard = document.createElement('div');
            audioCard.className = 'media-file-item selected audio-file-item';
            audioCard.dataset.type = 'audio';
            audioCard.dataset.url = data.audio;
            audioCard.dataset.filename = audioFilename;

            audioCard.innerHTML = `
                <div class="item-checkbox-col">
                    <input type="checkbox" class="file-checkbox-input" id="chk_audio" checked title="Chọn tệp âm thanh này">
                </div>
                <div class="audio-preview-box" title="Âm thanh nền MP3">
                    🎵
                </div>
                <div class="item-details-col">
                    <div class="item-file-title">Âm thanh nền TikTok (MP3)</div>
                    <div class="item-file-desc">
                        <span class="quality-tag audio">MP3 128KBPS</span>
                        <span>Âm thanh gốc chất lượng cao</span>
                    </div>
                    <div class="audio-player-wrap">
                        <audio controls class="mini-audio-player" src="${data.audio}" preload="none"></audio>
                    </div>
                </div>
                <div class="item-actions-col">
                    <button type="button" class="btn-item-download audio btn-single-dl" title="Tải file âm thanh MP3 về máy">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                        <span>Tải MP3</span>
                    </button>
                </div>
            `;

            const audioDlBtn = audioCard.querySelector('.btn-single-dl');
            audioDlBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                downloadMediaFile(data.audio, audioFilename);
            });

            mediaItemsContainer.appendChild(audioCard);
        }

        // 3. Quản lý trạng thái Checkbox & Đếm số lượng
        updateSelectionState();

        // Lắng nghe sự kiện checkbox từng item
        const allCheckboxes = mediaItemsContainer.querySelectorAll('.file-checkbox-input');
        allCheckboxes.forEach(cb => {
            cb.addEventListener('change', () => {
                const parentCard = cb.closest('.media-file-item');
                if (cb.checked) {
                    parentCard.classList.add('selected');
                } else {
                    parentCard.classList.remove('selected');
                }
                updateSelectionState();
            });
        });

        // Checkbox Chọn tất cả
        selectAllCheckbox.onchange = () => {
            const isChecked = selectAllCheckbox.checked;
            allCheckboxes.forEach(cb => {
                cb.checked = isChecked;
                const parentCard = cb.closest('.media-file-item');
                if (isChecked) {
                    parentCard.classList.add('selected');
                } else {
                    parentCard.classList.remove('selected');
                }
            });
            updateSelectionState();
        };

        // Nút Tải ZIP hàng loạt
        btnDownloadZip.onclick = () => {
            handleBatchZipDownload(safeBaseName);
        };

        // Nút Tải trực tiếp lần lượt
        btnDownloadDirect.onclick = () => {
            handleBatchDirectDownload();
        };
    }

    // Cập nhật trạng thái đếm & nút chọn tất cả
    function updateSelectionState() {
        const allCheckboxes = mediaItemsContainer.querySelectorAll('.file-checkbox-input');
        const checkedBoxes = mediaItemsContainer.querySelectorAll('.file-checkbox-input:checked');
        const total = allCheckboxes.length;
        const selected = checkedBoxes.length;

        selectedCountBadge.textContent = `${selected}/${total}`;
        selectAllCheckbox.checked = (selected === total && total > 0);
        selectAllCheckbox.indeterminate = (selected > 0 && selected < total);

        btnDownloadZip.disabled = (selected === 0);
        btnDownloadDirect.disabled = (selected === 0);
    }

    // Lấy danh sách các tệp đang được tick checkbox
    function getSelectedFiles() {
        const checkedBoxes = mediaItemsContainer.querySelectorAll('.file-checkbox-input:checked');
        const list = [];
        checkedBoxes.forEach(cb => {
            const card = cb.closest('.media-file-item');
            if (card) {
                list.push({
                    type: card.dataset.type,
                    url: card.dataset.url,
                    filename: card.dataset.filename
                });
            }
        });
        return list;
    }

    // Tải hàng loạt đóng gói ZIP
    async function handleBatchZipDownload(baseName) {
        const selectedFiles = getSelectedFiles();
        if (selectedFiles.length === 0) {
            alert('Vui lòng chọn ít nhất 1 tệp để tải!');
            return;
        }

        if (typeof JSZip === 'undefined') {
            alert('Thư viện nén ZIP chưa tải xong, đang chuyển sang tải lần lượt...');
            handleBatchDirectDownload();
            return;
        }

        const zip = new JSZip();
        zipProgressWrapper.style.display = 'block';
        btnDownloadZip.disabled = true;
        btnDownloadDirect.disabled = true;

        const total = selectedFiles.length;
        let completed = 0;

        try {
            for (let i = 0; i < total; i++) {
                const item = selectedFiles[i];
                zipProgressText.textContent = `Đang tải tệp ${i + 1}/${total}: ${item.filename}...`;
                const progressPct = Math.round((i / total) * 70);
                zipProgressBar.style.width = `${progressPct}%`;
                zipProgressPercent.textContent = `${progressPct}%`;

                try {
                    const response = await fetch(item.url, { mode: 'cors' });
                    if (response.ok) {
                        const blob = await response.blob();
                        zip.file(item.filename, blob);
                    } else {
                        throw new Error('Direct fetch failed');
                    }
                } catch (fetchErr) {
                    // Fallback qua proxy PHP lấy stream
                    const isHttp = window.location.protocol.startsWith('http');
                    if (isHttp) {
                        const proxyUrl = `api.php?action=download&filename=${encodeURIComponent(item.filename)}&url=${encodeURIComponent(item.url)}`;
                        const pRes = await fetch(proxyUrl);
                        if (pRes.ok) {
                            const pBlob = await pRes.blob();
                            zip.file(item.filename, pBlob);
                        }
                    }
                }
                completed++;
            }

            zipProgressText.textContent = 'Đang đóng gói file ZIP hoàn thiện...';
            zipProgressBar.style.width = '85%';
            zipProgressPercent.textContent = '85%';

            const zipContent = await zip.generateAsync({ type: 'blob' }, (metadata) => {
                const compPct = 85 + Math.round(metadata.percent * 0.15);
                zipProgressBar.style.width = `${compPct}%`;
                zipProgressPercent.textContent = `${compPct}%`;
            });

            zipProgressText.textContent = 'Nén thành công! Bắt đầu tải về...';
            zipProgressBar.style.width = '100%';
            zipProgressPercent.textContent = '100%';

            const downloadUrl = URL.createObjectURL(zipContent);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `${baseName}_Album.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            setTimeout(() => {
                URL.revokeObjectURL(downloadUrl);
                zipProgressWrapper.style.display = 'none';
            }, 3000);

        } catch (zipErr) {
            console.error('Lỗi đóng gói zip:', zipErr);
            alert('Đã xảy ra lỗi khi tạo file ZIP. Hệ thống sẽ chuyển sang tải lần lượt từng tệp.');
            handleBatchDirectDownload();
        } finally {
            btnDownloadZip.disabled = false;
            btnDownloadDirect.disabled = false;
        }
    }

    // Tải hàng loạt lần lượt từng file (có delay để tránh bị chặn pop-up)
    async function handleBatchDirectDownload() {
        const selectedFiles = getSelectedFiles();
        if (selectedFiles.length === 0) {
            alert('Vui lòng chọn ít nhất 1 tệp để tải!');
            return;
        }

        btnDownloadZip.disabled = true;
        btnDownloadDirect.disabled = true;

        for (let i = 0; i < selectedFiles.length; i++) {
            const item = selectedFiles[i];
            await downloadMediaFile(item.url, item.filename);
            // Delay 400ms giữa các lần tải
            if (i < selectedFiles.length - 1) {
                await new Promise(r => setTimeout(r, 400));
            }
        }

        btnDownloadZip.disabled = false;
        btnDownloadDirect.disabled = false;
    }

    // Lightbox modal preview
    function openLightbox(imgUrl, title, filename) {
        lightboxImg.src = imgUrl;
        lightboxCaption.textContent = title;
        lightboxDownloadBtn.onclick = (e) => {
            e.preventDefault();
            downloadMediaFile(imgUrl, filename);
        };
        imageLightbox.style.display = 'flex';
        imageLightbox.setAttribute('aria-hidden', 'false');
    }

    function closeLightbox() {
        imageLightbox.style.display = 'none';
        imageLightbox.setAttribute('aria-hidden', 'true');
        lightboxImg.src = '';
    }

    lightboxClose.addEventListener('click', closeLightbox);
    lightboxOverlay.addEventListener('click', closeLightbox);
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && imageLightbox.style.display !== 'none') {
            closeLightbox();
        }
    });

    function hideResult() {
        resultCard.style.display = 'none';
        currentParsedData = null;
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
