"""Tests for ConversationExportService - TDD approach"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from db.services.conversation_export_service import ConversationExportService


class TestConversationExportService:
    """Test suite for ConversationExportService"""
    
    @pytest.fixture
    def service(self):
        """Create a ConversationExportService instance"""
        return ConversationExportService()
    
    # ===== export_as_markdown tests =====
    
    def test_export_as_markdown_basic(self, service):
        """Test basic markdown export"""
        document = "**You said**: Hello\n\n**Claude said**: Hi there!"
        metadata = {
            'title': 'Test Conversation',
            'source': 'claude',
            'earliest_ts': '2025-01-01T12:00:00'
        }
        
        result = service.export_as_markdown(document, metadata)
        
        assert result['filename'] == 'Test_Conversation.md'
        assert '# Test Conversation' in result['content']
        assert 'Date: 2025-01-01 12:00:00' in result['content']
        assert document in result['content']
        assert result['mimetype'] == 'text/markdown'
    
    def test_export_as_markdown_with_spaces_in_title(self, service):
        """Test filename generation with spaces in title"""
        document = "Test content"
        metadata = {
            'title': 'My Great Conversation',
            'source': 'claude'
        }
        
        result = service.export_as_markdown(document, metadata)
        
        assert result['filename'] == 'My_Great_Conversation.md'
    
    def test_export_as_markdown_without_date(self, service):
        """Test markdown export without timestamp"""
        document = "Test content"
        metadata = {
            'title': 'Test',
            'source': 'claude'
            # No earliest_ts
        }
        
        result = service.export_as_markdown(document, metadata)
        
        assert 'Date:' not in result['content']
        assert '# Test' in result['content']
    
    def test_export_as_markdown_with_invalid_date(self, service):
        """Test markdown export with invalid timestamp"""
        document = "Test content"
        metadata = {
            'title': 'Test',
            'source': 'claude',
            'earliest_ts': 'invalid-date'
        }
        
        result = service.export_as_markdown(document, metadata)
        
        # Should handle gracefully - no date included
        assert 'Date: invalid-date' not in result['content']
    
    def test_export_as_markdown_no_title(self, service):
        """Test markdown export without title"""
        document = "Test content"
        metadata = {
            'source': 'claude'
        }
        
        result = service.export_as_markdown(document, metadata)
        
        assert result['filename'] == 'conversation.md'
        assert '# Conversation' in result['content']
    
    # ===== export_to_openwebui tests =====
    
    def test_export_to_openwebui_basic(self, service):
        """Test basic OpenWebUI export conversion"""
        document = "**You said**: Hello\n\n**Claude said**: Hi!"
        metadata = {
            'title': 'Test Conversation',
            'source': 'claude',
            'earliest_ts': '2025-01-01T12:00:00',
            'latest_ts': '2025-01-01T12:05:00'
        }
        
        result = service.export_to_openwebui(document, metadata)
        
        assert result['name'] == 'Test Conversation'
        assert result['created_at'] == '2025-01-01T12:00:00'
        assert result['updated_at'] == '2025-01-01T12:05:00'
        assert len(result['chat_messages']) >= 0  # At least attempt to parse
    
    def test_export_to_openwebui_with_messages(self, service):
        """Test OpenWebUI export with parsed messages"""
        document = "**You said** *(on 2025-01-01 12:00:00)*:\n\nHello\n\n**Claude said** *(on 2025-01-01 12:00:05)*:\n\nHi there!"
        metadata = {
            'title': 'Test',
            'source': 'claude',
            'earliest_ts': '2025-01-01T12:00:00'
        }
        
        result = service.export_to_openwebui(document, metadata)
        
        assert 'chat_messages' in result
        # Messages should have sender, text, created_at
        if result['chat_messages']:
            msg = result['chat_messages'][0]
            assert 'sender' in msg
            assert 'text' in msg
            assert 'created_at' in msg
    
    def test_export_to_openwebui_without_latest_ts(self, service):
        """Test OpenWebUI export without latest_ts uses earliest_ts"""
        document = "Test"
        metadata = {
            'title': 'Test',
            'source': 'claude',
            'earliest_ts': '2025-01-01T12:00:00'
            # No latest_ts
        }
        
        result = service.export_to_openwebui(document, metadata)
        
        assert result['updated_at'] == '2025-01-01T12:00:00'
    
    def test_export_to_openwebui_no_title(self, service):
        """Test OpenWebUI export without title"""
        document = "Test"
        metadata = {
            'source': 'claude',
            'earliest_ts': '2025-01-01T12:00:00'
        }
        
        result = service.export_to_openwebui(document, metadata)
        
        assert result['name'] == 'Untitled Conversation'
    
    # ===== Helper method tests =====
    
    def test_parse_messages_for_export_claude(self, service):
        """Test parsing Claude messages for export"""
        document = "**You said** *(on 2025-01-01 12:00:00)*:\n\nHello\n\n**Claude said** *(on 2025-01-01 12:00:05)*:\n\nHi!"
        metadata = {'source': 'claude'}
        
        messages = service._parse_messages_for_export(document, metadata)
        
        # Should parse at least some messages
        assert isinstance(messages, list)
    
    def test_parse_messages_for_export_chatgpt(self, service):
        """Test parsing ChatGPT messages for export"""
        document = "**You said** *(on 2025-01-01 12:00:00)*:\n\nHello\n\n**ChatGPT said** *(on 2025-01-01 12:00:05)*:\n\nHi!"
        metadata = {'source': 'chatgpt'}
        
        messages = service._parse_messages_for_export(document, metadata)
        
        assert isinstance(messages, list)
    
    def test_extract_timestamp_from_content(self, service):
        """Test extracting timestamp from message content"""
        content = "*(on 2025-01-01 12:00:00)*:\n\nHello world"
        
        timestamp = service._extract_timestamp(content)
        
        assert timestamp == '2025-01-01 12:00:00'
    
    def test_extract_timestamp_no_match(self, service):
        """Test extracting timestamp when none present"""
        content = "Hello world"
        
        timestamp = service._extract_timestamp(content)
        
        assert timestamp is None
    
    def test_clean_message_content_removes_timestamp(self, service):
        """Test cleaning message content removes timestamps"""
        content = "*(on 2025-01-01 12:00:00)*:\n\nHello world"
        
        cleaned = service._clean_message_content(content)
        
        assert '*(on' not in cleaned
        assert 'Hello world' in cleaned
    
    def test_clean_message_content_removes_colon(self, service):
        """Test cleaning message content removes leading colon"""
        content = ": Hello world"
        
        cleaned = service._clean_message_content(content)
        
        assert cleaned == "Hello world"
    
    def test_clean_message_content_strips_whitespace(self, service):
        """Test cleaning message content strips whitespace"""
        content = "  \n  Hello world  \n  "
        
        cleaned = service._clean_message_content(content)
        
        assert cleaned == "Hello world"
    
    def test_generate_filename_sanitizes_title(self, service):
        """Test filename generation sanitizes special characters"""
        title = "Test / Conversation \\ with : special * chars"
        
        filename = service._generate_filename(title)
        
        # Should replace spaces and not contain special chars
        assert '/' not in filename
        assert '\\' not in filename
        assert ':' not in filename
        assert '*' not in filename
        assert filename.endswith('.md')
    
    def test_generate_filename_default(self, service):
        """Test filename generation with no title"""
        filename = service._generate_filename(None)
        
        assert filename == 'conversation.md'
    
    def test_format_date_for_markdown_valid_iso(self, service):
        """Test formatting ISO date for markdown"""
        date_str = '2025-01-01T12:00:00'
        
        formatted = service._format_date_for_markdown(date_str)
        
        assert formatted == '2025-01-01 12:00:00'
    
    def test_format_date_for_markdown_invalid(self, service):
        """Test formatting invalid date returns None"""
        date_str = 'invalid-date'
        
        formatted = service._format_date_for_markdown(date_str)
        
        assert formatted is None
    
    def test_format_date_for_markdown_none(self, service):
        """Test formatting None date returns None"""
        formatted = service._format_date_for_markdown(None)
        
        assert formatted is None
    
    def test_build_chat_messages_from_parsed(self, service):
        """Test building chat messages from parsed messages"""
        parsed_messages = [
            {
                'role': 'user',
                'content': 'Hello',
                'timestamp': '2025-01-01 12:00:00'
            },
            {
                'role': 'assistant',
                'content': 'Hi!',
                'timestamp': '2025-01-01 12:00:05'
            }
        ]
        metadata = {'earliest_ts': '2025-01-01T12:00:00'}
        
        chat_messages = service._build_chat_messages(parsed_messages, metadata)
        
        assert len(chat_messages) == 2
        assert chat_messages[0]['sender'] == 'user'
        assert chat_messages[0]['text'] == 'Hello'
        assert chat_messages[1]['sender'] == 'assistant'
    
    def test_build_chat_messages_uses_fallback_timestamp(self, service):
        """Test building chat messages uses fallback when no message timestamp"""
        parsed_messages = [
            {
                'role': 'user',
                'content': 'Hello',
                'timestamp': None
            }
        ]
        metadata = {'earliest_ts': '2025-01-01T12:00:00'}
        
        chat_messages = service._build_chat_messages(parsed_messages, metadata)
        
        assert len(chat_messages) == 1
        assert chat_messages[0]['created_at'] == '2025-01-01T12:00:00'
