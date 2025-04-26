// Main JavaScript for Video Downloader application
document.addEventListener('DOMContentLoaded', function() {
    const videoUrlInput = document.getElementById('video-url');
    const platformSelect = document.getElementById('platform-select');
    const previewBtn = document.getElementById('preview-btn');
    const errorMessage = document.getElementById('error-message');
    const videoPreview = document.getElementById('video-preview');
    
    // Kiểm tra xem các phần tử có tồn tại không
    if (!videoUrlInput || !previewBtn) {
        console.error('Không tìm thấy các phần tử cần thiết trong trang');
        return;
    }
    
    // Xử lý nút preview
    previewBtn.addEventListener('click', function() {
        const videoUrl = videoUrlInput.value.trim();
        const platform = platformSelect ? platformSelect.value : 'auto';
        
        if (!videoUrl) {
            showError('Vui lòng nhập URL video');
            return;
        }
        
        // Hiển thị trạng thái đang tải
        previewBtn.disabled = true;
        previewBtn.textContent = 'Đang tải...';
        
        // Gửi request đến API
        fetch('/api/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: videoUrl,
                platform: platform
            })
        })
        .then(response => response.json())
        .then(data => {
            previewBtn.disabled = false;
            previewBtn.textContent = 'Xem trước';
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            // Hiển thị video preview
            displayVideoPreview(data.data);
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Đã xảy ra lỗi khi xử lý yêu cầu');
            previewBtn.disabled = false;
            previewBtn.textContent = 'Xem trước';
        });
    });
    
    // Hàm hiển thị preview video
    function displayVideoPreview(data) {
        if (!videoPreview) {
            console.error('Không tìm thấy phần tử video-preview');
            return;
        }
        
        // Tạo nội dung HTML cho preview với các tùy chọn chất lượng chi tiết
        let previewHTML = `
            <div class="preview-container">
                <div class="video-header">
                    <h2>${data.title || 'Video'}</h2>
                    ${data.is_shorts ? 
                        '<span class="shorts-label"><i class="fas fa-mobile-alt"></i> YouTube Shorts</span>' : ''}
                </div>
                <div class="embed-container">
                    ${data.embed_url ? `<iframe src="${data.embed_url}" frameborder="0" allowfullscreen></iframe>` : 
                      data.thumbnail ? `<img src="${data.thumbnail}" alt="${data.title}">` : ''}
                </div>
                <div class="video-info">
                    ${data.uploader ? `<p>Người đăng: ${data.uploader}</p>` : ''}
                    ${data.duration ? `<p>Thời lượng: ${formatDuration(data.duration)}</p>` : ''}
                    ${data.view_count ? `<p>Lượt xem: ${formatNumber(data.view_count)}</p>` : ''}
                    
                    <div class="download-options">
                        <h3>Tùy chọn tải xuống:</h3>
                        
                        <!-- Nhóm tùy chọn chất lượng cao -->
                        <div class="quality-group">
                            <h4>Chất lượng cao</h4>
                            <div class="quality-buttons">
                                ${data.available_resolutions && data.available_resolutions.length > 0 ? 
                                    data.available_resolutions.filter(res => res >= 720).map(res => {
                                        const formatDetail = data.format_detail && data.format_detail[res];
                                        const formatId = formatDetail ? formatDetail.format_id : '';
                                        const ext = formatDetail ? formatDetail.ext : 'mp4';
                                        const fps = formatDetail && formatDetail.fps ? `${formatDetail.fps}fps` : '';
                                        return `
                                            <button class="quality-btn" 
                                                    data-quality="${res}" 
                                                    data-format-id="${formatId}">
                                                ${res}p${fps ? ' ' + fps : ''} (${ext})
                                            </button>`;
                                    }).join('') : 
                                    `<button class="quality-btn" data-quality="best">Chất lượng cao nhất</button>`
                                }
                            </div>
                        </div>
                        
                        <!-- Nhóm tùy chọn chất lượng tiêu chuẩn -->
                        <div class="quality-group">
                            <h4>Chất lượng tiêu chuẩn</h4>
                            <div class="quality-buttons">
                                ${data.available_resolutions && data.available_resolutions.length > 0 ? 
                                    data.available_resolutions.filter(res => res < 720 && res >= 360).map(res => {
                                        const formatDetail = data.format_detail && data.format_detail[res];
                                        const formatId = formatDetail ? formatDetail.format_id : '';
                                        const ext = formatDetail ? formatDetail.ext : 'mp4';
                                        return `
                                            <button class="quality-btn" 
                                                    data-quality="${res}"
                                                    data-format-id="${formatId}">
                                                ${res}p (${ext})
                                            </button>`;
                                    }).join('') : 
                                    `<button class="quality-btn" data-quality="480">480p</button>`
                                }
                            </div>
                        </div>
                        
                        <!-- Tùy chọn đặc biệt -->
                        <div class="quality-group">
                            <h4>Tùy chọn khác</h4>
                            <div class="quality-buttons">
                                <button class="quality-btn special" data-quality="original">Định dạng gốc</button>
                                <button class="quality-btn special audio" data-quality="audio">MP3 (Chỉ âm thanh)</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Cập nhật HTML và hiển thị preview
        videoPreview.innerHTML = previewHTML;
        videoPreview.style.display = 'block';
        
        // Scroll đến khu vực preview
        videoPreview.scrollIntoView({ behavior: 'smooth' });
        
        // Thêm event listener cho các nút chất lượng
        document.querySelectorAll('.quality-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const quality = this.getAttribute('data-quality');
                const formatId = this.getAttribute('data-format-id');
                
                // Hiển thị trạng thái đang tải
                this.disabled = true;
                this.innerText = "Đang tải...";
                
                // Gọi hàm download với format_id nếu có
                downloadVideo(
                    videoUrlInput.value.trim(),
                    platformSelect ? platformSelect.value : 'auto',
                    quality,
                    formatId
                );
            });
        });
    }
    
    // Format thời lượng video từ giây
    function formatDuration(seconds) {
        if (!seconds) return '';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${String(minutes).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`;
        } else {
            return `${minutes}:${String(remainingSeconds).padStart(2, '0')}`;
        }
    }
    
    // Hàm tải xuống với thêm tham số format_id
    function downloadVideo(url, platform, quality, formatId = null) {
        // Tạo form để submit
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/api/download';
        
        // Thêm các input fields
        const urlInput = document.createElement('input');
        urlInput.type = 'hidden';
        urlInput.name = 'url';
        urlInput.value = url;
        form.appendChild(urlInput);
        
        const platformInput = document.createElement('input');
        platformInput.type = 'hidden';
        platformInput.name = 'platform';
        platformInput.value = platform;
        form.appendChild(platformInput);
        
        const qualityInput = document.createElement('input');
        qualityInput.type = 'hidden';
        qualityInput.name = 'quality';
        qualityInput.value = quality;
        form.appendChild(qualityInput);
        
        // Thêm format_id nếu có
        if (formatId) {
            const formatIdInput = document.createElement('input');
            formatIdInput.type = 'hidden';
            formatIdInput.name = 'format_id';
            formatIdInput.value = formatId;
            form.appendChild(formatIdInput);
        }
        
        // Thêm form vào document và submit
        document.body.appendChild(form);
        form.submit();
    }
    
    // Hàm format số lượt xem
    function formatNumber(num) {
        if (!num) return '';
        return new Intl.NumberFormat().format(num);
    }
    
    // Hàm hiển thị thông báo lỗi
    function showError(message) {
        if (!errorMessage) {
            console.error('Không tìm thấy phần tử error-message');
            alert(message);
            return;
        }
        
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }
});