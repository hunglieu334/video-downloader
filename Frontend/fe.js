document.addEventListener('DOMContentLoaded', function() {
    // Constants
    const DEBOUNCE_DELAY = 300;
    const MIN_URL_LENGTH = 10;
    const URL_REGEX = /^(https?:\/\/)/;
    
    // Cache DOM elements
    const elements = {
        form: document.getElementById('videoForm'),
        platform: document.getElementById('platform'),
        url: document.getElementById('url'),
        quality: document.getElementById('quality'),
        downloadBtn: document.getElementById('downloadBtn'),
        preview: document.getElementById('preview')
    };

    // Skip if we're not on the index page with the video form
    if (!elements.form) return;

    // Debounce function
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Preview video function
    async function previewVideo() {
        const url = elements.url.value;
        const platform = elements.platform.value;

        // Reset UI
        resetPreview();

        // Validate URL
        if (!isValidUrl(url)) return;

        // Show loading
        showLoading();

        try {
            const data = await fetchPreviewData(platform, url);
            handlePreviewResponse(data);
        } catch (error) {
            showError(error.message);
        }
    }

    // Helper functions
    function resetPreview() {
        elements.preview.innerHTML = '';
        elements.quality.innerHTML = '<option value="">Chọn chất lượng</option>';
        elements.downloadBtn.disabled = true;
    }

    function isValidUrl(url) {
        return url && url.length >= MIN_URL_LENGTH && URL_REGEX.test(url);
    }

    function showLoading() {
        elements.preview.innerHTML = '<p class="loading">Đang tải bản xem trước...</p>';
    }

    function showError(message) {
        elements.preview.innerHTML = `<div class="error">${message}</div>`;
    }

    async function fetchPreviewData(platform, url) {
        const response = await fetch('/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `platform=${encodeURIComponent(platform)}&url=${encodeURIComponent(url)}`
        });
        return response.json();
    }

    function handlePreviewResponse(data) {
        elements.preview.innerHTML = '';
        
        if (data.error) {
            showError(data.error);
            return;
        }

        // Show preview
        elements.preview.innerHTML = generatePreviewHTML(data);

        // Update quality options
        if (data.qualities?.length) {
            updateQualityOptions(data.qualities);
            elements.downloadBtn.disabled = false;
        } else {
            showError('Không tìm thấy chất lượng video!');
        }
    }

    function generatePreviewHTML(data) {
        let html = `<div class="video-info">
            <h2>${data.title || 'Video Preview'}</h2>`;
            
        if (data.thumbnail) {
            html += `<img src="${data.thumbnail}" alt="Thumbnail" class="thumbnail">`;
        }
        
        if (data.embed_url) {
            html += `<div class="embed-container">
                <iframe src="${data.embed_url}" frameborder="0" allowfullscreen></iframe>
            </div>`;
        }
        
        html += '</div>';
        return html;
    }

    function updateQualityOptions(qualities) {
        const qualitySelect = elements.quality;
        qualitySelect.innerHTML = '';
        
        qualities.forEach(q => {
            const option = document.createElement('option');
            option.value = q.value;
            option.textContent = q.label;
            qualitySelect.appendChild(option);
        });
        
        // Select the first option by default
        if (qualities.length > 0) {
            qualitySelect.value = qualities[0].value;
        }

        if (!isFFmpegInstalled && qualities.some(q => q.value !== 'best')) {
            const notice = document.createElement('div');
            notice.className = 'ffmpeg-notice';
            notice.innerHTML = '<strong>Lưu ý:</strong> Để tải video chất lượng cao nhất, hãy <a href="/ffmpeg-help">cài đặt FFmpeg</a>';
            qualitySelect.parentNode.appendChild(notice);
        }
    }

    // Event listeners
    elements.url.addEventListener('input', debounce(previewVideo, DEBOUNCE_DELAY));
    elements.platform.addEventListener('change', () => {
        if (elements.url.value) {
            previewVideo();
        }
    });
    
    elements.form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        if (!elements.url.value || !elements.quality.value) {
            return;
        }
        
        // Create and submit a form for downloading
        const downloadForm = document.createElement('form');
        downloadForm.method = 'POST';
        downloadForm.action = '/download';
        
        // Add form fields
        const platformInput = document.createElement('input');
        platformInput.type = 'hidden';
        platformInput.name = 'platform';
        platformInput.value = elements.platform.value;
        
        const urlInput = document.createElement('input');
        urlInput.type = 'hidden';
        urlInput.name = 'url';
        urlInput.value = elements.url.value;
        
        const qualityInput = document.createElement('input');
        qualityInput.type = 'hidden';
        qualityInput.name = 'quality';
        qualityInput.value = elements.quality.value;
        
        downloadForm.appendChild(platformInput);
        downloadForm.appendChild(urlInput);
        downloadForm.appendChild(qualityInput);
        
        document.body.appendChild(downloadForm);
        downloadForm.submit();
        document.body.removeChild(downloadForm);
    });
});