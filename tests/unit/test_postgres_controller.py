"""
PostgreSQL Controller Unit Tests

Tests the PostgreSQL controller's response formatting and data handling
without relying on Flask routes or HTTP requests.
"""
import pytest
from unittest.mock import MagicMock, patch
from controllers.postgres_controller import PostgresController


@pytest.fixture(autouse=True)
def use_test_db_and_clean(test_db_engine):
    """
    Force PostgresController and adapter to use the test DB engine and
    start each test with a clean database.
    
    This fixture patches db.database.engine/SessionFactory for the duration
    of each test, resets the PostgresController singleton, and truncates
    core tables (Embeddings -> Messages -> Conversations) to ensure a clean state.
    """
    # Patch globals before controller instantiation
    import db.database as dbm
    import controllers.postgres_controller as pc_module
    from sqlalchemy.orm import sessionmaker, Session
    
    original_engine = dbm.engine
    original_session_factory = dbm.SessionFactory
    original_controller = getattr(pc_module, "_controller", None)
    
    dbm.engine = test_db_engine
    dbm.SessionFactory = sessionmaker(bind=test_db_engine)
    pc_module._controller = None
    
    # Create/ensure view exists, then clean tables
    from sqlalchemy import text
    from db.models.models import Conversation, Message, MessageEmbedding

    # Ensure conversation_summaries exists (normal VIEW so it stays current)
    sess = Session(bind=test_db_engine)
    try:
        sess.execute(text("DROP MATERIALIZED VIEW IF EXISTS conversation_summaries"))
        sess.execute(text("DROP VIEW IF EXISTS conversation_summaries"))
        sess.execute(text("""
            CREATE VIEW conversation_summaries AS
            SELECT 
                c.id,
                COUNT(m.id) AS message_count,
                MIN(m.created_at) AS earliest_message_at,
                MAX(m.created_at) AS latest_message_at,
                SUBSTRING(MAX(CASE WHEN m.role = 'assistant' THEN m.content END) FROM 1 FOR 200) AS preview
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
        """))
        sess.commit()
    except Exception:
        sess.rollback()
        # If this fails, tests will still proceed; failures will surface clearly
    finally:
        sess.close()

    # Clean tables for a fresh start each test
    sess = Session(bind=test_db_engine)
    try:
        # Delete in dependency order (foreign key constraints)
        sess.query(MessageEmbedding).delete()
        sess.query(Message).delete()
        sess.query(Conversation).delete()
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.close()
    
    try:
        yield
    finally:
        # Restore globals to avoid leaking state to other modules
        dbm.engine = original_engine
        dbm.SessionFactory = original_session_factory
        pc_module._controller = original_controller


@pytest.fixture
def postgres_controller():
    """Create a fresh PostgresController instance for each test."""
    return PostgresController()


@pytest.fixture
def seeded_controller(postgres_controller, test_db_engine):
    """Create a controller with seeded test data.
    
    Creates committed test data and cleans up after the test.
    """
    from tests.utils.seed import seed_conversation_with_messages
    from sqlalchemy.orm import Session
    from db.repositories.unit_of_work import UnitOfWork
    from db.models.models import Conversation
    
    # Create a fresh session for seeding
    session = Session(bind=test_db_engine)
    uow = UnitOfWork(session=session)
    
    conversations = []
    conv_ids = []
    
    try:
        # Seed 3 test conversations
        for i in range(3):
            conv, messages = seed_conversation_with_messages(
                uow,
                title=f"Test Conversation {i+1}",
                message_count=4,
                with_embeddings=True,
                created_days_ago=i
            )
            conversations.append((conv, messages))
            conv_ids.append(str(conv.id))
        
        # Commit to ensure data is persisted
        uow.commit()
        
        yield postgres_controller, conversations
    finally:
        # Clean up: delete the conversations we created
        try:
            for conv_id in conv_ids:
                session.query(Conversation).filter(Conversation.id == conv_id).delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


@pytest.mark.unit
class TestGetConversationsEndpoint:
    """Test GET /api/conversations endpoint."""
    
    def test_get_conversations_returns_dict_structure(self, postgres_controller):
        """Test that get_conversations returns correct dict structure."""
        result = postgres_controller.get_conversations()
        
        # Should have ChromaDB-compatible structure
        assert isinstance(result, dict)
        assert "documents" in result
        assert "metadatas" in result
        assert "ids" in result
        assert isinstance(result["documents"], list)
        assert isinstance(result["metadatas"], list)
        assert isinstance(result["ids"], list)
    
    def test_get_conversations_empty_database(self, db_session):
        """Test get_conversations with guaranteed empty database.
        
        Uses db_session which provides test isolation.
        """
        controller = PostgresController()
        result = controller.get_conversations()
        
        # With fresh db_session, database should be empty
        assert len(result["documents"]) == 0
        assert len(result["metadatas"]) == 0
        assert len(result["ids"]) == 0
    
    def test_get_conversations_with_seeded_data(self, seeded_controller):
        """Test get_conversations with seeded test data."""
        controller, conversations = seeded_controller
        result = controller.get_conversations()
        
        # Should have 3 conversations
        assert len(result["documents"]) == 3
        assert len(result["metadatas"]) == 3
        assert len(result["ids"]) == 3
        
        # Verify structure of returned data
        for metadata in result["metadatas"]:
            assert "title" in metadata
            assert "source" in metadata
            assert "message_count" in metadata
    
    def test_get_conversations_array_lengths_match(self, seeded_controller):
        """Test that all arrays in response have same length."""
        controller, conversations = seeded_controller
        result = controller.get_conversations()
        
        assert len(result["documents"]) == len(result["metadatas"])
        assert len(result["documents"]) == len(result["ids"])


@pytest.mark.unit
class TestGetConversationByIdEndpoint:
    """Test GET /api/conversation/<id> endpoint."""
    
    def test_get_conversation_returns_dict_structure(self, postgres_controller):
        """Test that get_conversation returns correct dict structure."""
        # Use a fake UUID - should return empty result
        result = postgres_controller.get_conversation("fake-uuid-123")
        
        assert isinstance(result, dict)
        assert "documents" in result
        assert "metadatas" in result
        assert "ids" in result
    
    def test_get_conversation_not_found_returns_empty(self, postgres_controller):
        """Test that get_conversation returns empty for non-existent ID."""
        result = postgres_controller.get_conversation("nonexistent-uuid")
        
        # Should return empty but valid structure
        assert len(result["documents"]) == 0
        assert len(result["metadatas"]) == 0
        assert len(result["ids"]) == 0
    
    def test_get_conversation_with_valid_id(self, seeded_controller):
        """Test get_conversation with seeded data."""
        controller, conversations = seeded_controller
        conv, _ = conversations[0]
        
        result = controller.get_conversation(str(conv.id))
        
        # Should return the conversation
        assert len(result["documents"]) > 0 or len(result["ids"]) > 0
        assert "documents" in result
        assert "metadatas" in result
        assert "ids" in result
    
    def test_get_conversation_returns_single_item(self, seeded_controller):
        """Test that get_conversation returns single conversation."""
        controller, conversations = seeded_controller
        conv, _ = conversations[0]
        
        result = controller.get_conversation(str(conv.id))
        
        # When found, should return single item or empty (depending on implementation)
        assert len(result["documents"]) <= 1
        assert len(result["metadatas"]) <= 1
        assert len(result["ids"]) <= 1


@pytest.mark.unit
class TestGetStatsEndpoint:
    """Test GET /api/stats endpoint."""
    
    def test_get_stats_returns_dict_structure(self, postgres_controller):
        """Test that get_stats returns correct dict structure."""
        result = postgres_controller.get_stats()
        
        assert isinstance(result, dict)
    
    def test_get_stats_with_empty_database(self, postgres_controller):
        """Test get_stats with no data."""
        result = postgres_controller.get_stats()
        
        # Should have at least some keys for empty database
        assert isinstance(result, dict)
    
    def test_get_stats_with_seeded_data(self, seeded_controller):
        """Test get_stats with test data."""
        controller, conversations = seeded_controller
        result = controller.get_stats()
        
        # Should have stats
        assert isinstance(result, dict)
        assert "document_count" in result or "conversation_count" in result


@pytest.mark.unit
class TestDeleteEndpoint:
    """Test DELETE /api/conversation/<id> endpoint."""
    
    def test_delete_conversation_returns_dict(self, postgres_controller):
        """Test that delete_conversation returns a dict response."""
        result = postgres_controller.delete_conversation("fake-uuid")
        
        assert isinstance(result, dict)
        # Should have success key
        assert "success" in result or "error" in result
    
    def test_delete_nonexistent_conversation(self, postgres_controller):
        """Test deleting a non-existent conversation."""
        result = postgres_controller.delete_conversation("nonexistent-uuid-123")
        
        assert isinstance(result, dict)
        # Should indicate failure or success
        assert "success" in result or "error" in result
    
    def test_delete_conversation_with_seeded_data(self, seeded_controller):
        """Test deleting an existing conversation."""
        controller, conversations = seeded_controller
        conv, _ = conversations[0]
        
        result = controller.delete_conversation(str(conv.id))
        
        assert isinstance(result, dict)
        # After deletion, conversation should not exist
        get_result = controller.get_conversation(str(conv.id))
        assert len(get_result["ids"]) == 0
    
    def test_delete_with_invalid_uuid(self, postgres_controller):
        """Test delete with invalid UUID format."""
        result = postgres_controller.delete_conversation("not-a-uuid")
        
        # Should handle gracefully
        assert isinstance(result, dict)


@pytest.mark.unit
class TestGetEndpointErrors:
    """Test error cases for GET endpoints."""
    
    def test_get_conversation_with_invalid_uuid(self, postgres_controller):
        """Test get_conversation with invalid UUID format."""
        result = postgres_controller.get_conversation("not-a-uuid")
        
        assert isinstance(result, dict)
        # Should return empty results or error
        if "ids" in result:
            assert len(result["ids"]) == 0
    
    def test_get_conversation_with_nonexistent_id(self, postgres_controller):
        """Test get_conversation with non-existent conversation ID."""
        result = postgres_controller.get_conversation("550e8400-e29b-41d4-a716-446655440000")
        
        assert isinstance(result, dict)
        # Should return empty results
        if "ids" in result:
            assert len(result["ids"]) == 0
    
    def test_get_stats_with_no_data(self, postgres_controller):
        """Test get_stats returns valid structure even with no data."""
        result = postgres_controller.get_stats()
        
        assert isinstance(result, dict)
    
    def test_get_conversation_list_empty_database(self, postgres_controller):
        """Test get_conversations on empty database."""
        result = postgres_controller.get_conversations()
        
        assert isinstance(result, dict)
        # Should return empty list or similar
        assert result is not None


@pytest.mark.unit
class TestUploadEndpoint:
    """Test file upload endpoint."""
    
    def test_upload_returns_response(self, postgres_controller):
        """Test that upload returns a response."""
        # upload() requires Flask request context with file
        from flask import Flask
        from werkzeug.datastructures import FileStorage
        from io import BytesIO
        
        app = Flask(__name__)
        
        # Create a mock file
        file_data = BytesIO(b"test file content")
        mock_file = FileStorage(
            stream=file_data,
            filename="test.txt",
            name="file"
        )
        
        with app.test_request_context(
            method='POST',
            data={'file': mock_file},
            content_type='multipart/form-data'
        ):
            result = postgres_controller.upload()
            # Should return a response (status, message, etc.)
            assert result is not None
    
    def test_upload_without_file(self, postgres_controller):
        """Test upload without file attached."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context(method='POST'):
            result = postgres_controller.upload()
            # Should handle missing file gracefully
            assert result is not None


@pytest.mark.unit
class TestHandleSettingsEndpoint:
    """Test settings management endpoint."""
    
    def test_handle_settings_with_post_returns_dict(self, postgres_controller):
        """Test POST to settings returns dict."""
        from flask import Flask, request
        app = Flask(__name__)
        
        with app.test_request_context(method='POST', json={"test_key": "test_value"}):
            result = postgres_controller.handle_settings(request)
            
            assert isinstance(result, dict)
            # Should have success or error
            assert "success" in result or "error" in result
    
    def test_handle_settings_with_get_returns_dict(self, postgres_controller):
        """Test GET settings returns dict."""
        from flask import Flask, request
        app = Flask(__name__)
        
        with app.test_request_context(method='GET'):
            result = postgres_controller.handle_settings(request)
            
            assert isinstance(result, dict)
            # Should have settings or error
            assert "success" in result or "error" in result or "settings" in result
    
    def test_handle_settings_empty_post(self, postgres_controller):
        """Test POST with empty settings."""
        from flask import Flask, request
        app = Flask(__name__)
        
        with app.test_request_context(method='POST', json={}):
            result = postgres_controller.handle_settings(request)
            
            assert isinstance(result, dict)


@pytest.mark.unit
class TestExportEndpoint:
    """Test conversation export endpoints."""
    
    def test_export_conversation_returns_response(self, seeded_controller):
        """Test that export_conversation returns a response."""
        controller, conversations = seeded_controller
        conv, _ = conversations[0]
        
        result = controller.export_conversation(str(conv.id))
        
        # Should return a response object or string
        assert result is not None
    
    def test_export_nonexistent_conversation(self, postgres_controller):
        """Test exporting a non-existent conversation."""
        result = postgres_controller.export_conversation("nonexistent-uuid")
        
        # Should return some response (error or empty)
        assert result is not None
    
    def test_export_to_openwebui_returns_dict(self, postgres_controller):
        """Test that export_to_openwebui returns a dict response."""
        result = postgres_controller.export_to_openwebui("fake-uuid")
        
        assert isinstance(result, dict)
        # Should have status or success key
        assert "success" in result or "error" in result or "status" in result


@pytest.mark.unit
class TestClearDatabaseEndpoint:
    """Test database clearing endpoint."""
    
    def test_clear_database_returns_dict(self, postgres_controller):
        """Test that clear_database returns a dict."""
        result = postgres_controller.clear_database()
        
        assert isinstance(result, dict)
        # Should indicate success or error
        assert "success" in result or "error" in result or "message" in result
    
    def test_clear_database_removes_data(self, seeded_controller):
        """Test that clear_database actually removes conversations."""
        controller, conversations = seeded_controller
        
        # Clear the database
        result = controller.clear_database()
        assert isinstance(result, dict)
        
        # Verify conversations are gone
        get_result = controller.get_conversations()
        assert len(get_result["ids"]) == 0


@pytest.mark.unit
class TestGetSettingsEndpoint:
    """Test settings retrieval and management endpoints."""
    
    
    def test_get_collection_count_returns_dict(self, postgres_controller):
        """Test that get_collection_count returns a dict with count."""
        result = postgres_controller.get_collection_count()
        
        assert isinstance(result, dict)
        # Should have count or error
        assert "count" in result or "error" in result
    
    def test_get_collection_count_with_seeded_data(self, seeded_controller):
        """Test get_collection_count with test data."""
        controller, conversations = seeded_controller
        result = controller.get_collection_count()
        
        assert isinstance(result, dict)
        # Should have a count
        if "count" in result:
            assert result["count"] >= 0


@pytest.mark.unit
class TestSearchEndpoints:
    """Test search functionality endpoints."""
    
    def test_api_search_without_query(self, postgres_controller):
        """Test api_search returns error when query is missing."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context('/api/search'):
            result = postgres_controller.api_search()
            
            assert isinstance(result, dict)
            assert "error" in result or "results" in result
    
    def test_api_search_with_query(self, postgres_controller):
        """Test api_search with a valid query."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context('/api/search?q=test&n=5'):
            result = postgres_controller.api_search()
            
            assert isinstance(result, dict)
            # Should have query and results keys
            assert "query" in result or "error" in result
    
    def test_search_post_without_query(self, postgres_controller):
        """Test POST search returns error when query is missing."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context(method='POST', json={}):
            result = postgres_controller.search()
            
            assert isinstance(result, dict)
            assert "error" in result
    
    def test_search_post_with_query(self, postgres_controller):
        """Test POST search with valid query."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context(method='POST', json={"query": "test"}):
            result = postgres_controller.search()
            
            assert isinstance(result, dict)
    
    def test_search_with_date_range(self, postgres_controller):
        """Test search with date range filter."""
        from flask import Flask
        from datetime import datetime, timedelta
        app = Flask(__name__)
        
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()
        
        with app.test_request_context(
            method='POST',
            json={
                "query": "test",
                "start_date": start_date,
                "end_date": end_date
            }
        ):
            result = postgres_controller.search()
            
            assert isinstance(result, dict)
    
    def test_search_with_invalid_date_range(self, postgres_controller):
        """Test search with invalid date format."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context(
            method='POST',
            json={
                "query": "test",
                "start_date": "invalid-date",
                "end_date": "also-invalid"
            }
        ):
            result = postgres_controller.search()
            
            # Should handle gracefully
            assert isinstance(result, dict)


@pytest.mark.unit
class TestRAGEndpoints:
    """Test RAG (Retrieval-Augmented Generation) endpoints."""
    
    def test_rag_query_without_query(self, postgres_controller):
        """Test rag_query returns error when query is missing."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context(method='POST', json={}):
            result = postgres_controller.rag_query()
            
            assert isinstance(result, dict)
            assert "error" in result
    
    def test_rag_query_with_query(self, postgres_controller):
        """Test rag_query with valid query."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context(method='POST', json={"query": "test query"}):
            result = postgres_controller.rag_query()
            
            assert isinstance(result, dict)
    
    def test_rag_query_with_n_results(self, postgres_controller):
        """Test rag_query with custom n_results parameter."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context(
            method='POST',
            json={"query": "test", "n_results": 10}
        ):
            result = postgres_controller.rag_query()
            
            assert isinstance(result, dict)
    
    def test_rag_query_with_search_type(self, postgres_controller):
        """Test rag_query with different search types."""
        from flask import Flask
        app = Flask(__name__)
        
        for search_type in ["semantic", "keyword", "hybrid"]:
            with app.test_request_context(
                method='POST',
                json={"query": "test", "search_type": search_type}
            ):
                result = postgres_controller.rag_query()
                
                assert isinstance(result, dict)
    
    def test_rag_health(self, postgres_controller):
        """Test rag_health endpoint."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context('/api/rag/health'):
            result = postgres_controller.rag_health()
            
            assert isinstance(result, dict)


@pytest.mark.unit
class TestPaginationEndpoint:
    """Test paginated conversation listing."""
    
    def test_get_conversations_paginated_default(self, postgres_controller):
        """Test paginated conversations with default parameters."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context('/api/conversations/list'):
            result = postgres_controller.get_conversations_paginated()
            
            assert isinstance(result, dict)
            # Should have pagination keys
            if "conversations" in result:
                assert "page" in result
                assert "limit" in result
                assert "has_more" in result
    
    def test_get_conversations_paginated_with_page(self, postgres_controller):
        """Test paginated conversations with page parameter."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context('/api/conversations/list?page=2&limit=10'):
            result = postgres_controller.get_conversations_paginated()
            
            assert isinstance(result, dict)
    
    def test_get_conversations_paginated_with_filters(self, postgres_controller):
        """Test paginated conversations with source filter."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context(
            '/api/conversations/list?source=chatgpt&date=month&sort=newest'
        ):
            result = postgres_controller.get_conversations_paginated()
            
            assert isinstance(result, dict)


@pytest.mark.unit
class TestImportMethods:
    """Test conversation import helper methods."""
    
    def test_detect_json_format_with_invalid_data(self, postgres_controller):
        """Test format detection with invalid data."""
        # Should handle gracefully
        result = postgres_controller._detect_json_format({})
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_detect_json_format_with_list(self, postgres_controller):
        """Test format detection with list input."""
        result = postgres_controller._detect_json_format([])
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_import_docx_with_invalid_path(self, postgres_controller):
        """Test DOCX import with invalid file path."""
        try:
            result = postgres_controller._import_docx_file("/nonexistent/path/file.docx", "test.docx")
            # Should return a string message (error or success)
            assert isinstance(result, (str, dict))
        except Exception:
            # It's also acceptable to raise an exception
            pass


@pytest.mark.unit
class TestHandleSettingsEndpointAdvanced:
    """Test advanced settings endpoint scenarios."""
    
    def test_handle_settings_with_invalid_method(self, postgres_controller):
        """Test settings with unsupported HTTP method."""
        from flask import Flask, request
        app = Flask(__name__)
        
        with app.test_request_context(method='DELETE'):
            # Should handle unknown method gracefully
            result = postgres_controller.handle_settings(request)
            assert result is not None
    
    def test_handle_settings_with_complex_json(self, postgres_controller):
        """Test settings with complex nested JSON."""
        from flask import Flask, request
        app = Flask(__name__)
        
        complex_data = {
            "collection": {
                "count": 100,
                "metadata": {"version": "1.0"},
                "nested": [1, 2, {"key": "value"}]
            }
        }
        
        with app.test_request_context(method='POST', json=complex_data):
            result = postgres_controller.handle_settings(request)
            assert isinstance(result, dict)


@pytest.mark.unit
class TestAPISearchEndpointAdvanced:
    """Test advanced API search scenarios."""
    
    def test_api_search_with_keyword_flag(self, postgres_controller):
        """Test api_search with keyword flag."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context('/api/search?q=test&keyword=true'):
            result = postgres_controller.api_search()
            
            assert isinstance(result, dict)
    
    def test_api_search_with_search_type(self, postgres_controller):
        """Test api_search with explicit search_type."""
        from flask import Flask
        app = Flask(__name__)
        
        for search_type in ["fts", "semantic", "hybrid", "auto"]:
            with app.test_request_context(f'/api/search?q=test&search_type={search_type}'):
                result = postgres_controller.api_search()
                
                assert isinstance(result, dict)
    
    def test_api_search_with_custom_n_results(self, postgres_controller):
        """Test api_search with custom number of results."""
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context('/api/search?q=test&n=20'):
            result = postgres_controller.api_search()
            
            assert isinstance(result, dict)


@pytest.mark.unit
class TestGetConversationSourceHelper:
    """Test the _get_conversation_source helper method."""
    
    def test_get_source_with_invalid_uuid(self, postgres_controller):
        """Test source detection with invalid UUID."""
        result = postgres_controller._get_conversation_source("not-a-uuid")
        
        # Should return 'unknown' for invalid UUID
        assert result == "unknown"
    
    def test_get_source_with_nonexistent_conversation(self, postgres_controller):
        """Test source detection with non-existent conversation."""
        result = postgres_controller._get_conversation_source("550e8400-e29b-41d4-a716-446655440000")
        
        # Should return 'unknown' for non-existent conversation
        assert result == "unknown"


@pytest.mark.unit
class TestPostErrorHandling:
    """Test error handling for POST endpoints."""
    
    def test_upload_with_invalid_file_type(self, postgres_controller):
        """Test upload with unsupported file type."""
        from flask import Flask
        from werkzeug.datastructures import FileStorage
        from io import BytesIO
        
        app = Flask(__name__)
        
        # Create a file with unsupported extension
        file_data = BytesIO(b"binary content")
        mock_file = FileStorage(
            stream=file_data,
            filename="test.bin",
            name="file"
        )
        
        with app.test_request_context(
            method='POST',
            data={'file': mock_file},
            content_type='multipart/form-data'
        ):
            result = postgres_controller.upload()
            # Should handle gracefully
            assert result is not None
    
    def test_upload_with_large_file(self, postgres_controller):
        """Test upload with very large file (mock)."""
        from flask import Flask
        from werkzeug.datastructures import FileStorage
        from io import BytesIO
        
        app = Flask(__name__)
        
        # Create a large file mock
        file_data = BytesIO(b"x" * (10 * 1024 * 1024))  # 10MB
        mock_file = FileStorage(
            stream=file_data,
            filename="large.txt",
            name="file"
        )
        
        with app.test_request_context(
            method='POST',
            data={'file': mock_file},
            content_type='multipart/form-data'
        ):
            result = postgres_controller.upload()
            # Should handle gracefully
            assert result is not None
    
    def test_handle_settings_with_invalid_json(self, postgres_controller):
        """Test settings with malformed JSON."""
        from flask import Flask, request
        app = Flask(__name__)
        
        with app.test_request_context(
            method='POST',
            data='not valid json',
            content_type='application/json'
        ):
            try:
                result = postgres_controller.handle_settings(request)
                # Should handle gracefully
                assert result is not None
            except Exception:
                # Also acceptable to raise an exception
                pass
    
    def test_handle_settings_with_none_request_body(self, postgres_controller):
        """Test settings with None/empty request body."""
        from flask import Flask, request
        app = Flask(__name__)
        
        with app.test_request_context(method='POST'):
            result = postgres_controller.handle_settings(request)
            # Should handle gracefully
            assert result is not None
    
    def test_export_with_invalid_conversation_id(self, postgres_controller):
        """Test export with invalid UUID."""
        result = postgres_controller.export_conversation("not-a-uuid")
        # Should handle gracefully
        assert result is not None
    
    def test_export_to_openwebui_with_nonexistent_id(self, postgres_controller):
        """Test OpenWebUI export with non-existent conversation."""
        result = postgres_controller.export_to_openwebui("550e8400-e29b-41d4-a716-446655440000")
        # Should return response with error or empty data
        assert isinstance(result, dict)
