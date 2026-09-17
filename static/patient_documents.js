/**
 * ArogyaCare - Patient Documents Script
 * Handles drag-and-drop uploading, file validation, and preview modal.
 */

document.addEventListener('DOMContentLoaded', () => {
    initDropzone();
    initModalAccessibility();
});

/**
 * Mobile Navigation Drawer Toggle
 */
function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (sidebar && overlay) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
    }
}

/**
 * File Dropzone & Validation
 */
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB Limit
const ALLOWED_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png'];

function initDropzone() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');

    if (!dropzone || !fileInput) return;

    // Drag events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            fileInput.files = files;
            handleFileSelection(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (fileInput.files && fileInput.files.length > 0) {
            handleFileSelection(fileInput.files[0]);
        }
    });
}

function triggerFileInput() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) fileInput.click();
}

function handleFileSelection(file) {
    const feedback = document.getElementById('uploadFeedback');
    const ext = file.name.split('.').pop().toLowerCase();

    // Validate type
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
        showFeedback('Invalid file type. Please upload a PDF, JPG, JPEG, or PNG document.', 'error');
        clearSelectedFile();
        return;
    }

    // Validate size
    if (file.size > MAX_FILE_SIZE_BYTES) {
        showFeedback('File size exceeds the 10 MB limit.', 'error');
        clearSelectedFile();
        return;
    }

    // Clear feedback and display selected state
    if (feedback) feedback.style.display = 'none';

    document.getElementById('selectedFileName').textContent = file.name;
    document.getElementById('selectedFileSize').textContent = formatBytes(file.size);

    document.getElementById('dropzoneIdle').style.display = 'none';
    document.getElementById('dropzoneSelected').style.display = 'block';
}

function clearSelectedFile() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) fileInput.value = '';

    document.getElementById('dropzoneIdle').style.display = 'block';
    document.getElementById('dropzoneSelected').style.display = 'none';
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function showFeedback(message, type) {
    const feedback = document.getElementById('uploadFeedback');
    if (feedback) {
        feedback.textContent = message;
        feedback.className = `upload-feedback ${type}`;
        feedback.style.display = 'block';
    }
}

/**
 * Preview Modal Integration
 */
function openDocumentPreview(buttonElement) {
    const card = buttonElement.closest('.document-card');
    if (!card) return;

    const dataScript = card.querySelector('.document-data');
    if (!dataScript) return;

    try {
        const data = JSON.parse(dataScript.textContent);
        const container = document.getElementById('previewContainer');

        document.getElementById('modalDocTitle').textContent = data.name || 'Document Preview';
        document.getElementById('modalDocType').textContent = (data.type || 'FILE') + ' Document';
        document.getElementById('modalDocDate').textContent = 'Uploaded: ' + (data.date || 'Not specified');

        container.innerHTML = '';

        if (data.url && data.url.trim() !== '') {
            const ext = data.url.split('.').pop().toLowerCase();
            if (['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext) || data.type === 'IMAGE') {
                const img = document.createElement('img');
                img.src = data.url;
                img.alt = data.name;
                img.className = 'preview-img';
                container.appendChild(img);
            } else if (ext === 'pdf' || data.type === 'PDF') {
                const iframe = document.createElement('iframe');
                iframe.src = data.url;
                iframe.className = 'preview-frame';
                container.appendChild(iframe);
            } else {
                renderUnavailablePreview(container);
            }
        } else {
            renderUnavailablePreview(container);
        }

        const modal = document.getElementById('previewModal');
        if (modal) {
            modal.classList.add('open');
            modal.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
        }
    } catch (e) {
        console.error('Error opening document preview:', e);
    }
}

function renderUnavailablePreview(container) {
    container.innerHTML = `
        <div class="preview-unavailable">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                <line x1="9" x2="15" y1="15" y2="15"/>
            </svg>
            <p>Preview is not available for this document.</p>
        </div>
    `;
}

function closePreviewModal() {
    const modal = document.getElementById('previewModal');
    if (modal) {
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }
}

function initModalAccessibility() {
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closePreviewModal();
    });

    const modal = document.getElementById('previewModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closePreviewModal();
        });
    }
}