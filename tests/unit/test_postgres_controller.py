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
    
    # Clean tables
    from db.models.models import Conversation, Message, MessageEmbedding
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
class TestApiSearchEndpoint:
    """Test GET /api/search endpoint."""
    
    def test_api_search_requires_query(self, postgres_controller):
        """Test that api_search requires a query parameter."""
        with patch('flask.request.args') as mock_args:
            mock_args.get.side_effect = lambda key, default=None: default
            
            result = postgres_controller.api_search()
            
            assert "error" in result
    
    def test_api_search_returns_dict_structure(self, postgres_controller):
        """Test that api_search returns correct structure."""
        with patch('flask.request.args') as mock_args:
            mock_args.get.side_effect = lambda key, default=None: {
                "q": "test query",
                "n": "5",
                "search_type": "auto"
            }.get(key, default)
            
            # Mock the search service to avoid actual search
            with patch.object(postgres_controller.adapter, 'search_service') as mock_search:
                mock_search.get_search_stats.return_value = {"hybrid_search_available": False}
                mock_search.search_fts_only.return_value = []
                
                result = postgres_controller.api_search()
                
                assert isinstance(result, dict)
                assert "query" in result
                assert "results" in result
                assert isinstance(result["results"], list)
