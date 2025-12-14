// static/js/view-page.js
/**
 * JavaScript functionality for the view page
 */

export class ViewPageHandler {
    constructor() {
        this.init();
    }

    init() {
        // Format dates when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            this.formatDates();
        });
        
        // Set up copy conversation button
        const copyButton = document.querySelector('.copy-button');
        if (copyButton) {
            copyButton.addEventListener('click', () => {
                this.copyConversationAsMarkdown();
            });
        }
    }

    formatDates() {
        const dateElements = document.querySelectorAll('.date-to-format');
        
        dateElements.forEach(element => {
            const dateStr = element.textContent.trim();
            // Store original date for copy functionality
            element.setAttribute('data-original', dateStr);
            const formattedDate = this.formatDateNicely(dateStr);
            element.textContent = formattedDate;
        });
    }

    copyConversationAsMarkdown() {
        try {
            // Get the conversation title
            const titleElement = document.querySelector('.conversation-title');
            const title = titleElement ? titleElement.textContent.trim() : 'Conversation';
            
            // Get the date from metadata
            const dateElement = document.querySelector('.conversation-metadata .date-to-format');
            let date = '';
            if (dateElement) {
                // Get the original date text (before formatting)
                const originalDate = dateElement.getAttribute('data-original') || dateElement.textContent.trim();
                date = originalDate;
            }
            
            // Start building markdown content
            let markdown = `# ${title}\n\n`;
            if (date) {
                markdown += `**Date:** ${date}\n\n`;
            }
            markdown += '---\n\n';
            
            // Get all messages
            const messages = document.querySelectorAll('.message');
            
            messages.forEach((message, index) => {
                // Get the role
                const roleElement = message.querySelector('.role-name');
                const role = roleElement ? roleElement.textContent.trim() : 'Unknown';
                
                // Get the timestamp
                const timestampElement = message.querySelector('.timestamp');
                let timestamp = '';
                if (timestampElement && timestampElement.textContent.trim()) {
                    // Get original timestamp if available, otherwise formatted
                    timestamp = timestampElement.getAttribute('data-original') || timestampElement.textContent.trim();
                }
                
                // Get the message content and convert it back to markdown
                const contentElement = message.querySelector('.message-content');
                let content = '';
                
                if (contentElement) {
                    // Clone the element to avoid modifying the original
                    const clonedContent = contentElement.cloneNode(true);
                    
                    // Convert HTML back to approximate markdown
                    content = this.htmlToMarkdown(clonedContent);
                }
                
                // Add the message to markdown
                if (timestamp && timestamp !== '') {
                    markdown += `**${role}** *(on ${timestamp})*:\n\n`;
                } else {
                    markdown += `**${role}**:\n\n`;
                }
                markdown += content + '\n\n';
            });
            
            // Copy to clipboard
            navigator.clipboard.writeText(markdown).then(() => {
                // Show success message
                const successMessage = document.getElementById('copySuccess');
                if (successMessage) {
                    successMessage.textContent = 'Conversation copied to clipboard!';
                    successMessage.style.display = 'block';
                    
                    // Hide after 2 seconds
                    setTimeout(() => {
                        successMessage.style.display = 'none';
                    }, 2000);
                }
            }).catch((err) => {
                console.error('Failed to copy: ', err);
                // Fallback: show error message
                const successMessage = document.getElementById('copySuccess');
                if (successMessage) {
                    successMessage.textContent = 'Failed to copy to clipboard';
                    successMessage.style.backgroundColor = '#dc3545';
                    successMessage.style.display = 'block';
                    
                    setTimeout(() => {
                        successMessage.style.display = 'none';
                        successMessage.style.backgroundColor = '#28a745';
                    }, 2000);
                }
            });
        } catch (err) {
            console.error('Error copying conversation:', err);
        }
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
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            
            // Add year if not the current year
            if (date.getFullYear() !== new Date().getFullYear()) {
                options.year = 'numeric';
            }
            
            return date.toLocaleDateString(undefined, options);
            
        } catch (e) {
            console.error("Error formatting date:", e);
            return dateStr;
        }
    }

    htmlToMarkdown(element) {
        // This is a simplified version - in production, import from utils.js
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
                        text += this.htmlToMarkdown(node) + '\n\n';
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
                        text += this.htmlToMarkdown(node);
                        break;
                }
            }
        }
        
        return text;
    }
}
