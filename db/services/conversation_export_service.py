"""ConversationExportService - Handles conversation export functionality

This service extracts export logic from ConversationController, following
the Single Responsibility Principle. It handles:
- Markdown export
- OpenWebUI format conversion
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional


class ConversationExportService:
    """Service for exporting conversations to different formats"""
    
    def export_as_markdown(self, document: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Export conversation as markdown
        
        Args:
            document: Raw conversation document text
            metadata: Conversation metadata dict with fields:
                - title: Conversation title
                - earliest_ts: Earliest timestamp (optional)
        
        Returns:
            Dict with keys:
                - filename: Generated filename (e.g. "conversation.md")
                - content: Full markdown content with headers
                - mimetype: MIME type ("text/markdown")
        """
        # Generate filename
        title = metadata.get('title', 'conversation')
        filename = self._generate_filename(title)
        
        # Build markdown content
        markdown_content = f"# {metadata.get('title', 'Conversation')}\n\n"
        
        # Add date if available
        if metadata.get('earliest_ts'):
            formatted_date = self._format_date_for_markdown(metadata['earliest_ts'])
            if formatted_date:
                markdown_content += f"Date: {formatted_date}\n\n"
        
        # Add document content
        markdown_content += document
        
        return {
            'filename': filename,
            'content': markdown_content,
            'mimetype': 'text/markdown'
        }
    
    def export_to_openwebui(self, document: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Export conversation to OpenWebUI format
        
        Args:
            document: Raw conversation document text
            metadata: Conversation metadata dict with fields:
                - title: Conversation title
                - source: Source (claude, chatgpt, etc.)
                - earliest_ts: Earliest timestamp
                - latest_ts: Latest timestamp (optional)
        
        Returns:
            Dict with OpenWebUI conversation format:
                - name: Conversation name
                - created_at: Creation timestamp
                - updated_at: Update timestamp
                - chat_messages: List of message dicts with sender, text, created_at
        """
        # Parse messages from document
        messages = self._parse_messages_for_export(document, metadata)
        
        # Build chat_messages in OpenWebUI format
        chat_messages = self._build_chat_messages(messages, metadata)
        
        # Build conversation object
        openwebui_conv = {
            'name': metadata.get('title', 'Untitled Conversation'),
            'created_at': metadata.get('earliest_ts', ''),
            'updated_at': metadata.get('latest_ts') or metadata.get('earliest_ts', ''),
            'chat_messages': chat_messages
        }
        
        return openwebui_conv
    
    # ===== Helper methods =====
    
    def _parse_messages_for_export(self, document: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse document into messages for export
        
        Args:
            document: Raw document text
            metadata: Conversation metadata
        
        Returns:
            List of message dicts with 'role', 'content', 'timestamp' keys
        """
        messages = []
        source = metadata.get('source', '').lower()
        
        # Different patterns based on source
        if source == 'chatgpt':
            # ChatGPT format: **You said** and **ChatGPT said**
            parts = document.split('**You said**')
            
            for i, part in enumerate(parts[1:], 1):  # Skip first empty part
                if '**ChatGPT said**' in part:
                    user_content, ai_content = part.split('**ChatGPT said**', 1)
                    
                    # Extract timestamps and clean content
                    user_timestamp = self._extract_timestamp(user_content)
                    ai_timestamp = self._extract_timestamp(ai_content)
                    
                    user_msg = self._clean_message_content(user_content)
                    ai_msg = self._clean_message_content(ai_content)
                    
                    if user_msg.strip():
                        messages.append({
                            'role': 'user',
                            'content': user_msg,
                            'timestamp': user_timestamp
                        })
                    
                    if ai_msg.strip():
                        messages.append({
                            'role': 'assistant',
                            'content': ai_msg,
                            'timestamp': ai_timestamp
                        })
        
        elif source == 'claude':
            # Claude format: **You said** and **Claude said**
            parts = document.split('**You said**')
            
            for i, part in enumerate(parts[1:], 1):
                if '**Claude said**' in part:
                    user_content, ai_content = part.split('**Claude said**', 1)
                    
                    user_timestamp = self._extract_timestamp(user_content)
                    ai_timestamp = self._extract_timestamp(ai_content)
                    
                    user_msg = self._clean_message_content(user_content)
                    ai_msg = self._clean_message_content(ai_content)
                    
                    if user_msg.strip():
                        messages.append({
                            'role': 'user',
                            'content': user_msg,
                            'timestamp': user_timestamp
                        })
                    
                    if ai_msg.strip():
                        messages.append({
                            'role': 'assistant',
                            'content': ai_msg,
                            'timestamp': ai_timestamp
                        })
        
        else:
            # Generic format - try to split on common patterns
            if '**You said**' in document and '**AI said**' in document:
                parts = document.split('**You said**')
                for i, part in enumerate(parts[1:], 1):
                    if '**AI said**' in part:
                        user_content, ai_content = part.split('**AI said**', 1)
                        
                        user_msg = self._clean_message_content(user_content)
                        ai_msg = self._clean_message_content(ai_content)
                        
                        if user_msg.strip():
                            messages.append({
                                'role': 'user',
                                'content': user_msg,
                                'timestamp': None
                            })
                        
                        if ai_msg.strip():
                            messages.append({
                                'role': 'assistant',
                                'content': ai_msg,
                                'timestamp': None
                            })
        
        return messages
    
    def _build_chat_messages(self, parsed_messages: List[Dict[str, Any]], 
                            metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build chat_messages list for OpenWebUI format
        
        Args:
            parsed_messages: List of parsed message dicts
            metadata: Conversation metadata (for fallback timestamp)
        
        Returns:
            List of chat message dicts with sender, text, created_at
        """
        chat_messages = []
        
        for msg in parsed_messages:
            chat_msg = {
                'sender': msg['role'],
                'text': msg['content'],
                'created_at': msg.get('timestamp') or metadata.get('earliest_ts', '')
            }
            chat_messages.append(chat_msg)
        
        return chat_messages
    
    def _extract_timestamp(self, content: str) -> Optional[str]:
        """Extract timestamp from message content
        
        Args:
            content: Message content
        
        Returns:
            Timestamp string or None
        """
        # Look for patterns like *(on 2025-04-05 02:20:02)*:
        timestamp_match = re.search(r'\*\(on ([\d\-\s:]+)\)\*', content)
        if timestamp_match:
            return timestamp_match.group(1)
        return None
    
    def _clean_message_content(self, content: str) -> str:
        """Clean message content by removing timestamps and formatting
        
        Args:
            content: Raw message content
        
        Returns:
            Cleaned content
        """
        # Remove timestamp patterns
        content = re.sub(r'\*\(on [\d\-\s:]+\)\*', '', content)
        # Remove leading/trailing whitespace and newlines
        content = content.strip()
        # Remove leading colon and whitespace
        if content.startswith(':'):
            content = content[1:].strip()
        return content
    
    def _generate_filename(self, title: Optional[str]) -> str:
        """Generate safe filename from title
        
        Args:
            title: Conversation title
        
        Returns:
            Safe filename with .md extension
        """
        if not title:
            return 'conversation.md'
        
        # Replace spaces with underscores and remove unsafe characters
        safe_title = title.replace(' ', '_')
        # Remove characters that are problematic in filenames
        safe_title = re.sub(r'[/\\:*?"<>|]', '', safe_title)
        
        return f"{safe_title}.md"
    
    def _format_date_for_markdown(self, date_str: Optional[str]) -> Optional[str]:
        """Format date string for markdown header
        
        Args:
            date_str: ISO format date string
        
        Returns:
            Formatted date string or None
        """
        if not date_str:
            return None
        
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, AttributeError):
            return None
