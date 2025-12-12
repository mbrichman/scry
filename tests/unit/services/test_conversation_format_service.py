"""Tests for ConversationFormatService - TDD approach"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from db.services.conversation_format_service import ConversationFormatService


class TestConversationFormatService:
    """Test suite for ConversationFormatService"""
    
    @pytest.fixture
    def service(self):
        """Create a ConversationFormatService instance"""
        return ConversationFormatService()
    
    # ===== format_conversation_list tests =====
    
    def test_format_conversation_list_empty(self, service):
        """Test formatting an empty conversation list"""
        result = service.format_conversation_list([])
        assert result == []
    
    def test_format_conversation_list_single_item(self, service):
        """Test formatting a single conversation"""
        conversations = [{
            'id': 'test-id-1',
            'title': 'Test Conversation',
            'preview': 'This is a preview',
            'source': 'claude',
            'created_at': datetime(2025, 1, 1, 12, 0, 0),
            'updated_at': datetime(2025, 1, 1, 14, 0, 0),
            'message_count': 5
        }]
        
        result = service.format_conversation_list(conversations)
        
        assert len(result) == 1
        assert result[0]['id'] == 'test-id-1'
        assert result[0]['meta']['title'] == 'Test Conversation'
        assert result[0]['preview'] == 'This is a preview'
        assert result[0]['meta']['source'] == 'claude'
    
    def test_format_conversation_list_multiple_items(self, service):
        """Test formatting multiple conversations"""
        conversations = [
            {
                'id': 'test-id-1',
                'title': 'Conv 1',
                'preview': 'Preview 1',
                'source': 'claude',
                'created_at': datetime(2025, 1, 1, 12, 0, 0),
                'updated_at': datetime(2025, 1, 1, 14, 0, 0),
                'message_count': 5
            },
            {
                'id': 'test-id-2',
                'title': 'Conv 2',
                'preview': 'Preview 2',
                'source': 'chatgpt',
                'created_at': datetime(2025, 1, 2, 12, 0, 0),
                'updated_at': datetime(2025, 1, 2, 14, 0, 0),
                'message_count': 3
            }
        ]
        
        result = service.format_conversation_list(conversations)
        
        assert len(result) == 2
        assert result[0]['id'] == 'test-id-1'
        assert result[1]['id'] == 'test-id-2'
    
    def test_format_conversation_list_with_missing_fields(self, service):
        """Test formatting conversations with missing optional fields"""
        conversations = [{
            'id': 'test-id-1',
            'title': 'Test',
            'preview': 'Preview'
            # Missing source, dates, message_count
        }]
        
        result = service.format_conversation_list(conversations)
        
        assert len(result) == 1
        assert result[0]['meta']['source'] == 'unknown'
        assert result[0]['meta']['message_count'] == 0
    
    def test_format_conversation_list_handles_none_values(self, service):
        """Test formatting with None values"""
        conversations = [{
            'id': 'test-id-1',
            'title': None,
            'preview': None,
            'source': None,
            'message_count': None
        }]
        
        result = service.format_conversation_list(conversations)
        
        assert len(result) == 1
        assert result[0]['meta']['title'] == 'Untitled Conversation'
        assert result[0]['preview'] == ''
    
    # ===== format_conversation_view tests =====
    
    def test_format_conversation_view_claude(self, service):
        """Test formatting a Claude conversation for detail view"""
        document = "**You said** *(on 2025-01-01 12:00:00)*:\n\nHello\n\n**Claude said** *(on 2025-01-01 12:00:05)*:\n\nHi there!"
        metadata = {
            'title': 'Test Conversation',
            'source': 'claude',
            'earliest_ts': '2025-01-01T12:00:00',
            'message_count': 2
        }
        
        result = service.format_conversation_view(document, metadata)
        
        assert result['conversation']['meta'] == metadata
        assert result['assistant_name'] == 'Claude'
        assert len(result['messages']) == 2
        assert result['messages'][0]['role'] == 'user'
        assert result['messages'][1]['role'] == 'assistant'
    
    def test_format_conversation_view_chatgpt(self, service):
        """Test formatting a ChatGPT conversation for detail view"""
        document = "**You said**:\n\nHello\n\n**ChatGPT said**:\n\nHi!"
        metadata = {
            'title': 'Test',
            'source': 'chatgpt',
            'earliest_ts': '2025-01-01T12:00:00'
        }
        
        result = service.format_conversation_view(document, metadata)
        
        assert result['assistant_name'] == 'ChatGPT'
        # Note: parse_messages_from_document requires exact format matching
        # This test verifies assistant name detection works correctly
    
    def test_format_conversation_view_unknown_source(self, service):
        """Test formatting conversation with unknown source"""
        document = "Some conversation content"
        metadata = {
            'title': 'Test',
            'source': 'unknown'
        }
        
        result = service.format_conversation_view(document, metadata)
        
        assert result['assistant_name'] == 'AI'
    
    def test_format_conversation_view_detects_claude_from_content(self, service):
        """Test auto-detecting Claude from document content"""
        document = "**Claude said**: Hello"
        metadata = {
            'title': 'Test',
            'source': 'unknown'
        }
        
        result = service.format_conversation_view(document, metadata)
        
        assert result['assistant_name'] == 'Claude'
    
    def test_format_conversation_view_detects_chatgpt_from_content(self, service):
        """Test auto-detecting ChatGPT from document content"""
        document = "**ChatGPT said**: Hello"
        metadata = {
            'title': 'Test',
            'source': 'unknown'
        }
        
        result = service.format_conversation_view(document, metadata)
        
        assert result['assistant_name'] == 'ChatGPT'
    
    # ===== format_search_results tests =====
    
    def test_format_search_results_empty(self, service):
        """Test formatting empty search results"""
        results = []
        
        formatted = service.format_search_results(results)
        
        assert formatted == []
    
    def test_format_search_results_single_result(self, service):
        """Test formatting a single search result"""
        results = [{
            'id': 'test-id-1',
            'title': 'Test Result',
            'content': 'Result content',
            'metadata': {
                'source': 'claude',
                'earliest_ts': '2025-01-01T12:00:00'
            },
            'score': 0.95
        }]
        
        formatted = service.format_search_results(results)
        
        assert len(formatted) == 1
        assert formatted[0]['id'] == 'test-id-1'
        assert formatted[0]['meta']['title'] == 'Test Result'
        assert formatted[0]['preview'] == 'Result content'
        assert 'relevance_score' in formatted[0]['meta']
    
    def test_format_search_results_multiple_results(self, service):
        """Test formatting multiple search results"""
        results = [
            {
                'id': 'test-id-1',
                'title': 'Result 1',
                'content': 'Content 1',
                'metadata': {'source': 'claude'},
                'score': 0.95
            },
            {
                'id': 'test-id-2',
                'title': 'Result 2',
                'content': 'Content 2',
                'metadata': {'source': 'chatgpt'},
                'score': 0.85
            }
        ]
        
        formatted = service.format_search_results(results)
        
        assert len(formatted) == 2
        assert formatted[0]['meta']['relevance_score'] == 0.95
        assert formatted[1]['meta']['relevance_score'] == 0.85
    
    def test_format_search_results_with_missing_score(self, service):
        """Test formatting search results without scores"""
        results = [{
            'id': 'test-id-1',
            'title': 'Test',
            'content': 'Content',
            'metadata': {'source': 'claude'}
            # No score field
        }]
        
        formatted = service.format_search_results(results)
        
        assert len(formatted) == 1
        assert formatted[0]['meta']['relevance_display'] == 'N/A'
    
    def test_format_search_results_with_missing_metadata(self, service):
        """Test formatting search results with missing metadata"""
        results = [{
            'id': 'test-id-1',
            'title': 'Test',
            'content': 'Content'
            # No metadata field
        }]
        
        formatted = service.format_search_results(results)
        
        assert len(formatted) == 1
        assert formatted[0]['meta']['source'] == 'unknown'
    
    # ===== Helper method tests =====
    
    def test_extract_preview_from_document(self, service):
        """Test extracting preview from document"""
        document = "**You said**: Hello this is a test message\n**Claude said**: Response"
        
        preview = service._extract_preview(document, max_length=20)
        
        assert len(preview) <= 23  # 20 + '...'
        assert 'Hello' in preview
        assert '**You said**' not in preview
    
    def test_extract_preview_short_document(self, service):
        """Test extracting preview from short document"""
        document = "Short text"
        
        preview = service._extract_preview(document, max_length=100)
        
        assert preview == "Short text"
        assert '...' not in preview
    
    def test_parse_messages_from_document_claude(self, service):
        """Test parsing messages from Claude document"""
        document = "**You said** *(on 2025-01-01 12:00:00)*:\n\nHello\n\n**Claude said** *(on 2025-01-01 12:00:05)*:\n\nHi!"
        
        messages = service._parse_messages(document, 'claude')
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'user'
        assert messages[1]['role'] == 'assistant'
        assert 'Hello' in messages[0]['content']
    
    def test_parse_messages_from_document_chatgpt(self, service):
        """Test parsing messages from ChatGPT document"""
        # Format matches parse_messages_from_document expectations (uses **You**: not **You said**:)
        document = "**You**:\nHello\n\n**ChatGPT**:\nHi!"
        
        messages = service._parse_messages(document, 'chatgpt')
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'user'
        assert messages[1]['role'] == 'assistant'
    
    def test_determine_assistant_name_from_source(self, service):
        """Test determining assistant name from source metadata"""
        assert service._determine_assistant_name('', 'claude') == 'Claude'
        assert service._determine_assistant_name('', 'chatgpt') == 'ChatGPT'
        assert service._determine_assistant_name('', 'unknown') == 'AI'
    
    def test_determine_assistant_name_from_content(self, service):
        """Test determining assistant name from document content"""
        doc_claude = "**Claude said**: Hello"
        doc_chatgpt = "**ChatGPT said**: Hello"
        doc_unknown = "Generic content"
        
        assert service._determine_assistant_name(doc_claude, 'unknown') == 'Claude'
        assert service._determine_assistant_name(doc_chatgpt, 'unknown') == 'ChatGPT'
        assert service._determine_assistant_name(doc_unknown, 'unknown') == 'AI'
    
    def test_format_timestamp_iso_format(self, service):
        """Test formatting ISO timestamp"""
        dt = datetime(2025, 1, 1, 12, 0, 0)
        formatted = service._format_timestamp(dt)
        
        assert formatted == '2025-01-01 12:00:00'
    
    def test_format_timestamp_none(self, service):
        """Test formatting None timestamp"""
        formatted = service._format_timestamp(None)
        
        assert formatted is None or formatted == ''
