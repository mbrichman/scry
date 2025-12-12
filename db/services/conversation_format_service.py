"""ConversationFormatService - Formats conversation data for different views

This service extracts formatting logic from ConversationController, following
the Single Responsibility Principle. It handles:
- List view formatting
- Detail view formatting  
- Search results formatting
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.conversation_view_model import (
    extract_preview_content,
    parse_messages_from_document
)


class ConversationFormatService:
    """Service for formatting conversation data for different views"""
    
    def format_conversation_list(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format conversations for list view
        
        Args:
            conversations: List of conversation dictionaries with fields:
                - id: Conversation ID
                - title: Conversation title
                - preview: Preview text
                - source: Source (claude, chatgpt, etc.)
                - created_at: Created datetime (optional)
                - updated_at: Updated datetime (optional)
                - message_count: Number of messages (optional)
        
        Returns:
            List of formatted conversations with structure:
                - id: Conversation ID
                - meta: Dict with title, source, earliest_ts, latest_ts, message_count
                - preview: Preview text
        """
        if not conversations:
            return []
        
        formatted = []
        for conv in conversations:
            formatted_conv = {
                'id': conv.get('id', ''),
                'meta': {
                    'title': conv.get('title') or 'Untitled Conversation',
                    'source': conv.get('source') or 'unknown',
                    'earliest_ts': self._format_timestamp(conv.get('created_at')) or '',
                    'latest_ts': self._format_timestamp(conv.get('updated_at')) or '',
                    'message_count': conv.get('message_count') or 0,
                    'relevance_display': 'N/A'
                },
                'preview': conv.get('preview') or ''
            }
            formatted.append(formatted_conv)
        
        return formatted
    
    def format_conversation_view(self, document: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single conversation for detail view
        
        Args:
            document: Raw conversation document text
            metadata: Conversation metadata dict with fields:
                - title: Conversation title
                - source: Source (claude, chatgpt, etc.)
                - earliest_ts: Earliest timestamp
                - message_count: Number of messages
        
        Returns:
            Dict with keys:
                - conversation: Dict with 'meta' and 'document' keys
                - messages: List of parsed message dicts
                - assistant_name: Name of the assistant (Claude, ChatGPT, AI)
        """
        # Parse messages from document
        messages = self._parse_messages(document, metadata.get('source', ''))
        
        # Determine assistant name
        assistant_name = self._determine_assistant_name(
            document, 
            metadata.get('source', '').lower()
        )
        
        # Build conversation object
        conversation = {
            'meta': metadata,
            'document': document
        }
        
        return {
            'conversation': conversation,
            'messages': messages,
            'assistant_name': assistant_name
        }
    
    def format_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format search results for display
        
        Args:
            results: List of search result dicts with fields:
                - id: Result ID
                - title: Result title
                - content: Result content/preview
                - metadata: Result metadata dict
                - score: Relevance score (optional)
        
        Returns:
            List of formatted results with structure:
                - id: Result ID
                - meta: Dict with title, source, earliest_ts, relevance_score, relevance_display
                - preview: Preview text
        """
        if not results:
            return []
        
        formatted = []
        for result in results:
            metadata = result.get('metadata', {})
            score = result.get('score')
            
            formatted_result = {
                'id': result.get('id', ''),
                'meta': {
                    'title': result.get('title', 'Untitled'),
                    'source': metadata.get('source', 'unknown'),
                    'earliest_ts': metadata.get('earliest_ts', ''),
                    'latest_ts': metadata.get('latest_ts', ''),
                    'message_count': metadata.get('message_count', 0),
                    'relevance_score': score,
                    'relevance_display': f'{score:.3f}' if score is not None else 'N/A'
                },
                'preview': result.get('content', '')
            }
            formatted.append(formatted_result)
        
        return formatted
    
    # ===== Helper methods =====
    
    def _extract_preview(self, document: str, max_length: int = 200) -> str:
        """Extract clean preview text from document
        
        Args:
            document: Raw document text
            max_length: Maximum preview length
        
        Returns:
            Cleaned preview text, truncated to max_length
        """
        return extract_preview_content(document, max_length)
    
    def _parse_messages(self, document: str, source: str) -> List[Dict[str, Any]]:
        """Parse document into individual messages
        
        Args:
            document: Raw document text
            source: Source type (claude, chatgpt, etc.)
        
        Returns:
            List of message dicts with 'role', 'content', 'timestamp' keys
        """
        return parse_messages_from_document(document)
    
    def _determine_assistant_name(self, document: str, source: str) -> str:
        """Determine assistant name from source or document content
        
        Args:
            document: Raw document text
            source: Source type (claude, chatgpt, etc.)
        
        Returns:
            Assistant name: 'Claude', 'ChatGPT', or 'AI'
        """
        source_lower = source.lower() if source else ''
        
        if source_lower == 'claude':
            return 'Claude'
        elif source_lower == 'chatgpt':
            return 'ChatGPT'
        else:
            # Try to detect from document content
            if '**Claude said**' in document or '**Claude**:' in document:
                return 'Claude'
            elif '**ChatGPT said**' in document or '**ChatGPT**:' in document:
                return 'ChatGPT'
            else:
                return 'AI'
    
    def _format_timestamp(self, dt: Optional[datetime]) -> Optional[str]:
        """Format datetime to string
        
        Args:
            dt: Datetime object or None
        
        Returns:
            Formatted timestamp string or None
        """
        if dt is None:
            return None
        
        if isinstance(dt, datetime):
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return None
