
document.addEventListener('DOMContentLoaded', () => {
    // Basic Elements
    const fileInput = document.getElementById('imageInput');
    const uploadBox = document.getElementById('uploadBox');
    const previewSection = document.getElementById('previewSection');
    const imagePreview = document.getElementById('imagePreview');
    const scanButton = document.getElementById('scanButton');
    const resultSection = document.getElementById('resultSection');
    const plateNumberEl = document.getElementById('plateNumber');
    const stateInfoEl = document.getElementById('stateInfo');
    const errorMessageEl = document.getElementById('errorMessage');
    const loader = document.getElementById('loader');
    let currentFile = null;

    // Handle file selection via Click
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    // Optimize drag and drop experience
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadBox.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    uploadBox.addEventListener('dragover', () => {
        uploadBox.classList.add('drag-over');
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.classList.remove('drag-over');
    });

    uploadBox.addEventListener('drop', (e) => {
        uploadBox.classList.remove('drag-over');
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file.');
            return;
        }
        currentFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            previewSection.classList.remove('hidden');
            scanButton.classList.remove('hidden');
            resultSection.classList.add('hidden'); // Hide previous results
            errorMessageEl.classList.add('hidden'); // Hide previous errors
        };
        reader.readAsDataURL(file);
    }

    scanButton.addEventListener('click', async () => {
        if (!currentFile) return;

        // Reset UI
        scanButton.classList.add('hidden');
        loader.classList.remove('hidden');
        resultSection.classList.add('hidden');
        errorMessageEl.classList.add('hidden');

        const formData = new FormData();
        formData.append('image', currentFile);

        try {
            const response = await fetch('/scan', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            loader.classList.add('hidden');
            resultSection.classList.remove('hidden');
            scanButton.classList.remove('hidden');

            if (data.success) {
                plateNumberEl.textContent = data.plate_text;
                stateInfoEl.textContent = `State: ${data.state}`;
                errorMessageEl.classList.add('hidden');
            } else {
                plateNumberEl.textContent = "---";
                stateInfoEl.textContent = "";
                errorMessageEl.textContent = data.error || "Could not detect plate.";
                errorMessageEl.classList.remove('hidden');
            }

        } catch (error) {
            console.error('Error:', error);
            loader.classList.add('hidden');
            scanButton.classList.remove('hidden');
            errorMessageEl.textContent = "An error occurred while scanning.";
            errorMessageEl.classList.remove('hidden');
            resultSection.classList.remove('hidden'); // Show error area
        }
    });
});
