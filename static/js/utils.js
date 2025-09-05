// static/js/utils.js
/**
 * Utility functions for the ChatGPT Search application
 */

/**
 * Format date nicely based on current time
 * @param {string} dateStr - Date string to format
 * @returns {string} Formatted date string 
 */
export function formatDateNicely(dateStr) {
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
        
        // Format the date based on how recent it is
        const now = new Date();
        const isToday = date.toDateString() === now.toDateString();
        const isYesterday = new Date(now - 86400000).toDateString() === date.toDateString();
        const isThisYear = date.getFullYear() === now.getFullYear();
        
        // Format time part
        const time = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        if (isToday) {
            return `Today at ${time}`;
        } else if (isYesterday) {
            return `Yesterday at ${time}`;
        } else if (isThisYear) {
            // For dates this year, use Month Day format
            const monthDay = date.toLocaleDateString([], {month: 'short', day: 'numeric'});
            return `${monthDay}, ${time}`;
        } else {
            // For older dates, include the year
            const monthDayYear = date.toLocaleDateString([], {
                month: 'short', 
                day: 'numeric',
                year: 'numeric'
            });
            return `${monthDayYear}, ${time}`;
        }
        
    } catch (e) {
        console.error("Error formatting date:", e);
        return dateStr;
    }
}

/**
 * Convert HTML to markdown
 * @param {HTMLElement} element - DOM element to convert
 * @returns {string} Markdown string
 */
export function htmlToMarkdown(element) {
    let text = '';
    
    for (let node of element.childNodes) {
        if (node.nodeType === Node.TEXT_NODE) {
            text += node.textContent;
        } else if (node.nodeType === Node.ELEMENT_NODE) {
            const tagName = node.tagName.toLowerCase();
            
            switch (tagName) {
                case 'h1':
                    text += '# ' + node.textContent + '\n\n';
                    break;
                case 'h2':
                    text += '## ' + node.textContent + '\n\n';
                    break;
                case 'h3':
                    text += '### ' + node.textContent + '\n\n';
                    break;
                case 'h4':
                    text += '#### ' + node.textContent + '\n\n';
                    break;
                case 'h5':
                    text += '##### ' + node.textContent + '\n\n';
                    break;
                case 'h6':
                    text += '###### ' + node.textContent + '\n\n';
                    break;
                case 'p':
                    text += htmlToMarkdown(node) + '\n\n';
                    break;
                case 'strong':
                case 'b':
                    text += '**' + node.textContent + '**';
                    break;
                case 'em':
                case 'i':
                    text += '*' + node.textContent + '*';
                    break;
                case 'code':
                    text += '`' + node.textContent + '`';
                    break;
                case 'pre':
                    const codeContent = node.textContent;
                    text += '```\n' + codeContent + '\n```\n\n';
                    break;
                case 'blockquote':
                    const quoteLines = node.textContent.split('\n');
                    text += quoteLines.map(line => '> ' + line).join('\n') + '\n\n';
                    break;
                case 'ul':
                    const ulItems = node.querySelectorAll('li');
                    ulItems.forEach(li => {
                        text += '- ' + li.textContent + '\n';
                    });
                    text += '\n';
                    break;
                case 'ol':
                    const olItems = node.querySelectorAll('li');
                    olItems.forEach((li, index) => {
                        text += `${index + 1}. ${li.textContent}\n`;
                    });
                    text += '\n';
                    break;
                case 'table':
                    // Simple table handling
                    const rows = node.querySelectorAll('tr');
                    rows.forEach((row, rowIndex) => {
                        const cells = row.querySelectorAll('td, th');
                        const cellContents = Array.from(cells).map(cell => cell.textContent.trim());
                        text += '| ' + cellContents.join(' | ') + ' |\n';
                        
                        // Add header separator after first row
                        if (rowIndex === 0 && node.querySelector('th')) {
                            text += '|' + ' --- |'.repeat(cellContents.length) + '\n';
                        }
                    });
                    text += '\n';
                    break;
                case 'a':
                    const href = node.getAttribute('href');
                    if (href) {
                        text += `[${node.textContent}](${href})`;
                    } else {
                        text += node.textContent;
                    }
                    break;
                case 'br':
                    text += '\n';
                    break;
                default:
                    // For other elements, just get the text content and recurse
                    text += htmlToMarkdown(node);
                    break;
            }
        }
    }
    
    return text;
}

/**
 * Format date for display in stats charts
 * @param {string} dateStr - Date string to format  
 * @returns {string} Formatted date string
 */
export function formatDateForDisplay(dateStr) {
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
