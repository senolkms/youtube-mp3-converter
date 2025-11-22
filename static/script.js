document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('convertForm');
    const urlInput = document.getElementById('urlInput');
    const convertBtn = document.getElementById('convertBtn');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressStatus = document.getElementById('progressStatus');
    const statusMessage = document.getElementById('statusMessage');
    const downloadActions = document.getElementById('downloadActions');
    const downloadLink = document.getElementById('downloadLink');
    const convertAnotherBtn = document.getElementById('convertAnotherBtn');

    // Format selection logic
    const formatOptions = document.querySelectorAll('.option-card');
    const qualitySection = document.getElementById('qualitySection');

    formatOptions.forEach(option => {
        option.addEventListener('click', () => {
            // Remove selected class from all options
            formatOptions.forEach(opt => opt.classList.remove('selected'));
            // Add selected class to clicked option
            option.classList.add('selected');
            // Check the radio button
            const radio = option.querySelector('input[type="radio"]');
            radio.checked = true;

            // Show/hide quality section based on format
            if (radio.value === 'mp4') {
                qualitySection.classList.add('show');
            } else {
                qualitySection.classList.remove('show');
            }
        });
    });

    // Quality selection logic
    const qualityChips = document.querySelectorAll('.quality-chip');
    qualityChips.forEach(chip => {
        chip.addEventListener('click', () => {
            qualityChips.forEach(c => c.classList.remove('selected'));
            chip.classList.add('selected');
            chip.querySelector('input[type="radio"]').checked = true;
        });
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const url = urlInput.value.trim();
        if (!url) return;

        // Reset UI
        statusMessage.style.display = 'none';
        downloadActions.style.display = 'none';
        progressContainer.style.display = 'block';
        convertBtn.disabled = true;
        
        // Get selected options
        const format = document.querySelector('input[name="format"]:checked').value;
        const quality = document.querySelector('input[name="quality"]:checked').value;

        try {
            // Start download process
            const response = await fetch('/start_download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url, format, quality })
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            const taskId = data.task_id;
            startProgressTracking(taskId);

        } catch (error) {
            showError(error.message);
            resetUI();
        }
    });

    function startProgressTracking(taskId) {
        const eventSource = new EventSource(`/progress/${taskId}`);

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.status === 'downloading') {
                const percent = Math.round(data.percent);
                progressBar.style.width = `${percent}%`;
                progressText.textContent = `${percent}%`;
                progressStatus.textContent = 'İndiriliyor...';
            } else if (data.status === 'processing') {
                progressBar.style.width = '100%';
                progressText.textContent = '100%';
                progressStatus.textContent = 'İşleniyor...';
            } else if (data.status === 'completed') {
                eventSource.close();
                showSuccess(data.filename);
            } else if (data.status === 'error') {
                eventSource.close();
                showError(data.error);
                resetUI();
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            showError('Bağlantı hatası oluştu.');
            resetUI();
        };
    }

    function showSuccess(filename) {
        progressContainer.style.display = 'none';
        statusMessage.className = 'status-message success';
        statusMessage.textContent = '✅ Dönüştürme tamamlandı!';
        statusMessage.style.display = 'block';
        
        downloadLink.href = `/get_file/${filename}`;
        downloadActions.style.display = 'flex';
        convertBtn.style.display = 'none';
    }

    function showError(message) {
        progressContainer.style.display = 'none';
        statusMessage.className = 'status-message error';
        statusMessage.textContent = `❌ ${message}`;
        statusMessage.style.display = 'block';
    }

    function resetUI() {
        convertBtn.disabled = false;
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
    }

    convertAnotherBtn.addEventListener('click', (e) => {
        e.preventDefault();
        urlInput.value = '';
        statusMessage.style.display = 'none';
        downloadActions.style.display = 'none';
        convertBtn.style.display = 'flex';
        convertBtn.disabled = false;
        progressBar.style.width = '0%';
    });
});
