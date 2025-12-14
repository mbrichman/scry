// static/js/conversation-filters.js
/**
 * Conversation filter management for the conversations page
 */

export class ConversationFilters {
    constructor() {
        this.sourceFilter = document.getElementById('sourceFilter');
        this.dateFilter = document.getElementById('dateFilter');
        this.sortOrder = document.getElementById('sortOrder');
        this.init();
    }

    init() {
        this.readUrlParams();
        this.setupEventListeners();
        this.formatDates();
    }

    // Read URL parameters and set filter values
    readUrlParams() {
        const params = new URLSearchParams(window.location.search);
        
        const source = params.get('source');
        const date = params.get('date');
        const sort = params.get('sort');
        
        if (source && this.sourceFilter) {
            this.sourceFilter.value = source;
        }
        if (date && this.dateFilter) {
            this.dateFilter.value = date;
        }
        if (sort && this.sortOrder) {
            this.sortOrder.value = sort;
        }
    }

    // Setup event listeners for filter changes
    setupEventListeners() {
        const filters = [this.sourceFilter, this.dateFilter, this.sortOrder];
        
        filters.forEach(filter => {
            if (filter) {
                filter.addEventListener('change', () => {
                    this.applyFilters();
                });
            }
        });
    }

    // Get current filter values
    getCurrentFilters() {
        return {
            source: this.sourceFilter?.value || 'all',
            date: this.dateFilter?.value || 'all',
            sort: this.sortOrder?.value || 'newest'
        };
    }

    // Build URL with current filter values
    buildFilterUrl() {
        const filters = this.getCurrentFilters();
        const params = new URLSearchParams();
        
        if (filters.source !== 'all') {
            params.set('source', filters.source);
        }
        if (filters.date !== 'all') {
            params.set('date', filters.date);
        }
        if (filters.sort !== 'newest') {
            params.set('sort', filters.sort);
        }
        
        const queryString = params.toString();
        return window.location.pathname + (queryString ? '?' + queryString : '');
    }

    // Apply filters by navigating to new URL
    applyFilters() {
        const newUrl = this.buildFilterUrl();
        
        // Navigate to the filtered URL
        window.location.href = newUrl;
    }

    // Format date elements for display
    formatDates() {
        const dateElements = document.querySelectorAll('.date-to-format');
        
        dateElements.forEach(element => {
            const dateStr = element.textContent.trim();
            
            if (dateStr && dateStr !== 'Unknown date') {
                try {
                    const date = new Date(dateStr);
                    
                    if (!isNaN(date.getTime())) {
                        const options = {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        };
                        
                        element.textContent = date.toLocaleDateString(undefined, options);
                    }
                } catch (e) {
                    // Keep original text if parsing fails
                    console.warn('Date parsing failed for:', dateStr, e);
                }
            }
        });
    }
}
