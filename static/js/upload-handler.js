// static/js/upload-handler.js
/**
 * File upload and handling functionality for the upload page
 */

export class UploadHandler {
    constructor() {
        this.init();
    }

    init() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const selectFileBtn = document.getElementById('selectFileBtn');
        const uploadForm = document.getElementById('uploadForm');
        const statusArea = document.getElementById('statusArea');
        const clearDbBtn = document.getElementById('clearDbBtn');
        
        // Handle file selection button
        if (selectFileBtn) {
            selectFileBtn.addEventListener('click', () => {
                fileInput.click();
            });
        }
        
        // Handle file selection via input
        if (fileInput) {
            fileInput.addEventListener('change', () => {
                if (fileInput.files.length > 0) {
                    this.uploadFile(fileInput.files[0]);
                }
            });
        }
        
        // Handle drag and drop
        if (dropZone) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, this.preventDefaults, false);
            });
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, this.highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, this.unhighlight, false);
            });
            
            dropZone.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                
                if (files.length > 0) {
                    this.uploadFile(files[0]);
                }
            }, false);
        }
        
        // Handle clear database button
        if (clearDbBtn) {
            clearDbBtn.addEventListener('click', () => {
                this.handleClearDatabase();
            });
        }
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlight() {
        const dropZone = document.getElementById('dropZone');
        if (dropZone) {
            dropZone.classList.add('highlight');
        }
    }

    unhighlight() {
        const dropZone = document.getElementById('dropZone');
        if (dropZone) {
            dropZone.classList.remove('highlight');
        }
    }

    uploadFile(file) {
        // Update UI to show uploading
        this.showStatus('Uploading and indexing file...', 'info');
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            return response.text().then(text => {
                return {
                    status: response.status,
                    text: text
                };
            });
        })
        .then(result => {
            if (result.status === 200) {
                this.showStatus(result.text, 'success');
            } else {
                this.showStatus(result.text, 'error');
            }
        })
        .catch(error => {
            this.showStatus('Error uploading file: ' + error.message, 'error');
        });
    }

    showStatus(message, type) {
        const statusArea = document.getElementById('statusArea');
        if (statusArea) {
            statusArea.textContent = message;
            statusArea.style.display = 'block';
            
            // Remove all status classes
            statusArea.classList.remove('status-success', 'status-error', 'status-info');
            
            // Add appropriate class
            if (type === 'success') {
                statusArea.classList.add('status-success');
            } else if (type === 'error') {
                statusArea.classList.add('status-error');
            } else {
                statusArea.classList.add('alert', 'alert-info');
            }
        }
    }

    handleClearDatabase() {
        if (confirm('Are you sure you want to clear the database? This action cannot be undone.')) {
            fetch('/clear_db', {
                method: 'POST',
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.showStatus('Database cleared successfully', 'success');
                } else {
                    this.showStatus('Error: ' + data.message, 'error');
                }
            })
            .catch(error => {
                this.showStatus('Error: ' + error.message, 'error');
            });
        }
    }
}
