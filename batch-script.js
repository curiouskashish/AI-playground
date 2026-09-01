// Batch Processing Script
// API Base URL - adjust if your backend is on a different port/domain
const API_BASE = 'http://localhost:5001/api';
const IDEA_IMAGE_BATCH_API_FAST_INTERVAL_MS = 15000;
const IDEA_IMAGE_BATCH_API_SLOW_INTERVAL_MS = 60000;
const IDEA_IMAGE_BATCH_API_MAX_RETRIES = 40;

// Initialize batch processing when batch tab is active
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if batch processing tab exists
    const batchTab = document.getElementById('batch-processing');
    if (batchTab) {
        initializeBatchProcessing();
    }
});

// Single source of truth for per-card DOM ID conventions.
const BATCH_CARDS = {
    idea:      { fileInput: 'ideaFileInput',           uploadArea: 'ideaUploadArea',            fileInfo: 'ideaFileInfo',            evaluateBtn: 'ideaEvaluateBtn',            status: 'ideaStatus',            label: 'Evaluate Ideas' },
    pitch:     { fileInput: 'pitchFileInput',          uploadArea: 'pitchUploadArea',           fileInfo: 'pitchFileInfo',           evaluateBtn: 'pitchEvaluateBtn',           status: 'pitchStatus',           label: 'Evaluate Videos' },
    sector:    { fileInput: 'sectorFileInput',         uploadArea: 'sectorUploadArea',          fileInfo: 'sectorFileInfo',          evaluateBtn: 'sectorEvaluateBtn',          status: 'sectorStatus',          label: 'Assign Sectors' },
    ideagen:   { fileInput: 'ideaGenBatchFileInput',   uploadArea: 'ideaGenBatchUploadArea',    fileInfo: 'ideaGenBatchFileInfo',    evaluateBtn: 'ideaGenBatchEvaluateBtn',    status: 'ideaGenBatchStatus',    label: 'Generate Ideas' },
    ideaimage: { fileInput: 'ideaImageBatchFileInput', uploadArea: 'ideaImageBatchUploadArea',  fileInfo: 'ideaImageBatchFileInfo',  evaluateBtn: 'ideaImageBatchEvaluateBtn',  status: 'ideaImageBatchStatus',  label: 'Generate Images' },
    ideaimagebatchapi: { fileInput: 'ideaImageBatchApiFileInput', uploadArea: 'ideaImageBatchApiUploadArea', fileInfo: 'ideaImageBatchApiFileInfo', evaluateBtn: 'ideaImageBatchApiSubmitBtn', status: 'ideaImageBatchApiStatus', label: 'Submit Batch Job' },
};

function initializeBatchProcessing() {
    Object.keys(BATCH_CARDS).forEach(type => {
        const cfg = BATCH_CARDS[type];
        const fileInput   = document.getElementById(cfg.fileInput);
        const uploadArea  = document.getElementById(cfg.uploadArea);
        const fileInfo    = document.getElementById(cfg.fileInfo);
        const evaluateBtn = document.getElementById(cfg.evaluateBtn);
        const refreshBtn  = cfg.refreshBtn ? document.getElementById(cfg.refreshBtn) : null;
        if (fileInput && uploadArea && fileInfo && evaluateBtn) {
            setupFileHandlers(fileInput, uploadArea, fileInfo, evaluateBtn, type);
        }
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                const lastJobId = localStorage.getItem('ideaImageBatchApiLastJobId');
                if (lastJobId) {
                    refreshIdeaImageBatchApiStatus(lastJobId, { manual: true });
                } else {
                    showBatchStatus('ideaimagebatchapi', 'No saved batch job found to refresh.', 'error');
                }
            });
        }
        if (evaluateBtn) {
            evaluateBtn.addEventListener('click', () => {
                evaluateBatch(type, fileInput, evaluateBtn, document.getElementById(cfg.status));
            });
        }
    });

    initializeIdeaImageBatchPrompt();
    initializeIdeaGenBatchPrompt();
    initializeIdeaImageBatchApiPrompt();
}

// Populate the Card 2 image-prompt textarea from the shared localStorage key.
// Edits sync via the same key, so the single-idea page picks them up.
function initializeIdeaImageBatchPrompt() {
    const textarea = document.getElementById('ideaImageBatchPrompt');
    if (!textarea) return;

    const saved = (typeof loadPromptTemplate === 'function') ? loadPromptTemplate('ideagen-image') : null;
    textarea.value = saved || '';

    const modelSelect = document.getElementById('ideaImageBatchModel');
    if (modelSelect) {
        const model = (typeof loadImageModel === 'function') ? loadImageModel() : 'gpt-image-2';
        modelSelect.value = model;
    }

    const saveBtn = document.getElementById('saveIdeaImageBatchPrompt');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const v = textarea.value.trim();
            if (!v) {
                showBatchStatus('ideaimage', '❌ Cannot save empty prompt', 'error');
                return;
            }
            if (typeof savePromptTemplate === 'function') {
                savePromptTemplate('ideagen-image', v);
            }
            // Mirror into the single-idea textarea if it's already in the DOM.
            const singleTextarea = document.getElementById('ideaImagePrompt');
            if (singleTextarea) singleTextarea.value = v;
            showBatchStatus('ideaimage', '✅ Prompt saved — shared with the single-idea page', 'success');
        });
    }
}

function initializeIdeaGenBatchPrompt() {
    const textarea = document.getElementById('ideaGenBatchPrompt');
    if (!textarea) return;

    const fallback = (typeof DEFAULT_IDEA_GEN_PROMPT !== 'undefined') ? DEFAULT_IDEA_GEN_PROMPT : '';
    const saved = (typeof loadPromptTemplate === 'function') ? loadPromptTemplate('ideagen') : null;
    textarea.value = saved || fallback;

    const saveBtn = document.getElementById('saveIdeaGenBatchPrompt');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const v = textarea.value.trim();
            if (!v) {
                showBatchStatus('ideagen', '❌ Cannot save empty prompt', 'error');
                return;
            }
            if (typeof savePromptTemplate === 'function') {
                savePromptTemplate('ideagen', v);
            }
            const singleTextarea = document.getElementById('ideaGenSystemPrompt');
            if (singleTextarea) singleTextarea.value = v;
            showBatchStatus('ideagen', '✅ Prompt saved — shared with the single-idea page', 'success');
        });
    }
}

function initializeIdeaImageBatchApiPrompt() {
    const textarea = document.getElementById('ideaImageBatchApiPrompt');
    if (!textarea) return;

    const saved = (typeof loadPromptTemplate === 'function')
        ? loadPromptTemplate('ideagen-image-batch-api') || loadPromptTemplate('ideagen-image')
        : null;
    textarea.value = saved || '';

    const modelSelect = document.getElementById('ideaImageBatchApiModel');
    if (modelSelect) {
        const model = (typeof loadImageModel === 'function') ? loadImageModel() : 'gpt-image-2';
        modelSelect.value = model;
    }

    const saveBtn = document.getElementById('saveIdeaImageBatchApiPrompt');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const v = textarea.value.trim();
            if (!v) {
                showBatchStatus('ideaimagebatchapi', '❌ Cannot save empty prompt', 'error');
                return;
            }
            if (typeof savePromptTemplate === 'function') {
                savePromptTemplate('ideagen-image-batch-api', v);
            }
            showBatchStatus('ideaimagebatchapi', '✅ Prompt saved for the Batch API module', 'success');
        });
    }

    const lastJobId = localStorage.getItem('ideaImageBatchApiLastJobId');
    if (lastJobId) {
        showBatchStatus('ideaimagebatchapi', `ℹ️ Last batch job found: <code>${lastJobId}</code>. Refreshing status...`, 'processing');
        refreshIdeaImageBatchApiStatus(lastJobId);
    }
}

function setupFileHandlers(input, uploadArea, fileInfo, evaluateBtn, type) {
    if (!input || !uploadArea || !fileInfo || !evaluateBtn) return;

    // Click to upload
    uploadArea.addEventListener('click', () => input.click());
    
    // File selected
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            fileInfo.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
            fileInfo.classList.add('has-file');
            evaluateBtn.disabled = false;
            hideStatus(type);
        }
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const file = e.dataTransfer.files[0];
        if (file && file.name.endsWith('.csv')) {
            // Create a new FileList-like object for the input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            input.files = dataTransfer.files;
            
            fileInfo.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
            fileInfo.classList.add('has-file');
            evaluateBtn.disabled = false;
            hideStatus(type);
        } else {
            showBatchStatus(type, 'Please select a valid CSV file', 'error');
        }
    });
}

async function evaluateBatch(type, fileInput, button, statusElement) {
    if (type === 'ideaimagebatchapi') {
        await submitIdeaImageBatchApi(fileInput, button, statusElement);
        return;
    }

    const file = fileInput.files[0];
    if (!file) {
        showBatchStatus(type, 'Please select a file first', 'error');
        return;
    }

    // Get API key, model, and temperature from the header controls
    const apiKey = document.getElementById('apiKey')?.value || '';
    const model = document.getElementById('modelSelect')?.value || 'gpt-5-mini';
    const temperature = document.getElementById('temperature')?.value || '1';
    
    // Get system prompt based on type
    let systemPrompt = '';
    if (type === 'idea') {
        const promptElement = document.getElementById('ideaSystemPrompt');
        systemPrompt = promptElement ? promptElement.value.trim() : '';
        console.log('Idea evaluation prompt:', systemPrompt ? `Found (${systemPrompt.length} chars)` : 'Not found or empty');
    } else if (type === 'pitch') {
        const promptElement = document.getElementById('pitchSystemPrompt');
        systemPrompt = promptElement ? promptElement.value.trim() : '';
        console.log('Pitch evaluation prompt:', systemPrompt ? `Found (${systemPrompt.length} chars)` : 'Not found or empty');
    } else if (type === 'ideagen') {
        const promptElement = document.getElementById('ideaGenBatchPrompt') || document.getElementById('ideaGenSystemPrompt');
        systemPrompt = promptElement ? promptElement.value.trim() : '';
        if (!systemPrompt) {
            showBatchStatus(type, 'Idea generation prompt is empty. Edit it in the batch prompt box or single-idea tab.', 'error');
            return;
        }
    }
    // sector and ideaimage do not use the text system_prompt field.

    if (!apiKey) {
        showBatchStatus(type, 'Please enter an API key in the header controls', 'error');
        return;
    }

    // For Card 2: validate the image prompt template and confirm large runs before sending.
    let imagePrompt = '';
    if (type === 'ideaimage') {
        const imageTextarea = document.getElementById('ideaImageBatchPrompt');
        imagePrompt = imageTextarea ? imageTextarea.value.trim() : '';
        if (!imagePrompt) {
            showBatchStatus(type, 'Image prompt template is empty. Edit it in this card.', 'error');
            return;
        }
        const approxRows = await countCsvRowsApprox(file);
        const CONFIRM_THRESHOLD = 50;
        const HARD_CAP = 200;
        if (approxRows > HARD_CAP) {
            showBatchStatus(type, `❌ CSV has ~${approxRows} rows — above the hard cap of ${HARD_CAP}. Split the file and run multiple batches.`, 'error');
            return;
        }
        if (approxRows > CONFIRM_THRESHOLD) {
            const ok = window.confirm(
                `About to generate images for up to ~${approxRows} rows.\n\n` +
                `The selected image model will be used for each row. ` +
                `Estimated cost ~$${(approxRows * 0.04).toFixed(2)} and wall-clock time ~${Math.ceil(approxRows * 15 / 60)} min at default concurrency.\n\n` +
                `Continue?`
            );
            if (!ok) {
                showBatchStatus(type, 'Cancelled.', 'error');
                return;
            }
        }
    }

    // Show processing state
    button.disabled = true;
    button.innerHTML = '<span class="loading-spinner-batch"></span>Processing...';
    showBatchStatus(type, 'Processing your file, please wait...', 'processing');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('api_key', apiKey);
    formData.append('model', model);
    formData.append('temperature', temperature);
    // Always send system_prompt (even if empty, so backend knows to use default)
    formData.append('system_prompt', systemPrompt || '');
    if (type === 'sector') {
        const maxConcurrent = document.getElementById('sectorMaxConcurrent')?.value || '15';
        const chunkSize = document.getElementById('sectorChunkSize')?.value || '3000';
        formData.append('max_concurrent', maxConcurrent);
        formData.append('chunk_size', chunkSize);
    } else if (type === 'ideagen') {
        const conc = document.getElementById('ideaGenBatchConcurrency')?.value || '10';
        formData.append('text_concurrency', conc);
    } else if (type === 'ideaimage') {
        const conc = document.getElementById('ideaImageBatchConcurrency')?.value || '3';
        const skipExisting = document.getElementById('ideaImageBatchSkipExisting')?.checked;
        const imageModel = document.getElementById('ideaImageBatchModel')?.value || document.getElementById('ideaImageModel')?.value || (typeof loadImageModel === 'function' ? loadImageModel() : 'gpt-image-2');
        formData.append('image_concurrency', conc);
        formData.append('image_prompt', imagePrompt);
        formData.append('image_model', imageModel);
        formData.append('skip_existing', skipExisting ? 'true' : 'false');
    }

    console.log('Sending batch request with:', {
        type: type,
        model: model,
        temperature: temperature,
        promptLength: systemPrompt.length,
        promptPreview: systemPrompt.substring(0, 100) + (systemPrompt.length > 100 ? '...' : '')
    });

    let endpoint;
    if (type === 'idea') endpoint = `${API_BASE}/batch/evaluate/idea-submission`;
    else if (type === 'pitch') endpoint = `${API_BASE}/batch/evaluate/pitch-video`;
    else if (type === 'sector') endpoint = `${API_BASE}/batch/evaluate/sector-only`;
    else if (type === 'ideagen') endpoint = `${API_BASE}/batch/idea-generation`;
    else if (type === 'ideaimage') endpoint = `${API_BASE}/batch/idea-images`;
    else endpoint = `${API_BASE}/batch/evaluate/idea-submission`;

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        // Check if response is JSON (error or success with download_url)
        const contentType = response.headers.get('content-type') || '';
        
        if (contentType.includes('application/json')) {
            const data = await response.json();
            
            // If download failed but file was saved
            if (data.download_url) {
                const downloadUrl = `http://localhost:5001${data.download_url}`;
                showBatchStatus(type, 
                    `✅ Processing complete! File saved. <a href="${downloadUrl}" download style="color: #10b981; text-decoration: underline;">Click here to download: ${data.file_path}</a>`, 
                    'success'
                );
                button.disabled = false;
                button.textContent = getBatchButtonLabel(type);
                return;
            }
            
            // It's an error response
            if (!response.ok) {
                throw new Error(data.error || `Server error: ${response.status}`);
            }
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error occurred' }));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }

        // Get the filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = type === 'idea'
            ? `idea_submission_evaluations_${new Date().getTime()}.csv`
            : type === 'pitch'
                ? `pitch_video_evaluations_${new Date().getTime()}.csv`
                : `sector_assignment_${new Date().getTime()}.csv`;
        
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        }

        // Download the file (handle large files)
        try {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            // Show success message
            showBatchStatus(type, `✅ Evaluation complete! File downloaded: ${filename}`, 'success');
        } catch (downloadError) {
            // If download fails, check if file was saved on server
            console.error('Download error:', downloadError);
            showBatchStatus(type, 
                `⚠️ Processing complete, but download failed. Check the Flask terminal for the saved file path in the 'results' folder.`, 
                'error'
            );
        }
        
        // Reset button
        button.disabled = false;
        button.textContent = getBatchButtonLabel(type);

    } catch (error) {
        console.error('Evaluation error:', error);
        // Check if processing completed but download failed
        if (error.message.includes('Failed to fetch') || error.message.includes('timeout')) {
            showBatchStatus(type, 
                `⚠️ Processing may have completed, but download timed out. Check the Flask terminal - the file should be saved in the 'results' folder.`, 
                'error'
            );
        } else {
            showBatchStatus(type, `❌ Error: ${error.message}`, 'error');
        }
        button.disabled = false;
        button.textContent = getBatchButtonLabel(type);
    }
}

async function submitIdeaImageBatchApi(fileInput, button, statusElement) {
    const file = fileInput.files[0];
    if (!file) {
        showBatchStatus('ideaimagebatchapi', 'Please select a file first', 'error');
        return;
    }

    const apiKey = document.getElementById('apiKey')?.value || '';
    if (!apiKey) {
        showBatchStatus('ideaimagebatchapi', 'Please enter an API key in the header controls', 'error');
        return;
    }

    const imageTextarea = document.getElementById('ideaImageBatchApiPrompt');
    const imagePrompt = imageTextarea ? imageTextarea.value.trim() : '';
    const imageModel = document.getElementById('ideaImageBatchApiModel')?.value || document.getElementById('ideaImageModel')?.value || (typeof loadImageModel === 'function' ? loadImageModel() : 'gpt-image-2');
    if (!imagePrompt) {
        showBatchStatus('ideaimagebatchapi', 'Image prompt template is empty. Edit it in this card.', 'error');
        return;
    }

    button.disabled = true;
    button.innerHTML = '<span class="loading-spinner-batch"></span>Submitting...';
    showBatchStatus('ideaimagebatchapi', 'Submitting your batch job to OpenAI, please wait...', 'processing');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('api_key', apiKey);
    formData.append('image_prompt', imagePrompt);
    formData.append('image_model', imageModel);

    try {
        const response = await fetch(`${API_BASE}/batch/idea-images-batch/submit`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || `Server error: ${response.status}`);
        }

        const job = data.job || {};
        if (job.job_id) {
            localStorage.setItem('ideaImageBatchApiLastJobId', job.job_id);
        }

        showBatchStatus(
            'ideaimagebatchapi',
            `✅ Batch job submitted. Job ID: <code>${job.job_id || 'unknown'}</code>. Refreshing status...`,
            'success'
        );
        button.disabled = false;
        button.textContent = getBatchButtonLabel('ideaimagebatchapi');

        if (job.job_id) {
            refreshIdeaImageBatchApiStatus(job.job_id);
        }
    } catch (error) {
        console.error('Batch API submit error:', error);
        showBatchStatus('ideaimagebatchapi', `❌ Error: ${error.message}`, 'error');
        button.disabled = false;
        button.textContent = getBatchButtonLabel('ideaimagebatchapi');
    }
}

const ideaImageBatchApiPollState = new Map();

async function refreshIdeaImageBatchApiStatus(jobId, options = {}) {
    if (!jobId) return;
    const autoKey = `ideaImageBatchApiAutoDownloaded_${jobId}`;
    const state = ideaImageBatchApiPollState.get(jobId) || {
        fastAttempts: 0,
        timer: null,
        completed: false,
    };
    if (state.completed) return;

    try {
        const apiKey = document.getElementById('apiKey')?.value || '';
        if (!apiKey) {
            throw new Error('Please enter an API key in the header controls');
        }
        const response = await fetch(`${API_BASE}/batch/idea-images-batch/status/${encodeURIComponent(jobId)}?api_key=${encodeURIComponent(apiKey)}`);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || `Server error: ${response.status}`);
        }

        const job = data.job || {};
        localStorage.setItem('ideaImageBatchApiLastJobId', jobId);
        renderIdeaImageBatchApiJob(job);

        const status = (job.batch && job.batch.status) ? String(job.batch.status).toLowerCase() : '';
        if (status === 'completed' || job.download_ready) {
            state.completed = true;
            if (state.timer) clearTimeout(state.timer);
            ideaImageBatchApiPollState.set(jobId, state);
            const alreadyAutoDownloaded = localStorage.getItem(autoKey) === '1';
            if (!alreadyAutoDownloaded) {
                await autoDownloadIdeaImageBatchApi(job);
                localStorage.setItem(autoKey, '1');
            } else {
                renderIdeaImageBatchApiJob(job);
            }
            ideaImageBatchApiPollState.set(jobId, state);
            return;
        }
        if (status === 'failed' || status === 'cancelled' || status === 'expired') {
            state.completed = true;
            if (state.timer) clearTimeout(state.timer);
            ideaImageBatchApiPollState.set(jobId, state);
            return;
        }

        if (!options.manual) {
            state.fastAttempts += 1;
            if (state.timer) clearTimeout(state.timer);
            const nextDelay = state.fastAttempts < IDEA_IMAGE_BATCH_API_MAX_RETRIES
                ? IDEA_IMAGE_BATCH_API_FAST_INTERVAL_MS
                : IDEA_IMAGE_BATCH_API_SLOW_INTERVAL_MS;
            state.timer = setTimeout(() => refreshIdeaImageBatchApiStatus(jobId), nextDelay);
            ideaImageBatchApiPollState.set(jobId, state);
        }
    } catch (error) {
        showBatchStatus('ideaimagebatchapi', `⚠️ Could not refresh status: ${error.message}`, 'error');
    }
}

function renderIdeaImageBatchApiJob(job) {
    const status = (job.batch && job.batch.status) ? String(job.batch.status).toLowerCase() : 'unknown';
    const counts = job.batch && job.batch.request_counts ? JSON.stringify(job.batch.request_counts) : '{}';
    const jobId = job.job_id || 'unknown';
    const downloadUrl = job.download_url ? `http://localhost:5001${job.download_url}` : '';

    let message = `Batch job <code>${jobId}</code> is <strong>${status}</strong>. Request counts: <code>${counts}</code>.`;
    if (job.download_ready && downloadUrl) {
        message += ` <a href="${downloadUrl}" download style="color: #10b981; text-decoration: underline;">Download finished CSV</a>`;
    } else if (status === 'completed') {
        message += ' Finalizing output CSV...';
    } else if (status === 'failed' || status === 'cancelled' || status === 'expired') {
        if (job.error) {
            message += ` <span style="color: #fca5a5;">${job.error}</span>`;
        }
    } else {
        message += ' The job is still running. You can close this page and come back later.';
    }

    showBatchStatus(
        'ideaimagebatchapi',
        message,
        status === 'failed' || status === 'cancelled' || status === 'expired' ? 'error' : (status === 'completed' || job.download_ready ? 'success' : 'processing')
    );
}

async function autoDownloadIdeaImageBatchApi(job) {
    const downloadUrl = job.download_url ? `http://localhost:5001${job.download_url}` : '';
    if (!downloadUrl) {
        showBatchStatus('ideaimagebatchapi', '✅ Batch completed, but no download URL was returned.', 'success');
        return;
    }

    try {
        showBatchStatus('ideaimagebatchapi', `✅ Batch completed. Downloading results for <code>${job.job_id || 'unknown'}</code>...`, 'success');
        const response = await fetch(downloadUrl);
        if (!response.ok) {
            throw new Error(`Download request failed: ${response.status} ${response.statusText}`);
        }

        const blob = await response.blob();
        const filename = extractDownloadFilename(response.headers.get('content-disposition')) || `idea_images_batch_api_${job.job_id || Date.now()}.csv`;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.setTimeout(() => {
            window.URL.revokeObjectURL(url);
            a.remove();
        }, 1000);

        showBatchStatus(
            'ideaimagebatchapi',
            `✅ Download complete: ${filename}. <a href="${downloadUrl}" download style="color: #10b981; text-decoration: underline;">Download again</a>`,
            'success'
        );
    } catch (error) {
        showBatchStatus('ideaimagebatchapi', `❌ Download failed after completion: ${error.message}`, 'error');
    }
}

function extractDownloadFilename(contentDisposition) {
    if (!contentDisposition) return null;
    const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match && match[1]) {
        return match[1].replace(/['"]/g, '');
    }
    return null;
}

function getBatchButtonLabel(type) {
    return (BATCH_CARDS[type] && BATCH_CARDS[type].label) || 'Evaluate';
}

function showBatchStatus(type, message, statusType) {
    const statusId = BATCH_CARDS[type] && BATCH_CARDS[type].status;
    if (!statusId) return;
    const statusElement = document.getElementById(statusId);
    if (statusElement) {
        // Use innerHTML to properly render any HTML content (like download links)
        statusElement.innerHTML = message;
        statusElement.className = `status-message visible ${statusType}`;
    }
}

function hideStatus(type) {
    const statusId = BATCH_CARDS[type] && BATCH_CARDS[type].status;
    if (!statusId) return;
    const statusElement = document.getElementById(statusId);
    if (statusElement) {
        statusElement.classList.remove('visible');
    }
}

// Approximate row count for a CSV file. Counts non-empty lines minus the
// header. Wrong by a little for CSVs with quoted embedded newlines, which
// is fine for a "are you sure?" prompt and a coarse hard-cap check.
async function countCsvRowsApprox(file) {
    try {
        const text = await file.text();
        const lines = text.split(/\r?\n/).filter(l => l.length > 0);
        return Math.max(0, lines.length - 1);
    } catch (err) {
        console.warn('countCsvRowsApprox failed:', err);
        return 0;
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
