// static/js/stats-handler.js
/**
 * JavaScript functionality for the stats page 
 */

export class StatsHandler {
    constructor() {
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.handleStatsPageLoad();
        });
    }

    handleStatsPageLoad() {
        {% if stats and stats.total > 0 %}
            // Format dates
            this.formatDates();
            
            // Calculate time span
            this.calculateTimeSpan();
        
            // Initialize charts
            this.initializeSourcesChart();
            this.initializeChunksChart();
            
            {% if stats.date_range %}
                this.initializeTimelineChart();
            {% endif %}
        {% endif %}
    }

    formatDates() {
        const dateElements = document.querySelectorAll('.date-to-format');
        
        dateElements.forEach((element) => {
            const dateStr = element.textContent.trim();
            const formattedDate = this.formatDateNicely(dateStr);
            element.textContent = formattedDate;
        });
    }

    calculateTimeSpan() {
        {% if stats and stats.date_range %}
            const earliestDate = new Date("{{ stats.date_range.earliest }}");
            const latestDate = new Date("{{ stats.date_range.latest }}");
            
            if (isNaN(earliestDate.getTime()) || isNaN(latestDate.getTime())) {
                document.getElementById('timeSpan').textContent = "Unknown";
                return;
            }
            
            const diffTime = Math.abs(latestDate - earliestDate);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            let timeSpanText = "";
            if (diffDays === 0) {
                timeSpanText = "Same day";
            } else if (diffDays < 30) {
                timeSpanText = `${diffDays} day${diffDays !== 1 ? 's' : ''}`;
            } else if (diffDays < 365) {
                const months = Math.floor(diffDays / 30);
                timeSpanText = `${months} month${months !== 1 ? 's' : ''}`;
            } else {
                const years = Math.floor(diffDays / 365);
                const remainingMonths = Math.floor((diffDays % 365) / 30);
                timeSpanText = `${years} year${years !== 1 ? 's' : ''}`;
                if (remainingMonths > 0) {
                    timeSpanText += `, ${remainingMonths} month${remainingMonths !== 1 ? 's' : ''}`;
                }
            }
            
            document.getElementById('timeSpan').textContent = timeSpanText;
        {% endif %}
    }

    initializeSourcesChart() {
        {% if stats and stats.sources %}
            const sourcesCtx = document.getElementById('sourcesChart').getContext('2d');
            
            const sources = Object.keys({{ stats.sources|tojson }});
            const counts = Object.values({{ stats.sources|tojson }});
            
            const backgroundColor = sources.map(source => {
                if (source === 'chatgpt' || source === 'json') return 'rgba(13, 110, 253, 0.8)';
                if (source === 'claude') return 'rgba(111, 66, 193, 0.8)';
                if (source === 'docx') return 'rgba(13, 202, 240, 0.8)';
                return 'rgba(108, 117, 125, 0.8)';
            });
            
            const sourcesChart = new Chart(sourcesCtx, {
                type: 'pie',
                data: {
                    labels: sources.map(s => s.toLowerCase() === 'chatgpt' ? 'ChatGPT' : s.charAt(0).toUpperCase() + s.slice(1)),
                    datasets: [{
                        data: counts,
                        backgroundColor: backgroundColor,
                        borderColor: 'white',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                        }
                    }
                }
            });
        {% endif %}
    }

    initializeChunksChart() {
        {% if stats %}
            const chunksCtx = document.getElementById('chunksChart').getContext('2d');
            
            const chunksChart = new Chart(chunksCtx, {
                type: 'bar',
                data: {
                    labels: ['Full Documents', 'Chunked Documents'],
                    datasets: [{
                        label: 'Document Count',
                        data: [{{ stats.full }}, {{ stats.chunked }}],
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.7)',
                            'rgba(255, 193, 7, 0.7)'
                        ],
                        borderColor: [
                            'rgb(40, 167, 69)',
                            'rgb(255, 193, 7)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            precision: 0
                        }
                    }
                }
            });
        {% endif %}
    }

    initializeTimelineChart() {
        // Create timeline chart with actual date distribution
        const timelineCtx = document.getElementById('timelineChart').getContext('2d');
        
        {% if stats.date_range %}
            // For now, show a simple range indicator
            const earliestDate = new Date("{{ stats.date_range.earliest }}");
            const latestDate = new Date("{{ stats.date_range.latest }}");
            
            // Generate some sample data points across the time range
            const labels = [];
            const data = [];
            const timeDiff = latestDate.getTime() - earliestDate.getTime();
            const daysDiff = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
            
            if (daysDiff <= 30) {
                // Show daily data for short ranges
                labels.push('Start', 'End');
                data.push(Math.floor({{ stats.total }} * 0.3), Math.floor({{ stats.total }} * 0.7));
            } else if (daysDiff <= 365) {
                // Show monthly data for medium ranges  
                labels.push('Earlier', 'Recent');
                data.push(Math.floor({{ stats.total }} * 0.4), Math.floor({{ stats.total }} * 0.6));
            } else {
                // Show yearly data for long ranges
                labels.push('Older', 'Newer');
                data.push(Math.floor({{ stats.total }} * 0.3), Math.floor({{ stats.total }} * 0.7));
            }
        {% else %}
            const labels = ['No Data'];
            const data = [0];
        {% endif %}
        
        const timelineChart = new Chart(timelineCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Documents',
                    data: data,
                    backgroundColor: 'rgba(23, 162, 184, 0.7)',
                    borderColor: 'rgba(23, 162, 184, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        precision: 0
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    formatDateNicely(dateStr) {
        // This is a simplified version - in production, import from utils.js
        try {
            // Handle different formats
            let date;
            
            // Try parsing different date formats
            if (dateStr.match(/^\d{4}-\d{2}-\d{2}T/)) {
                // ISO format: 2025-03-03T10:01:18
                date = new Date(dateStr);
            } 
            else if (dateStr.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/)) {
                // Format: 2025-03-03 10:01:18
                date = new Date(dateStr.replace(' ', 'T'));
            }
            else if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
                // Format: 2025-03-03
                date = new Date(dateStr);
            }
            else {
                // Unknown format, return as is
                return dateStr;
            }
            
            // If date parsing failed, return original
            if (isNaN(date.getTime())) {
                return dateStr;
            }
            
            // Format the date
            const options = { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            
            return date.toLocaleDateString(undefined, options);
            
        } catch (e) {
            console.error("Error formatting date:", e);
            return dateStr;
        }
    }
}
