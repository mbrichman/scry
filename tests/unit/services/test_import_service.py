"""
Unit tests for ConversationImportService.

Tests the import service without Flask dependency or actual file I/O.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from db.services.import_service import ConversationImportService
from db.models.import_result import ImportResult


@pytest.fixture
def import_service():
    """Provide a fresh import service instance for each test."""
    return ConversationImportService()


class TestImportResultDataclass:
    """Test ImportResult dataclass."""
    
    def test_import_result_initialization(self):
        """Test ImportResult initializes with defaults."""
        result = ImportResult()
        
        assert result.imported_count == 0
        assert result.skipped_duplicates == 0
        assert result.failed_count == 0
        assert result.format_detected == "Unknown"
        assert result.messages == []
        assert result.errors == []
    
    def test_import_result_str_representation(self):
        """Test ImportResult string representation."""
        result = ImportResult(
            imported_count=5,
            skipped_duplicates=2,
            format_detected="ChatGPT"
        )
        
        result_str = str(result)
        assert "5" in result_str
        assert "2" in result_str
        assert "ChatGPT" in result_str
    
    def test_import_result_to_dict(self):
        """Test ImportResult converts to dict for JSON serialization."""
        result = ImportResult(
            imported_count=3,
            skipped_duplicates=1,
            format_detected="Claude",
            messages=["Test message"],
            errors=[]
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["imported_count"] == 3
        assert result_dict["skipped_duplicates"] == 1
        assert result_dict["format_detected"] == "Claude"
        assert "summary" in result_dict
        assert isinstance(result_dict["summary"], str)


class TestImportServiceInitialization:
    """Test service initialization."""
    
    def test_service_initializes(self, import_service):
        """Test ConversationImportService initializes without error."""
        assert import_service is not None


class TestFormatDetection:
    """Test format detection functionality."""
    
    def test_detect_format_with_chatgpt_data(self, import_service):
        """Test format detection for ChatGPT format."""
        chatgpt_data = {
            "conversations": [
                {
                    "id": "conv-123",
                    "title": "Python Help",
                    "mapping": {
                        "node-1": {
                            "message": {
                                "content": {"parts": ["Hello"]},
                                "role": "user"
                            }
                        }
                    },
                    "create_time": 1695000000,
                    "update_time": 1695001000
                }
            ]
        }
        
        conversations, format_type = import_service._detect_format(chatgpt_data)
        
        assert format_type == "ChatGPT"
        assert len(conversations) == 1
    
    def test_detect_format_with_claude_data(self, import_service):
        """Test format detection for Claude format."""
        claude_data = {
            "conversations": [
                {
                    "uuid": "uuid-123",
                    "name": "Claude Conversation",
                    "chat_messages": [
                        {
                            "uuid": "msg-1",
                            "text": "Hello",
                            "created_at": "2023-09-18T10:00:00Z"
                        }
                    ],
                    "created_at": "2023-09-18T10:00:00Z",
                    "updated_at": "2023-09-18T10:05:00Z"
                }
            ]
        }
        
        conversations, format_type = import_service._detect_format(claude_data)
        
        assert format_type == "Claude"
        assert len(conversations) == 1
    
    def test_detect_format_with_unknown_data(self, import_service):
        """Test format detection returns Unknown for unrecognized format."""
        unknown_data = {
            "conversations": [
                {
                    "random_field": "value",
                    "unrecognized": "format"
                }
            ]
        }
        
        conversations, format_type = import_service._detect_format(unknown_data)
        
        assert format_type == "Unknown"
        assert len(conversations) == 1


class TestImportJsonData:
    """Test JSON import functionality."""
    
    @patch('db.services.import_service.get_unit_of_work')
    def test_import_json_with_unknown_format(self, mock_uow, import_service):
        """Test import_json_data raises error for unknown format."""
        unknown_data = {
            "conversations": [
                {
                    "random_field": "value",
                    "unrecognized": "format"
                }
            ]
        }
        
        with pytest.raises(ValueError):
            import_service.import_json_data(unknown_data)
    
    @patch('db.services.import_service.get_unit_of_work')
    def test_import_json_with_empty_conversations(self, mock_uow, import_service):
        """Test import_json_data with empty conversations list."""
        empty_data = {"conversations": []}
        
        with pytest.raises(ValueError):
            import_service.import_json_data(empty_data)


class TestBuildExistingConversationsMap:
    """Test duplicate detection map building."""
    
    @patch('db.services.import_service.get_unit_of_work')
    def test_build_existing_conversations_map_empty_db(self, mock_uow, import_service):
        """Test building map with no existing conversations."""
        # Mock empty database
        mock_unit_of_work = MagicMock()
        mock_unit_of_work.conversations.get_all.return_value = []
        mock_uow.return_value.__enter__.return_value = mock_unit_of_work
        
        result_map = import_service._build_existing_conversations_map()
        
        assert isinstance(result_map, dict)
        assert len(result_map) == 0
    
    @patch('db.services.import_service.get_unit_of_work')
    def test_build_existing_conversations_map_with_data(self, mock_uow, import_service):
        """Test building map with existing conversations."""
        # Mock existing conversation
        mock_conv = Mock()
        mock_conv.id = "conv-uuid-123"
        
        mock_msg = Mock()
        mock_msg.content = "Test content"
        mock_msg.message_metadata = {'original_conversation_id': 'original-123'}
        
        mock_unit_of_work = MagicMock()
        mock_unit_of_work.conversations.get_all.return_value = [mock_conv]
        mock_unit_of_work.messages.get_by_conversation.return_value = [mock_msg]
        mock_uow.return_value.__enter__.return_value = mock_unit_of_work
        
        result_map = import_service._build_existing_conversations_map()
        
        assert isinstance(result_map, dict)
        assert 'original-123' in result_map


class TestImportResultMessages:
    """Test ImportResult message formatting."""
    
    def test_import_result_with_all_counts(self):
        """Test ImportResult with imported, skipped, and failed conversations."""
        result = ImportResult(
            imported_count=10,
            skipped_duplicates=3,
            failed_count=1,
            format_detected="ChatGPT"
        )
        
        result_str = str(result)
        
        assert "10" in result_str
        assert "3" in result_str
        assert "1" in result_str
        assert "ChatGPT" in result_str
    
    def test_import_result_messages_list(self):
        """Test ImportResult maintains list of messages."""
        result = ImportResult()
        result.messages.append("Starting import")
        result.messages.append("Processing conversation")
        
        assert len(result.messages) == 2
        assert result.messages[0] == "Starting import"
        assert result.messages[1] == "Processing conversation"
    
    def test_import_result_errors_list(self):
        """Test ImportResult maintains list of errors."""
        result = ImportResult()
        result.errors.append("Error 1")
        result.errors.append("Error 2")
        
        assert len(result.errors) == 2
        assert result.errors[0] == "Error 1"


class TestImportServiceIntegration:
    """Integration tests for ConversationImportService."""
    
    def test_service_has_all_public_methods(self, import_service):
        """Test service has expected public methods."""
        assert hasattr(import_service, 'import_json_data')
        assert hasattr(import_service, 'import_docx_file')
        assert callable(import_service.import_json_data)
        assert callable(import_service.import_docx_file)
    
    def test_service_has_private_helper_methods(self, import_service):
        """Test service has expected private helper methods."""
        assert hasattr(import_service, '_detect_format')
        assert hasattr(import_service, '_build_existing_conversations_map')
        assert hasattr(import_service, '_import_single_conversation')
        assert callable(import_service._detect_format)
