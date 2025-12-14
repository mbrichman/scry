// static/js/search-handler.js
/**
 * Search functionality for the index page
 */

export class SearchHandler {
    constructor() {
        this.init();
    }

    init() {
        // Handle share button on search results page
        const shareButton = document.getElementById('shareButton');
        if (shareButton) {
            shareButton.addEventListener('click', () => {
                this.handleShareClick();
            });
        }
        
        // Highlight search terms
        this.highlightSearchTerms();
    }

    handleShareClick() {
        try {
            // Get the current search query
            const searchInput = document.querySelector('input[name="query"]');
            const shareQuery = document.getElementById('shareQuery');
            
            if (searchInput && searchInput.value && shareQuery) {
                // Set the query in the shareable form
                shareQuery.value = searchInput.value;
                
                // Create the shareable URL
                const shareForm = document.getElementById('shareForm');
                const formData = new FormData(shareForm);
                const queryString = new URLSearchParams(formData).toString();
                const shareableUrl = window.location.origin + window.location.pathname + '?' + queryString;
                
                // Copy to clipboard
                navigator.clipboard.writeText(shareableUrl).then(() => {
                    // Show success message
                    const successMessage = document.getElementById('copySuccess');
                    if (successMessage) {
                        successMessage.style.display = 'block';
                        
                        // Hide after 2 seconds
                        setTimeout(() => {
                            successMessage.style.display = 'none';
                        }, 2000);
                    }
                });
            }
        } catch (error) {
            console.error('Error handling share click:', error);
        }
    }

    highlightSearchTerms() {
        const searchInput = document.querySelector('input[name="query"]');
        if (searchInput && searchInput.value) {
            const searchTerm = searchInput.value.trim();
            if (searchTerm) {
                const messageContents = document.querySelectorAll('.message-content');
                
                messageContents.forEach(content => {
                    // Skip highlighting within tags
                    const html = content.innerHTML;
                    const regex = new RegExp(`(${searchTerm})`, 'gi');
                    
                    // This is a simple approach - for production, you'd want a more robust HTML-aware solution
                    content.innerHTML = html.replace(regex, '<mark>$1</mark>');
                });
            }
        }
    }
}
